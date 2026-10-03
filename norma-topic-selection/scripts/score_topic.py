#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""选题评分卡计算与一票否决判定（纯标准库，无第三方依赖）。

用法:
    python score_topic.py <scorecard.json>

输入 JSON:
{
  "scores":          {"空白真实性": 75, ...},   # 必填，学生自评
  "scores_advisor":  {"空白真实性": 70, ...},   # 可选，导师独立打分
  "weights":         {"空白真实性": 20, ...}    # 必填，权重合计应为 100
}

判定规则:
  规则 1  任一维度 < 50        -> 整体否决
  规则 2  空白真实性 < 70      -> 直接否决
  规则 3  双人单项分歧 > 20    -> 该维度必须重议

退出码:
  0 = 通过
  1 = 触发否决
  2 = 输入不完整或格式错误
"""
import json
import sys

ANY_VETO = 50
AUTHENTICITY_VETO = 70
DIVERGENCE_REVIEW = 20
PASS_LINE = 70
GOOD_LINE = 80

DEFAULT_WEIGHTS = {
    "空白真实性": 20, "重要性": 15, "新颖性": 15, "机理深度": 10,
    "可行性": 15, "可验证性": 10, "期刊匹配与撞题": 10, "退路设计": 5,
}

REQUIRED_DIMS = list(DEFAULT_WEIGHTS.keys())


def fail(msg):
    print("[INPUT-ERROR] %s" % msg)
    return 2


def weighted(scores, weights):
    total = 0.0
    wsum = 0.0
    for dim, w in weights.items():
        s = scores.get(dim)
        if s is None:
            continue
        total += float(s) * float(w)
        wsum += float(w)
    if wsum == 0:
        return 0.0
    return total / wsum


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    try:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            data = json.load(f)
    except (IOError, ValueError) as e:
        return fail("无法读取 JSON: %s" % e)

    scores = data.get("scores")
    if not isinstance(scores, dict) or not scores:
        return fail("缺少 scores 字典")

    weights = data.get("weights") or DEFAULT_WEIGHTS
    missing = [d for d in REQUIRED_DIMS if d not in weights]
    if missing:
        return fail("weights 缺少维度: %s" % "、".join(missing))
    wsum = sum(float(weights[d]) for d in REQUIRED_DIMS)
    if abs(wsum - 100.0) > 1e-6:
        return fail("权重合计应为 100，当前为 %s" % wsum)

    advisor = data.get("scores_advisor")
    if not isinstance(advisor, dict) or not advisor:
        advisor = None

    print("=" * 62)
    print("选题可发表性评分卡")
    print("=" * 62)

    total = weighted(scores, weights)
    veto_reasons = []

    print("\n%-16s %6s %6s %10s" % ("维度", "权重", "学生", "加权"))
    print("-" * 62)
    for dim in REQUIRED_DIMS:
        s = scores.get(dim)
        if s is None:
            print("%-16s %5d%% %6s   [缺]" % (dim, weights[dim], "-"))
            continue
        w = float(weights[dim])
        print("%-16s %5d%% %6s %9.1f" % (dim, weights[dim], s, float(s) * w / 100.0))
    print("-" * 62)
    print("加权总分: %.1f / 100" % total)

    # 规则 1：任一维度 < 50
    low_dims = [d for d in REQUIRED_DIMS
                if scores.get(d) is not None and float(scores[d]) < ANY_VETO]
    if low_dims:
        veto_reasons.append("规则1 任一维度 < %d: %s" % (ANY_VETO, "、".join(low_dims)))

    # 规则 2：空白真实性 < 70
    auth = scores.get("空白真实性")
    if auth is not None and float(auth) < AUTHENTICITY_VETO:
        veto_reasons.append("规则2 空白真实性 %.0f < %d" % (float(auth), AUTHENTICITY_VETO))

    # 规则 3：双人分歧
    divergences = []
    if advisor:
        print("\n--- 双人独立打分对照 ---")
        print("%-16s %6s %6s %8s" % ("维度", "学生", "导师", "分歧"))
        print("-" * 62)
        for dim in REQUIRED_DIMS:
            s1 = scores.get(dim)
            s2 = advisor.get(dim)
            if s1 is None or s2 is None:
                continue
            diff = abs(float(s1) - float(s2))
            flag = " <== 重议" if diff > DIVERGENCE_REVIEW else ""
            print("%-16s %6s %6s %8.1f%s" % (dim, s1, s2, diff, flag))
            if diff > DIVERGENCE_REVIEW:
                divergences.append(dim)
        if divergences:
            print("\n[WARN] 规则3 分歧 > %d 的维度: %s"
                  % (DIVERGENCE_REVIEW, "、".join(divergences)))
        else:
            print("\n[OK] 双人打分无重大分歧")
    else:
        print("\n[WARN] 未提供导师独立打分，规则 3 未生效"
              "（单人自评会让评分卡退化为自欺工具）")

    print("\n" + "=" * 62)
    if veto_reasons:
        print("判定: 否决")
        for r in veto_reasons:
            print("  - %s" % r)
        print("\n处置: 回 P3 补料或换题。不要靠调分数过关。")
        print("=" * 62)
        return 1

    if total >= GOOD_LINE:
        print("判定: 通过（优先推进，加权总分 >= %.0f）" % GOOD_LINE)
    elif total >= PASS_LINE:
        print("判定: 通过（可开题，加权总分 %.1f，参考线 %.0f）" % (total, PASS_LINE))
    else:
        print("判定: 未达参考线（%.1f < %.0f）—— 补料或换题" % (total, PASS_LINE))
    if divergences:
        print("附加: 规则3 待重议维度 -> %s" % "、".join(divergences))
    print("\n提醒: 高分不是免死金牌，真正的风险闸在 P6 MVP 最小验证。")
    print("=" * 62)
    return 0


if __name__ == "__main__":
    sys.exit(main())
