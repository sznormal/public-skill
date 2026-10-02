#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
进度仪表盘：让使用者随时看到"写到哪、卡在哪、还差什么"。

render_dashboard(title, sections)
    title    : 文档/课程标题，如 "《机器人编程与仿真》课程标准"
    sections : list of (name, status)
               status ∈ {"done"(已确认/已完成), "confirming"(待确认),
                         "pending"(待收集/待写)}
输出一张 ASCII 仪表盘 + 进度百分比。

用法：
    from progress_dashboard import render_dashboard
    render_dashboard("《XXX》课程标准", [
        ("头部信息栏", "done"),
        ("定位设计", "confirming"),
        ("课程目标", "pending"),
    ])
"""
from __future__ import annotations


def _glyph(status: str) -> str:
    return {
        "done": "▣",
        "confirming": "◈",
        "pending": "▢",
    }.get(status, "▢")


def _label(status: str) -> str:
    return {
        "done": "已确认",
        "confirming": "待确认",
        "pending": "待收集",
    }.get(status, "待收集")


def render_dashboard(title: str, sections: list[tuple[str, str]]) -> None:
    width = 52
    total = len(sections) or 1
    done = sum(1 for _, s in sections if s == "done")
    pct = int(done / total * 100)
    bar_len = 30
    filled = int(bar_len * pct / 100)
    bar = "█" * filled + "░" * (bar_len - filled)

    print("╔" + "═" * (width + 2) + "╗")
    head = f" {title} · 进度仪表盘"
    print("║" + head + " " * (width + 1 - len(head)) + "║")
    print("╠" + "═" * (width + 2) + "╣")
    for name, st in sections:
        line = f" {_glyph(st)} {name:<8} [{_label(st)}]"
        print("║" + line + " " * (width + 1 - len(line)) + "║")
    print("╠" + "═" * (width + 2) + "╣")
    prog = f" 进度 {done}/{total}  {bar}  {pct}%"
    print("║" + prog + " " * (width + 1 - len(prog)) + "║")
    print("╚" + "═" * (width + 2) + "╝")


if __name__ == "__main__":
    # 自测
    render_dashboard("《机器人编程与仿真》课程标准", [
        ("头部信息栏", "done"),
        ("定位设计", "confirming"),
        ("课程目标", "pending"),
        ("内容要求", "pending"),
        ("实践教学", "pending"),
        ("课程实施", "pending"),
        ("考核评价", "pending"),
        ("线上资源", "pending"),
        ("其他说明", "pending"),
    ])
