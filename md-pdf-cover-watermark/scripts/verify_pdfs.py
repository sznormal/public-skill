# -*- coding: utf-8 -*-
"""PDF 交付验收：逐份检查封面文字、水印、页脚页码、页面尺寸与空白页。

用法：
    python verify_pdfs.py "E:\\教材\\第1-10章_PDF" --school 深圳信息职业技术大学
"""
import argparse
import re
import sys
from pathlib import Path

import pymupdf

A4_W, A4_H = 595.28, 841.89


def check(pdf: Path, school: str, author: str, book: str) -> dict:
    doc = pymupdf.open(pdf)
    n = doc.page_count
    res = {
        "file": pdf.name,
        "pages": n,
        "errors": [],
        "warns": [],
        "cover_ok": False,
        "wm_min": 10 ** 9,
        "footer_ok": 0,
        "body_pages": n - 1,
        "blank": [],
    }

    # --- 页面尺寸 ---
    for i in range(n):
        r = doc.load_page(i).rect
        if abs(r.width - A4_W) > 2 or abs(r.height - A4_H) > 2:
            res["errors"].append(f"第{i+1}页尺寸异常 {r.width:.1f}x{r.height:.1f}pt")
            break

    # --- 封面（第 1 页）---
    flat = doc.load_page(0).get_text().replace("\u3000", "").replace(" ", "")
    need = [book, f"编著：{author}", f"单位：{school}"]
    missing = [x for x in need if x.replace(" ", "") not in flat]
    if missing:
        res["errors"].append("封面缺少: " + "、".join(missing))
    elif school not in doc.load_page(0).get_text():
        res["errors"].append("封面无水印")
    else:
        res["cover_ok"] = True
    if re.search(r"第\s*1\s*页", flat):
        res["warns"].append("封面出现页脚页码")

    # --- 逐页：水印 / 页脚 / 日期页眉 / 空白 ---
    for i in range(n):
        t = doc.load_page(i).get_text()
        wm = t.count(school)
        res["wm_min"] = min(res["wm_min"], wm)
        if wm < 10:
            res["errors"].append(f"第{i+1}页水印过少({wm})")
        if re.search(r"\d{4}/\d{1,2}/\d{1,2}", t):
            res["errors"].append(f"第{i+1}页出现日期页眉")
        if i > 0:
            if f"第 {i} 页" in t:
                res["footer_ok"] += 1
            else:
                res["errors"].append(f"第{i+1}页缺少页码『第 {i} 页』")
        pg = doc.load_page(i)
        if i > 0 and len(t.replace(school, "").strip()) < 40 and len(pg.get_drawings()) < 3:
            res["blank"].append(i + 1)

    doc.close()
    return res


def main():
    ap = argparse.ArgumentParser(description="PDF 交付验收")
    ap.add_argument("pdf_dir", help="PDF 所在目录")
    ap.add_argument("--school", default="深圳信息职业技术大学")
    ap.add_argument("--author", default="郑洪英")
    ap.add_argument("--book", default="机器人编程基础")
    args = ap.parse_args()

    pdf_dir = Path(args.pdf_dir).resolve()
    files = sorted(
        pdf_dir.glob("*.pdf"),
        key=lambda p: int(re.findall(r"\d+", p.name)[0]) if re.findall(r"\d+", p.name) else 0,
    )
    if not files:
        print(f"{pdf_dir} 下未找到 PDF")
        return 1

    bad = 0
    print(f"{'文件':<40} {'页数':>4} {'封面':>4} {'最小水印':>7} {'页码':>8} {'空白页':>7}")
    print("-" * 92)
    for f in files:
        r = check(f, args.school, args.author, args.book)
        if r["errors"]:
            bad += 1
        print(
            f"{r['file'][:38]:<40} {r['pages']:>4} "
            f"{'OK' if r['cover_ok'] else 'NG':>4} {r['wm_min']:>7} "
            f"{r['footer_ok']}/{r['body_pages']:<6} {str(r['blank']):>7}"
        )
        for e in r["errors"]:
            print(f"    [错误] {e}")
        for w in r["warns"]:
            print(f"    [警告] {w}")
    print("-" * 92)
    print(f"共 {len(files)} 份，异常 {bad} 份")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
