#!/usr/bin/env python3
# norma-lit-review · 正式刊出文献检索与核验脚本（OpenAlex / Crossref / OpenCitations）
# Copyright (C) 2026 Norma
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details:
# <https://www.gnu.org/licenses/>.
"""正式刊出文献检索与核验（仅 stdlib，无需 API key，带限速）。

四个子命令
----------
search   OpenAlex 正式刊出检索（含被引数 / 期刊 / OA 状态）  → P2 多库检索
verify   Crossref 按 DOI 核验 + 0.70 标题相似度交叉校验      → P6 真实性核验
citing   OpenCitations 引文关系（施引 / 参考文献）           → T4 文献计量
enrich   按 DOI 从 OpenAlex 取规范元数据与被引数             → P6 补强 / T4 计量

关于邮箱（重要）
----------------
OpenAlex 与 Crossref 提供 "polite pool"（更宽松的限流），需要一个**真实个人邮箱**：
它不是注册、不是 API key，官方仅用作限流时的联系方式，也不会发营销邮件。

获取顺序（先命中先用）：
  1. `--mailto` 命令行参数
  2. 环境变量 `LIT_MAILTO`（次选 `OPENALEX_MAILTO` / `CROSSREF_MAILTO`）
  3. 交互式提示（仅当标准输入为交互终端时询问；不会落盘、不写进任何配置文件）
  4. 以上都没有 → 使用**公共池**（限速更严），并在 stderr 明确告警

若在脚本化/非交互环境下运行，第 3 步会自动跳过（避免卡住），
此时建议预先设置环境变量：`export LIT_MAILTO=you@example.com`

设计约束
--------
- 只用 Python 标准库（urllib / json / difflib），无需 pip、无需 venv。
- 三个 API **均免费、无需注册、无需 API key**。
- **限速为默认行为**：串行请求 + 相邻间隔 sleep；429/5xx 指数退避重试。
- 输出统一为 UTF-8 JSON，可直接喂给 raw_literature_list.json（search）
  或核验报告（verify）。

已知服务端实况（2026-09 实测，影响用法）
----------------------------------------
- OpenCitations 的 `metadata` 端点**已下线，返回 HTTP 410 Gone** → 不要用。
  取元数据请用 `enrich`（走 OpenAlex）。
- OpenCitations 的 `citations`（施引）对**高被引 DOI 响应极慢**（实测 60s 超时）。
  属预期行为，脚本会报 TIMEOUT 并建议降级，不代表脚本故障。
- OpenCitations 返回**空数组 ≠ 零被引**，只表示"未被 COCI 索引"，
  不得据此判定论文不存在或无影响力。

用法示例
--------
  # P2 正式刊出检索：具身智能，2022 年后，按被引排序，取 30 篇
  python fetch_lit.py search --query "embodied intelligence" \
      --year-from 2022 --sort cited_by_count --max-results 30 --output raw_openalex.json

  # 只打印最终 URL（用于写进检索日志 search_log.md，不发起请求）
  python fetch_lit.py search --query "machine vision" --dry-run --no-prompt

  # P6 DOI 核验（refs.json = [{"ref":"[1]","doi":"10.1038/xxx","title":"..."}]）
  python fetch_lit.py verify --input refs.json --output doi_verify.json

  # T4 引文计量：谁引了它 / 它引了谁
  python fetch_lit.py citing --doi 10.1038/nature14539 --direction both

  # 按 DOI 取规范元数据与被引数
  python fetch_lit.py enrich --dois 10.1038/nature14539,10.1109/TRO.2024.1234567

退出码
------
  0 成功；1 输入/用法错误；2 网络或服务端错误且重试耗尽（或超时）。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from difflib import SequenceMatcher

OPENALEX_API = "https://api.openalex.org/works"
CROSSREF_API = "https://api.crossref.org/works"
COCI_API = "https://opencitations.net/index/coci/api/v1"

TITLE_SIM_THRESHOLD = 0.70
DEFAULT_TIMEOUT = 30
DEFAULT_RETRIES = 3
DEFAULT_PER_PAGE = 25          # OpenAlex 单页条数（上限 200）
DEFAULT_MAX_RESULTS = 50

# 各子命令默认限速（秒/请求）。依据官方政策取保守值：
#   OpenAlex 官方允许 10 req/s（polite pool）→ 0.5s 远有余量
#   Crossref polite 池单条 10 req/s → 0.5s
#   OpenCitations 建议 1–5 req/s 且实测响应慢 → 1.5s
SLEEP_DEFAULTS = {
    "search": 0.5,
    "verify": 0.5,
    "citing": 1.5,
    "enrich": 0.5,
}
CITING_TIMEOUT = 60            # 引文端点容易慢，单独放宽

USER_AGENT_BASE = "norma-lit-review/1.0 (+OpenAlex/Crossref/OpenCitations metadata fetcher; stdlib urllib)"


class LitError(RuntimeError):
    """网络或服务端错误且重试耗尽。"""


# ---------------------------------------------------------------- 基础工具

def _clean(text):
    if not text:
        return ""
    return " ".join(str(text).split())


def _norm_title(text):
    """标题归一化：小写 + 去标点 + 折叠空白，保留中英文数字。"""
    if not text:
        return ""
    t = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", " ", str(text).lower())
    return " ".join(t.split())


def title_similarity(a, b):
    """归一化后的标题相似度（0–1），与 fetch_arxiv.py / verify_references.py 口径一致。"""
    na, nb = _norm_title(a), _norm_title(b)
    if not na or not nb:
        return 0.0
    return round(SequenceMatcher(None, na, nb).ratio(), 4)


def _norm_doi(doi):
    """去前缀、去 URL，返回裸 DOI（小写）。"""
    if not doi:
        return ""
    d = str(doi).strip()
    d = re.sub(r"^https?://(dx\.)?doi\.org/", "", d, flags=re.I)
    d = re.sub(r"^doi:\s*", "", d, flags=re.I)
    d = re.sub(r"^\s*https?://\S*\b(10\.\d{4,9}/)", r"\1", d)
    return d.strip().rstrip(".,;").lower()


class Pacer:
    """串行限速器：保证相邻两次请求间隔不小于 interval 秒（首次请求不等待）。"""

    def __init__(self, interval):
        self.interval = max(0.0, interval)
        self._last = None

    def wait(self):
        if self._last is not None and self.interval > 0:
            elapsed = time.monotonic() - self._last
            if elapsed < self.interval:
                time.sleep(self.interval - elapsed)
        self._last = time.monotonic()


# ---------------------------------------------------------------- 邮箱（polite pool）

def _env_mailto():
    for key in ("LIT_MAILTO", "OPENALEX_MAILTO", "CROSSREF_MAILTO"):
        val = os.environ.get(key, "").strip()
        if val:
            return val
    return ""


def _valid_mailto(mail):
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", mail or ""))


def resolve_mailto(args, required_apis):
    """按优先级解析邮箱：参数 → 环境变量 → 交互提示 → 公共池。

    返回 (mailto, how)。how 用于 stderr 说明，便于写入检索日志做透明披露。
    """
    if getattr(args, "mailto", ""):
        mail = args.mailto.strip()
        if not _valid_mailto(mail):
            print(f"警告：--mailto 值 '{mail}' 不像有效邮箱，将按公共池处理。",
                  file=sys.stderr)
            return "", "invalid"
        return mail, "arg"

    env = _env_mailto()
    if env and _valid_mailto(env):
        return env, "env"

    no_prompt_env = os.environ.get("LIT_NO_PROMPT", "").strip().lower() in ("1", "true", "yes")
    if getattr(args, "no_prompt", False) or no_prompt_env:
        print("提示：未配置邮箱，使用公共池（限速更严）。"
              "可设环境变量 LIT_MAILTO 或用 --mailto 提升限额。", file=sys.stderr)
        return "", "public"

    # 交互提示：仅当标准输入是交互终端时询问。
    # 注意：某些 shell/包装环境即使重定向了 stdin 也会判定为 tty，
    # 因此 EOFError 降级是最终保险——非交互时直接回车或 Ctrl-D 即可，不会卡死。
    try:
        interactive = sys.stdin is not None and sys.stdin.isatty()
    except Exception:  # noqa: BLE001
        interactive = False

    if interactive:
        msg = (
            "\n[polite pool] {} 需要一个真实个人邮箱——不是注册、不是 API key，\n"
            "仅作为限流时的联系方式（官方不会发送营销邮件）。\n"
            "请输入邮箱（直接回车 = 使用公共池，限速更严）；\n"
            "脚本化/非交互运行请加 --no-prompt 或设 LIT_NO_PROMPT=1。\n"
            "> ".format(required_apis)
        )
        try:
            print(msg, file=sys.stderr, flush=True)
            ans = input().strip()
        except (EOFError, KeyboardInterrupt):
            ans = ""
            print("（未获取到输入）", file=sys.stderr)
        if ans and _valid_mailto(ans):
            return ans, "input"
        if ans:
            print("警告：输入不像有效邮箱，改用公共池。", file=sys.stderr)
        print("→ 本次使用公共池。想免除询问：设环境变量 LIT_MAILTO，"
              "或用 --mailto / --no-prompt。", file=sys.stderr)
        return "", "public"

    print("提示：非交互环境且未配置邮箱 → 使用公共池（限速更严）。"
          "可设环境变量 LIT_MAILTO 或用 --mailto 提升限额。", file=sys.stderr)
    return "", "public"


def _user_agent(mailto):
    if mailto:
        return f"{USER_AGENT_BASE}; mailto:{mailto}"
    return USER_AGENT_BASE


# ---------------------------------------------------------------- HTTP

def _http_get(url, pacer, timeout, retries, sleep, mailto="", accept="application/json"):
    """带限速与指数退避的 GET。返回 (bytes, http_error_code_or_None)。"""
    last = "未知错误"
    for attempt in range(retries + 1):
        pacer.wait()
        req = urllib.request.Request(url, headers={
            "User-Agent": _user_agent(mailto),
            "Accept": accept,
        })
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read(), None
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code} {e.reason}"
            # 404 是确定性结果（DOI 不存在），不重试
            if e.code == 404:
                return None, 404
            if e.code == 410:
                return None, 410
            if e.code in (429, 500, 502, 503, 504) and attempt < retries:
                time.sleep(max(sleep, 1.0) * (2 ** attempt))
                continue
            return None, e.code
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last = f"网络错误 {e}"
            if attempt < retries:
                time.sleep(max(sleep, 1.0) * (2 ** attempt))
                continue
            return None, last
    return None, last


def _get_json(url, pacer, timeout, retries, sleep, mailto=""):
    payload, err = _http_get(url, pacer, timeout, retries, sleep, mailto)
    if err is not None:
        return None, err
    try:
        return json.loads(payload.decode("utf-8")), None
    except Exception as e:  # noqa: BLE001
        return None, f"JSON 解析失败 {e}"


# ---------------------------------------------------------------- OpenAlex 解析

def _reconstruct_abstract(inverted):
    """OpenAlex 的 abstract_inverted_index 还原成纯文本。"""
    if not isinstance(inverted, dict) or not inverted:
        return ""
    slots = []
    for word, positions in inverted.items():
        for p in positions:
            slots.append((p, word))
    slots.sort(key=lambda x: x[0])
    return " ".join(w for _, w in slots)


def _oa_authors(work):
    out = []
    for a in work.get("authorships", []) or []:
        name = (a.get("author") or {}).get("display_name", "")
        if name:
            out.append(name)
    return out


def _oa_topics(work):
    out = []
    for t in (work.get("topics") or [])[:3]:
        name = t.get("display_name")
        if name:
            out.append({"name": name, "score": t.get("score")})
    if not out:
        for c in (work.get("concepts") or [])[:3]:
            name = c.get("display_name")
            if name:
                out.append({"name": name, "score": c.get("score")})
    return out


def _oa_work_to_dict(work, with_abstract=False):
    doi = _norm_doi(work.get("doi") or "")
    oa = work.get("best_oa_location") or {}
    host = work.get("primary_location") or {}
    source = (host.get("source") or {}) or {}
    venue = source.get("display_name") or (oa.get("source") or {}).get("display_name", "")
    item = {
        "source": "openalex",
        "openalex_id": (work.get("id") or "").rsplit("/", 1)[-1],
        "doi": doi,
        "verifiable_id": f"doi:{doi}" if doi else "",
        "title": _clean(work.get("title") or work.get("display_name")),
        "authors": _oa_authors(work),
        "year": work.get("publication_year"),
        "publication_date": work.get("publication_date", ""),
        "venue": venue,
        "type": work.get("type", ""),
        "cited_by_count": work.get("cited_by_count"),
        "is_oa": bool(work.get("open_access", {}).get("is_oa")),
        "oa_url": (oa.get("pdf_url") or oa.get("landing_page_url")
                   or work.get("doi") or ""),
        "topics": _oa_topics(work),
    }
    if with_abstract:
        item["abstract"] = _reconstruct_abstract(work.get("abstract_inverted_index"))
    return item


def _openalex_filters(args):
    """把命令行过滤条件拼成 OpenAlex filter 串（逗号 = AND）。"""
    parts = []
    if args.year_from:
        parts.append(f"from_publication_date:{int(args.year_from)}-01-01")
    if args.year_to:
        parts.append(f"to_publication_date:{int(args.year_to)}-12-31")
    if args.type:
        parts.append(f"type:{args.type}")
    if args.oa_only:
        parts.append("is_oa:true")
    if args.cited_by_min is not None:
        parts.append(f"cited_by_count:>{int(args.cited_by_min)}")
    for v in [x.strip() for x in (args.venue or "").split(",") if x.strip()]:
        parts.append(f"primary_location.source.display_name.search:{v}")
    return ",".join(parts)


def cmd_search(args, pacer, mailto):
    params = {}
    if args.title_only:
        if not args.query:
            print("错误：--title-only 需要配合 --query。", file=sys.stderr)
            return 1
        params["filter"] = f"title.search:{args.query}"
    elif args.query:
        params["search"] = args.query
    else:
        print("错误：--query 至少给一个检索词。", file=sys.stderr)
        return 1

    flt = _openalex_filters(args)
    if flt:
        params["filter"] = flt if "filter" not in params else params["filter"] + "," + flt
    if mailto:
        params["mailto"] = mailto
    if args.sort:
        params["sort"] = args.sort

    per_page = max(1, min(args.per_page, 200))
    cursor = "*"
    collected = []
    while len(collected) < args.max_results:
        p = dict(params)
        p["per-page"] = min(per_page, args.max_results - len(collected))
        p["cursor"] = cursor
        url = f"{OPENALEX_API}?{urllib.parse.urlencode(p)}"
        if args.dry_run:
            print(url)
            return 0
        data, err = _get_json(url, pacer, args.timeout, args.retries, args.sleep, mailto)
        if err is not None:
            print(f"OpenAlex 请求失败：{err}", file=sys.stderr)
            return 2
        works = data.get("results", []) or []
        if not works:
            break
        for w in works:
            collected.append(_oa_work_to_dict(w, args.abstract))
        cursor = (data.get("meta") or {}).get("next_cursor")
        if not cursor or len(works) < p["per-page"]:
            break

    collected = collected[:args.max_results]
    _emit(collected, args.output, args.indent)
    shown = {k: v for k, v in params.items() if k != "cursor"}
    print(f"OpenAlex 检索参数：{json.dumps(shown, ensure_ascii=False)}", file=sys.stderr)
    print(f"取回 {len(collected)} 条（polite pool: {'是' if mailto else '否'}）",
          file=sys.stderr)
    return 0


def cmd_enrich(args, pacer, mailto):
    dois = []
    for part in (args.dois or "").split(","):
        d = _norm_doi(part)
        if d:
            dois.append(d)
    if args.input:
        try:
            with open(args.input, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:  # noqa: BLE001
            print(f"读取 --input 失败：{e}", file=sys.stderr)
            return 1
        if not isinstance(data, list):
            print("--input 必须是 JSON 数组", file=sys.stderr)
            return 1
        for item in data:
            if isinstance(item, dict) and _norm_doi(item.get("doi", "")):
                dois.append(_norm_doi(item["doi"]))
            elif isinstance(item, str) and _norm_doi(item):
                dois.append(_norm_doi(item))
    seen, ordered = set(), []
    for d in dois:
        if d not in seen:
            seen.add(d)
            ordered.append(d)
    if not ordered:
        print("错误：请用 --dois 或 --input 提供至少一个 DOI。", file=sys.stderr)
        return 1

    results = []
    for d in ordered:
        url = f"{OPENALEX_API}/doi:{urllib.parse.quote(d)}"
        if mailto:
            url += f"?mailto={urllib.parse.quote(mailto)}"
        if args.dry_run:
            print(url)
            continue
        data, err = _get_json(url, pacer, args.timeout, args.retries, args.sleep, mailto)
        if err is not None:
            code = err if isinstance(err, int) else None
            if code == 404:
                results.append({"doi": d, "found": False,
                                "note": "OpenAlex 未收录该 DOI（可能是最新文献、预印本或 DOI 有误）"})
            else:
                results.append({"doi": d, "found": False, "error": str(err),
                                "note": "请求失败，可加大 --sleep 重试或改走 Crossref verify"})
            continue
        results.append(dict(_oa_work_to_dict(data, args.abstract), found=True))

    if args.dry_run:
        return 0
    _emit(results, args.output, args.indent)
    ok = sum(1 for r in results if r.get("found"))
    print(f"查到 {ok}/{len(results)} 条", file=sys.stderr)
    return 0


# ---------------------------------------------------------------- Crossref 核验

def _crossref_to_dict(msg):
    """Crossref /works/{doi} 单条 → 精简规范记录。"""
    title = (msg.get("title") or [""])[0]
    authors = []
    for a in msg.get("author", []) or []:
        name = " ".join(x for x in (a.get("given", ""), a.get("family", "")) if x)
        if not name and a.get("name"):
            name = a["name"]
        if name:
            authors.append(name.strip())
    issued = ((msg.get("issued") or {}).get("date-parts") or [[]])[0]
    year = issued[0] if issued else None
    return {
        "doi": _norm_doi(msg.get("DOI", "")),
        "title": _clean(title),
        "authors": authors,
        "year": year,
        "venue": _clean((msg.get("container-title") or [""])[0]),
        "type": msg.get("type", ""),
        "publisher": _clean(msg.get("publisher", "")),
        "url": msg.get("URL", ""),
    }


def cmd_verify(args, pacer, mailto):
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            refs = json.load(f)
    except Exception as e:  # noqa: BLE001
        print(f"读取输入失败：{e}", file=sys.stderr)
        return 1
    if not isinstance(refs, list):
        print("输入 JSON 必须是数组", file=sys.stderr)
        return 1

    to_check = []
    for r in refs:
        if isinstance(r, dict) and _norm_doi(r.get("doi", "")):
            to_check.append(_norm_doi(r["doi"]))

    if args.dry_run:
        for d in to_check:
            url = f"{CROSSREF_API}/{urllib.parse.quote(d)}"
            if mailto:
                url += f"?mailto={urllib.parse.quote(mailto)}"
            print(url)
        return 0

    canonical = {}
    for d in to_check:
        url = f"{CROSSREF_API}/{urllib.parse.quote(d)}"
        if mailto:
            url += f"?mailto={urllib.parse.quote(mailto)}"
        data, err = _get_json(url, pacer, args.timeout, args.retries, args.sleep, mailto)
        if err == 404:
            canonical[d] = None
        elif err is not None:
            canonical[d] = {"__error__": str(err)}
        else:
            canonical[d] = _crossref_to_dict(data.get("message", {}) or {})

    summary = {"MATCH": 0, "DOI_MISMATCH": 0, "NOT_FOUND": 0, "NO_DOI": 0, "ERROR": 0}
    results = []
    for item in refs:
        if not isinstance(item, dict):
            continue
        rid = item.get("ref", "?")
        draft_title = item.get("title", "")
        doi = _norm_doi(item.get("doi", ""))
        if not doi:
            summary["NO_DOI"] += 1
            results.append({"ref": rid, "doi": "", "status": "NO_DOI",
                            "draft_title": draft_title, "canonical_title": "",
                            "similarity": 0.0,
                            "note": "无 DOI，改用 arXiv ID 走 fetch_arxiv.py，或人工核对"})
            continue

        hit = canonical.get(doi, "missing")
        if hit == "missing":
            summary["ERROR"] += 1
            results.append({"ref": rid, "doi": doi, "status": "ERROR",
                            "draft_title": draft_title, "similarity": 0.0,
                            "note": "未执行核验（未出现在待查列表中）"})
            continue
        if isinstance(hit, dict) and hit.get("__error__"):
            summary["ERROR"] += 1
            results.append({"ref": rid, "doi": doi, "status": "ERROR",
                            "draft_title": draft_title, "similarity": 0.0,
                            "note": f"Crossref 请求失败：{hit['__error__']}；可重试或人工核对"})
            continue
        if hit is None:
            summary["NOT_FOUND"] += 1
            results.append({"ref": rid, "doi": doi, "status": "NOT_FOUND",
                            "draft_title": draft_title, "canonical_title": "",
                            "similarity": 0.0,
                            "note": "Crossref 查无此 DOI，疑似占位符/编造 DOI → 须删除或重写"})
            continue

        c_title = hit.get("title", "")
        sim = title_similarity(draft_title, c_title) if draft_title else 1.0
        if sim >= TITLE_SIM_THRESHOLD:
            status = "MATCH"
            note = "DOI 与规范标题一致"
        else:
            status = "DOI_MISMATCH"
            note = f"标题漂移 → 以 Crossref 规范标题修正：{c_title}"
        summary[status] += 1
        results.append({"ref": rid, "doi": doi, "status": status,
                        "draft_title": draft_title, "canonical_title": c_title,
                        "similarity": sim, "year": hit.get("year"),
                        "authors": hit.get("authors", []), "venue": hit.get("venue"),
                        "publisher": hit.get("publisher"),
                        "type": hit.get("type"), "note": note})

    payload = {
        "source": "crossref",
        "threshold": TITLE_SIM_THRESHOLD,
        "total": len(results),
        "summary": summary,
        "results": results,
    }
    _emit(payload, args.output, args.indent)
    print("统计：MATCH {MATCH} / DOI_MISMATCH {DOI_MISMATCH} / NOT_FOUND {NOT_FOUND} / "
          "NO_DOI {NO_DOI} / ERROR {ERROR}".format(**summary), file=sys.stderr)
    return 0


# ---------------------------------------------------------------- OpenCitations 引文

def _oc_extract_doi(raw):
    """COCI 的 ID 可能是 'omid:br/xxx doi:10.xx/y openalex:W.. pmid:..' 复合串。
    只取 doi 部分；取不到则原样返回（避免把一篇算成多篇）。"""
    if not raw:
        return ""
    s = str(raw)
    m = re.search(r"\bdoi:\s*(\S+)", s)
    if m:
        return _norm_doi(m.group(1))
    m = re.search(r"\b(10\.\d{4,9}/\S+)", s)
    if m:
        return _norm_doi(m.group(1))
    return s.strip()


def _coci_fetch(kind, doi, pacer, args, mailto):
    """kind: 'citations'（施引）/ 'references'（参考文献）。返回 (items, err)。"""
    url = f"{COCI_API}/{kind}/{urllib.parse.quote(doi)}"
    if args.dry_run:
        print(url)
        return [], "dry-run"
    data, err = _get_json(url, pacer, CITING_TIMEOUT, args.retries, args.sleep, mailto)
    if err is not None:
        return [], err
    if not isinstance(data, list):
        return [], f"返回格式异常：{type(data).__name__}"
    return data, None


def _coci_items(records, self_doi, direction):
    """把 COCI 记录转成条目并按对方 DOI 去重。

    citations（谁引了它）：对方 = citing 字段
    references（它引了谁）：对方 = cited 字段
    """
    out, seen = [], set()
    for r in records or []:
        other = _oc_extract_doi(r.get("citing") if direction == "citing" else r.get("cited"))
        if not other or _norm_doi(other) == self_doi:
            continue
        if other in seen:
            continue
        seen.add(other)
        out.append({
            "doi": other,
            "creation": r.get("creation", ""),
            "timespan": r.get("timespan", ""),
            "has_journal_sc": str(r.get("journal_sc", "")).lower() == "yes",
            "has_author_sc": str(r.get("author_sc", "")).lower() == "yes",
        })
    return out


def cmd_citing(args, pacer, mailto):
    doi = _norm_doi(args.doi)
    if not doi:
        print("错误：请用 --doi 提供一个 DOI。", file=sys.stderr)
        return 1
    if args.direction not in ("citing", "cited", "both"):
        print("错误：--direction 只能是 citing / cited / both。", file=sys.stderr)
        return 1

    want = ("citing", "cited") if args.direction == "both" else (args.direction,)
    blocks, failed = {}, False
    for direction in want:
        kind = "citations" if direction == "citing" else "references"
        records, err = _coci_fetch(kind, doi, pacer, args, mailto)
        if args.dry_run:
            continue
        if err:
            failed = True
            blocks[direction] = {
                "direction": direction, "error": str(err), "count": 0, "items": [],
                "note": ("OpenCitations 请求失败/超时。高被引 DOI 常见，属服务端限制；"
                         "建议改用 enrich 取 OpenAlex 的 cited_by_count，或降级并透明披露。"),
            }
            continue
        items = _coci_items(records, doi, direction)[:args.max_results]
        blocks[direction] = {
            "direction": direction,
            "api": f"{COCI_API}/{kind}/{doi}",
            "raw_count": len(records or []),
            "count": len(items),
            "items": items,
        }

    if args.dry_run:
        return 0

    payload = {
        "source": "opencitations",
        "doi": doi,
        "blocks": [blocks[d] for d in want if d in blocks],
        "note": ("空数组 ≠ 零被引，只表示未被 COCI 索引；不得据此判定文献不存在或无影响力。"),
    }
    _emit(payload, args.output, args.indent)
    for d in want:
        b = blocks.get(d, {})
        label = "施引（谁引了它）" if d == "citing" else "参考文献（它引了谁）"
        if b.get("error"):
            print(f"{label}：失败 → {b['error']}", file=sys.stderr)
        else:
            print(f"{label}：{b.get('count', 0)} 条（原始 {b.get('raw_count', 0)} 条）",
                  file=sys.stderr)
    return 2 if failed else 0


# ---------------------------------------------------------------- I/O

def _emit(data, output, indent):
    text = json.dumps(data, ensure_ascii=False, indent=indent)
    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(f"已写入 {output}", file=sys.stderr)
    else:
        print(text)


COMMON_DEFAULTS = {
    "timeout": DEFAULT_TIMEOUT,
    "retries": DEFAULT_RETRIES,
    "indent": 2,
    "output": None,
    "dry_run": False,
    "mailto": "",
    "no_prompt": False,
}


def _common_parser():
    """公共参数。用 SUPPRESS 作默认值，避免子命令默认值覆盖顶层赋值，
    从而支持「公共参数放在子命令前或后」两种写法。"""
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("--timeout", type=float, default=argparse.SUPPRESS,
                   help=f"单次请求超时秒数，默认 {DEFAULT_TIMEOUT}")
    p.add_argument("--retries", type=int, default=argparse.SUPPRESS,
                   help=f"429/5xx/网络错误重试次数，默认 {DEFAULT_RETRIES}")
    p.add_argument("--indent", type=int, default=argparse.SUPPRESS,
                   help="JSON 缩进，默认 2")
    p.add_argument("--output", default=argparse.SUPPRESS,
                   help="输出文件路径（默认打印到标准输出）")
    p.add_argument("--dry-run", dest="dry_run", action="store_true",
                   default=argparse.SUPPRESS,
                   help="只打印将要请求的 URL，不发起网络请求（用于写检索日志）")
    p.add_argument("--mailto", default=argparse.SUPPRESS,
                   help="polite pool 邮箱（非注册、非 key）。也可用环境变量 LIT_MAILTO")
    p.add_argument("--no-prompt", dest="no_prompt", action="store_true",
                   default=argparse.SUPPRESS,
                   help="不交互询问邮箱，直接使用公共池（脚本化调用时用）")
    return p


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    common = _common_parser()
    ap = argparse.ArgumentParser(
        parents=[common],
        description="正式刊出文献检索与核验（OpenAlex / Crossref / OpenCitations；"
                    "纯 stdlib，无需 API key，默认限速）")

    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search", parents=[common], help="OpenAlex 正式刊出检索")
    s.add_argument("--query", default="", help="检索词（默认全字段搜索）")
    s.add_argument("--title-only", action="store_true", help="只匹配标题字段")
    s.add_argument("--year-from", type=int, help="起始出版年份")
    s.add_argument("--year-to", type=int, help="截止出版年份")
    s.add_argument("--type", default="", help="文献类型，如 article / review / preprint")
    s.add_argument("--oa-only", action="store_true", help="只要开放获取")
    s.add_argument("--cited-by-min", type=int, help="最低被引数过滤")
    s.add_argument("--venue", default="", help="期刊名过滤，逗号分隔（模糊匹配）")
    s.add_argument("--sort", default="",
                   choices=["", "cited_by_count:desc", "publication_date:desc",
                            "publication_date:asc", "relevance_score:desc"],
                   help="排序方式，默认留空=按相关度（综述检索推荐）。"
                        "注意：cited_by_count:desc 会牺牲相关度，容易拉入高被引但"
                        "主题无关的论文，建议先按相关度取全，再用 --cited-by-min 过滤")
    s.add_argument("--max-results", type=int, default=DEFAULT_MAX_RESULTS,
                   help=f"最多取回条数，默认 {DEFAULT_MAX_RESULTS}")
    s.add_argument("--per-page", type=int, default=DEFAULT_PER_PAGE,
                   help=f"单页条数，默认 {DEFAULT_PER_PAGE}（上限 200）")
    s.add_argument("--abstract", action="store_true", help="一并输出摘要（响应更大）")
    s.set_defaults(func=cmd_search)

    v = sub.add_parser("verify", parents=[common], help="Crossref DOI 核验（抓标题漂移）")
    v.add_argument("--input", required=True,
                   help='JSON 数组：[{"ref":"[1]","doi":"10.1038/xxx","title":"..."}]')
    v.set_defaults(func=cmd_verify)

    c = sub.add_parser("citing", parents=[common], help="OpenCitations 引文关系（T4 计量）")
    c.add_argument("--doi", required=True, help="目标文献 DOI")
    c.add_argument("--direction", default="cited",
                   choices=["citing", "cited", "both"],
                   help="citing=谁引了它；cited=它引了谁；both=两者都要")
    c.add_argument("--max-results", type=int, default=200,
                   help="每个方向最多保留条数，默认 200")
    c.set_defaults(func=cmd_citing)

    e = sub.add_parser("enrich", parents=[common], help="按 DOI 取 OpenAlex 规范元数据")
    e.add_argument("--dois", default="", help="逗号分隔的 DOI 列表")
    e.add_argument("--input", help="JSON 数组：元素为 DOI 字符串或含 doi 的对象")
    e.add_argument("--abstract", action="store_true", help="一并输出摘要")
    e.set_defaults(func=cmd_enrich)

    args = ap.parse_args()
    for key, value in COMMON_DEFAULTS.items():
        if not hasattr(args, key):
            setattr(args, key, value)

    # 限速：--sleep 未显式指定时，按子命令取保守默认值
    if not hasattr(args, "sleep"):
        args.sleep = SLEEP_DEFAULTS.get(args.cmd, 1.0)
    pacer = Pacer(args.sleep)

    mailto, how = resolve_mailto(args, "OpenAlex / Crossref")
    if how == "public":
        print("注意：当前使用公共池。Crossref 列表 1 req/s、单条 5 req/s；"
              "OpenAlex 无邮箱约 1 万积分/天。", file=sys.stderr)

    try:
        rc = args.func(args, pacer, mailto)
        return rc if rc is not None else 0
    except LitError as e:
        print(f"请求失败：{e}", file=sys.stderr)
        print("提示：可能是网络不通或被限流；可加大 --sleep 后重试，"
              "或回退 WebFetch 人工核对并透明披露。", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
