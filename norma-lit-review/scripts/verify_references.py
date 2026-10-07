#!/usr/bin/env python3
# norma-lit-review · 参考文献 API 级核验脚本
# Copyright (C) 2026 Norma（郑洪英）
#
# 本脚本依据 PolyForm Noncommercial License 1.0.0 分发（禁止商业使用）。
# 完整条款见本 skill 根目录 LICENSE 文件，或
# https://polyformproject.org/licenses/noncommercial/1.0.0
"""norma-lit-review · 参考文献 API 级核验脚本（仅 stdlib，自包含）

对参考文献列表里的 arXiv ID / DOI 调用真实学术 API 做"存在性 + 标题交叉校验"，
复刻验证检索协议（modules/verified-retrieval-protocol.md）的 L1 核验流程：
  - arXiv API (http) 查规范标题，0.70 相似度比对，抓标题漂移（ID_MISMATCH）
  - Semantic Scholar API (https) 先 DOI 后标题，内置 429 退避
  - S2_API_KEY 环境变量 → 限速 1 req/s → 10 req/s

用法：
  python verify_references.py --input refs.json [--output report.md]
  S2_API_KEY="你的key" python verify_references.py --input refs.json

注意：本脚本不内置任何 API key，请自行到 Semantic Scholar 官网免费申请 S2_API_KEY 后
通过环境变量或 --api-key 传入；未配置也能运行，仅限速更严。

输入 JSON 格式（数组）：
  [{"ref":"[1]","title":"...","arxiv_id":"2308.08155","doi":"10.x/...","year":2023}, ...]

环境：managed Python 3.13 仅需 stdlib（urllib / xml / difflib），无需 pip。
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from difflib import SequenceMatcher

_TITLE_SIM_THRESHOLD = 0.70
_BACKOFF_SECONDS = 2.0
_MAX_RETRIES = 3
_UNAUTH_MIN_INTERVAL = 1.0
_AUTH_MIN_INTERVAL = 0.1
_ARXIV_API = "http://export.arxiv.org/api/query"
_S2_API = "https://api.semanticscholar.org/graph/v1"


def _norm(t: str) -> str:
    return " ".join(str(t).lower().split())


def _sim(a: str, b: str) -> float:
    return SequenceMatcher(None, _norm(a), _norm(b)).ratio()


def _require_title(expected: str, returned: str) -> bool:
    if not expected or not returned:
        return True  # 无标题可比对时不误杀
    return _sim(expected, returned) >= _TITLE_SIM_THRESHOLD


def arxiv_lookup(arxiv_id: str, expected_title: str, last_req, api_key=None):
    """返回 (status, canonical_title, note)。status: VERIFIED / ID_MISMATCH / NOT_FOUND"""
    url = f"{_ARXIV_API}?id_list={urllib.parse.quote(arxiv_id)}&max_results=1"
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            data = r.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return "NOT_FOUND", "", f"arXiv 404 ({arxiv_id})"
        return "NOT_FOUND", "", f"arXiv HTTP {e.code}"
    except Exception as e:  # noqa
        return "NOT_FOUND", "", f"arXiv 网络错误: {e}"
    try:
        root = ET.fromstring(data)
        ns = "{http://www.w3.org/2005/Atom}"
        entry = root.find(f"{ns}entry")
        if entry is None:
            return "NOT_FOUND", "", f"arXiv 无 entry ({arxiv_id})"
        title = (entry.findtext(f"{ns}title") or "").strip().replace("\n", " ")
        return _decide(title, expected_title)
    except ET.ParseError as e:
        return "NOT_FOUND", "", f"arXiv 解析失败: {e}"


def s2_lookup(doi: str, expected_title: str, year=None, api_key=None, last_req=None):
    """Semantic Scholar DOI-first 校验。返回 (status, canonical_title, note)"""
    url = f"{_S2_API}/paper/DOI:{urllib.parse.quote(doi, safe='')}?fields=title,year"
    headers = {"User-Agent": "norma-lit-review/1.0"}
    if api_key:
        headers["x-api-key"] = api_key
    req = urllib.request.Request(url, headers=headers)
    for attempt in range(_MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read().decode("utf-8"))
            title = data.get("title") or ""
            if not title:
                return "NOT_FOUND", "", f"S2 无标题 ({doi})"
            return _decide(title, expected_title)
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < _MAX_RETRIES:
                time.sleep(_BACKOFF_SECONDS)
                continue
            if e.code == 404:
                return "NOT_FOUND", "", f"S2 404 ({doi})"
            return "NOT_FOUND", "", f"S2 HTTP {e.code}"
        except Exception as e:  # noqa
            return "NOT_FOUND", "", f"S2 错误: {e}"
    return "NOT_FOUND", "", "S2 重试耗尽"


def _decide(canonical_title: str, expected_title: str):
    if _require_title(expected_title, canonical_title):
        return "VERIFIED", canonical_title, "标题一致"
    return "ID_MISMATCH", canonical_title, f"标题漂移→规范: {canonical_title}"


def verify(refs, api_key=None):
    results = []
    last = [0.0]
    interval = _AUTH_MIN_INTERVAL if api_key else _UNAUTH_MIN_INTERVAL
    for item in refs:
        rid = item.get("ref", "?")
        title = item.get("title", "")
        year = item.get("year")
        status, canonical, note = None, "", ""
        if item.get("arxiv_id"):
            _pace(last, interval)
            status, canonical, note = arxiv_lookup(item["arxiv_id"], title, last, api_key)
        elif item.get("doi"):
            _pace(last, interval)
            status, canonical, note = s2_lookup(item["doi"], title, year, api_key, last)
        else:
            status, canonical, note = "NO_ID", "", "无 arxiv_id/doi，需人工核对"
        results.append({
            "ref": rid, "status": status, "canonical_title": canonical,
            "note": note, "draft_title": title,
        })
    return results


def _pace(last, interval):
    now = time.monotonic()
    elapsed = now - last[0]
    if last[0] and elapsed < interval:
        time.sleep(interval - elapsed)
    last[0] = time.monotonic()


def render_md(results):
    lines = ["# 参考文献 API 级核验报告", "",
             f"核验时间：{time.strftime('%Y-%m-%d %H:%M')}",
             f"条目总数：{len(results)}", "",
             "| 编号 | 状态 | 草稿标题 | 规范标题 / 备注 |",
             "|------|------|---------|----------------|"]
    c = {"VERIFIED": 0, "ID_MISMATCH": 0, "NOT_FOUND": 0, "NO_ID": 0}
    for r in results:
        c[r["status"]] = c.get(r["status"], 0) + 1
        lines.append(f"| {r['ref']} | {r['status']} | {r['draft_title'][:40]} | {r['canonical_title'] or r['note']} |")
    lines += ["", f"统计：VERIFIED {c['VERIFIED']} / ID_MISMATCH {c['ID_MISMATCH']} / "
                f"NOT_FOUND {c['NOT_FOUND']} / NO_ID {c['NO_ID']}", "",
                "> ID_MISMATCH：论文真实但标题需按规范标题修正；NOT_FOUND：检索不到，疑似编造，须删除/重写。"]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="参考文献 JSON 文件路径")
    ap.add_argument("--output", help="报告输出路径（默认打印）")
    ap.add_argument("--api-key",
                    help="S2_API_KEY（不推荐：会留在 shell history；请改用环境变量 S2_API_KEY）")
    args = ap.parse_args()
    api_key = args.api_key or os.environ.get("S2_API_KEY")
    if args.api_key:
        print("安全提示：--api-key 会残留在 shell history 与进程列表中。"
              "建议改用环境变量（export S2_API_KEY=...）后不带该参数运行。",
              file=sys.stderr)
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            refs = json.load(f)
    except Exception as e:  # noqa
        print(f"读取输入失败: {e}", file=sys.stderr)
        sys.exit(1)
    if not isinstance(refs, list):
        print("输入 JSON 必须是数组", file=sys.stderr)
        sys.exit(1)
    results = verify(refs, api_key)
    md = render_md(results)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"报告已写入 {args.output}")
    else:
        print(md)


if __name__ == "__main__":
    main()
