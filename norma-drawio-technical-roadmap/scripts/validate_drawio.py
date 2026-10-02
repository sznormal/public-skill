#!/usr/bin/env python3
"""校验 draw.io XML 是否可以导入。只读，不联网，不启动子进程，不修改输入文件。

用法：
    python validate_drawio.py <file.drawio>

退出码：
    0  无错误
    1  存在错误
    2  用法错误或文件不可读
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

BARE_AMP = re.compile(r"&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[0-9A-Fa-f]+);)")
CJK = re.compile(r"[\u4e00-\u9fff]")
NO_CJK_FONT = {"", "helvetica", "arial", "none", "default"}


def style_map(style: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for part in (style or "").split(";"):
        if "=" in part:
            key, _, value = part.partition("=")
            result[key.strip()] = value.strip()
    return result


def check(path: Path) -> dict:
    errors: list[str] = []
    warnings: list[str] = []

    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return {
            "file": str(path),
            "errors": ["文件不是 UTF-8 编码，请改存 UTF-8 后重试"],
            "warnings": [],
            "counts": {},
            "ok": False,
        }

    if 'compressed="true"' in raw:
        errors.append("检测到 compressed=\"true\"，必须输出未压缩明文 XML")

    for match in BARE_AMP.finditer(raw):
        start = max(0, match.start() - 20)
        snippet = raw[start : match.start() + 20].replace("\n", " ")
        errors.append(f"第 {raw[: match.start()].count(chr(10)) + 1} 行存在未转义的 & ：...{snippet}...")
        break

    try:
        tree = ET.parse(str(path))
    except ET.ParseError as exc:
        errors.append(f"XML 解析失败：{exc}；仅完成文本级检查，结构检查已跳过")
        return {
            "file": str(path),
            "errors": errors,
            "warnings": warnings,
            "counts": {},
            "ok": False,
        }

    root_el = tree.getroot()
    if root_el.tag != "mxfile":
        errors.append(f"根元素应为 mxfile，实际为 {root_el.tag}")

    diagrams = root_el.findall(".//diagram")
    if not diagrams:
        errors.append("缺少 diagram 元素")

    models = root_el.findall(".//mxGraphModel")
    if not models:
        errors.append("缺少 mxGraphModel 元素")

    roots = root_el.findall(".//root")
    if not roots:
        errors.append("缺少 root 元素")

    cells = root_el.findall(".//mxCell")
    if not cells:
        errors.append("未找到任何 mxCell")
        return {
            "file": str(path),
            "errors": errors,
            "warnings": warnings,
            "counts": {"cells": 0},
            "ok": False,
        }

    ids: list[str] = []
    id_set: set[str] = set()
    duplicates: list[str] = []
    for cell in cells:
        cell_id = cell.get("id")
        if cell_id is None:
            errors.append("存在缺少 id 的 mxCell")
            continue
        ids.append(cell_id)
        if cell_id in id_set:
            duplicates.append(cell_id)
        id_set.add(cell_id)

    if duplicates:
        errors.append(f"存在重复 id：{sorted(set(duplicates))}")

    for required in ("0", "1"):
        if required not in id_set:
            errors.append(f"缺少保留节点 id=\"{required}\"")

    vertices = 0
    edges = 0
    for cell in cells:
        cell_id = cell.get("id")
        style = style_map(cell.get("style", ""))
        value = cell.get("value", "") or ""
        is_vertex = cell.get("vertex") == "1"
        is_edge = cell.get("edge") == "1"

        if is_vertex:
            vertices += 1
            geometry = cell.find("mxGeometry")
            if geometry is None:
                errors.append(f"顶点 id={cell_id} 缺少 mxGeometry")
                continue
            for attr in ("x", "y", "width", "height"):
                raw_value = geometry.get(attr)
                if raw_value is None:
                    errors.append(f"顶点 id={cell_id} 的 mxGeometry 缺少 {attr}")
                else:
                    try:
                        number = float(raw_value)
                    except ValueError:
                        errors.append(f"顶点 id={cell_id} 的 {attr} 不是数字：{raw_value}")
                        continue
                    if number % 10 != 0:
                        warnings.append(f"顶点 id={cell_id} 的 {attr}={raw_value} 不是 10 的倍数")

        if is_edge:
            edges += 1
            if cell.find("mxGeometry") is None:
                warnings.append(f"连线 id={cell_id} 缺少 mxGeometry relative=\"1\"")
            for attr in ("source", "target"):
                ref = cell.get(attr)
                if not ref:
                    errors.append(f"连线 id={cell_id} 缺少 {attr}")
                elif ref not in id_set:
                    errors.append(f"连线 id={cell_id} 的 {attr}={ref} 指向不存在的节点")

        if cell.get("parent") not in (None, "0", "1") and cell.get("parent") not in id_set:
            errors.append(f"节点 id={cell_id} 的 parent={cell.get('parent')} 不存在")

        if CJK.search(value):
            font = style.get("fontFamily", "").lower()
            if font in NO_CJK_FONT:
                warnings.append(f"节点 id={cell_id} 含中文但未指定中文字体，建议 fontFamily=Microsoft YaHei")

    return {
        "file": str(path),
        "counts": {"cells": len(cells), "vertices": vertices, "edges": edges},
        "errors": errors,
        "warnings": warnings,
        "ok": not errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="校验 draw.io XML 是否可导入")
    parser.add_argument("file", help="待校验的 .drawio 或 .xml 文件路径")
    args = parser.parse_args()

    path = Path(args.file).expanduser()
    if not path.is_file():
        print(json.dumps({"error": f"文件不存在：{path}"}, ensure_ascii=False, indent=2))
        return 2

    report = check(path)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
