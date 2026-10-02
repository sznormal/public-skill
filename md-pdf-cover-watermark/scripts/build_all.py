# -*- coding: utf-8 -*-
"""
批量构建：把目录下「第 A 章 ~ 第 B 章」的 Markdown 一次性转成
带封面、带水印、带页码的 PDF（复用同一个 Chrome 实例）。

用法示例：
    python build_all.py "E:\\教材\\学生版" --from 1 --to 10
    python build_all.py "E:\\教材\\学生版" -o "E:\\教材\\PDF" --from 11 --to 30 \
        --book "机器人编程基础" --school "深圳信息职业技术大学" --author "郑洪英"
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_chapter as B  # noqa: E402
from cdp_print import ChromeCDP  # noqa: E402


def collect(src_dir: Path, lo: int, hi: int):
    """收集 src_dir 下第 lo~hi 章的 .md（自动跳过网盘冲突文件/副本）。"""
    out = []
    for f in src_dir.glob("*.md"):
        if any(k in f.name for k in ("冲突文件", "副本", "conflicted", "~$")):
            continue
        n = B.chapter_number(f.name)
        if n.isdigit() and lo <= int(n) <= hi:
            out.append((int(n), f))
    return sorted(out, key=lambda x: x[0])


def main():
    ap = argparse.ArgumentParser(description="批量 Markdown → 带封面/水印 PDF")
    ap.add_argument("src_dir", help="Markdown 所在目录")
    ap.add_argument("-o", "--out-dir", default=None, help="输出目录（默认 src_dir 下 第X-Y章_PDF）")
    ap.add_argument("--from", dest="lo", type=int, default=1, help="起始章号")
    ap.add_argument("--to", dest="hi", type=int, default=10, help="结束章号")
    ap.add_argument("--book", default=B.CFG["book"], help="封面主标题（书名）")
    ap.add_argument("--school", default=B.CFG["school"], help="单位名称（封面/页脚）")
    ap.add_argument("--author", default=B.CFG["author"], help="编著者姓名")
    ap.add_argument("--badge", default=B.CFG["badge"], help="封面徽标，如：学生版")
    ap.add_argument("--watermark", default=B.CFG["watermark"], help="水印文字（默认同单位）")
    args = ap.parse_args()

    B.CFG.update(
        book=args.book,
        school=args.school,
        author=args.author,
        badge=args.badge,
        watermark=args.watermark,
    )

    src_dir = Path(args.src_dir).resolve()
    out_dir = (
        Path(args.out_dir).resolve()
        if args.out_dir
        else src_dir / f"第{args.lo}-{args.hi}章_PDF"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    items = collect(src_dir, args.lo, args.hi)
    if not items:
        print(f"在 {src_dir} 未找到第 {args.lo}-{args.hi} 章的 Markdown")
        return 1

    B.prepare_build_dir()
    print(f"待处理 {len(items)} 章 → {out_dir}\n")

    results = []
    with ChromeCDP(B.find_browser()) as cdp:
        for idx, (no, f) in enumerate(items, 1):
            try:
                info = B.render_pdf(f, out_dir / (f.stem + ".pdf"), cdp=cdp)
                size = (out_dir / (f.stem + ".pdf")).stat().st_size / 1024
                results.append((no, f.name, info, None))
                print(
                    f"[{idx}/{len(items)}] 第{no}章 OK | {info['total_pages']} 页 "
                    f"(封面{info['cover_pages']}+正文{info['body_pages']}) | "
                    f"mermaid {info['mermaid_rendered']} 缩放{info['mermaid_scales']} | "
                    f"{size:.0f} KB"
                )
            except Exception as e:
                results.append((no, f.name, None, repr(e)))
                print(f"[{idx}/{len(items)}] 第{no}章 失败: {e!r}")

    print("\n================ 汇总 ================")
    ok = sum(1 for r in results if r[3] is None)
    print(f"成功 {ok} / {len(results)}")
    for no, name, info, err in results:
        if err:
            print(f"  ✗ 第{no}章 {name}: {err}")
        elif info["mermaid_error"]:
            print(f"  ! 第{no}章 mermaid 报错: {info['mermaid_error']}")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
