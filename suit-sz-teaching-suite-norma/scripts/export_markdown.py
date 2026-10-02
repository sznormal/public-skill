#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
零依赖降级产出（L2）：把结构化 JSON 渲染成 Markdown 教学文件，并附「版式对照表」。

仅用标准库，任何 Python 3.8+ 都能跑。当 python-docx 不可用时用它交付，
用户把内容粘贴进本校 Word 模板后，按文末对照表设置字体/字号/缩进即可。

用法：
    python scripts/export_markdown.py --data draft.json --type standard --out 课程标准-XXX.md
    python scripts/export_markdown.py --demo            # 生成示例文件，用于验证渲染效果

JSON 结构（blocks 流式，三种类型）：
{
  "title": "《嵌入式Linux应用》课程标准",
  "meta":  {"课程类别": "专业核心课", "适用专业": "嵌入式技术（三二分段）"},
  "blocks": [
    {"type": "heading",   "level": 1, "text": "一、课程定位和课程设计"},
    {"type": "heading",   "level": 2, "text": "（一）课程性质"},
    {"type": "paragraph", "text": "本课程是……"},
    {"type": "table", "caption": "表1 学时分配表",
     "rows": [["模块", "讲授", "实践", "小计"], ["模块一 系统构建", "8", "8", "16"]]}
  ]
}

type 取值：standard（课程标准）/ lesson（教案）/ schedule（授课计划）
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# 版式对照表：告诉用户在 Word 模板里每个元素该怎么设字体
FORMAT_GUIDE = {
    "standard": [
        ("文档标题《XXX》课程标准", "黑体", "22pt（二号）", "居中", "顶格"),
        ("一级标题（一、二、…）", "黑体", "16pt（三号）", "左", "**顶格**"),
        ("二级标题（（一）（二）、教材使用）", "楷体", "16pt（三号）", "左", "2 字符"),
        ("正文 / 编号子标题 / 表格", "仿宋", "16pt（三号）", "左", "2 字符"),
        ("头部信息栏 · 标签（如 课程类别：）", "仿宋 **加黑**", "16pt（三号）", "左", "顶格"),
        ("头部信息栏 · 冒号后的值", "仿宋 不加黑", "16pt（三号）", "左", "顶格"),
        ("表格标题", "仿宋", "16pt（三号）", "居中", "顶格"),
    ],
    "lesson": [
        ("封面标题", "方正公文小标宋 / 华文中宋", "22–26pt", "居中", "—"),
        ("封面填写值", "楷体_GB2312", "15pt（小三）", "居中 + 下划线", "—"),
        ("教案表头标签", "黑体", "14pt", "左", "—"),
        ("小标题（教学目的及要求 等）", "楷体", "14pt", "左", "—"),
        ("表格填写值", "仿宋_GB2312", "14pt（四号）", "左", "2 字符"),
    ],
    "schedule": [
        ("封面标题", "方正公文小标宋 / 华文中宋", "22–26pt", "居中", "—"),
        ("封面填写值", "楷体_GB2312", "15pt（小三）", "居中 + 下划线", "—"),
        ("表格0 填写值", "楷体_GB2312", "12pt", "左", "—"),
        ("周次表填写值", "仿宋_GB2312", "10pt", "日期/课型/时数/平台居中，内容/作业左", "—"),
    ],
}

GENERAL_NOTES = [
    "行距：固定值 28 磅，段前段后 0（以本校模板实测为准）。",
    "中文字体必须设置「中文字体 / eastAsia」属性，只改西文字体对中文无效。",
    "首行缩进请用「2 字符」（对应 w:firstLineChars=200），不要用固定磅值，避免换字号后错位。",
    "标题必须位于其所属表格的**上方**。",
    "生成新文件另存，不要覆盖正在编辑的模板。",
]

DEMO = {
    "title": "《示例课程》课程标准",
    "meta": {"课程类别": "专业核心课", "适用专业": "示例专业（三年制）", "学分": "4", "学时": "64"},
    "blocks": [
        {"type": "heading", "level": 1, "text": "一、课程定位和课程设计"},
        {"type": "heading", "level": 2, "text": "（一）课程性质"},
        {"type": "paragraph", "text": "本课程是示例专业的核心课程，面向……"},
        {"type": "table", "caption": "表1 学时分配表",
         "rows": [["模块", "讲授", "实践", "小计"],
                  ["模块一 环境搭建", "8", "8", "16"],
                  ["模块二 驱动开发", "12", "12", "24"]]},
    ],
}


def render(data: dict, doc_type: str) -> str:
    lines: list[str] = []

    title = data.get("title", "（未命名教学文件）")
    lines.append(f"# {title}")
    lines.append("")

    meta = data.get("meta") or {}
    if meta:
        for k, v in meta.items():
            lines.append(f"**{k}：** {v}")
        lines.append("")

    for b in data.get("blocks", []):
        t = b.get("type")
        if t == "heading":
            level = int(b.get("level", 1))
            lines.append(f"{'#' * min(level + 1, 6)} {b.get('text', '')}")
            lines.append("")
        elif t == "paragraph":
            lines.append(b.get("text", ""))
            lines.append("")
        elif t == "table":
            cap = b.get("caption")
            if cap:
                lines.append(f"**{cap}**")
                lines.append("")
            rows = b.get("rows") or []
            if rows:
                head = rows[0]
                lines.append("| " + " | ".join(str(c) for c in head) + " |")
                lines.append("|" + "|".join(["---"] * len(head)) + "|")
                for r in rows[1:]:
                    cells = [str(c) for c in r] + [""] * (len(head) - len(r))
                    lines.append("| " + " | ".join(cells[: len(head)]) + " |")
                lines.append("")

    # 版式对照表附录（L2 降级的核心交付物之一）
    lines.append("---")
    lines.append("")
    lines.append("## 附：Word 版式对照表")
    lines.append("")
    lines.append("> 本文件由 Markdown 降级模式生成。把上方内容粘贴进本校 Word 模板后，"
                 "按下表逐项设置字体、字号与缩进，即可获得与模板一致的排版效果。")
    lines.append("")
    lines.append("| 元素 | 字体 | 字号 | 对齐 | 首行缩进 |")
    lines.append("|---|---|---|---|---|")
    for row in FORMAT_GUIDE.get(doc_type, FORMAT_GUIDE["standard"]):
        lines.append("| " + " | ".join(str(c) for c in row) + " |")
    lines.append("")
    lines.append("### 通用注意事项")
    lines.append("")
    for n in GENERAL_NOTES:
        lines.append(f"- {n}")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="零依赖 Markdown 降级产出")
    ap.add_argument("--data", help="结构化草稿 JSON 路径")
    ap.add_argument("--type", default="standard",
                    choices=["standard", "lesson", "schedule"], help="文档类型")
    ap.add_argument("--out", help="输出 .md 路径（缺省打印到标准输出）")
    ap.add_argument("--demo", action="store_true", help="用内置示例渲染，用于验证")
    args = ap.parse_args()

    if args.demo:
        data = DEMO
    elif args.data:
        p = Path(args.data)
        if not p.exists():
            print(f"[错误] 找不到数据文件: {p}", file=sys.stderr)
            return 1
        data = json.loads(p.read_text(encoding="utf-8"))
    else:
        ap.print_help()
        return 1

    md = render(data, args.type)

    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md, encoding="utf-8")
        print(f"[OK] 已生成 {out}（{len(md)} 字符）")
    else:
        print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
