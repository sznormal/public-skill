#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阶段3：护栏校验通过后分批删除。
护栏（任一失败即退出，不删任何东西）：
  1) old_contents.jsonl 存在，条数 == 计划删除文件数，且每条正文非空
  2) 新摘要文档可回读且正文长度 >= --min-len
  3) 待删清单不含摘要文档自身

用法:
  python delete.py --plan "<outdir>/plan.json" --require-kuid <摘要文档kuid> [--min-len 1000]
"""
import argparse
import json
import os
import subprocess
import sys
import time

CLI = r"D:\program\node\node_global\kwiki-cli.cmd"


def env():
    e = dict(os.environ)
    if not e.get("X_KWIKI_AUTH"):
        print("错误: 未设置 X_KWIKI_AUTH。", file=sys.stderr)
        sys.exit(2)
    return e


ENV = None


def run_cli(args):
    r = subprocess.run([CLI] + args, capture_output=True, env=ENV, shell=True)
    return r.stdout.decode("utf-8", errors="replace").strip()


def verify_doc(kuid, min_len):
    txt = run_cli(["kwiki", "file-content", "--kuid", kuid, "--content-format", "markdown", "--format", "json"])
    try:
        d = json.loads(txt)
        return len(d.get("content", "")) >= min_len, len(d.get("content", ""))
    except Exception:
        return False, 0


def delete(kuid):
    out = run_cli(["kwiki", "file-delete", "--kuid", kuid, "--format", "json"])
    ok = "error" not in out.lower() and out != ""
    # file-delete 成功时返回 JSON；失败通常含 "api error"
    if "api error" in out.lower():
        ok = False
    return ok, out[:160]


def list_titles(kuid):
    txt = run_cli(["kwiki", "file-list", "--kuid", kuid, "--format", "json"])
    try:
        return [f["title"] for f in json.loads(txt).get("list", [])]
    except Exception:
        return []


def main():
    global ENV
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--require-kuid", required=True, help="新写入的摘要文档 kuid（护栏2）")
    ap.add_argument("--min-len", type=int, default=1000)
    ap.add_argument("--batch", type=int, default=10)
    args = ap.parse_args()
    ENV = env()

    plan = json.load(open(args.plan, encoding="utf-8"))
    if plan.get("old_count", 0) == 0:
        print("计划为空，无需删除。")
        return

    # 护栏1：备份完整性
    backup = plan.get("backup", "")
    n_expected = plan["old_count"]
    if not os.path.exists(backup):
        print("❌ 护栏1失败: 备份文件不存在，拒绝删除。"); sys.exit(1)
    rows = [json.loads(l) for l in open(backup, encoding="utf-8")]
    empty = [r["title"] for r in rows if not r.get("content", "").strip()]
    if len(rows) != n_expected:
        print(f"❌ 护栏1失败: 备份 {len(rows)} 条 != 计划 {n_expected} 条，拒绝删除。"); sys.exit(1)
    if empty:
        print(f"❌ 护栏1失败: {len(empty)} 条备份正文为空: {empty[:5]}，拒绝删除。"); sys.exit(1)
    print(f"✓ 护栏1通过: 备份 {len(rows)} 条完整")

    # 护栏3：清单不含摘要文档
    all_del = [f["kuid"] for f in plan.get("files", [])] + [f["kuid"] for f in plan.get("folders", [])]
    if args.require_kuid in all_del:
        print("❌ 护栏3失败: 待删清单包含摘要文档自身，拒绝删除。"); sys.exit(1)
    print("✓ 护栏3通过: 摘要文档不在待删清单")

    # 护栏2：摘要文档可读
    ok, ln = verify_doc(args.require_kuid, args.min_len)
    if not ok:
        print(f"❌ 护栏2失败: 摘要文档 {args.require_kuid} 回读长度 {ln} < {args.min_len}，拒绝删除。")
        sys.exit(1)
    print(f"✓ 护栏2通过: 摘要文档正文 {ln} 字")

    # 执行分批删除
    targets = ([("文件夹", f["title"], f["kuid"]) for f in plan.get("folders", [])]
               + [("文件", f["title"], f["kuid"]) for f in plan.get("files", [])])
    print(f"\n待删 {len(targets)} 个对象，每批 {args.batch}：")
    okn, fails = 0, []
    for i in range(0, len(targets), args.batch):
        batch = targets[i:i + args.batch]
        for kind, title, kuid in batch:
            s, msg = delete(kuid)
            print(f"  [{'OK' if s else 'FAIL'}] {kind} {title[:44]} ({kuid})" + ("" if s else f" {msg}"))
            (okn := okn + 1) if s else fails.append((title, kuid, msg))
            time.sleep(0.4)
        print("  根目录剩余:", list_titles(plan["kuid"]))
        time.sleep(1)

    print(f"\n==== 删除完成: 成功 {okn}/{len(targets)}，失败 {len(fails)} ====")
    for t, k, m in fails:
        print("  失败:", t, k, m)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
