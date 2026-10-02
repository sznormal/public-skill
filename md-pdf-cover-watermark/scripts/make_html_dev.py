# -*- coding: utf-8 -*-
"""开发期辅助：生成用于截图检查的 HTML（不依赖 playwright）。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_chapter as B


def make(md_path: Path, mode: str) -> Path:
    raw = md_path.read_text(encoding="utf-8")
    title, body = B.split_title(raw)
    b2, mer = B.extract_mermaid(body)
    h = B.restore_mermaid(B.md_to_html(b2), mer)
    doc = B.build_html(title, h)
    B.prepare_build_dir()

    if mode == "cover":
        doc = doc.replace(
            "<style>\n", "<style>\n.content{display:none !important;}\n", 1
        )
    else:
        doc = doc.replace(
            "<style>\n", "<style>\n.cover{display:none !important;}\n", 1
        )
    out = B.BUILD / f"dev_{mode}.html"
    out.write_text(doc, encoding="utf-8")
    return out


if __name__ == "__main__":
    md = Path(sys.argv[1])
    for mode in ("cover", "content"):
        print(make(md, mode))
