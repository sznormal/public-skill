#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# norma-lit-review · 阶段控制台（Stage Console）脚本
# Copyright (C) 2026 Norma（郑洪英）
#
# 本脚本依据 PolyForm Noncommercial License 1.0.0 分发（禁止商业使用）。
# 完整条款见本 skill 根目录 LICENSE 文件，或
# https://polyformproject.org/licenses/noncommercial/1.0.0
"""
stage_ctl.py — norma-lit-review 阶段控制台（Stage Console）

提供四件事的机械实现，让流水线"看得见、记得住、退得回"：
  1. dashboard  渲染全阶段进度仪表盘（P0..P9，✅完成/🔄进行中/⏳待运行/↩️已回退），
               每行阶段后附「≤10 字阶段小结」（来自台账 summary 字段）
  2. snapshot   每阶段收尾时对 outputs/lit-review 做产物快照（回退用）
  3. ledger     追加/查看"阶段结果台账"记录（含 decision/metrics/artifacts/checkpoint/summary）
  4. back       回退到某阶段：恢复该阶段快照 + 回写 HUD + 标记后续阶段为已回退，
               并在 dry-run 与 --apply 后均提醒用户"需重新走一遍后续流程"

纯标准库实现，无需 pip / 无需 venv。

用法：
  python stage_ctl.py dashboard [--project PATH]
  python stage_ctl.py snapshot --stage P3 [--project PATH]
  python stage_ctl.py log     --stage P3 --summary "已定综述类型" --decision "..." [--metrics k=v ...] [--artifacts a,b] [--checkpoint "..."] [--project PATH]
  python stage_ctl.py ledger  [--project PATH]
  python stage_ctl.py back    --to P2 [--project PATH] [--apply]

说明：
  - 状态文件固定为 {project}/outputs/lit-review/hud_state.json
  - 台账文件固定为 {project}/outputs/lit-review/stage_ledger.json
  - 快照目录为   {project}/outputs/lit-review/stage_snapshots/<Pn>_<时间戳>/
  - 无 --apply 时 back 只打印"将做什么"，不改动任何文件（安全）。
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime

# ── 阶段定义（与 SKILL.md 路由表保持一致）──────────────────────────────
STAGES = [
    ("P0", "综述类型选择"),
    ("P1", "检索策略制定"),
    ("P2", "多库检索执行"),
    ("P3", "文献筛选与分类"),
    ("P4", "文献分析与综合"),
    ("P5", "综述撰写"),
    ("P6", "参考文献真实性核验"),
    ("P7", "质量审核"),
    ("P8", "审稿人发表级审查"),
    ("P9", "审稿后修订"),
]
STAGE_NAME = dict(STAGES)
STAGE_ORDER = [s for s, _ in STAGES]

# 断点续传目录固定名
LR_DIR = "outputs/lit-review"
HUD_FILE = "hud_state.json"
LEDGER_FILE = "stage_ledger.json"
SNAP_DIR = "stage_snapshots"


def _now():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _ts():
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _resolve_project(project):
    """解析项目根目录：--project 直接给；否则从 cwd 向上找含 outputs/lit-review 的目录。"""
    if project:
        return os.path.abspath(project)
    cur = os.getcwd()
    # 向上最多 6 层找 outputs/lit-review
    for _ in range(6):
        if os.path.isdir(os.path.join(cur, LR_DIR)):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    # 找不到就落在 cwd（后续命令会自行建目录）
    return os.getcwd()


def _lr_path(project):
    return os.path.join(project, LR_DIR)


def _load_json(path, default):
    if not os.path.isfile(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return default


def _save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _status_of(stage, hud, ledger):
    """返回某阶段的显示状态：done / active / pending / rolled_back"""
    completed = set(hud.get("history", {}).get("completed_stages", []))
    current = hud.get("meta", {}).get("current_stage", "P0")
    # 台账里若有 rolled_back 标记则优先
    for e in ledger:
        if e.get("stage") == stage and e.get("status") == "rolled_back":
            return "rolled_back"
    if stage in completed:
        return "done"
    if stage == current:
        return "active"
    return "pending"


def _last_ledger_line(ledger):
    for e in reversed(ledger):
        if e.get("status") != "rolled_back":
            return e
    return None


# ── 命令实现 ─────────────────────────────────────────────────────────
def cmd_dashboard(args):
    project = _resolve_project(args.project)
    lr = _lr_path(project)
    hud = _load_json(os.path.join(lr, HUD_FILE), {})
    ledger = _load_json(os.path.join(lr, LEDGER_FILE), [])
    topic = hud.get("search", {}).get("topic", "") or hud.get("meta", {}).get("skill_name", "")
    current = hud.get("meta", {}).get("current_stage", "P0")
    recent = _last_ledger_line(ledger)

    # 阶段小结映射：取每个阶段最新一条（非 rolled_back）台账的 summary
    summary_map = {}
    for e in ledger:
        if e.get("status") == "rolled_back":
            continue
        stg = e.get("stage")
        if stg:
            summary_map[stg] = (e.get("summary") or "").strip()

    lines = []
    lines.append("╭─ Norma理工科综述 · 阶段仪表盘 ───────────────────────────────╮")
    for s, name in STAGES:
        st = _status_of(s, hud, ledger)
        icon = {"done": "✅", "active": "🔄", "pending": "⏳", "rolled_back": "↩️"}[st]
        disp_summary = summary_map.get(s) or "—"
        lines.append(f"│ {s} {name:<10} {icon} {st:<11} {disp_summary}")
    lines.append("│" + "─" * 60)
    if topic:
        lines.append(f"│ 主题：{topic[:46]}")
    lines.append(f"│ 当前阶段：{current} · {STAGE_NAME.get(current, '')}")
    if recent:
        km = recent.get("key_metrics") or {}
        km_str = "  ".join(f"{k}={v}" for k, v in km.items()) if km else ""
        lines.append(f"│ 最近记录：{recent.get('stage')} {recent.get('status','')} — {km_str}".rstrip())
    # 计算进度
    done = sum(1 for s, _ in STAGES if _status_of(s, hud, ledger) == "done")
    lines.append(f"│ 进度：{done}/{len(STAGES)} 阶段完成")
    lines.append("╰──────────────────────────────────────────────────────────────╯")
    print("\n".join(lines))
    return 0


def cmd_snapshot(args):
    project = _resolve_project(args.project)
    lr = _lr_path(project)
    stage = args.stage
    if stage not in STAGE_ORDER:
        print(f"[ERR] 未知阶段 {stage}，可选：{', '.join(STAGE_ORDER)}", file=sys.stderr)
        return 2
    os.makedirs(lr, exist_ok=True)
    # 收集要快照的文件（排除状态文件与快照目录自身）
    exclude = {HUD_FILE, LEDGER_FILE, SNAP_DIR}
    src_files = []
    for entry in os.listdir(lr):
        full = os.path.join(lr, entry)
        if entry in exclude:
            continue
        if os.path.isdir(full) and entry == SNAP_DIR:
            continue
        src_files.append(full)
    if not src_files:
        print(f"[WARN] {lr} 下无可快照产物（仅状态文件），跳过。")
        return 0
    dest = os.path.join(lr, SNAP_DIR, f"{stage}_{_ts()}")
    os.makedirs(dest, exist_ok=True)
    for f in src_files:
        if os.path.isdir(f):
            shutil.copytree(f, os.path.join(dest, os.path.basename(f)), dirs_exist_ok=True)
        else:
            shutil.copy2(f, dest)
    print(f"[OK] 已快照 {stage} 阶段产物 → {dest}（{len(src_files)} 项）")
    return 0


def cmd_log(args):
    project = _resolve_project(args.project)
    lr = _lr_path(project)
    stage = args.stage
    if stage not in STAGE_ORDER:
        print(f"[ERR] 未知阶段 {stage}", file=sys.stderr)
        return 2
    ledger = _load_json(os.path.join(lr, LEDGER_FILE), [])
    metrics = {}
    for kv in (args.metrics or []):
        if "=" in kv:
            k, v = kv.split("=", 1)
            metrics[k.strip()] = v.strip()
    arts = [a.strip() for a in (args.artifacts or "").split(",") if a.strip()]
    # 阶段小结：≤10 字，超长截断并警告
    summary = (args.summary or "").strip()
    if summary:
        n = len(summary)
        if n > 10:
            print(f"[WARN] 阶段小结「{summary}」共 {n} 字，超过 10 字上限，已截断为前 10 字。", file=sys.stderr)
            summary = summary[:10]
    elif not args.note:
        print("[WARN] 未提供阶段小结（--summary），仪表盘该项将显示「—」。建议每阶段补一句 ≤10 字小结。", file=sys.stderr)
    entry = {
        "stage": stage,
        "name": STAGE_NAME.get(stage, ""),
        "ts": _now(),
        "status": "done",
        "summary": summary,
        "decision": args.decision or "",
        "key_metrics": metrics,
        "artifacts": arts,
        "checkpoint": args.checkpoint or "",
        "note": args.note or "",
    }
    ledger.append(entry)
    _save_json(os.path.join(lr, LEDGER_FILE), ledger)
    # 同步把完成阶段写进 HUD（若 HUD 存在）
    hud = _load_json(os.path.join(lr, HUD_FILE), {})
    if hud:
        hud.setdefault("history", {}).setdefault("completed_stages", [])
        if stage not in hud["history"]["completed_stages"]:
            hud["history"]["completed_stages"].append(stage)
        hud.setdefault("meta", {})["current_stage"] = _next_stage(stage)
        _save_json(os.path.join(lr, HUD_FILE), hud)
    print(f"[OK] 已记录阶段台账：{stage} · {entry['ts']}")
    return 0


def cmd_ledger(args):
    project = _resolve_project(args.project)
    lr = _lr_path(project)
    ledger = _load_json(os.path.join(lr, LEDGER_FILE), [])
    if not ledger:
        print("[INFO] 暂无阶段台账记录。")
        return 0
    for e in ledger:
        km = "  ".join(f"{k}={v}" for k, v in e.get("key_metrics", {}).items())
        print(f"• {e.get('stage')} [{e.get('status')}] {e.get('ts')}")
        print(f"    决策：{e.get('decision')}")
        if km:
            print(f"    指标：{km}")
        if e.get("artifacts"):
            print(f"    产物：{', '.join(e.get('artifacts'))}")
        if e.get("checkpoint"):
            print(f"    检查点：{e.get('checkpoint')}")
    return 0


def _next_stage(stage):
    i = STAGE_ORDER.index(stage)
    return STAGE_ORDER[min(i + 1, len(STAGE_ORDER) - 1)]


def cmd_back(args):
    project = _resolve_project(args.project)
    lr = _lr_path(project)
    target = args.to
    if target not in STAGE_ORDER:
        print(f"[ERR] 未知阶段 {target}", file=sys.stderr)
        return 2
    hud = _load_json(os.path.join(lr, HUD_FILE), {})
    ledger = _load_json(os.path.join(lr, LEDGER_FILE), [])
    current = hud.get("meta", {}).get("current_stage", "P0")
    cur_idx = STAGE_ORDER.index(current) if current in STAGE_ORDER else 0
    tgt_idx = STAGE_ORDER.index(target)

    if tgt_idx >= cur_idx:
        print(f"[WARN] 目标 {target} 不早于当前 {current}，回退无意义（请用更小的阶段号）。")
        return 0

    # 找目标阶段最新快照
    snap_root = os.path.join(lr, SNAP_DIR)
    cand = []
    if os.path.isdir(snap_root):
        for d in os.listdir(snap_root):
            if d.startswith(target + "_"):
                cand.append(d)
    cand.sort(reverse=True)
    subseq = STAGE_ORDER[tgt_idx + 1:cur_idx + 1]
    plan = []
    plan.append(f"将回退：{current} → {target}")
    if subseq:
        plan.append(f"后续阶段将被标记为已回退：{', '.join(subseq)}")
        plan.append(f"⚠️ 回退后需重新走一遍后续流程：{' → '.join(subseq)}")
    else:
        plan.append("（目标之后无后续阶段）")
    if cand:
        plan.append(f"将恢复快照：{cand[0]}")
    else:
        plan.append(f"[!] 未发现 {target} 的快照，将仅回写 HUD/台账，不恢复产物文件")
    print("── 回退计划（dry-run）──")
    for p in plan:
        print("  " + p)
    if not args.apply:
        print("\n[SAFE] 未加 --apply，未做任何改动。确认无误后加 --apply 执行。")
        return 0

    # 执行前自动备份当前产物（防误回退：恢复快照会覆盖 lr 下文件）
    rb = os.path.join(snap_root, "rollback_backup_" + _now().replace(":", "-").replace("T", "_"))
    os.makedirs(rb, exist_ok=True)
    backed = 0
    for entry in os.listdir(lr):
        if entry in (HUD_FILE, LEDGER_FILE, SNAP_DIR):
            continue
        src = os.path.join(lr, entry)
        try:
            if os.path.isdir(src):
                shutil.copytree(src, os.path.join(rb, entry), dirs_exist_ok=True)
            else:
                shutil.copy2(src, os.path.join(rb, entry))
            backed += 1
        except OSError:
            pass
    if backed:
        print(f"[INFO] 已自动备份当前产物（{backed} 项）到 {os.path.basename(rb)}，误回退可恢复。")

    # 执行：恢复快照产物
    if cand:
        snap_path = os.path.join(snap_root, cand[0])
        for entry in os.listdir(snap_path):
            src = os.path.join(snap_path, entry)
            dst = os.path.join(lr, entry)
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)
    # 回写 HUD
    hud.setdefault("meta", {})["current_stage"] = target
    completed = hud.setdefault("history", {}).setdefault("completed_stages", [])
    hud["history"]["completed_stages"] = [s for s in completed if STAGE_ORDER.index(s) <= tgt_idx]
    _save_json(os.path.join(lr, HUD_FILE), hud)
    # 标记后续阶段台账为 rolled_back
    for e in ledger:
        if e.get("stage") in STAGE_ORDER[tgt_idx + 1:cur_idx + 1]:
            e["status"] = "rolled_back"
    _save_json(os.path.join(lr, LEDGER_FILE), ledger)
    print("\n[OK] 已回退到 " + target + "，HUD 与台账已更新。")
    if subseq:
        print("⚠️ 提醒：请重新走一遍后续流程 —— " + " → ".join(subseq))
        print("   从「" + STAGE_NAME.get(subseq[0], subseq[0]) + "」(" + subseq[0] +
              ") 开始，逐阶段重做产物并重新记台账 / 快照。")
    return 0


def build_parser():
    p = argparse.ArgumentParser(description="norma-lit-review 阶段控制台")
    sub = p.add_subparsers(dest="cmd", required=True)

    # --project 用 parent 注入每个子命令（argparse 子命令不继承顶层参数）
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--project", help="项目根目录（默认自动探测 outputs/lit-review）")

    sub.add_parser("dashboard", parents=[common], help="渲染全阶段进度仪表盘")
    sub.add_parser("ledger", parents=[common], help="查看阶段结果台账")

    sp = sub.add_parser("snapshot", parents=[common], help="对当前产物做阶段快照")
    sp.add_argument("--stage", required=True, help="阶段号，如 P3")

    lp = sub.add_parser("log", parents=[common], help="追加一条阶段结果记录")
    lp.add_argument("--stage", required=True)
    lp.add_argument("--summary", default="", help="本阶段小结，≤10 字，将显示在仪表盘每行阶段后")
    lp.add_argument("--decision", default="")
    lp.add_argument("--metrics", nargs="*", default=[], help="k=v 形式，可多个")
    lp.add_argument("--artifacts", default="", help="逗号分隔的产物文件名")
    lp.add_argument("--checkpoint", default="")
    lp.add_argument("--note", default="")

    bp = sub.add_parser("back", parents=[common], help="回退到某阶段（默认 dry-run）")
    bp.add_argument("--to", required=True, help="目标阶段号，如 P2")
    bp.add_argument("--apply", action="store_true", help="真正执行回退（不加则只打印计划）")
    return p


def main():
    args = build_parser().parse_args()
    dispatch = {
        "dashboard": cmd_dashboard,
        "ledger": cmd_ledger,
        "snapshot": cmd_snapshot,
        "log": cmd_log,
        "back": cmd_back,
    }
    return dispatch[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
