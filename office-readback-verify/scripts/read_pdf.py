#!/usr/bin/env python3
"""Minimal PDF text extractor -- no external deps (no pdftotext / poppler needed).

Why this exists: the review machine has no pdftotext, and the only way to *prove*
that a built PDF actually renders what we intended (author block, emails,
corresponding-author note) is to read the content streams back.

Usage:
    python pdftxt.py file.pdf                 # dump all text
    python pdftxt.py file.pdf --find NEEDLE   # dump the region around NEEDLE
    python pdftxt.py file.pdf --grep A B C    # report hit counts, whitespace-insensitive

Caveats (these are extractor artefacts, NOT PDF defects):
  * kerning splits words ("Sino-GermanRoboticsSchool")
  * ff/fi ligatures swallow characters ("scienti\fc", "veri\fability")
  * --find/--grep strip ALL whitespace before matching to survive the above.
"""
import re
import sys
import zlib


def _unescape(bs: bytes) -> bytes:
    out = bytearray()
    i = 0
    simple = {0x6E: 10, 0x72: 13, 0x74: 9, 0x62: 8, 0x66: 12,
              0x28: 0x28, 0x29: 0x29, 0x5C: 0x5C}
    while i < len(bs):
        c = bs[i]
        if c == 0x5C and i + 1 < len(bs):
            n = bs[i + 1]
            if n in simple:
                out.append(simple[n]); i += 2; continue
            if 0x30 <= n <= 0x37:
                m = re.match(rb'[0-7]{1,3}', bs[i + 1:i + 4])
                out.append(int(m.group(0), 8) & 0xFF); i += 1 + len(m.group(0)); continue
            if n in (0x0A, 0x0D):
                i += 2; continue
            i += 2; continue
        out.append(c); i += 1
    return bytes(out)


def _render(stream: bytes) -> str:
    txt = stream.decode('latin-1')
    out = []
    pat = r'\((?:[^()\\]|\\.)*\)|<[0-9A-Fa-f\s]+>|Td|TD|T\*|ET|TJ|Tj'
    for m in re.finditer(pat, txt):
        tok = m.group(0)
        if tok in ('Td', 'TD', 'T*', 'ET'):
            out.append('\n')
        elif tok.startswith('<'):
            h = re.sub(r'\s', '', tok[1:-1])
            try:
                out.append(_unescape(bytes.fromhex(h)).decode('latin-1'))
            except Exception:
                pass
        elif tok.startswith('('):
            out.append(_unescape(tok[1:-1].encode('latin-1')).decode('latin-1'))
    return ''.join(out)


def extract_streams(path):
    data = open(path, 'rb').read()
    pages = []
    for s in re.findall(rb'stream\r?\n(.*?)endstream', data, re.S):
        try:
            d = zlib.decompress(s)
        except Exception:
            continue
        if b'BT' in d and (b'Tj' in d or b'TJ' in d):
            pages.append(_render(d))
    return pages


def main():
    if len(sys.argv) < 2:
        print(__doc__); return 1
    pdf = sys.argv[1]
    args = sys.argv[2:]
    pages = extract_streams(pdf)
    full = '\n'.join(pages)
    flat = re.sub(r'\s+', '', full)

    if '--grep' in args:
        for needle in args[args.index('--grep') + 1:]:
            n = re.sub(r'\s+', '', needle)
            print('%-34s %s' % (needle, 'OK' if n in flat else 'MISSING'))
        return 0

    if '--find' in args:
        needle = re.sub(r'\s+', '', args[args.index('--find') + 1])
        for i, p in enumerate(pages, 1):
            fp = re.sub(r'\s+', '', p)
            j = fp.find(needle)
            if j >= 0:
                print('--- page stream %d ---' % i)
                print(p[max(0, j - 900):j + 900])
                print()
        return 0

    print(full)
    return 0


if __name__ == '__main__':
    sys.exit(main())
