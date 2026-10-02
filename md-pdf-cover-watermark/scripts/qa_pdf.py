# -*- coding: utf-8 -*-
"""PDF 质检：把指定页渲染为 PNG，便于人工/模型目视核对。"""
import sys
from pathlib import Path

import fitz  # pymupdf

QA_DIR = Path(r"C:\Users\admin\.workbuddy\tmp\pdfqa")


def render(pdf_path: str, pages, dpi=110, tag="qa"):
    QA_DIR.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    outs = []
    total = doc.page_count
    for p in pages:
        if p < 1 or p > total:
            continue
        page = doc.load_page(p - 1)
        pix = page.get_pixmap(dpi=dpi)
        out = QA_DIR / f"{tag}_p{p:02d}.png"
        pix.save(str(out))
        outs.append((p, out, pix.width, pix.height))
    doc.close()
    return total, outs


if __name__ == "__main__":
    pdf = sys.argv[1]
    tag = sys.argv[2] if len(sys.argv) > 2 else "qa"
    pages = [int(x) for x in sys.argv[3:]] if len(sys.argv) > 3 else [1, 2, 3]
    total, outs = render(pdf, pages, tag=tag)
    print(f"总页数 {total}")
    for p, out, w, h in outs:
        print(f"  第{p}页 -> {out}  ({w}x{h})")
