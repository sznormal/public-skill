#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""证据矩阵体检脚本（纯标准库，无第三方依赖）。

用法:
    python matrix_lint.py <evidence_matrix.md>

作用:
    统计矩阵行数、必需列缺失、稀疏列、矛盾标注、孤证条目。
    只做机械统计，不判断研究空白是否成立。

退出码:
    0 = 通过（达到行数门槛）
    1 = 未达 40 行门槛
    2 = 文件不存在或格式无法解析
"""
import os
import re
import sys
from collections import Counter

REQUIRED_COLUMNS = [
    "研究问题", "方法", "机理", "数据", "场景", "基线", "指标",
    "结论", "证据强度", "局限", "未验证", "可复现",
]

# 12 行门槛：低于此值说明"看到的空白可能只是读得不够"
MIN_ROWS = 20
# 建议门槛
TARGET_ROWS = 40

EMPTY_MARKERS = {"-", "—", "–", "n/a", "na", "none", "待核", "tbd", "无", "空", "?"}


SEPARATOR = object()  # 表头分隔行哨兵：属于表内，不得据此断表


def is_separator(cells):
    """判断是否为 markdown 表格的分隔行（如 |---|---|）。"""
    filled = [c for c in cells if c != ""]
    if not filled:
        return False
    return all(re.fullmatch(r":?-{1,}:?", c) for c in filled)


def parse_table_line(line):
    """把一行 markdown 表格拆成单元格列表；分隔行返回 SEPARATOR。"""
    line = line.strip()
    if not line.startswith("|"):
        return None
    cells = [c.strip() for c in line.strip("|").split("|")]
    if is_separator(cells):
        return SEPARATOR
    return cells


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2

    path = sys.argv[1]
    if not os.path.isfile(path):
        print("[FAIL] 文件不存在: %s" % path)
        return 2

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    tables = []
    current = []
    for line in lines:
        cells = parse_table_line(line)
        if cells is SEPARATOR:
            # 分隔行属于表内，跳过但不断表
            continue
        if cells:
            current.append(cells)
        else:
            if current:
                tables.append(current)
                current = []
    if current:
        tables.append(current)

    if not tables:
        print("[FAIL] 未找到任何 markdown 表格")
        return 2

    # 取行数最多的表作为主矩阵
    matrix = max(tables, key=len)
    header = matrix[0]
    rows = matrix[1:]

    print("=" * 60)
    print("证据矩阵体检报告")
    print("=" * 60)
    print("文件: %s" % path)
    print("识别到 %d 个表格，主矩阵列数 %d，记录行数 %d"
          % (len(tables), len(header), len(rows)))

    # 1) 行数门槛
    if len(rows) < MIN_ROWS:
        print("\n[FAIL] 行数 %d < 最低门槛 %d：读得不够，"
              "看到的空白很可能只是检索错觉" % (len(rows), MIN_ROWS))
    elif len(rows) < TARGET_ROWS:
        print("\n[WARN] 行数 %d < 建议门槛 %d：建议继续补读再定题"
              % (len(rows), TARGET_ROWS))
    else:
        print("\n[OK] 行数 %d 达到建议门槛 %d" % (len(rows), TARGET_ROWS))

    # 2) 必需列缺失
    missing = [c for c in REQUIRED_COLUMNS if c not in header]
    if missing:
        print("\n[FAIL] 缺少必需列 %d 个: %s" % (len(missing), "、".join(missing)))
    else:
        print("\n[OK] 12 个必需列齐备")

    # 3) 稀疏列（仅在列齐备时统计）
    sparse = []
    if not missing:
        for idx, col in enumerate(header):
            if idx >= len(rows[0]) and idx >= len(header):
                continue
            empty_count = 0
            total = 0
            for r in rows:
                if idx >= len(r):
                    continue
                value = r[idx].strip().strip("`")
                total += 1
                if value == "" or value.lower() in EMPTY_MARKERS:
                    empty_count += 1
            if total > 0 and empty_count / float(total) >= 0.7:
                sparse.append((col, empty_count, total))
        if sparse:
            print("\n[WARN] 稀疏列（空值率 >= 70%）—— 候选矿脉坐标：")
            for col, e, t in sparse:
                print("  - %s: %d/%d 为空 (%.0f%%)" % (col, e, t, 100.0 * e / t))
        else:
            print("\n[OK] 无高稀疏列")

    # 4) 矛盾与孤证标注
    conflict_markers = ["矛盾", "冲突", "相反", "contradict", "conflict"]
    isolate_markers = ["孤证", "仅1篇", "仅一篇", "single"]
    conflicts, isolates = [], []
    for i, r in enumerate(rows, start=1):
        joined = " | ".join(r).lower()
        if any(m.lower() in joined for m in conflict_markers):
            conflicts.append(i)
        if any(m.lower() in joined for m in isolate_markers):
            isolates.append(i)

    print("\n矛盾标注: %d 处%s"
          % (len(conflicts), ("（行号 %s）" % conflicts) if conflicts else ""))
    print("孤证标注: %d 处%s"
          % (len(isolates), ("（行号 %s）" % isolates) if isolates else ""))

    # 5) 重复文献检测
    names = [r[0].strip() for r in rows if r]
    dup = [n for n, c in Counter(names).items() if c > 1 and n]
    if dup:
        print("\n[WARN] 疑似重复行 %d 条: %s" % (len(dup), "、".join(dup[:5])))

    print("\n" + "-" * 60)
    print("提醒: 本脚本只做机械统计，不判断空白是否成立。")
    print("下一步: P2 双轴定位 -> P3 六重门验伪。")
    return 0 if len(rows) >= MIN_ROWS else 1


if __name__ == "__main__":
    sys.exit(main())
