#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wikiskill — WikiSkill 进化循环工作区管理器

实现论文 WikiSkill (arXiv:2608.27454) 的三层架构与四组件循环：

    raw/                     不可变原始轨迹  (只追加)
    wiki/                    持久知识库      (永不回滚)
      patterns/*.md          失败模式 / 成功策略
      logs.md                进化日志
      skill-impact.md        提案审计轨迹
      index.md               模式目录
    skills/                  可执行技能      (可回滚)
      <name>/SKILL.md
      <name>/PURPOSE.md
    .wikiskill/              元数据
      state.json             循环状态机
      snapshots/iter-XXXX/   已接受版本的技能快照

设计红线:
  1. 本工具不提供任何删除 wiki 内容的命令 —— Wiki 永不回滚
  2. 门控拒绝时只回滚 skills/, wiki 保持原样
  3. 轨迹采样与根因分析由 LLM agent (Wiki Maintainer / Skill Proposer) 完成,
     本工具只提供文件操作原语与状态管理

用法:
  python wikiskill.py init      --root DIR --name N --eval-cmd CMD
  python wikiskill.py status    --root DIR
  python wikiskill.py evaluate  --root DIR --split val
  python wikiskill.py baseline  --root DIR [--score X]
  python wikiskill.py ingest    --root DIR --run K --file F
  python wikiskill.py pattern new  --root DIR --slug S --title T --kind K --body-file F
  python wikiskill.py pattern edit --root DIR --slug S --mode append|replace|insert ...
  python wikiskill.py pattern list --root DIR
  python wikiskill.py propose   --root DIR --run K --skill N --action create|patch
                                --diff-file F --intent T [--sources S1,S2]
  python wikiskill.py gate      --root DIR --run K [--score X]
  python wikiskill.py prune     --root DIR --keep N
  python wikiskill.py export    --root DIR --target DIR
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

RAW = "raw"
WIKI = "wiki"
PATTERNS = "wiki/patterns"
SKILLS = "skills"
META = ".wikiskill"
STATE = ".wikiskill/state.json"
SNAPS = ".wikiskill/snapshots"

KINDS = ("failure", "success")
ACTIONS = ("create", "patch")


# --------------------------------------------------------------------------
# 基础工具
# --------------------------------------------------------------------------

def now_iso():
    return datetime.now().isoformat(timespec="seconds")


def die(msg, code=1):
    print(f"[wikiskill] ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def say(msg):
    print(f"[wikiskill] {msg}")


def wpath(root):
    return Path(root).resolve()


def resolve_path(p):
    """兼容 Git Bash 风格路径（/c/..., /tmp/...）到 Windows 真实路径。

    在 Git Bash 下传入 /tmp/x.md 时，Windows Python 会解析成 \\tmp\\x.md 而失败。
    """
    path = Path(p)
    if path.exists():
        return path
    s = str(p).replace("\\", "/")
    m = re.match(r"^/([a-zA-Z])/(.*)$", s)
    if m:
        cand = Path(f"{m.group(1).upper()}:/{m.group(2)}")
        if cand.exists():
            return cand
    if s.startswith("/tmp/"):
        cand = Path(tempfile.gettempdir()) / s[5:]
        if cand.exists():
            return cand
    return path


def read_text(p):
    return Path(p).read_text(encoding="utf-8")


def write_text(p, s):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8")


def append_text(p, s):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(s)


def load_state(root):
    sp = wpath(root) / STATE
    if not sp.exists():
        die(f"未找到 {STATE}，请先在 {root} 执行 init")
    return json.loads(read_text(sp))


def save_state(root, st):
    write_text(wpath(root) / STATE, json.dumps(st, ensure_ascii=False, indent=2))


def tag(run):
    return f"iter-{int(run):04d}"


def copy_tree(src, dst):
    src, dst = Path(src), Path(dst)
    if dst.exists():
        shutil.rmtree(dst)
    if src.exists():
        shutil.copytree(src, dst)


# --------------------------------------------------------------------------
# 骨架初始化
# --------------------------------------------------------------------------

def cmd_init(a):
    root = wpath(a.root)
    (root / RAW).mkdir(parents=True, exist_ok=True)
    (root / PATTERNS).mkdir(parents=True, exist_ok=True)
    (root / SKILLS).mkdir(parents=True, exist_ok=True)
    (root / META).mkdir(parents=True, exist_ok=True)
    (root / SNAPS).mkdir(parents=True, exist_ok=True)

    write_text(root / WIKI / "index.md",
               "# Wiki 模式目录\n\n"
               "> 由 `wikiskill.py pattern` 自动维护，请勿手工编辑本表格。\n\n"
               "| Slug | 类型 | 标题 | 首次出现 | 最近更新 | 出现次数 | 关联技能 |\n"
               "| --- | --- | --- | --- | --- | --- | --- |\n"
               "| _(暂无)_ | | | | | | |\n")

    write_text(root / WIKI / "logs.md",
               "# 进化日志\n\n"
               "> 每轮迭代由 Wiki Maintainer 追加本轮发现摘要。本文件只追加，不删除。\n\n")

    write_text(root / WIKI / "skill-impact.md",
               "# 技能提案审计轨迹\n\n"
               "> 由门控 (gate) 在每轮验证后自动追加。记录被否决的提案是核心资产，\n"
               "> 用于避免后续迭代重复提出已被证明无效的修改。\n\n")

    st = {
        "name": a.name,
        "created": now_iso(),
        "eval_cmd": a.eval_cmd,
        "train": a.train,
        "val": a.val,
        "current_run": 0,
        "r_best": None,
        "r_baseline": None,
        "skills_version": 0,
        "last_accepted_snapshot": "base",
        "early_stopped": False,
        "history": [],
    }
    save_state(root, st)

    # 基线快照：初始（通常为空）技能集
    copy_tree(root / SKILLS, root / SNAPS / "base" / SKILLS)

    say(f"工作区已初始化: {root}")
    say(f"  raw/    不可变轨迹")
    say(f"  wiki/   持久知识库（永不回滚）")
    say(f"  skills/ 可执行技能（可回滚，基线快照 base 已建立）")
    if not a.eval_cmd:
        say("警告: 未设置 --eval-cmd，门控将只能使用 --score 手动传入验证分数")


# --------------------------------------------------------------------------
# 评估
# --------------------------------------------------------------------------

def run_eval(root, split="val"):
    st = load_state(root)
    root = wpath(root)
    if not st.get("eval_cmd"):
        die("未配置 eval_cmd，无法自动评估。请改用 --score 手动传入验证分数")

    cmd = (st["eval_cmd"]
           .replace("{skills}", str(root / SKILLS))
           .replace("{split}", split)
           .replace("{root}", str(root)))

    say(f"执行评估: {cmd}")
    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        die(f"评估命令失败 (exit={proc.returncode})\nSTDERR:\n{proc.stderr[:2000]}")

    out = proc.stdout.strip()
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        die("评估命令的 stdout 必须是 JSON，形如 {\"score\": 0.42, \"details\": [...]}\n"
            f"实际输出前 500 字符:\n{out[:500]}")

    if "score" not in data:
        die("评估输出 JSON 缺少 score 字段")
    return float(data["score"]), data


def cmd_evaluate(a):
    score, data = run_eval(a.root, a.split)
    if a.json:
        print(json.dumps({"score": score, "raw": data}, ensure_ascii=False, indent=2))
    else:
        say(f"{a.split} 集得分: {score:.4f}")
        if isinstance(data.get("details"), list):
            fails = [d for d in data["details"] if isinstance(d, dict) and not d.get("pass")]
            say(f"  用例总数 {len(data['details'])}，失败 {len(fails)}")


def cmd_baseline(a):
    root = wpath(a.root)
    st = load_state(root)
    score = a.score if a.score is not None else run_eval(root, "val")[0]
    st["r_baseline"] = score
    st["r_best"] = score
    save_state(root, st)
    say(f"基线验证分已记录: {score:.4f}  (门控阈值 R_best 初始化为该值)")


# --------------------------------------------------------------------------
# ① Inference：轨迹写入
# --------------------------------------------------------------------------

def cmd_ingest(a):
    root = wpath(a.root)
    st = load_state(root)
    t = tag(a.run)
    dstdir = root / RAW / t
    dstdir.mkdir(parents=True, exist_ok=True)

    n = 0
    for f in a.file:
        src = Path(f)
        if not src.exists():
            die(f"轨迹文件不存在: {src}")
        shutil.copy2(src, dstdir / src.name)
        n += 1

    st["current_run"] = max(st.get("current_run", 0), int(a.run))
    save_state(root, st)
    say(f"已写入 {n} 条轨迹 -> raw/{t}/   (raw 层只追加，不可修改)")


# --------------------------------------------------------------------------
# ② Wiki Maintainer：pattern 维护
# --------------------------------------------------------------------------

def parse_pattern_meta(body):
    meta = {}
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("- **") and "**:" in line:
            # 前缀 "- **" 长度为 4，键名位于 [4, index("**:"))
            idx = line.index("**:")
            k = line[4:idx]
            v = line[idx + 3:].strip()
            meta[k] = v
    return meta


def set_pattern_meta(body, key, value):
    lines = body.splitlines()
    target = f"- **{key}**:"
    for i, ln in enumerate(lines):
        if ln.strip().startswith(target):
            lines[i] = f"- **{key}**: {value}"
            return "\n".join(lines)
    # 未找到则插到第一个空行前 / 标题后
    for i, ln in enumerate(lines):
        if ln.strip() == "" and i > 0 and lines[i - 1].startswith("#"):
            lines.insert(i, f"- **{key}**: {value}")
            return "\n".join(lines)
    lines.insert(1, f"- **{key}**: {value}")
    return "\n".join(lines)


def cmd_pattern(a):
    root = wpath(a.root)
    pdir = root / PATTERNS

    if a.pattern_cmd == "new":
        if a.kind not in KINDS:
            die(f"--kind 必须是 {KINDS} 之一")
        p = pdir / f"{a.slug}.md"
        if p.exists():
            die(f"pattern 已存在: {p}（如需修改请用 pattern edit）")
        body = (a.body_file and read_text(resolve_path(a.body_file))) or a.body or ""
        doc = (f"# {a.title}\n\n"
               f"- **Slug**: {a.slug}\n"
               f"- **Kind**: {a.kind}\n"
               f"- **First seen**: {tag(a.run) if a.run is not None else 'unknown'}\n"
               f"- **Last updated**: {tag(a.run) if a.run is not None else 'unknown'}\n"
               f"- **Occurrences**: 1\n"
               f"- **Linked skills**: _(none)_\n\n"
               f"{body}\n\n"
               f"## 更新记录\n\n"
               f"- {tag(a.run) if a.run is not None else 'unknown'}: 首次记录\n")
        write_text(p, doc)
        rebuild_index(root)
        say(f"已创建 pattern: wiki/patterns/{a.slug}.md")

    elif a.pattern_cmd == "edit":
        p = pdir / f"{a.slug}.md"
        if not p.exists():
            die(f"pattern 不存在: {p}")
        body = read_text(p)

        if a.mode == "append":
            text = (a.body_file and read_text(resolve_path(a.body_file))) or a.body or ""
            if not text:
                die("append 模式需要 --body 或 --body-file")
            # 保证「## 更新记录」始终位于文件末尾
            marker = "\n## 更新记录"
            if marker in body:
                idx = body.index(marker)
                body = body[:idx].rstrip() + "\n\n" + text.strip() + "\n" + body[idx:]
            else:
                body = body.rstrip() + "\n\n" + text.strip() + "\n"
        elif a.mode == "replace":
            old = (a.old_file and read_text(resolve_path(a.old_file))) or a.old
            new = (a.new_file and read_text(resolve_path(a.new_file))) or a.new
            if not old:
                die("replace 模式需要 --old 或 --old-file")
            if old not in body:
                die("replace 失败：--old 文本在 pattern 中未找到（请精确匹配原文）")
            body = body.replace(old, new or "")
        elif a.mode == "insert":
            if not a.anchor:
                die("insert 模式需要 --anchor（在该文本之后插入）")
            text = (a.body_file and read_text(resolve_path(a.body_file))) or a.body or ""
            if a.anchor not in body:
                die("insert 失败：--anchor 文本在 pattern 中未找到")
            body = body.replace(a.anchor, a.anchor + "\n" + text.strip() + "\n", 1)
        else:
            die(f"未知编辑模式: {a.mode}")

        # 维护元数据
        meta = parse_pattern_meta(body)
        if a.run is not None:
            body = set_pattern_meta(body, "Last updated", tag(a.run))
            try:
                occ = int(str(meta.get("Occurrences", "1")).strip())
            except ValueError:
                occ = 1
            body = set_pattern_meta(body, "Occurrences", str(occ + 1))
        if a.link_skill:
            cur = meta.get("Linked skills", "").strip()
            cur = "" if cur in ("", "_(none)_") else cur + ", "
            body = set_pattern_meta(body, "Linked skills", cur + a.link_skill)

        if a.note:
            body = body.rstrip() + f"\n- {tag(a.run) if a.run is not None else '?'}: {a.note}\n"
        elif a.run is not None:
            body = body.rstrip() + f"\n- {tag(a.run)}: {a.mode} 更新\n"

        write_text(p, body)
        rebuild_index(root)
        say(f"已更新 pattern: wiki/patterns/{a.slug}.md ({a.mode})")

    elif a.pattern_cmd == "list":
        if not pdir.exists() or not any(pdir.glob("*.md")):
            say("暂无 pattern")
            return
        rows = []
        for p in sorted(pdir.glob("*.md")):
            meta = parse_pattern_meta(read_text(p))
            rows.append({
                "slug": p.stem,
                "kind": meta.get("Kind", "?"),
                "title": read_text(p).splitlines()[0].lstrip("# ").strip() if read_text(p) else "",
                "first": meta.get("First seen", "?"),
                "last": meta.get("Last updated", "?"),
                "occ": meta.get("Occurrences", "?"),
                "linked": meta.get("Linked skills", "-"),
            })
        if a.json:
            print(json.dumps(rows, ensure_ascii=False, indent=2))
        else:
            print(f"{'SLUG':<34}{'KIND':<10}{'OCC':<5}{'FIRST':<12}{'LAST':<12}")
            for r in rows:
                print(f"{r['slug']:<34}{r['kind']:<10}{str(r['occ']):<5}{r['first']:<12}{r['last']:<12}")

    elif a.pattern_cmd == "show":
        p = pdir / f"{a.slug}.md"
        if not p.exists():
            die(f"pattern 不存在: {p}")
        print(read_text(p))


def rebuild_index(root):
    root = wpath(root)
    pdir = root / PATTERNS
    rows = []
    for p in sorted(pdir.glob("*.md")):
        if p.name == "index.md":
            continue
        body = read_text(p)
        meta = parse_pattern_meta(body)
        title = body.splitlines()[0].lstrip("# ").strip() if body else p.stem
        rows.append((p.stem, meta.get("Kind", "?"), title,
                     meta.get("First seen", "?"), meta.get("Last updated", "?"),
                     meta.get("Occurrences", "?"), meta.get("Linked skills", "-")))

    lines = ["# Wiki 模式目录", "",
             "> 由 `wikiskill.py pattern` 自动维护，请勿手工编辑本表格。", "",
             "| Slug | 类型 | 标题 | 首次出现 | 最近更新 | 出现次数 | 关联技能 |",
             "| --- | --- | --- | --- | --- | --- | --- |"]
    if rows:
        for r in rows:
            lines.append(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} | {r[6]} |")
    else:
        lines.append("| _(暂无)_ | | | | | | |")
    write_text(root / WIKI / "index.md", "\n".join(lines) + "\n")


def cmd_index_rebuild(a):
    rebuild_index(a.root)
    say("index.md 已重建")


def cmd_log(a):
    root = wpath(a.root)
    text = (a.body_file and read_text(resolve_path(a.body_file))) or a.body or ""
    if not text:
        die("需要 --body 或 --body-file")
    append_text(root / WIKI / "logs.md",
                f"\n## {tag(a.run)} — {now_iso()}\n\n{text.strip()}\n")
    say(f"已追加进化日志 -> wiki/logs.md ({tag(a.run)})")


# --------------------------------------------------------------------------
# ③ Skill Proposer：提案登记
# --------------------------------------------------------------------------

def cmd_propose(a):
    root = wpath(a.root)
    st = load_state(root)
    if a.action not in ACTIONS:
        die(f"--action 必须是 {ACTIONS} 之一")

    diff = (a.diff_file and read_text(resolve_path(a.diff_file))) or a.diff or ""
    if not diff:
        die("必须提供 --diff-file 或 --diff（unified diff 或变更描述）")

    t = tag(a.run)
    rec = {
        "run": int(a.run),
        "tag": t,
        "skill": a.skill,
        "action": a.action,
        "intent": a.intent or "",
        "sources": [s.strip() for s in (a.sources or "").split(",") if s.strip()],
        "diff": diff,
        "proposed_at": now_iso(),
        "verdict": "pending",
        "score": None,
    }
    st.setdefault("proposals", []).append(rec)
    st["current_run"] = max(st.get("current_run", 0), int(a.run))
    save_state(root, st)
    say(f"提案已登记: [{a.action}] {a.skill} @ {t}")
    say("下一步：把改动实际应用到 skills/ 后，执行 gate 做验证门控")


# --------------------------------------------------------------------------
# ④ Gating & Rollback
# --------------------------------------------------------------------------

def cmd_gate(a):
    root = wpath(a.root)
    st = load_state(root)

    if st.get("r_best") is None:
        die("尚未记录基线验证分，请先执行 baseline")

    t = tag(a.run)
    score = a.score if a.score is not None else run_eval(root, "val")[0]
    r_best = st["r_best"]

    if r_best is not None and abs(score - 1.0) < 1e-9 and abs(r_best - 1.0) < 1e-9:
        st["early_stopped"] = True

    accepted = score > r_best + 1e-12
    verdict = "accepted" if accepted else "rejected"

    # 定位本轮提案
    prop = None
    for p in reversed(st.get("proposals", [])):
        if p["tag"] == t and p["verdict"] == "pending":
            prop = p
            break

    skill_name = prop["skill"] if prop else (a.skill or "unknown")
    action = prop["action"] if prop else "unknown"
    intent = prop["intent"] if prop else ""
    diff = prop["diff"] if prop else ""

    if accepted:
        copy_tree(root / SKILLS, root / SNAPS / t / SKILLS)
        st["last_accepted_snapshot"] = t
        st["r_best"] = score
        st["skills_version"] = st.get("skills_version", 0) + 1
        say(f"ACCEPTED  验证分 {r_best:.4f} -> {score:.4f}   技能快照 {t} 已建立")
    else:
        base = st.get("last_accepted_snapshot", "base")
        snap = root / SNAPS / base / SKILLS
        rel = "低于" if score < r_best - 1e-12 else "持平于"
        if snap.exists():
            copy_tree(snap, root / SKILLS)
            say(f"REJECTED  验证分 {score:.4f} {rel} R_best {r_best:.4f}"
                f"   技能已回滚至快照 {base}")
        else:
            say(f"REJECTED  验证分 {score:.4f} {rel} R_best {r_best:.4f}   (无快照可回滚)")

    if prop:
        prop["verdict"] = verdict
        prop["score"] = score

    st.setdefault("history", []).append({
        "run": int(a.run), "tag": t, "score": score,
        "prev_best": r_best, "verdict": verdict,
        "skill": skill_name, "action": action, "intent": intent,
        "gated_at": now_iso(),
    })
    save_state(root, st)

    # 审计轨迹 —— 无论接受与否都写入，这是 Wiki 不回滚的体现
    entry = [
        f"\n## {t} — {verdict.upper()} — {now_iso()}",
        f"\n- **目标技能**: `{skill_name}`",
        f"- **动作**: {action}",
        f"- **意图**: {intent or '_(未填写)_'}",
        f"- **触发模式**: {', '.join(prop['sources']) if prop and prop.get('sources') else '_(未标注)_'}",
        f"- **验证分**: {score:.4f}  (门控前 R_best = {r_best:.4f})",
        f"- **判定**: {'接受，已建立快照' if accepted else '拒绝，技能回滚，本条记录保留'}",
        "\n### 变更内容\n",
        "```diff",
        diff.rstrip(),
        "```",
    ]
    append_text(root / WIKI / "skill-impact.md", "\n".join(entry) + "\n")

    say(f"审计记录已追加 -> wiki/skill-impact.md  (Wiki 永不回滚)")

    if a.json:
        print(json.dumps({
            "run": int(a.run), "score": score, "prev_best": r_best,
            "verdict": verdict, "skill": skill_name,
            "r_best": st["r_best"], "early_stopped": st.get("early_stopped", False),
        }, ensure_ascii=False, indent=2))


# --------------------------------------------------------------------------
# 状态 / 剪枝 / 导出
# --------------------------------------------------------------------------

def cmd_status(a):
    root = wpath(a.root)
    st = load_state(root)
    hist = st.get("history", [])
    n_acc = sum(1 for h in hist if h["verdict"] == "accepted")
    n_rej = len(hist) - n_acc
    n_pat = len(list((root / PATTERNS).glob("*.md")))
    n_skill = len([d for d in (root / SKILLS).iterdir() if d.is_dir()]) if (root / SKILLS).exists() else 0

    view = {
        "name": st["name"],
        "run": st.get("current_run", 0),
        "r_baseline": st.get("r_baseline"),
        "r_best": st.get("r_best"),
        "gain": (round(st["r_best"] - st["r_baseline"], 4)
                 if st.get("r_best") is not None and st.get("r_baseline") is not None else None),
        "proposals_accepted": n_acc,
        "proposals_rejected": n_rej,
        "patterns": n_pat,
        "skills": n_skill,
        "skills_version": st.get("skills_version", 0),
        "last_accepted_snapshot": st.get("last_accepted_snapshot"),
        "early_stopped": st.get("early_stopped", False),
    }

    if a.json:
        print(json.dumps(view, ensure_ascii=False, indent=2))
        return

    print("=" * 58)
    print(f"  WikiSkill 工作区: {st['name']}")
    print("=" * 58)
    print(f"  迭代轮次        : {view['run']}    (已接受 {n_acc} / 已拒绝 {n_rej})")
    print(f"  验证分 基线→最优: {view['r_baseline']} → {view['r_best']}"
          + (f"   (+{view['gain']})" if view["gain"] is not None else ""))
    print(f"  Wiki 模式数     : {n_pat}")
    print(f"  技能数 / 版本   : {n_skill} / {view['skills_version']}")
    print(f"  当前技能快照    : {view['last_accepted_snapshot']}")
    if view["early_stopped"]:
        print("  状态            : 已达验证集满分，早停")
    print("-" * 58)
    if hist:
        print("  近期门控记录:")
        for h in hist[-8:]:
            mark = "+" if h["verdict"] == "accepted" else "-"
            print(f"    [{mark}] {h['tag']}  {h['score']:.4f}  {h['skill']} ({h['action']})")
    print("=" * 58)
    print("  红线提醒: Inference Agent 在训练 rollout 期间禁止访问 wiki/")


def cmd_prune(a):
    """只清理 raw/ 轨迹与旧快照 —— wiki/ 永不剪枝内容，本命令不涉及它。"""
    root = wpath(a.root)
    st = load_state(root)
    removed = 0

    def prune_dir(base):
        nonlocal removed
        if not base.exists():
            return
        items = sorted([d for d in base.iterdir() if d.is_dir()])
        if len(items) <= a.keep:
            return
        for d in items[:-a.keep]:
            if a.keep_accepted and d.name == st.get("last_accepted_snapshot"):
                continue
            shutil.rmtree(d)
            removed += 1

    if a.raw:
        prune_dir(root / RAW)
    if a.snapshots:
        prune_dir(root / SNAPS)

    say(f"已清理 {removed} 个旧目录（raw/snapshots）。wiki/ 内容未被触碰。")


def cmd_export(a):
    root = wpath(a.root)
    st = load_state(root)
    tgt = Path(a.target)
    tgt.mkdir(parents=True, exist_ok=True)
    copy_tree(root / SKILLS, tgt / SKILLS)

    summary = [
        f"# WikiSkill 导出摘要 — {st['name']}",
        "",
        f"- 导出时间: {now_iso()}",
        f"- 迭代轮次: {st.get('current_run', 0)}",
        f"- 验证分: {st.get('r_baseline')} → {st.get('r_best')}",
        f"- 技能版本: {st.get('skills_version', 0)}",
        f"- Wiki 模式数: {len(list((root / PATTERNS).glob('*.md')))}",
        "",
        "## 门控历史", "",
        "| 轮次 | 验证分 | 判定 | 技能 | 动作 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for h in st.get("history", []):
        summary.append(f"| {h['tag']} | {h['score']:.4f} | {h['verdict']} | "
                       f"{h['skill']} | {h['action']} |")
    write_text(tgt / "EXPORT-SUMMARY.md", "\n".join(summary) + "\n")

    if a.with_wiki:
        copy_tree(root / WIKI, tgt / WIKI)

    say(f"已导出技能 -> {tgt}   摘要: EXPORT-SUMMARY.md")


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        prog="wikiskill",
        description="WikiSkill 进化循环工作区管理器 (arXiv:2608.27454)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add(name, help_):
        p = sub.add_parser(name, help=help_)
        p.add_argument("--root", required=True, help="工作区根目录")
        return p

    p = add("init", "初始化三层工作区")
    p.add_argument("--name", required=True)
    p.add_argument("--eval-cmd", default="",
                   help="评估命令，支持 {skills} {split} {root} 占位符，"
                        "stdout 需输出 JSON: {\"score\": 0.42, \"details\": [...]}")
    p.add_argument("--train", default="", help="训练集描述/路径")
    p.add_argument("--val", default="", help="验证集描述/路径")
    p.set_defaults(func=cmd_init)

    p = add("status", "查看循环状态")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_status)

    p = add("evaluate", "运行评估命令")
    p.add_argument("--split", default="val")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_evaluate)

    p = add("baseline", "记录无技能基线验证分")
    p.add_argument("--score", type=float)
    p.set_defaults(func=cmd_baseline)

    p = add("ingest", "写入本轮训练轨迹 (raw 层)")
    p.add_argument("--run", type=int, required=True)
    p.add_argument("--file", nargs="+", required=True)
    p.set_defaults(func=cmd_ingest)

    p = add("log", "追加本轮进化日志 (Wiki Maintainer)")
    p.add_argument("--run", type=int, required=True)
    p.add_argument("--body")
    p.add_argument("--body-file")
    p.set_defaults(func=cmd_log)

    p = sub.add_parser("pattern", help="维护 wiki/patterns")
    psub = p.add_subparsers(dest="pattern_cmd", required=True)

    q = psub.add_parser("new", help="新建模式页")
    q.add_argument("--root", required=True)
    q.add_argument("--slug", required=True)
    q.add_argument("--title", required=True)
    q.add_argument("--kind", required=True, choices=list(KINDS))
    q.add_argument("--run", type=int)
    q.add_argument("--body")
    q.add_argument("--body-file")

    q = psub.add_parser("edit", help="增量补丁编辑模式页")
    q.add_argument("--root", required=True)
    q.add_argument("--slug", required=True)
    q.add_argument("--mode", required=True, choices=["append", "replace", "insert"])
    q.add_argument("--run", type=int)
    q.add_argument("--body")
    q.add_argument("--body-file")
    q.add_argument("--old")
    q.add_argument("--old-file")
    q.add_argument("--new")
    q.add_argument("--new-file")
    q.add_argument("--anchor", help="insert 模式：在该文本之后插入")
    q.add_argument("--link-skill")
    q.add_argument("--note")

    q = psub.add_parser("list", help="列出模式")
    q.add_argument("--root", required=True)
    q.add_argument("--json", action="store_true")

    q = psub.add_parser("show", help="查看模式全文")
    q.add_argument("--root", required=True)
    q.add_argument("--slug", required=True)

    p.set_defaults(func=cmd_pattern)

    p = add("index-rebuild", "重建 wiki/index.md")
    p.set_defaults(func=cmd_index_rebuild)

    p = add("propose", "登记原子提案 (Skill Proposer)")
    p.add_argument("--run", type=int, required=True)
    p.add_argument("--skill", required=True)
    p.add_argument("--action", required=True, choices=list(ACTIONS))
    p.add_argument("--diff-file")
    p.add_argument("--diff")
    p.add_argument("--intent")
    p.add_argument("--sources", default="", help="触发该提案的 pattern slug，逗号分隔")
    p.set_defaults(func=cmd_propose)

    p = add("gate", "验证门控：接受则建快照，拒绝则回滚技能")
    p.add_argument("--run", type=int, required=True)
    p.add_argument("--score", type=float, help="手动传入验证分；省略则调用 eval-cmd")
    p.add_argument("--skill", help="提案未登记时的兜底技能名")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_gate)

    p = add("prune", "清理旧轨迹与旧快照（不涉及 wiki 内容）")
    p.add_argument("--keep", type=int, default=3)
    p.add_argument("--raw", action="store_true")
    p.add_argument("--snapshots", action="store_true")
    p.add_argument("--keep-accepted", action="store_true")
    p.set_defaults(func=cmd_prune)

    p = add("export", "导出最终技能集")
    p.add_argument("--target", required=True)
    p.add_argument("--with-wiki", action="store_true")
    p.set_defaults(func=cmd_export)

    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
