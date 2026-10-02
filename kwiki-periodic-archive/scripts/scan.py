#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阶段1：扫描知识库，找出 N 天前的旧内容，备份正文并生成归档计划。
只读操作，不做任何写/删。

用法:
  python scan.py --kuid 0s_3159273167 --days 7 --outdir D:\\...\\kwiki_archive\\2026-09-17

产出:
  tree.json            全量文件树（递归）
  old_contents.jsonl   旧文件完整正文备份（护栏1）
  digest.txt           每篇标题+摘录，供归纳
  plan.json            待删清单
  report.txt           汇总报告
"""
import argparse
import json
import os
import subprocess
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta

CLI = r"D:\program\node\node_global\kwiki-cli.cmd"
TZ = timezone(timedelta(hours=8))


def env():
    e = dict(os.environ)
    tok = e.get("X_KWIKI_AUTH", "")
    if not tok:
        print("错误: 未设置 X_KWIKI_AUTH，无法鉴权。", file=sys.stderr)
        sys.exit(2)
    return e


ENV = None  # lazy


def run_cli(args, timeout=120):
    r = subprocess.run([CLI] + args, capture_output=True, env=ENV, shell=True, timeout=timeout)
    return r.stdout.decode("utf-8", errors="replace")


def file_list(kuid, page_size=100):
    txt = run_cli(["kwiki", "file-list", "--kuid", kuid, "--page-size", str(page_size), "--format", "json"])
    try:
        return json.loads(txt)
    except Exception:
        return {}


def walk(root_kuid):
    files, folders = [], []
    stack = [(root_kuid, "")]
    while stack:
        kuid, path = stack.pop()
        for f in file_list(kuid).get("list", []):
            node = {
                "title": f.get("title", ""), "kuid": f.get("kuid", ""),
                "path": (path + "/" + f.get("title", "")).strip("/"),
                "ctime": f.get("ctime", 0), "doc_type": f.get("doc_type", ""),
                "size": f.get("size", 0), "file_id": f.get("file_id", ""),
                "parent_kuid": kuid,
            }
            if f.get("doc_type") == "folder":
                folders.append(node)
                stack.append((node["kuid"], node["path"]))
            else:
                files.append(node)
    return files, folders


def fetch_content(kuid):
    txt = run_cli(["kwiki", "file-content", "--kuid", kuid, "--content-format", "markdown", "--format", "json"])
    try:
        d = json.loads(txt)
        data = d.get("data", d)
        return data.get("content", "") or ""
    except Exception:
        return ""


def main():
    global ENV
    ap = argparse.ArgumentParser()
    ap.add_argument("--kuid", required=True, help="知识库 kuid（0s 开头）")
    ap.add_argument("--drive-id", default="", help="drive_id（写入摘要时用，可留空由知识库详情补）")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--exclude-kuid", action="append", default=[],
                    help="排除的文件 kuid（如上次生成的摘要文档），可多次")
    args = ap.parse_args()
    ENV = env()

    os.makedirs(args.outdir, exist_ok=True)
    cutoff = (datetime.now(TZ) - timedelta(days=args.days)).timestamp()
    cutoff_str = datetime.fromtimestamp(cutoff, TZ).strftime("%Y-%m-%d %H:%M")
    print(f"知识库: {args.kuid}  界线: 早于 {cutoff_str}（{args.days} 天）")

    files, folders = walk(args.kuid)
    exclude = set(args.exclude_kuid)
    old = [f for f in files if f["ctime"] < cutoff and f["kuid"] not in exclude]
    old.sort(key=lambda x: x["ctime"])
    print(f"文件总数: {len(files)}  文件夹: {len(folders)}  旧文件: {len(old)}")

    # 备份正文（护栏1）
    backup_path = os.path.join(args.outdir, "old_contents.jsonl")
    if old:
        with ThreadPoolExecutor(max_workers=6) as ex:
            contents = list(ex.map(fetch_content, [f["kuid"] for f in old]))
        empty = []
        with open(backup_path, "w", encoding="utf-8") as fh:
            for f, c in zip(old, contents):
                if not c.strip():
                    empty.append(f["title"])
                fh.write(json.dumps({"kuid": f["kuid"], "title": f["title"], "path": f["path"],
                                     "ctime": f["ctime"], "content": c}, ensure_ascii=False) + "\n")
        total_chars = sum(len(c) for c in contents)
        print(f"备份完成: {backup_path}  共 {len(old)} 条 / {total_chars:,} 字"
              + (f"  ⚠ {len(empty)} 条正文为空: {empty[:5]}" if empty else ""))
    else:
        print("没有旧内容，无需归档。写空报告后退出。")
        with open(os.path.join(args.outdir, "report.txt"), "w", encoding="utf-8") as fh:
            fh.write(f"归档检查 {datetime.now(TZ).strftime('%Y-%m-%d %H:%M')}: 无满 {args.days} 天的旧内容，跳过。\n")
        # 仍写出空 plan 以便幂等
        json.dump({"kuid": args.kuid, "old_count": 0, "folders": [], "files": []},
                  open(os.path.join(args.outdir, "plan.json"), "w", encoding="utf-8"), ensure_ascii=False)
        return

    # digest（每篇 420 字摘录）
    with open(os.path.join(args.outdir, "digest.txt"), "w", encoding="utf-8") as fh:
        for i, (f, c) in enumerate(zip(old, contents), 1):
            body = " ".join(c.split())
            fh.write(f"[{i:02d}|{datetime.fromtimestamp(f['ctime'], TZ).strftime('%m-%d')}] {f['title']}\n  {body[:420]}\n\n")

    # plan：整文件夹删 or 逐个删
    files_by_parent = {}
    for f in files:
        files_by_parent.setdefault(f["parent_kuid"], []).append(f)
    old_by_parent = {}
    for f in old:
        old_by_parent.setdefault(f["parent_kuid"], []).append(f)
    folder_by_kuid = {f["kuid"]: f for f in folders}
    child_folders = Counter(f["parent_kuid"] for f in folders)

    del_folders, del_files = [], []
    for pk, olds in old_by_parent.items():
        if pk == args.kuid or pk in child_folders:   # 根目录 or 含子文件夹 → 只删文件
            del_files.extend(olds)
            continue
        allf = files_by_parent.get(pk, [])
        if len(allf) == len(olds):                    # 文件夹内全是旧文件 → 整删
            fld = folder_by_kuid.get(pk)
            if fld:
                del_folders.append({"title": fld["title"], "kuid": pk, "n": len(olds)})
            else:
                del_files.extend(olds)
        else:                                         # 混合 → 只删旧文件
            del_files.extend(olds)

    plan = {
        "generated_at": datetime.now(TZ).strftime("%Y-%m-%d %H:%M"),
        "kuid": args.kuid, "days": args.days,
        "old_count": len(old),
        "backup": backup_path,
        "folders": del_folders,
        "files": [{"title": f["title"], "kuid": f["kuid"]} for f in del_files],
    }
    json.dump(plan, open(os.path.join(args.outdir, "plan.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    json.dump({"root": args.kuid, "files": files, "folders": folders},
              open(os.path.join(args.outdir, "tree.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    # 汇总
    lines = [f"归档扫描 {datetime.now(TZ).strftime('%Y-%m-%d %H:%M')}  界线 {cutoff_str}",
             f"旧文件 {len(old)} 个（整删文件夹 {len(del_folders)} 个/{sum(x['n'] for x in del_folders)} 文件 + 逐个删 {len(del_files)} 个）",
             "日期分布:"]
    for k, v in sorted(Counter(datetime.fromtimestamp(f["ctime"], TZ).strftime("%Y-%m-%d") for f in old).items()):
        lines.append(f"  {k}: {v}")
    report = "\n".join(lines)
    open(os.path.join(args.outdir, "report.txt"), "w", encoding="utf-8").write(report)
    print("\n" + report)
    print(f"\n下一步: Agent 读 digest.txt 撰写摘要 → pandoc 转 docx → file-upload → 回读校验 → delete.py")


if __name__ == "__main__":
    main()
