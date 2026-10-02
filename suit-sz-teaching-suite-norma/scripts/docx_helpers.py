# -*- coding: utf-8 -*-
"""教学文档 docx 通用操作（仅依赖 python-docx）。

用法：
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(<本技能目录>) / "scripts"))
    from docx_helpers import *

约定：
    - 所有函数只改传入的 docx 对象，不读写文件；文件落盘由调用方负责。
    - 中文必须写 w:rFonts/@w:eastAsia，run.font.name 对中文无效。
    - 段落首行缩进写 w:ind/@w:firstLineChars，随字号自适应，不用固定 twips。
"""
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


# ---------------------------------------------------------------- XML 基础

def drop_element(el):
    """从 XML 树中移除元素 el（等价于删除该子节点）。"""
    parent = el.getparent()
    if parent is None:
        return False
    del parent[list(parent).index(el)]
    return True


def _ind_element(p):
    pPr = p._p.get_or_add_pPr()
    ind = pPr.find(qn('w:ind'))
    if ind is None:
        ind = OxmlElement('w:ind')
        pPr.append(ind)
    return ind


def set_run_font(run, name, size=None, bold=None, underline=None):
    """设置 run 字体。中文走 eastAsia，否则 Word 中中文不生效。"""
    run.font.name = name
    rPr = run._element.get_or_add_rPr()
    rPr.get_or_add_rFonts().set(qn('w:eastAsia'), name)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    if underline is not None:
        run.font.underline = underline
    return run


def set_first_line_chars(p, chars=2, size_pt=14):
    """首行缩进 chars 个字符；firstLine 兜底值按字号换算。"""
    ind = _ind_element(p)
    ind.set(qn('w:firstLineChars'), str(int(chars * 100)))
    ind.set(qn('w:firstLine'), str(int(chars * 100 * size_pt / 10)))
    return p


def set_no_indent(p):
    """显式顶格：清零首行缩进。"""
    ind = _ind_element(p)
    ind.set(qn('w:firstLineChars'), '0')
    ind.set(qn('w:firstLine'), '0')
    return p


def set_exact_line_spacing(p, pt=28):
    """固定行距（课标正文 28 磅），段前段后 0。"""
    pf = p.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    pf.line_spacing = Pt(pt)
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    return p


# ---------------------------------------------------------------- 段落

def clear_runs(p):
    """删除段落上的全部 run，保留段落本身与段落格式。"""
    for r in list(p.runs):
        drop_element(r._element)
    return p


def reset_para(p, text, name=None, size=None, bold=None, underline=None, align=None):
    """清空段落全部 run 后写入单 run 文本（可选格式）。"""
    clear_runs(p)
    if align is not None:
        p.alignment = align
    run = p.add_run(text)
    if name is not None:
        set_run_font(run, name, size=size, bold=bold, underline=underline)
    return run


def add_header_para(doc, segments, name='仿宋', size=16):
    """头部信息栏一行：segments = [(标签, 值), ...]，标签加黑、值不加黑，顶格。"""
    p = doc.add_paragraph()
    set_no_indent(p)
    for label, value in segments:
        set_run_font(p.add_run(label), name, size=size, bold=True)
        if value:
            set_run_font(p.add_run(value), name, size=size, bold=False)
    return p


# ---------------------------------------------------------------- 单元格

def clear_cell(cell, line1=True):
    """清空单元格：删多余段落、清首段 run，返回可写首段。"""
    ps = list(cell.paragraphs)
    for p in ps[1:]:
        drop_element(p._element)
    p = ps[0]
    for r in list(p.runs):
        drop_element(r._element)
    if line1:
        p.paragraph_format.line_spacing = 1.0
    return p


def strip_cell(cell, keep_label=False):
    """删除模板占位段与括号提示文字。

    keep_label=True：保留首段（带标签行）并保留其 run，用于"标签+值"单元格。
    keep_label=False：清空首段，用于空值格。
    返回可写首段。
    """
    ps = list(cell.paragraphs)
    for p in ps[1:]:
        drop_element(p._element)
    p = ps[0]
    if keep_label:
        p.paragraph_format.line_spacing = 1.0
        return p
    for r in list(p.runs):
        drop_element(r._element)
    p.paragraph_format.line_spacing = 1.0
    return p


def value_cell(row):
    """合并单元格场景：按去重文本取"标签格之后"的值格。"""
    seen = []
    for c in row.cells:
        t = c.text.strip()
        if t not in [x[0] for x in seen]:
            seen.append((t, c))
    return seen[1][1] if len(seen) >= 2 else seen[0][1]


def _write_lines(cell, lines, name, size, indent, align, start_index=0):
    """从 start_index 段起写入 lines；start_index=0 表示复用单元格首段。"""
    paragraphs = list(cell.paragraphs)
    for offset, line in enumerate(lines):
        idx = start_index + offset
        if idx < len(paragraphs):
            p = paragraphs[idx]
            clear_runs(p)
        else:
            p = cell.add_paragraph()
        p.paragraph_format.line_spacing = 1.0
        if align is not None:
            p.alignment = align
        if indent:
            set_first_line_chars(p, 2, size_pt=size)
        else:
            set_no_indent(p)
        text = str(line)
        run = p.add_run(text[1:] if text.startswith('#') else text)
        set_run_font(run, name, size=size, bold=False)


def write_cell(cell, lines, name='仿宋_GB2312', size=14, indent=True, align=None):
    """覆盖式写入空值格：先裁剪模板占位段，再用首段起逐行写入。"""
    strip_cell(cell, keep_label=False)
    _write_lines(cell, lines, name, size, indent, align, start_index=0)
    return cell


def append_cell(cell, lines, name='仿宋_GB2312', size=14, indent=True, align=None):
    """追加式写入带标签格：保留标签首段，值写入其后的段落。"""
    strip_cell(cell, keep_label=True)
    _write_lines(cell, lines, name, size, indent, align, start_index=1)
    return cell


def fill_lines(row, lines, name='楷体_GB2312', size=12):
    """表格0式多行填写：清值格后逐行写入。"""
    return write_cell(value_cell(row), lines, name=name, size=size, indent=False)


def fill_center(cell, text, name='仿宋_GB2312', size=10):
    """周次表式短值：居中、无缩进。"""
    return write_cell(cell, [text], name=name, size=size, indent=False,
                      align=WD_ALIGN_PARAGRAPH.CENTER)


def fill_left(cell, text, name='仿宋_GB2312', size=10):
    """周次表式长文本：左对齐、无缩进。"""
    return write_cell(cell, [text], name=name, size=size, indent=False,
                      align=WD_ALIGN_PARAGRAPH.LEFT)


def fill_cover_label(doc, label, value):
    """封面"标签：值"段落：保留标签 run 与下划线格式，改写值 run。"""
    for p in doc.paragraphs:
        if p.text.strip().startswith(label):
            if len(p.runs) >= 2:
                p.runs[1].text = '  ' + value
                for r in list(p.runs[2:]):
                    drop_element(r._element)
            return True
    return False


# ---------------------------------------------------------------- 表格

def insert_heading_table_before(doc, anchor_para, title, rows, *,
                                title_font='仿宋', title_size=16,
                                body_font='仿宋', body_size=16, style=None):
    """在 anchor_para 之前依次插入「标题段 + 表格」，标题恒在表格上方。

    anchor_para : 段落对象（一般是模板中占位段落），新内容插在它之前
    title       : 表格上方标题文字
    rows        : list[list[str]]，第一行为表头
    返回 (title_para, table)
    """
    body = doc.element.body
    sectPr = body.find(qn('w:sectPr'))

    title_p = doc.add_paragraph()
    set_no_indent(title_p)
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title_p.add_run(title)
    set_run_font(run, title_font, size=title_size, bold=False)

    table = doc.add_table(rows=len(rows), cols=len(rows[0]))
    if style:
        table.style = style

    anchor = anchor_para._p if anchor_para is not None else sectPr
    anchor.addprevious(title_p._p)        # 先标题
    anchor.addprevious(table._tbl)        # 再表格 —— 顺序不可颠倒

    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            cell = table.cell(ri, ci)
            first = clear_cell(cell)
            r = first.add_run(str(val))
            set_run_font(r, body_font, size=body_size, bold=False)
            first.alignment = (WD_ALIGN_PARAGRAPH.CENTER if ri == 0
                               else WD_ALIGN_PARAGRAPH.LEFT)
    return title_p, table


def dump_tables(doc, max_text=120):
    """打印全部表格结构（去重合并格），用于动手前定位行/列。"""
    for ti, tb in enumerate(doc.tables):
        print('== TABLE', ti, 'rows=', len(tb.rows), 'cols=', len(tb.columns))
        for ri, row in enumerate(tb.rows):
            uniq = []
            for c in row.cells:
                t = '/'.join(c.text.strip().splitlines())
                if not uniq or uniq[-1] != t:
                    uniq.append(t)
            print(ri, '|', ' || '.join(uniq)[:max_text])
