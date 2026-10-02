#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
verify_xlsx.py — 把 xlsx 的实际单元格与「源数据」（CSV 或 JSON）做**逐格比对**。

动机：委派子代理 / MCP 工具写入 Office 文件后，工具会静默改写标点
（实测：中文全角引号 “ ” 被写成半角 "），也会静默截断长文本。
只数行数、数行列数**发现不了**这类失真，必须逐格比对。

用法：
    # 与 CSV 比对：CSV 第 1 行 = 表头，数据从 xlsx 第 --start-row 行开始
    python verify_xlsx.py <file.xlsx> <src.csv> [--sheet-name Sheet1]
                          [--start-row 3] [--ncols 15]

    # 与 JSON 比对：JSON 为二维数组 [[...],[...]]，或 {"rows": [[...]]}
    python verify_xlsx.py <file.xlsx> <src.json> --start-row 3

    # 只看结构（不比对内容）
    python verify_xlsx.py <file.xlsx> --structure

输出：差异格清单（行/列/期望/实际）与汇总计数。
退出码：0 无差异，1 存在差异或结构异常，2 参数/文件错误。
"""
import sys, os, csv as _csv, json, zipfile
from xml.etree import ElementTree as ET

S = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
RNS = '{http://schemas.openxmlformats.org/package/2006/relationships}'
RID = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'


def col_letter(idx):
    """0 -> A, 25 -> Z, 26 -> AA"""
    s = ''
    idx += 1
    while idx:
        idx, r = divmod(idx - 1, 26)
        s = chr(65 + r) + s
    return s


def col_index(letters):
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch.upper()) - 64)
    return n - 1


def load_xlsx(path, want_sheet=None):
    """返回 (rows_dict, merges)。rows_dict: {行号(int): {列字母: 值}}"""
    z = zipfile.ZipFile(path)
    ss = []
    if 'xl/sharedStrings.xml' in z.namelist():
        r = ET.fromstring(z.read('xl/sharedStrings.xml'))
        for si in r.findall(S + 'si'):
            ss.append(''.join(t.text or '' for t in si.iter(S + 't')))
    # 解析工作表名 -> 文件
    targets = []
    try:
        wb = ET.fromstring(z.read('xl/workbook.xml'))
        rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        rid2t = {x.get('Id'): x.get('Target') for x in rels.findall(RNS + 'Relationship')}
        for sh in wb.iter(S + 'sheet'):
            name = sh.get('name')
            tgt = rid2t.get(sh.get(RID), '')
            fn = 'xl/' + tgt.lstrip('/')
            if fn.startswith('xl/xl/'):
                fn = fn[3:]
            targets.append((name, fn))
    except Exception:
        pass
    if not targets:
        targets = [(n.split('/')[-1].replace('.xml', ''), n)
                   for n in z.namelist()
                   if n.startswith('xl/worksheets/sheet') and n.endswith('.xml')]

    if want_sheet:
        targets = [t for t in targets if t[0] == want_sheet] or targets
    chosen = targets[0]
    sh = ET.fromstring(z.read(chosen[1]))
    rows = {}
    for row in sh.iter(S + 'row'):
        try:
            rn = int(row.get('r'))
        except (TypeError, ValueError):
            continue
        d = {}
        for c in row:
            ref = c.get('r') or ''
            letters = ''.join(ch for ch in ref if ch.isalpha())
            t = c.get('t')
            v = c.find(S + 'v')
            isv = c.find(S + 'is')
            if t == 's' and v is not None and (v.text or '').isdigit():
                val = ss[int(v.text)]
            elif isv is not None:
                val = ''.join(x.text or '' for x in isv.iter(S + 't'))
            elif v is not None:
                val = v.text or ''
            else:
                val = ''
            if val != '':
                d[letters] = val
        if d:
            rows[rn] = d
    merges = [m.get('ref') for m in sh.iter(S + 'mergeCell')]
    return rows, merges, chosen[0]


def load_src(path):
    if path.lower().endswith('.json'):
        obj = json.load(open(path, encoding='utf-8'))
        if isinstance(obj, dict):
            obj = obj.get('rows', [])
        return [[('' if v is None else str(v)) for v in r] for r in obj]
    with open(path, encoding='utf-8-sig', newline='') as f:
        return [r for r in _csv.reader(f)]


def argval(args, key, default=None):
    return args[args.index(key) + 1] if key in args else default


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    xlsx = args[0]
    if not os.path.isfile(xlsx):
        print('文件不存在: %s' % xlsx)
        return 2
    start_row = int(argval(args, '--start-row', 3))
    ncols = int(argval(args, '--ncols', 15))
    sheet = argval(args, '--sheet-name')
    rows, merges, sname = load_xlsx(xlsx, sheet)
    data_rows = sorted(r for r in rows if r >= start_row)

    if '--structure' in args or len(args) < 2 or args[1].startswith('--'):
        print('工作表: %s' % sname)
        print('合并单元格: %s' % (merges or '无'))
        print('最大行号: %s   数据行数(>=%d): %d' % (max(rows) if rows else 0, start_row, len(data_rows)))
        for k in (2, start_row):
            if k in rows:
                print('第%d行: %s' % (k, [rows[k].get(col_letter(i), '') for i in range(ncols)]))
        if data_rows:
            last = data_rows[-1]
            print('末行(%d): %s' % (last, [rows[last].get(col_letter(i), '') for i in range(ncols)]))
        gaps = [r for r in range(start_row, (max(data_rows) + 1) if data_rows else 0) if r not in rows]
        print('中间空行: %s' % (gaps or '无'))
        return 0

    src = load_src(args[1])
    # 源数据：若首行与表头一致（第2行），则跳过
    body = src
    if rows.get(2) and src and src[0] and src[0][0] == rows[2].get('A', ''):
        body = src[1:]
    diffs = []
    for i, sr in enumerate(body):
        rn = start_row + i
        got = rows.get(rn, {})
        for j in range(ncols):
            col = col_letter(j)
            want = sr[j] if j < len(sr) else ''
            have = got.get(col, '')
            if want != have:
                diffs.append((rn, col, want, have))
    # 多余/缺失行
    if len(body) != len(data_rows):
        print('⚠️ 行数不一致：源 %d 行 vs 表 %d 行' % (len(body), len(data_rows)))
    print('比对范围: 第 %d ~ %d 行 × %d 列' % (start_row, start_row + len(body) - 1, ncols))
    print('差异格数: %d' % len(diffs))
    for rn, col, want, have in diffs[:40]:
        print('  R%d %s\n    期望: %r\n    实际: %r' % (rn, col, want, have))
    if len(diffs) > 40:
        print('  ... 其余 %d 处省略' % (len(diffs) - 40))
    return 1 if diffs else 0


if __name__ == '__main__':
    sys.exit(main())
