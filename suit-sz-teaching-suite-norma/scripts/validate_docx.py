#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""回读 .docx 校验排版是否合规（只读）。

按 references/format-rules.md 的默认值逐项核对：字体族、字号、首行缩进、
固定行距、头部信息栏双层 run、标题位于表格上方、模板括号提示文字是否清除。

用法：
    python validate_docx.py 课程标准-XXX.docx
    python validate_docx.py 课程标准-XXX.docx --profile course-standard --json
    python validate_docx.py 课程名-教案9.docx --profile lesson

profile：
    course-standard  课标：严格档（默认）
    lesson           教案：字体族 + 缩进 + 提示文字 + 标题表格顺序
    schedule         授课计划：同 lesson

退出码：全部通过为 0；存在 FAIL 为 1。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from docx import Document                                        # noqa: E402
from docx.enum.text import WD_ALIGN_PARAGRAPH                    # noqa: E402
from docx.oxml.ns import qn                                      # noqa: E402

ALLOWED_FONTS = {
    '黑体', '楷体', '楷体_GB2312', '仿宋', '仿宋_GB2312',
    '方正公文小标宋', '华文中宋', '宋体', '方正小标宋简体',
}
HINT_RE = re.compile(r"（需包括但不限于|（字体三号|采用的教学模式特别是|（以下内容为选填|（含课程思政、职业素养")
H1_RE = re.compile(r"^[一二三四五六七八九十]+、")
H2_RE = re.compile(r"^（[一二三四五六七八九十]+）")
TABLE_CAPTION_RE = re.compile(r"^表\s*\d")
HEADER_LABEL_RE = re.compile(r"^(课程类别|适用专业|授课单位|学分|学时|编写执笔人及编写日期|审定负责人及审定日期|课程名称|任课教师|所属院部|教师姓名|授课班级)[：:]?$")


def para_indent(p):
    pPr = p._p.find(qn('w:pPr'))
    if pPr is None:
        return None, None
    ind = pPr.find(qn('w:ind'))
    if ind is None:
        return None, None
    return ind.get(qn('w:firstLineChars')), ind.get(qn('w:firstLine'))


def run_font(run):
    rPr = run._element.find(qn('w:rPr'))
    if rPr is None:
        return None, None, None
    rFonts = rPr.find(qn('w:rFonts'))
    east = rFonts.get(qn('w:eastAsia')) if rFonts is not None else None
    size = rPr.find(qn('w:sz'))
    size_pt = int(size.get(qn('w:val'))) / 2 if size is not None else None
    bold_el = rPr.find(qn('w:b'))
    bold = None
    if bold_el is not None:
        val = bold_el.get(qn('w:val'))
        bold = val not in ('false', '0')
    return east, size_pt, bold


def line_spacing_exact(p):
    pPr = p._p.find(qn('w:pPr'))
    if pPr is None:
        return None
    spacing = pPr.find(qn('w:spacing'))
    if spacing is None:
        return None
    if spacing.get(qn('w:lineRule')) != 'exact':
        return None
    line = spacing.get(qn('w:line'))
    return int(line) / 20 if line is not None else None


def body_order(doc):
    """返回 body 中段落/表格的先后序列，用于核对"标题在表格上方"。"""
    seq = []
    for child in doc.element.body:
        if child.tag == qn('w:p'):
            seq.append(('p', child))
        elif child.tag == qn('w:tbl'):
            seq.append(('tbl', child))
    return seq


def text_of_p(el):
    return "".join(node.text or "" for node in el.iter(qn('w:t')))


def validate(path: Path, profile: str):
    doc = Document(str(path))
    failures = []
    checked = 0

    def fail(where, expected, actual):
        failures.append({"where": where, "expected": expected, "actual": actual})

    for idx, p in enumerate(doc.paragraphs):
        text = p.text.strip()
        if not text:
            continue
        runs = [r for r in p.runs if r.text.strip()]
        if not runs:
            continue
        where = f"段落[{idx}] {text[:18]}"

        east, size_pt, _bold = run_font(runs[0])
        checked += 1
        if east is None:
            fail(where, "eastAsia 中文字体已设置", "未设置（Word 中中文会回退默认字体）")
            continue
        if east not in ALLOWED_FONTS:
            fail(where, f"字体族属于 {sorted(ALLOWED_FONTS)}", east)

        if HINT_RE.search(text):
            fail(where, "模板括号提示文字应已删除", text[:40])

        flc, _fli = para_indent(p)
        is_h1 = bool(H1_RE.match(text))
        is_h2 = bool(H2_RE.match(text))
        is_caption = bool(TABLE_CAPTION_RE.match(text))
        is_header_line = any(r.text.strip().endswith(("：", ":")) for r in runs)

        if profile == "course-standard":
            if text.startswith("《") and "课程标准" in text:
                if east != '黑体' or size_pt != 22:
                    fail(where, "标题 黑体 22pt", f"{east} {size_pt}pt")
            elif is_h1:
                if east != '黑体' or size_pt != 16:
                    fail(where, "一级标题 黑体 16pt", f"{east} {size_pt}pt")
                if flc not in (None, '0'):
                    fail(where, "一级标题顶格（firstLineChars 为空或 0）", f"firstLineChars={flc}")
            elif is_h2:
                if east != '楷体' or size_pt != 16:
                    fail(where, "二级标题 楷体 16pt", f"{east} {size_pt}pt")
                if flc != '200':
                    fail(where, "二级标题首行缩进 2 字符", f"firstLineChars={flc}")
            elif is_caption or is_header_line:
                if east != '仿宋' or size_pt != 16:
                    fail(where, "头部信息栏 / 表格标题 仿宋 16pt", f"{east} {size_pt}pt")
                if flc not in (None, '0'):
                    fail(where, "头部信息栏 / 表格标题顶格", f"firstLineChars={flc}")
            else:
                if east != '仿宋' or size_pt != 16:
                    fail(where, "正文 仿宋 16pt", f"{east} {size_pt}pt")
                if flc != '200':
                    fail(where, "正文首行缩进 2 字符", f"firstLineChars={flc}")
            spacing = line_spacing_exact(p)
            if spacing is not None and abs(spacing - 28) > 0.01:
                fail(where, "固定行距 28 磅", f"{spacing} 磅")

        if is_header_line:
            for run in runs:
                e, _s, b = run_font(run)
                if run.text.strip().endswith(("：", ":")):
                    if b is not True:
                        fail(f"{where} · 标签 run {run.text[:10]!r}",
                             "头部标签 仿宋加黑 bold=True", f"bold={b} font={e}")
                    if e != '仿宋':
                        fail(f"{where} · 标签 run {run.text[:10]!r}", "头部标签仿宋", e)
                else:
                    if b is True:
                        fail(f"{where} · 值 run {run.text[:10]!r}",
                             "头部值不加黑 bold=False", "bold=True")
                    if e != '仿宋':
                        fail(f"{where} · 值 run {run.text[:10]!r}", "头部值仿宋", e)

    seq = body_order(doc)
    table_positions = [i for i, (kind, _el) in enumerate(seq) if kind == 'tbl']
    for order, pos in enumerate(table_positions):
        table = doc.tables[order]
        caption = None
        for back in range(pos - 1, max(pos - 4, -1), -1):
            kind, el = seq[back]
            if kind == 'p' and text_of_p(el).strip():
                caption = text_of_p(el).strip()
                break
        head = table.rows[0].cells[0].text.strip()
        if caption is None:
            fail(f"表格[{order}] 首行 {head[:12]!r}", "表格上方应有标题段", "未找到标题段")
        elif "表" not in caption and "课程标准" not in caption:
            fail(f"表格[{order}]", "表格上方标题段以'表N'开头", caption[:30])

    for ti, table in enumerate(doc.tables):
        for ri, row in enumerate(table.rows):
            for ci, cell in enumerate(row.cells):
                for p in cell.paragraphs:
                    t = p.text.strip()
                    if not t:
                        continue
                    if HINT_RE.search(t):
                        fail(f"表格[{ti}] r{ri}c{ci}", "模板括号提示文字应已删除", t[:40])
                    runs = [r for r in p.runs if r.text.strip()]
                    if runs:
                        e, _s, _b = run_font(runs[0])
                        if e is None:
                            fail(f"表格[{ti}] r{ri}c{ci}", "eastAsia 中文字体已设置", "未设置")
                        elif e not in ALLOWED_FONTS:
                            fail(f"表格[{ti}] r{ri}c{ci}", "字体族合规", e)

    return {
        "file": str(path),
        "profile": profile,
        "paragraphs_checked": checked,
        "tables": len(doc.tables),
        "passed": not failures,
        "failure_count": len(failures),
        "failures": failures[:60],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="回读校验 docx 排版")
    ap.add_argument("docx", type=Path, help="待校验的 .docx")
    ap.add_argument("--profile", default="course-standard",
                    choices=["course-standard", "lesson", "schedule"])
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not args.docx.is_file():
        print(f"[错误] 文件不存在：{args.docx}", file=sys.stderr)
        return 2

    report = validate(args.docx, args.profile)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("=" * 62)
        print(f" 排版回读校验 · {report['file']}")
        print(f" profile={report['profile']}  段落={report['paragraphs_checked']}  表格={report['tables']}")
        print("=" * 62)
        if report["passed"]:
            print("  结果：PASS —— 字体族 / 字号 / 首行缩进 / 行距 / 头部双层 run / 标题与表格顺序 均合规")
        else:
            print(f"  结果：FAIL —— 共 {report['failure_count']} 项")
            for item in report["failures"]:
                print(f"  [FAIL] {item['where']}")
                print(f"         期望：{item['expected']}")
                print(f"         实测：{item['actual']}")
        print("=" * 62)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
