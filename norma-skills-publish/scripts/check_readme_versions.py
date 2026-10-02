#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""norma-skills 仓库 README 登记一致性核对。

用途：monorepo 红线要求 README「Skill 清单」与各 skill 的 SKILL.md frontmatter
版本同步登记。远端提交常漏改 README（2026-10-02 实测），本脚本一键查出全部漂移。

用法：
    python check_readme_versions.py [仓库根目录]
不传参时默认取本脚本的上两级目录（即 <repo>/norma-skills-publish/scripts/ -> <repo>）。
"""
import io
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ROOT = os.path.dirname(os.path.dirname(HERE))
root = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_ROOT

readme_path = os.path.join(root, "README.md")
if not os.path.exists(readme_path):
    sys.exit("找不到 README.md：%s" % readme_path)

readme = io.open(readme_path, encoding="utf-8").read()

declared = {}
for m in re.finditer(r"^\|\s*`([^`]+)`\s*\|\s*([^|]+?)\s*\|", readme, re.M):
    declared[m.group(1)] = m.group(2).strip()

print("仓库根目录:", root)
print("README 登记 skill 数:", len(declared))


def frontmatter_version(path):
    txt = io.open(path, encoding="utf-8", errors="replace").read(4000)
    m = re.search(r"^version:\s*(.+?)\s*$", txt, re.M)
    return m.group(1).strip().strip('"') if m else None


bad, nodir, nover = [], [], []
for name, ver in sorted(declared.items()):
    d = os.path.join(root, name)
    sk = os.path.join(d, "SKILL.md")
    if not os.path.isdir(d):
        nodir.append(name)
        continue
    if not os.path.exists(sk):
        nodir.append(name + " (无 SKILL.md)")
        continue
    actual = frontmatter_version(sk)
    if actual is None:
        nover.append(name)
    elif ver not in ("—", "-", "") and actual != ver:
        bad.append((name, ver, actual))

print("\n=== A. 版本号不一致（README vs SKILL.md）===")
if not bad:
    print("  无")
for n, d, a in bad:
    print("  %-32s README=%-8s 实际=%s" % (n, d, a))

print("\n=== B. README 登记但目录缺失 ===", nodir or "无")
print("\n=== C. frontmatter 无 version 字段（README 版本无从校验）===")
print("  " + (", ".join(nover) if nover else "无"))

try:
    tracked = subprocess.run(["git", "ls-files"], cwd=root,
                             capture_output=True, text=True).stdout.splitlines()
    tops = sorted({p.replace("\\", "/").split("/")[0] for p in tracked})
    missing = [t for t in tops if t not in declared and os.path.isdir(os.path.join(root, t))]
    print("\n=== D. 仓库有目录但 README 未登记 ===", missing or "无")
except Exception as e:  # noqa: BLE001
    print("\n=== D. 跳过（git 不可用）===", e)

dirs = sorted(d for d in os.listdir(root)
              if os.path.isdir(os.path.join(root, d))
              and not d.startswith(".") and d != "_backup")
un = [d for d in dirs if d not in declared]
print("\n=== E. 磁盘有目录但 README 未登记（含第三方未入仓的）===", un or "无")

sys.exit(1 if (bad or nodir) else 0)
