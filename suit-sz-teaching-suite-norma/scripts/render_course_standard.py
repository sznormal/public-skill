#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把结构化 JSON 渲染成排版合规的《课程标准》.docx。

以技能内置空白模板作为「外壳」（保留页面设置、页边距、页眉页脚），
清空其正文后按排版规则重建内容，避免模板遗留的括号提示文字混进成品。

用法：
    python render_course_standard.py --data draft.json --out 课程标准-XXX.docx
    python render_course_standard.py --demo --out demo.docx
    python render_course_standard.py --data draft.json --no-template --out out.docx

JSON 结构：
{
  "title": "《嵌入式Linux应用》课程标准",
  "header": [
    [["课程类别：", "专业核心课"]],
    [["适用专业：", "嵌入式技术（三年制）"], ["授课单位：", "中德机器人学院"]],
    [["学分：", "4"], ["学时：", "64"]]
  ],
  "blocks": [
    {"type": "heading",   "level": 1, "text": "一、课程定位和课程设计"},
    {"type": "heading",   "level": 2, "text": "（一）课程性质"},
    {"type": "paragraph", "text": "本课程是……"},
    {"type": "table", "caption": "表1 学时分配表",
     "rows": [["序号", "教学内容", "学时"], ["1", "系统构建", "16"]]}
  ]
}

排版规则见 references/format-rules.md；产出后请用 validate_docx.py 回读校验。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from docx import Document                                        # noqa: E402
from docx.enum.text import WD_ALIGN_PARAGRAPH                    # noqa: E402
from docx.oxml.ns import qn                                      # noqa: E402

from docx_helpers import (                                       # noqa: E402
    drop_element, insert_heading_table_before, set_exact_line_spacing,
    set_first_line_chars, set_no_indent, set_run_font,
)

FONT_TITLE = '黑体'
FONT_H1 = '黑体'
FONT_H2 = '楷体'
FONT_BODY = '仿宋'
SIZE_TITLE = 22
SIZE_BODY = 16
LINE_PT = 28

DEMO = {
    "title": "《示例课程》课程标准",
    "header": [
        [["课程类别：", "专业核心课"]],
        [["适用专业：", "示例专业（三年制）"], ["授课单位：", "示例学院"]],
        [["学分：", "4"], ["学时：", "64"]],
        [["编写执笔人及编写日期：", "示例 2026/08/31"]],
        [["审定负责人及审定日期：", "示例 2026/09/05"]],
    ],
    "blocks": [
        {"type": "heading", "level": 1, "text": "一、课程定位和课程设计"},
        {"type": "heading", "level": 2, "text": "（一）课程性质"},
        {"type": "paragraph", "text": "本课程是示例专业的专业核心课程，面向嵌入式系统开发岗位。"},
        {"type": "heading", "level": 1, "text": "二、课程目标"},
        {"type": "heading", "level": 2, "text": "（三）课程思政融入表"},
        {"type": "table", "caption": "表2 课程思政融入表",
         "rows": [["知识点", "思政融入点", "思政案例"],
                  ["交叉编译", "自主可控", "国产工具链自主攻关"],
                  ["文件系统烧录", "工匠精神", "大国工匠胡双钱"]]},
        {"type": "heading", "level": 1, "text": "三、课程内容与要求"},
        {"type": "table", "caption": "表1 学时分配表",
         "rows": [["序号", "教学内容", "学时", "讲授", "实践"],
                  ["1", "环境搭建与交叉编译", "16", "8", "8"],
                  ["2", "驱动开发与文件系统", "24", "12", "12"]]},
    ],
}


def build_document(payload: dict, template: Path | None) -> Document:
    if template is not None and template.is_file():
        doc = Document(str(template))
        body = doc.element.body
        for child in list(body):
            if child.tag != qn('w:sectPr'):
                drop_element(child)
    else:
        doc = Document()

    para = doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_exact_line_spacing(para, LINE_PT)
    set_no_indent(para)
    set_run_font(para.add_run(payload.get("title", "《XXX》课程标准")),
                 FONT_TITLE, size=SIZE_TITLE, bold=False)

    for row in payload.get("header", []):
        p = doc.add_paragraph()
        set_exact_line_spacing(p, LINE_PT)
        set_no_indent(p)
        for pair in row:
            label = str(pair[0])
            value = str(pair[1]) if len(pair) > 1 else ""
            set_run_font(p.add_run(label), FONT_BODY, size=SIZE_BODY, bold=True)
            if value:
                set_run_font(p.add_run(value), FONT_BODY, size=SIZE_BODY, bold=False)

    for block in payload.get("blocks", []):
        kind = block.get("type")
        if kind == "heading":
            level = int(block.get("level", 1))
            p = doc.add_paragraph()
            set_exact_line_spacing(p, LINE_PT)
            if level <= 1:
                set_no_indent(p)
                font = FONT_H1
            else:
                set_first_line_chars(p, 2, size_pt=SIZE_BODY)
                font = FONT_H2
            set_run_font(p.add_run(str(block.get("text", ""))),
                         font, size=SIZE_BODY, bold=False)
        elif kind == "paragraph":
            p = doc.add_paragraph()
            set_exact_line_spacing(p, LINE_PT)
            set_first_line_chars(p, 2, size_pt=SIZE_BODY)
            set_run_font(p.add_run(str(block.get("text", ""))),
                         FONT_BODY, size=SIZE_BODY, bold=False)
        elif kind == "table":
            rows = block.get("rows") or []
            if not rows:
                continue
            caption = block.get("caption") or ""
            rows = [[("" if c is None else str(c)) for c in row] for row in rows]
            insert_heading_table_before(
                doc, None, caption, rows,
                title_font=FONT_BODY, title_size=SIZE_BODY,
                body_font=FONT_BODY, body_size=SIZE_BODY,
            )
    return doc


def main() -> int:
    ap = argparse.ArgumentParser(description="渲染《课程标准》.docx")
    ap.add_argument("--data", help="结构化草稿 JSON 路径")
    ap.add_argument("--out", required=True, help="输出 .docx 路径")
    ap.add_argument("--template", help="用作外壳的空白模板路径")
    ap.add_argument("--no-template", action="store_true", help="不使用模板外壳，直接新建文档")
    ap.add_argument("--demo", action="store_true", help="使用内置示例数据")
    args = ap.parse_args()

    if args.demo:
        payload = DEMO
    elif args.data:
        path = Path(args.data)
        if not path.is_file():
            print(f"[错误] 找不到数据文件：{path}", file=sys.stderr)
            return 1
        payload = json.loads(path.read_text(encoding="utf-8"))
    else:
        ap.print_help()
        return 1

    template = None
    if not args.no_template:
        template = Path(args.template) if args.template else SKILL_DIR / "templates" / "课程标准.docx"

    doc = build_document(payload, template)
    out = Path(args.out)
    if out.parent and str(out.parent):
        out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out))
    print(f"[OK] 已生成 {out}")
    print(f"     外壳模板：{template if template else '（未使用，直接新建）'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
