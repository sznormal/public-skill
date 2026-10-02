#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
read_office.py — 零依赖读取 Office 文件（docx / xlsx / pptx）。

动机：WorkBuddy 的 managed Python 环境默认不装 python-docx / openpyxl，
装在临时环境里又慢又不稳。Office 的 OOXML 本质是 zip + XML，用标准库
zipfile + xml.etree 就能拿到全部文本与表格结构，秒级可用。

用法：
    python read_office.py <file> [--out out.txt] [--json out.json]

支持：
    .docx  段落（按文档顺序） + 表格（[TABLE] ... [/TABLE]，单元格以 " | " 分隔）
    .xlsx  每个工作表逐行，形如 ROW 3 A3='x' | B3='y'
    .pptx  每页逐形状提取文本
退出码：0 成功，2 文件不存在/不支持的扩展名
"""
import sys, os, json, zipfile
from xml.etree import ElementTree as ET

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
S = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
P = '{http://schemas.openxmlformats.org/presentationml/2006/main}'


def _txt(el, ns):
    return ''.join(t.text or '' for t in el.iter(ns + 't'))


# ---------------- docx ----------------
def read_docx(path):
    z = zipfile.ZipFile(path)
    root = ET.fromstring(z.read('word/document.xml'))
    body = root.find(W + 'body')
    lines = []
    for child in body:
        tag = child.tag.split('}')[1]
        if tag == 'p':
            s = _txt(child, W).strip()
            if s:
                lines.append(s)
        elif tag == 'tbl':
            lines.append('[TABLE]')
            for tr in child.findall(W + 'tr'):
                cells = [_txt(tc, W).strip().replace('\n', ' ') for tc in tr.findall(W + 'tc')]
                lines.append(' | '.join(cells))
            lines.append('[/TABLE]')
    return lines


# ---------------- xlsx ----------------
def _shared_strings(z):
    out = []
    if 'xl/sharedStrings.xml' in z.namelist():
        r = ET.fromstring(z.read('xl/sharedStrings.xml'))
        for si in r.findall(S + 'si'):
            out.append(''.join(t.text or '' for t in si.iter(S + 't')))
    return out


def _sheet_names(z):
    """返回 {sheetN.xml: 表名}；缺失时回退为默认名。"""
    names = {}
    try:
        wb = ET.fromstring(z.read('xl/workbook.xml'))
        rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        RNS = '{http://schemas.openxmlformats.org/package/2006/relationships}'
        rid2target = {r.get('Id'): r.get('Target') for r in rels.findall(RNS + 'Relationship')}
        for i, sh in enumerate(wb.iter(S + 'sheet'), 1):
            rid = sh.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
            tgt = rid2target.get(rid, '')
            fname = 'xl/' + tgt.lstrip('/').replace('xl/', '')
            names[fname] = sh.get('name') or ('Sheet%d' % i)
    except Exception:
        pass
    if not names:
        for n in z.namelist():
            if n.startswith('xl/worksheets/sheet') and n.endswith('.xml'):
                names[n] = n.split('/')[-1].replace('.xml', '')
    return names


def read_xlsx(path):
    z = zipfile.ZipFile(path)
    ss = _shared_strings(z)
    lines = []
    for fname, sheetname in _sheet_names(z).items():
        if fname not in z.namelist():
            continue
        lines.append('=== SHEET %s (%s) ===' % (sheetname, fname))
        sh = ET.fromstring(z.read(fname))
        mg = [m.get('ref') for m in sh.iter(S + 'mergeCell')]
        if mg:
            lines.append('MERGED: ' + ', '.join(mg))
        for row in sh.iter(S + 'row'):
            cells = []
            for c in row:
                ref = c.get('r')
                t = c.get('t')
                v = c.find(S + 'v')
                isv = c.find(S + 'is')
                if t == 's' and v is not None:
                    val = ss[int(v.text)] if v.text and v.text.isdigit() else ''
                elif isv is not None:
                    val = ''.join(x.text or '' for x in isv.iter(S + 't'))
                elif v is not None:
                    val = v.text
                else:
                    val = ''
                if val:
                    cells.append('%s=%r' % (ref, val))
            if cells:
                lines.append('ROW %s %s' % (row.get('r'), ' | '.join(cells)))
    return lines


# ---------------- pptx ----------------
def read_pptx(path):
    z = zipfile.ZipFile(path)
    slides = sorted([n for n in z.namelist()
                     if n.startswith('ppt/slides/slide') and n.endswith('.xml')],
                    key=lambda n: int(''.join(ch for ch in n if ch.isdigit()) or 0))
    lines = []
    for i, n in enumerate(slides, 1):
        lines.append('=== SLIDE %d ===' % i)
        r = ET.fromstring(z.read(n))
        for p in r.iter(A + 'p'):
            s = ''.join(t.text or '' for t in p.iter(A + 't')).strip()
            if s:
                lines.append(s)
    return lines


READERS = {'.docx': read_docx, '.xlsx': read_xlsx, '.pptx': read_pptx}


def main():
    args = [a for a in sys.argv[1:]]
    if not args:
        print(__doc__)
        return 2
    path = args[0]
    out, js = None, None
    if '--out' in args:
        out = args[args.index('--out') + 1]
    if '--json' in args:
        js = args[args.index('--json') + 1]
    if not os.path.isfile(path):
        print('文件不存在: %s' % path)
        return 2
    ext = os.path.splitext(path)[1].lower()
    if ext not in READERS:
        print('不支持的扩展名: %s（支持 %s）' % (ext, '/'.join(READERS)))
        return 2
    lines = READERS[ext](path)
    text = '\n'.join(lines)
    if out:
        with open(out, 'w', encoding='utf-8') as f:
            f.write(text)
        print('WROTE %s (%d 行)' % (out, len(lines)))
    else:
        print(text)
    if js:
        with open(js, 'w', encoding='utf-8') as f:
            json.dump(lines, f, ensure_ascii=False, indent=1)
        print('WROTE %s' % js)
    return 0


if __name__ == '__main__':
    sys.exit(main())
