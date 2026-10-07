#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_submission.py — 论文投稿前引用/图表一致性门禁（norma-paper-format-check）
纯标准库，无外部依赖。

用法：
    # 编号制（默认）：Markdown / LaTeX 用 [N] 方括号引用
    python verify_submission.py <manuscript.md> [--refs-heading "References"]

    # 著者-年份制（biblatex / JAIR 一类）：扫描 LaTeX 源码反模式
    python verify_submission.py <manuscript.tex> --author-year

检查项：
  [默认 / 编号制]（对应 SOP 阶段四 / 阶段五 A–C 组）
    B 组 引用正确性：
        - 零孤儿：每条参考文献都被正文引用
        - 零缺项：正文每个 [N] 都有对应条目
        - 零越界：正文引用号不超过条目总数
        - 编号连续：1..N 无断号
    C 组 图表编号：
        - 图号、表号按正文首次出现顺序单调（无跳号 / 乱序 / 重复）

  [--author-year / 著者-年份制]（对应 SOP §4.5）
    源码级扫描两类可机检反模式（其余需渲染 PDF 人工核对）：
        - 拆分逗号组：\\cite{a}, \\cite{b} 各自带括号逗号连（应合并为一个 \\cite{a,b}）
        - 叙述式重名：Xxx et al. \\cite{n}（渲染成 "Xxx et al. (Xxx et al. 2024)"，应改 \\textcite）
    注意：编号制门禁（零孤儿/缺项/越界/连续）不适用 author-year，开此开关时跳过 B 组。

退出码：0 = 全部通过；1 = 存在失败项；2 = 参数 / 解析错误。

约定（约定驱动，可改下方正则适配你的稿件）：
    - 编号制正文引用：方括号 `[N]`，支持 `[1,2]` / `[1-3]` 区间；排除 Markdown 链接 `[text](url)`
    - 参考文献区：以标题含 References / 参考文献 的章节为界，条目以行首 `N.` 开头
    - 图题注：含 `Fig. N` 或 `图 N`
    - 表题注：含 `Table N` 或 `表 N`

说明：本脚本是"起点模板"，默认约定与多数编号制综述稿一致。若你的稿件用
author-year 制或不同标记，请相应调整下方正则，或改用 --author-year 开关。
"""

import argparse
import os
import re
import sys

# ---------- 可调整的正则（约定驱动） ----------
REF_CITATION_RE = re.compile(r"\[(\d+(?:[-,]\d+)*)\](?!\()")   # 正文 [N]，排除链接
REF_ENTRY_RE = re.compile(r"^\s*(\d+)\.\s")                    # 参考文献条目 N.
FIG_RE = re.compile(r"(?:Fig\.?\s*(\d+)|图\s*(\d+))")          # 图 N / 图N
TABLE_RE = re.compile(r"(?:Table\s*(\d+)|表\s*(\d+))")         # 表 N / 表N
REF_HEADING_RE = re.compile(r"^#{1,6}\s*(References|REFERENCES|参考文献|参考文献列表)\s*$", re.IGNORECASE)

# ---------- 著者-年份制（biblatex / JAIR）反模式正则 ----------
# ① 拆分逗号组：\cite{a}, \cite{b} 各自带括号 + 逗号连接 → 应合并 \cite{a,b}
AY_SPLIT_CITE_RE = re.compile(r"\\cite\{[^}]*\}\s*,\s*\\cite\{")
# ② 叙述式重名：Xxx et al. \cite{n} → 渲染成 "Xxx et al. (Xxx et al. 2024)"，应改 \textcite
AY_NARRATIVE_RE = re.compile(r"[A-Z][A-Za-z'’\-]+\s+et\s+al\.\s*\\cite\{")


def parse_args():
    p = argparse.ArgumentParser(description="论文投稿前引用/图表一致性门禁")
    p.add_argument("manuscript", help="稿件 Markdown 文件路径")
    p.add_argument("--refs-heading", default=None,
                   help="自定义参考文献区标题（默认自动识别 References/参考文献）")
    p.add_argument("--author-year", action="store_true",
                   help="著者-年份制模式：扫描 LaTeX 源码中 \\cite 反模式（拆分逗号组 / 叙述式重名），跳过编号制 B 组门禁")
    return p.parse_args()


def read_text(path):
    if not os.path.isfile(path):
        print(f"[ERROR] 文件不存在：{path}", file=sys.stderr)
        sys.exit(2)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:  # noqa: BLE001
        print(f"[ERROR] 读取失败：{e}", file=sys.stderr)
        sys.exit(2)


def split_body_refs(text, custom_heading):
    heading_re = REF_HEADING_RE
    if custom_heading:
        heading_re = re.compile(r"^#{1,6}\s*" + re.escape(custom_heading) + r"\s*$", re.IGNORECASE)
    lines = text.splitlines()
    split_idx = None
    for i, line in enumerate(lines):
        if heading_re.match(line.strip()):
            split_idx = i
            break
    if split_idx is None:
        # 没有显式参考文献区：把全文当正文，条目尝试在末尾找
        return text, ""
    body = "\n".join(lines[:split_idx])
    refs = "\n".join(lines[split_idx + 1:])
    return body, refs


def expand_citations(token):
    """把 '1-3' 或 '1,2' 展开成数字集合。"""
    nums = set()
    for part in token.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            try:
                nums.update(range(int(a), int(b) + 1))
            except ValueError:
                pass
        else:
            try:
                nums.add(int(part))
            except ValueError:
                pass
    return nums


def collect_cited(body):
    cited = set()
    for m in REF_CITATION_RE.finditer(body):
        cited |= expand_citations(m.group(1))
    return cited


def collect_entries(refs):
    entries = {}
    for line in refs.splitlines():
        m = REF_ENTRY_RE.match(line)
        if m:
            try:
                entries[int(m.group(1))] = True
            except ValueError:
                pass
    return entries


def check_references(body, refs):
    cited = collect_cited(body)
    entries = collect_entries(refs)
    fails = []

    if not entries:
        print("[WARN] 未识别到参考文献条目（行首 `N.`）；若用 author-year 制请改用对应检查。")
    else:
        max_entry = max(entries)
        # 零越界
        over = [c for c in cited if c > max_entry]
        if over:
            fails.append(f"零越界失败：正文引用号超出条目总数（最大 {max_entry}），越界号={sorted(over)}")
        # 零缺项
        missing = [c for c in cited if c not in entries]
        if missing:
            fails.append(f"零缺项失败：正文引用无对应条目，号={sorted(missing)}")
        # 零孤儿
        orphans = [e for e in entries if e not in cited]
        if orphans:
            fails.append(f"零孤儿失败：题录未被任何正文引用，号={sorted(orphans)}")
        # 编号连续
        expected = set(range(1, max_entry + 1))
        if set(entries.keys()) != expected:
            gaps = sorted(expected - set(entries.keys()))
            fails.append(f"编号连续失败：题录断号，缺失={gaps}")

    return fails


def check_captions(body, label, regex):
    """检查图/表编号按出现顺序单调（无跳号/乱序/重复）。"""
    seen = []
    for m in regex.finditer(body):
        num = m.group(1) or m.group(2)
        try:
            seen.append(int(num))
        except (ValueError, TypeError):
            pass
    fails = []
    if seen:
        # 单调不减且无重复
        if seen != sorted(seen):
            # 找出乱序位置
            bad = [seen[i] for i in range(1, len(seen)) if seen[i] < seen[i - 1]]
            fails.append(f"{label}编号非单调（出现顺序={seen}，乱序值={bad}）")
        dup = [x for x in seen if seen.count(x) > 1]
        if dup:
            fails.append(f"{label}编号有重复（={sorted(set(dup))}）；出现序列={seen}")
    return fails, seen


def check_author_year(text):
    """著者-年份制 LaTeX 源码级反模式扫描（对应 SOP §4.5）。

    返回 (fails, hits) —— fails 为失败描述列表，hits 为命中上下文片段列表。
    仅覆盖两类可机检反模式；嵌套括号等需在渲染 PDF 中人工核对。
    """
    fails = []
    hits = []
    for label, regex in (("拆分逗号组", AY_SPLIT_CITE_RE), ("叙述式重名", AY_NARRATIVE_RE)):
        for m in regex.finditer(text):
            ctx = text[max(0, m.start() - 40):m.end() + 20].replace("\n", " ")
            hits.append((label, ctx))
    if hits:
        fails.append(f"著者-年份制反模式：发现 {len(hits)} 处（见下方明细）；建议按 SOP §4.5 修正为 \\cite{{a,b}} 合并组 / \\textcite")
    return fails, hits


def main():
    args = parse_args()
    text = read_text(args.manuscript)
    body, refs = split_body_refs(text, args.refs_heading)

    print("=" * 60)
    print(f"投稿前门禁：{os.path.basename(args.manuscript)}")
    if args.author_year:
        print("模式：著者-年份制（biblatex / JAIR 一类）")
    print("=" * 60)

    all_fails = []

    # 著者-年份制：仅扫源码反模式，跳过编号制 B 组
    if args.author_year:
        print("\n[AY 组] 著者-年份制 \\cite 反模式（源码扫描）")
        ay_fails, ay_hits = check_author_year(text)
        for label, ctx in ay_hits:
            print(f"  ✗ [{label}] ...{ctx}...")
        if ay_fails:
            all_fails.extend(ay_fails)
        else:
            print("  ✓ 未发现拆分逗号组 / 叙述式重名反模式")
        print("  - 注：B 组（零孤儿/缺项/越界/连续）不适用于 author-year，已跳过；嵌套括号请在渲染 PDF 中人工核对")
    else:
        # B 组 引用
        print("\n[B 组] 引用正确性（零孤儿/缺项/越界/连续）")
        ref_fails = check_references(body, refs)
        if ref_fails:
            for f in ref_fails:
                print("  ✗ " + f)
            all_fails.extend(ref_fails)
        else:
            print("  ✓ 通过")

    # C 组 图表
    print("\n[C 组] 图表编号单调性")
    fig_fails, fig_seen = check_captions(body, "图(Fig)", FIG_RE)
    tab_fails, tab_seen = check_captions(body, "表(Table)", TABLE_RE)
    for f in fig_fails + tab_fails:
        print("  ✗ " + f)
    all_fails.extend(fig_fails + tab_fails)
    if not fig_fails:
        print(f"  ✓ 图编号通过（出现序列={fig_seen}）" if fig_seen else "  - 未发现图题注")
    if not tab_fails:
        print(f"  ✓ 表编号通过（出现序列={tab_seen}）" if tab_seen else "  - 未发现表题注")

    # 引用计数摘要
    cited = collect_cited(body)
    entries = collect_entries(refs)
    print(f"\n[摘要] 正文引用号 {len(cited)} 个；参考文献条目 {len(entries)} 条")

    print("\n" + "=" * 60)
    if all_fails:
        print(f"结果：FAIL（{len(all_fails)} 项待修）")
        for f in all_fails:
            print("  - " + f)
        sys.exit(1)
    else:
        print("结果：PASS（引用与图表门禁全部通过；人工复核项见 SOP 5.2）")
        sys.exit(0)


if __name__ == "__main__":
    main()
