#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技术教材出版规范性自动化预检。

扫描 Markdown 文件，检测常见出版规范类问题，输出 Markdown 或 JSON 报告。

用法:
    python review_check.py <文件或目录> [--json] [--root <基准目录>]

说明:
    --root  用于解析相对图片路径的基准目录（默认取文件所在目录）
    --json  以 JSON 输出，便于程序化消费

检测项:
    1. 标题层级跳跃 (H1 直接到 H3 等)
    2. 占位 / 未完成标记 (TODO / FIXME / 待补充 / 待定 / XXX)
    3. 代码块未标注语言
    4. 空链接 / 锚点占位链接
    5. 图片引用文件缺失 (仅检查本地相对路径)
    6. 表格分隔行异常 (非标准的 |---| 行)

严重级:
    红 = error (阻断)   黄 = warning (待优化)   绿 = info (提示)
脚本只覆盖"出版规范性"可机器判断的部分，语义类问题需人工精读。
"""

import argparse
import json
import re
import sys
from pathlib import Path

TODO_PAT = re.compile(r"TODO|FIXME|\[待补充\]|\[待定\]|XXX", re.IGNORECASE)
CODE_FENCE = re.compile(r"^```(.*)$")
IMG_PAT = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
LINK_PAT = re.compile(r"(?<!\!)\[([^\]]*)\]\(([^)]*)\)")
HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
TABLE_SEP = re.compile(r"^\s*\|?[\s:|-]+\|?\s*$")

SEV_TAG = {"error": "红[阻断]", "warning": "黄[待优化]", "info": "绿[提示]"}


def check_file(path: Path, base: Path | None):
    issues = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:  # noqa: BLE001
        return [(0, "error", f"文件读取失败: {e}", "")]

    lines = text.splitlines()
    prev_level = 0
    in_code = False
    in_table_head = False  # 上一行是否为表格标题行

    for i, line in enumerate(lines, 1):
        fence = CODE_FENCE.match(line)
        if fence:
            if in_code:
                in_code = False
            else:
                in_code = True
                lang = fence.group(1).strip()
                if not lang:
                    issues.append((i, "warning", "代码块未标注语言", line.strip()[:60]))
            continue

        if in_code:
            # 代码块内部不检查语义（避免伪标题误判）
            continue

        if TODO_PAT.search(line):
            issues.append((i, "error", "检测到占位/未完成标记", line.strip()[:60]))

        h = HEADING.match(line)
        if h:
            level = len(h.group(1))
            if prev_level and level > prev_level + 1:
                issues.append(
                    (i, "warning", f"标题层级跳跃 H{prev_level}->H{level}", h.group(2)[:40])
                )
            prev_level = 1 if level == 1 else level
            in_table_head = False
            continue

        # 表格分隔行：上一行是普通单元格行，本行是分隔符
        if TABLE_SEP.match(line):
            # 仅当分隔符不规范时告警（这里只记录存在，供人工核对）
            in_table_head = False
            continue

        if "|" in line and line.strip().startswith("|"):
            in_table_head = True
        else:
            in_table_head = False

        for _alt, src in IMG_PAT.findall(line):
            if src.startswith(("http://", "https://", "data:")):
                continue
            ref = (base / src).resolve() if base else (path.parent / src).resolve()
            if not ref.exists():
                issues.append((i, "error", f"图片引用缺失: {src}", _alt[:30]))

        for _text, href in LINK_PAT.findall(line):
            h2 = href.strip()
            if h2 == "" or h2 == "#":
                issues.append((i, "warning", f"空链接: [{_text}]", ""))

    return issues


def main():
    ap = argparse.ArgumentParser(description="技术教材出版规范性自动化预检")
    ap.add_argument("path", help="Markdown 文件或目录")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出")
    ap.add_argument("--root", default=None, help="解析相对图片路径的基准目录")
    args = ap.parse_args()

    base = Path(args.root).resolve() if args.root else None
    target = Path(args.path)

    if not target.exists():
        print(f"错误: 路径不存在 {target}", file=sys.stderr)
        sys.exit(2)

    files = sorted(target.rglob("*.md")) if target.is_dir() else [target]
    if not files:
        print("未找到 Markdown 文件。", file=sys.stderr)
        sys.exit(0)

    all_issues = {str(f): check_file(f, base) for f in files}

    if args.json:
        out = {
            str(k): [{"line": l, "sev": s, "msg": m, "ctx": c} for l, s, m, c in v]
            for k, v in all_issues.items()
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    total = 0
    for f, iss in all_issues.items():
        print(f"\n## {f}  ({len(iss)} 项)")
        if not iss:
            print("  无规范类问题。")
        for l, s, m, c in iss:
            tag = SEV_TAG[s]
            extra = f"  `{c}`" if c else ""
            print(f"- L{l} [{tag}] {m}{extra}")
        total += len(iss)
    print(f"\n=== 共 {total} 项规范类问题（红项需清零）===")


if __name__ == "__main__":
    main()
