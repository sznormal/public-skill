#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
extract_code.py — 从教材 Markdown 中抽取所有代码块，按所属小节汇总成 txt。

用途：教材课件 PPT 不贴代码，章节代码单独成文件。
用法：
    python extract_code.py <输入.md> <输出.txt> [--lang python]

规则：
- 只抽取围栏代码块（```lang ... ```），默认 lang=python，可传 --lang 指定。
- 每个代码块归属它"上方最近的一行 Markdown 标题"（#/##/###，去掉前缀#与多余空格）。
- 输出按出现顺序排列；同一小节的多个代码块之间用空行隔开。
- 原文件里的 # 注释、缩进一律保留，不做改动。
"""
import argparse
import sys
from pathlib import Path


def extract(md_path: Path, out_path: Path, lang: str = "python") -> int:
    lines = md_path.read_text(encoding="utf-8").splitlines()
    blocks = []          # list of (section_title, code_lines)
    current_section = "未命名小节"
    in_fence = False
    fence_lang = ""
    buf = []

    for raw in lines:
        stripped = raw.strip()
        # 围栏开始 / 结束
        if stripped.startswith("```"):
            if not in_fence:
                in_fence = True
                fence_lang = stripped[3:].strip().lower()
                buf = []
            else:
                # 结束围栏
                if fence_lang == lang.lower():
                    blocks.append((current_section, buf))
                in_fence = False
                fence_lang = ""
                buf = []
            continue

        if in_fence:
            buf.append(raw)
            continue

        # 非围栏行：识别 Markdown 标题，更新当前小节
        if stripped.startswith("#"):
            title = stripped.lstrip("#").strip()
            # 去掉标题里可能残留的 markdown 标记
            title = title.replace("**", "").strip()
            if title:
                current_section = title

    out = []
    out.append(f"# {md_path.stem} · 实例代码汇总")
    out.append("# 本文件由教材自动抽取，供上课/上机对照使用；PPT 正文不直接展示代码。")
    out.append("")
    idx = 0
    for section, code_lines in blocks:
        # 去掉代码块首尾空行
        while code_lines and not code_lines[0].strip():
            code_lines.pop(0)
        while code_lines and not code_lines[-1].strip():
            code_lines.pop()
        if not code_lines:
            continue
        idx += 1
        out.append("=" * 60)
        out.append(f"[{idx}] {section}")
        out.append("=" * 60)
        out.extend(code_lines)
        out.append("")
        out.append("")

    out_path.write_text("\n".join(out), encoding="utf-8")
    return idx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input_md")
    ap.add_argument("output_txt")
    ap.add_argument("--lang", default="python")
    args = ap.parse_args()

    n = extract(Path(args.input_md), Path(args.output_txt), args.lang)
    print(f"OK: extracted {n} code block(s) -> {args.output_txt}")


if __name__ == "__main__":
    main()
