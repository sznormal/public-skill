#!/usr/bin/env python3
# norma-lit-review · arXiv 元数据检索与核验脚本
# Copyright (C) 2026 Norma（郑洪英）
#
# 本脚本依据 PolyForm Noncommercial License 1.0.0 分发（禁止商业使用）。
# 完整条款见本 skill 根目录 LICENSE 文件，或
# https://polyformproject.org/licenses/noncommercial/1.0.0
"""arXiv 元数据检索与核验（仅 stdlib，无需 API key，带限速）。

三个子命令
----------
search  按检索式批量获取 arXiv 论文元数据  → P2 多库检索
lookup  按 arXiv ID 取回规范元数据        → P6 真实性核验
verify  按 ID + 标题做 0.70 相似度交叉校验，抓"ID 真实但标题漂移"

设计约束
--------
- 只用 Python 标准库（urllib / xml / difflib），无需 pip、无需 venv、无需建虚拟环境。
- arXiv Export API **完全免费、无需注册、无需任何 API key**。
- **限速为默认行为**：串行请求，相邻两次请求间隔默认 sleep 3 秒（arXiv 官方礼貌要求
  ≈1 req/3s），用 --sleep 调整；遇 429/5xx 按指数退避重试。
- 输出统一为 UTF-8 JSON，可直接喂给 raw_literature_list.json（search）
  或核验报告（verify）。

用法示例
--------
  # P2 检索：机器人方向具身智能，限 2022 年后，取 20 篇
  python fetch_arxiv.py search \
      --query 'all:"embodied intelligence"' --categories cs.RO,cs.LG \
      --year-from 2022 --max-results 20 --output raw_arxiv.json

  # 只打印最终检索 URL（用于写进检索日志 search_log.md，不发起请求）
  python fetch_arxiv.py search --query 'cat:cs.RO' --dry-run

  # P6 取规范元数据
  python fetch_arxiv.py lookup --ids 2308.08155,2409.05556

  # P6 按 ID + 标题交叉校验（refs.json = [{ref, arxiv_id, title}, ...]）
  python fetch_arxiv.py verify --input refs.json --output arxiv_verify.json

退出码
------
  0 成功；1 输入/用法错误；2 网络或服务端错误且重试耗尽。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from difflib import SequenceMatcher

ARXIV_API = "https://export.arxiv.org/api/query"
ATOM = "{http://www.w3.org/2005/Atom}"
ARXIV = "{http://arxiv.org/schemas/atom}"

TITLE_SIM_THRESHOLD = 0.70
DEFAULT_SLEEP = 3.0        # arXiv 礼貌限速：相邻请求间隔（秒）
DEFAULT_TIMEOUT = 30       # 单次请求超时（秒）
DEFAULT_PAGE_SIZE = 100    # 单页条数（arXiv 建议 ≤ 2000，取 100 更稳）
DEFAULT_BATCH = 20         # id_list 单批 ID 数
DEFAULT_RETRIES = 3        # 429/5xx/网络错误重试次数
USER_AGENT = "norma-lit-review/1.0 (+arXiv metadata fetcher; stdlib urllib)"


class ArxivError(RuntimeError):
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
    """归一化后的标题相似度（0–1），与 verify_references.py 口径一致。"""
    na, nb = _norm_title(a), _norm_title(b)
    if not na or not nb:
        return 0.0
    return round(SequenceMatcher(None, na, nb).ratio(), 4)


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


def build_url(params):
    return f"{ARXIV_API}?{urllib.parse.urlencode(params)}"


def _http_get(url, pacer, timeout, retries, sleep):
    """带限速与指数退避的 GET。返回 bytes。"""
    last = "未知错误"
    for attempt in range(retries + 1):
        pacer.wait()
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code} {e.reason}"
            if e.code in (429, 500, 502, 503, 504) and attempt < retries:
                time.sleep(sleep * (2 ** attempt))
                continue
            break
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last = f"网络错误 {e}"
            if attempt < retries:
                time.sleep(sleep * (2 ** attempt))
                continue
            break
    raise ArxivError(last)


# ---------------------------------------------------------------- 解析

def _split_id_version(tail):
    """'2409.05556v1' → ('2409.05556', '1')；'cs/0701001' → ('cs/0701001', '')。"""
    m = re.match(r"^(.*?)v(\d+)$", tail)
    if m:
        return m.group(1), m.group(2)
    return tail, ""


def _entry_to_dict(entry):
    raw_id = _clean(entry.findtext(ATOM + "id"))
    tail = raw_id.rsplit("/abs/", 1)[-1] if "/abs/" in raw_id else raw_id
    arxiv_id, version = _split_id_version(tail)

    authors = [
        _clean(a.findtext(ATOM + "name"))
        for a in entry.findall(ATOM + "author")
    ]
    authors = [a for a in authors if a]

    categories = [
        c.get("term") for c in entry.findall(ATOM + "category") if c.get("term")
    ]

    primary = entry.find(ARXIV + "primary_category")
    primary_term = primary.get("term") if primary is not None and primary.get("term") else ""

    pdf_node = entry.find(ATOM + 'link[@title="pdf"]')
    pdf_url = pdf_node.get("href") if pdf_node is not None else ""

    published = _clean(entry.findtext(ATOM + "published"))
    year = int(published[:4]) if published[:4].isdigit() else None

    return {
        "arxiv_id": arxiv_id,
        "version": version,
        "title": _clean(entry.findtext(ATOM + "title")),
        "abstract": _clean(entry.findtext(ATOM + "summary")),
        "authors": authors,
        "year": year,
        "published": published,
        "updated": _clean(entry.findtext(ATOM + "updated")),
        "primary_category": primary_term,
        "categories": categories,
        "doi": _clean(entry.findtext(ARXIV + "doi")),
        "journal_ref": _clean(entry.findtext(ARXIV + "journal_ref")),
        "comment": _clean(entry.findtext(ARXIV + "comment")),
        "abs_url": raw_id,
        "pdf_url": pdf_url,
        "source": "arxiv",
        "verifiable_id": f"arxiv:{arxiv_id}" if arxiv_id else "",
    }


def parse_feed(payload):
    """返回 (entries, errors)。arXiv 对无效 ID 会返回一个 api/errors 条目。"""
    root = ET.fromstring(payload)
    entries, errors = [], []
    for entry in root.findall(ATOM + "entry"):
        raw_id = _clean(entry.findtext(ATOM + "id"))
        if "api/errors" in raw_id:
            errors.append(_clean(entry.findtext(ATOM + "title")) or raw_id)
            continue
        entries.append(_entry_to_dict(entry))
    return entries, errors


# ---------------------------------------------------------------- search

def build_search_query(query, categories, year_from, year_to):
    parts = []
    if query and query.strip():
        parts.append(f"({query.strip()})")
    cats = [c.strip() for c in (categories or "").split(",") if c.strip()]
    if cats:
        parts.append("(" + " OR ".join(f"cat:{c}" for c in cats) + ")")
    if year_from or year_to:
        start = f"{int(year_from)}01010000" if year_from else "199101010000"
        end = f"{int(year_to)}12312359" if year_to else "210012312359"
        parts.append(f"submittedDate:[{start} TO {end}]")
    return " AND ".join(parts)


def cmd_search(args, pacer):
    search_query = build_search_query(args.query, args.categories,
                                      args.year_from, args.year_to)
    if not search_query:
        print("错误：--query 与 --categories 至少给一个。", file=sys.stderr)
        return 1

    page = max(1, min(args.page_size, DEFAULT_PAGE_SIZE))
    collected, start = [], args.start

    while len(collected) < args.max_results:
        want = min(page, args.max_results - len(collected))
        url = build_url({
            "search_query": search_query,
            "start": start,
            "max_results": want,
            "sortBy": args.sort_by,
            "sortOrder": args.sort_order,
        })
        if args.dry_run:
            print(url)
            return 0
        payload = _http_get(url, pacer, args.timeout, args.retries, args.sleep)
        entries, errors = parse_feed(payload)
        for e in errors:
            print(f"警告：arXiv 返回错误条目 → {e}", file=sys.stderr)
        if not entries:
            break
        collected.extend(entries)
        if len(entries) < want:
            break
        start += len(entries)

    collected = collected[:args.max_results]
    _emit(collected, args.output, args.indent)
    print(f"检索式：{search_query}", file=sys.stderr)
    print(f"取回 {len(collected)} 条", file=sys.stderr)
    return 0


# ---------------------------------------------------------------- lookup

def _load_ids(args):
    ids = []
    if args.ids:
        ids.extend(i.strip() for i in args.ids.split(",") if i.strip())
    if args.input:
        try:
            with open(args.input, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:  # noqa: BLE001
            raise ArxivError(f"读取 --input 失败：{e}")
        if not isinstance(data, list):
            raise ArxivError("--input 必须是 JSON 数组")
        for item in data:
            if isinstance(item, dict) and item.get("arxiv_id"):
                ids.append(str(item["arxiv_id"]).strip())
            elif isinstance(item, str):
                ids.append(item.strip())
    # 去重保序
    seen, out = set(), []
    for i in ids:
        if i and i not in seen:
            seen.add(i)
            out.append(i)
    return out


def _lookup_batch(ids, pacer, args):
    url = build_url({"id_list": ",".join(ids), "max_results": max(len(ids), 1)})
    if args.dry_run:
        print(url)
        return None, []
    payload = _http_get(url, pacer, args.timeout, args.retries, args.sleep)
    entries, errors = parse_feed(payload)
    for e in errors:
        print(f"警告：arXiv 返回错误条目 → {e}", file=sys.stderr)
    return entries, errors


def _batch_ids(ids, size):
    for i in range(0, len(ids), size):
        yield ids[i:i + size]


def cmd_lookup(args, pacer):
    ids = _load_ids(args)
    if not ids:
        print("错误：请用 --ids 或 --input 提供至少一个 arXiv ID。", file=sys.stderr)
        return 1

    found = {}
    for batch in _batch_ids(ids, max(1, args.batch)):
        entries, _ = _lookup_batch(batch, pacer, args)
        if entries is None:      # dry-run 已打印 URL
            return 0
        for e in entries:
            found[e["arxiv_id"]] = e

    results = []
    for i in ids:
        base = i[:-2] if re.match(r"^.+v\d+$", i) else i
        hit = found.get(i) or found.get(base)
        if hit:
            hit = dict(hit, found=True)
        else:
            hit = {"arxiv_id": base, "found": False,
                   "note": "arXiv 未返回该 ID，疑似无效编号或已被撤回"}
        results.append(hit)

    _emit(results, args.output, args.indent)
    ok = sum(1 for r in results if r.get("found"))
    print(f"查到 {ok}/{len(results)} 条", file=sys.stderr)
    return 0


# ---------------------------------------------------------------- verify

def cmd_verify(args, pacer):
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            refs = json.load(f)
    except Exception as e:  # noqa: BLE001
        print(f"读取输入失败：{e}", file=sys.stderr)
        return 1
    if not isinstance(refs, list):
        print("输入 JSON 必须是数组", file=sys.stderr)
        return 1

    to_check = [r for r in refs if isinstance(r, dict) and str(r.get("arxiv_id", "")).strip()]
    if args.dry_run:
        for batch in _batch_ids([str(r["arxiv_id"]).strip() for r in to_check],
                                max(1, args.batch)):
            print(build_url({"id_list": ",".join(batch), "max_results": len(batch)}))
        return 0

    canonical = {}
    for batch in _batch_ids([str(r["arxiv_id"]).strip() for r in to_check],
                            max(1, args.batch)):
        entries, _ = _lookup_batch(batch, pacer, args)
        if entries:
            for e in entries:
                canonical[e["arxiv_id"]] = e

    results, summary = [], {"MATCH": 0, "ID_MISMATCH": 0, "NOT_FOUND": 0, "NO_ID": 0}
    for item in refs:
        if not isinstance(item, dict):
            continue
        rid = item.get("ref", "?")
        draft_title = item.get("title", "")
        raw_id = str(item.get("arxiv_id", "")).strip()
        if not raw_id:
            summary["NO_ID"] += 1
            results.append({"ref": rid, "arxiv_id": "", "status": "NO_ID",
                            "draft_title": draft_title, "canonical_title": "",
                            "similarity": 0.0,
                            "note": "无 arXiv ID，改用 DOI 走 verify_references.py 或人工核对"})
            continue
        base = raw_id[:-2] if re.match(r"^.+v\d+$", raw_id) else raw_id
        hit = canonical.get(raw_id) or canonical.get(base)
        if not hit:
            summary["NOT_FOUND"] += 1
            results.append({"ref": rid, "arxiv_id": base, "status": "NOT_FOUND",
                            "draft_title": draft_title, "canonical_title": "",
                            "similarity": 0.0,
                            "note": "arXiv 检索不到，疑似占位符/编造编号 → 须删除或重写"})
            continue
        c_title = hit.get("title", "")
        sim = title_similarity(draft_title, c_title) if draft_title else 1.0
        if sim >= TITLE_SIM_THRESHOLD:
            status = "MATCH"
            note = "编号与规范标题一致"
        else:
            status = "ID_MISMATCH"
            note = f"标题漂移 → 以规范标题修正：{c_title}"
        summary[status] += 1
        results.append({"ref": rid, "arxiv_id": base, "status": status,
                        "draft_title": draft_title, "canonical_title": c_title,
                        "similarity": sim, "year": hit.get("year"),
                        "authors": hit.get("authors", []), "note": note})

    payload = {
        "threshold": TITLE_SIM_THRESHOLD,
        "total": len(results),
        "summary": summary,
        "results": results,
    }
    _emit(payload, args.output, args.indent)
    print("统计：MATCH {MATCH} / ID_MISMATCH {ID_MISMATCH} / "
          "NOT_FOUND {NOT_FOUND} / NO_ID {NO_ID}".format(**summary), file=sys.stderr)
    return 0


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
    "sleep": DEFAULT_SLEEP,
    "timeout": DEFAULT_TIMEOUT,
    "retries": DEFAULT_RETRIES,
    "batch": DEFAULT_BATCH,
    "indent": 2,
    "output": None,
    "dry_run": False,
}


def _common_parser():
    """公共参数。用 SUPPRESS 作为默认值，避免子命令的默认值覆盖顶层已赋的值，
    从而支持「公共参数放在子命令前或后」两种写法。"""
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("--sleep", type=float, default=argparse.SUPPRESS,
                   help=f"相邻请求间隔秒数，默认 {DEFAULT_SLEEP}"
                        f"（arXiv 礼貌限速；0 表示不限速，不推荐）")
    p.add_argument("--timeout", type=float, default=argparse.SUPPRESS,
                   help=f"单次请求超时秒数，默认 {DEFAULT_TIMEOUT}")
    p.add_argument("--retries", type=int, default=argparse.SUPPRESS,
                   help=f"429/5xx/网络错误重试次数，默认 {DEFAULT_RETRIES}")
    p.add_argument("--batch", type=int, default=argparse.SUPPRESS,
                   help=f"id_list 单批 ID 数，默认 {DEFAULT_BATCH}")
    p.add_argument("--indent", type=int, default=argparse.SUPPRESS,
                   help="JSON 缩进，默认 2")
    p.add_argument("--output", default=argparse.SUPPRESS,
                   help="输出文件路径（默认打印到标准输出）")
    p.add_argument("--dry-run", dest="dry_run", action="store_true",
                   default=argparse.SUPPRESS,
                   help="只打印将要请求的 URL，不发起网络请求（用于写检索日志）")
    return p


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    common = _common_parser()
    ap = argparse.ArgumentParser(
        parents=[common],
        description="arXiv 元数据检索与核验（纯 stdlib，无需 API key，默认限速 3 秒/请求）")

    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search", parents=[common], help="按检索式批量检索元数据")
    s.add_argument("--query", default="", help="arXiv 检索式，如 all:\"embodied intelligence\"")
    s.add_argument("--categories", default="",
                   help="分类限定，逗号分隔，如 cs.RO,cs.LG,eess.SY（自动转成 cat: 子句）")
    s.add_argument("--year-from", type=int, help="起始年份（按提交日期过滤）")
    s.add_argument("--year-to", type=int, help="截止年份（按提交日期过滤）")
    s.add_argument("--max-results", type=int, default=50, help="最多取回条数，默认 50")
    s.add_argument("--start", type=int, default=0, help="结果起始偏移，默认 0")
    s.add_argument("--page-size", type=int, default=DEFAULT_PAGE_SIZE,
                   help=f"单页条数，默认 {DEFAULT_PAGE_SIZE}（上限 100）")
    s.add_argument("--sort-by", default="relevance",
                   choices=["relevance", "submittedDate", "lastUpdatedDate"])
    s.add_argument("--sort-order", default="descending",
                   choices=["ascending", "descending"])
    s.set_defaults(func=cmd_search)

    l = sub.add_parser("lookup", parents=[common], help="按 arXiv ID 取回规范元数据")
    l.add_argument("--ids", help="逗号分隔的 arXiv ID，如 2308.08155,2409.05556")
    l.add_argument("--input", help="JSON 文件：数组，元素为字符串或含 arxiv_id 的对象")
    l.set_defaults(func=cmd_lookup)

    v = sub.add_parser("verify", parents=[common],
                       help="按 ID + 标题做相似度交叉校验（抓标题漂移）")
    v.add_argument("--input", required=True,
                   help='JSON 数组：[{"ref":"[1]","arxiv_id":"2409.05556","title":"..."}]')
    v.set_defaults(func=cmd_verify)

    args = ap.parse_args()
    for key, value in COMMON_DEFAULTS.items():
        if not hasattr(args, key):
            setattr(args, key, value)
    pacer = Pacer(args.sleep)

    try:
        return args.func(args, pacer)
    except ArxivError as e:
        print(f"arXiv 请求失败：{e}", file=sys.stderr)
        print("提示：可能是网络不通或被限流；可加大 --sleep 后重试，"
              "或回退 WebFetch 人工核对并透明披露。", file=sys.stderr)
        return 2
    except ET.ParseError as e:
        print(f"arXiv 返回内容解析失败：{e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
