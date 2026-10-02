#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""资料库 doc 的组件 XML → 干净 Markdown。

用法:
    python doc_xml_to_md.py <raw.txt> <out.md>

输入 raw.txt 是 `get_doc_reviews.py` 的原始 stdout（含末尾 KS_DOC_REVIEWS 行）。
输出为 GFM Markdown（标题 / 段落 / 列表 / 表格 / 加粗 / 斜体）。

设计要点（踩过的坑）:
- 开标签处**不能丢弃**已缓冲文本：`<Mark>` 等未识别节点要在 open 分支把 inner 塞回缓冲区，
  否则"本报告依据 DACUM…对以下三个岗位中"这类加粗前导文字会整段消失。
- `<TableCell>` 内嵌 `<Paragraph>`，需按 cell 缓冲，`</Table>` 时统一输出表格。
"""
import re
import sys

NEUTRAL = {"#FFFFFF", "#F7F9FC", "#1A2230", "#4A5568", "#8B97A8", "#D6DCE5", "#E5E7EB"}
TOKEN = re.compile(r"<(/?)([A-Za-z]+)((?:\s[^>]*?)?)/?>|([^<]+)")
KNOWN_OPEN = {"Heading", "Paragraph", "BulletedList", "NumberedList", "BlockQuote",
              "Divider", "Table", "TableRow", "TableCell"}


def convert(src: str) -> str:
    src = re.sub(r"^---\n.*?\n---\n", "", src, flags=re.S)
    src = re.sub(r"\nKS_DOC_REVIEWS.*$", "", src, flags=re.S)

    out: list[str] = []
    stack: list[tuple[str, str]] = []
    textbuf: list[str] = []
    mark_stack: list[str] = []
    table = None      # {"rows": [[cell, ...]], "cur": [...]}
    cellbuf = None

    def take() -> str:
        t = "".join(textbuf)
        textbuf.clear()
        return t

    def inline(s: str) -> str:
        s = s.replace("\u00a0", " ")
        return re.sub(r"[ \t\r\n]+", " ", s).strip()

    for close, name, attrs, chunk in TOKEN.findall(src):
        if chunk:
            textbuf.append(chunk)
            continue

        inner = take()

        if close:
            if name == "Heading":
                lvl = int(re.search(r'level="(\d+)"', stack[-1][1]).group(1)) if stack else 1
                txt = inline(inner)
                if txt:
                    out.append("#" * lvl + " " + txt)
            elif name == "Paragraph":
                txt = inline(inner)
                if cellbuf is not None:
                    if txt:
                        cellbuf.append(txt)
                elif txt:
                    out.append(txt)
            elif name == "BulletedList":
                txt = inline(inner)
                if txt:
                    out.append("- " + txt)
            elif name == "NumberedList":
                txt = inline(inner)
                if txt:
                    out.append("1. " + txt)
            elif name == "TableCell":
                if table is not None and cellbuf is not None:
                    table["cur"].append(" ".join(x for x in cellbuf if x))
                cellbuf = None
            elif name == "TableRow":
                if table is not None:
                    table["rows"].append(table["cur"])
                    table["cur"] = []
            elif name == "Table":
                if table and table["rows"]:
                    out.append("")
                    for ri, row in enumerate(table["rows"]):
                        out.append("| " + " | ".join(row) + " |")
                        if ri == 0:
                            out.append("|" + "---|" * len(row))
                    out.append("")
                table = None
            elif name == "Divider":
                out.append("\n---\n")
            elif name == "Mark":
                textbuf.append(inner)
                textbuf.append(mark_stack.pop() if mark_stack else "")
            else:
                textbuf.append(inner)
            if stack:
                stack.pop()
            continue

        # ---- open tag: 保留标签前的文本，别丢 ----
        textbuf.append(inner)

        if name == "Heading":
            stack.append((name, attrs))
        elif name == "Paragraph":
            stack.append((name, attrs))
        elif name in ("BulletedList", "NumberedList", "BlockQuote", "Divider"):
            stack.append((name, attrs))
        elif name == "Table":
            table = {"rows": [], "cur": []}
            stack.append((name, attrs))
        elif name == "TableRow":
            if table is not None and table["cur"]:
                table["rows"].append(table["cur"])
            if table is not None:
                table["cur"] = []
            stack.append((name, attrs))
        elif name == "TableCell":
            cellbuf = []
            stack.append((name, attrs))
        elif name == "Mark":
            m = "**" if "bold" in attrs else ("*" if "italic" in attrs else "")
            mark_stack.append(m)
            textbuf.append(m)
        else:
            stack.append((name, attrs))

    txt = "\n".join(out)
    return re.sub(r"\n{3,}", "\n\n", txt)


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    src = open(sys.argv[1], encoding="utf-8").read()
    md = convert(src)
    open(sys.argv[2], "w", encoding="utf-8").write(md)
    heads = [l for l in md.split("\n") if l.startswith("#")]
    print(f"written {len(md)} chars, {len(heads)} headings")
    for h in heads:
        print("  " + h)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
