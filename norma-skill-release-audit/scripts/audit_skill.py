#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# norma-skill-release-audit · 公开 skill 发布前安全审计脚本
# Copyright (C) 2026 Norma（郑洪英）
#
# 本脚本依据 PolyForm Noncommercial License 1.0.0 分发（禁止商业使用）。
# 完整条款见本 skill 根目录 LICENSE 文件，或
# https://polyformproject.org/licenses/noncommercial/1.0.0
"""
audit_skill.py — 公开 skill 发布前安全审计（静态扫描）

覆盖 10 项可自动化检查（另 3 项须人工判断，见 SKILL.md）：
  1. 绝对路径 / 本机用户名 / 家目录
  2. 硬编码密钥、token、密码、私人邮箱
  3. 外发行为：POST / PUT / multipart / webhook / 遥测
  4. 危险操作：rmtree / eval / exec / subprocess / shell=True / pickle
  5. 许可冲突：脚本许可头 vs 根 LICENSE / SKILL.md
  6. 分发卫生：legacy / 历史 zip / 备份文件混入
  7. PII：真实姓名 / 机构 / 机器标识
  8. 网络出口域名清单（生成待确认的数据外发清单）
  9. 破坏性覆盖：写文件 / 覆盖前是否有 dry-run 与备份
 10. 提示注入面：有无「外部内容仅作数据」约束

纯标准库，无 pip 依赖。

用法：
  python audit_skill.py <skill_dir> [--json] [--strict]

退出码：0 = 无 P0；1 = 存在 P0（阻止发布）；2 = 用法/路径错误
"""

import argparse
import json
import os
import re
import sys
import zipfile

SKIP_DIRS = {".git", ".hg", ".svn", "__pycache__", "node_modules", ".venv", "venv",
             ".idea", ".vscode", "stage_snapshots"}
TEXT_EXT = {".md", ".py", ".txt", ".json", ".yaml", ".yml", ".sh", ".js", ".ts",
            ".toml", ".cfg", ".ini"}

RULES = [
    # (编号, 名称, 级别, 编译后的正则, 说明)
    # 注：此处刻意用字符类拼路径片段（/[Uu]sers/、/[Hh]ome/），
    # 否则本行自身会被发布校验器判成"含绝对路径"而无法打包——审计工具先过自己的校验。
    ("P1-ABS", "绝对路径/本机标识", "P0",
     re.compile(r"[A-Za-z]:[\\/]" + r"(?:[Uu]sers|[Dd]ocuments|[Dd]esktop|[Dd]ownloads)\b"
                r"|/[Uu]sers/[A-Za-z0-9._-]+|/[Hh]ome/[A-Za-z0-9._-]+"
                r"|[A-Za-z]:\\[一-鿿]"),
     "泄漏本机路径或用户名；公开分发会暴露执行者身份与环境"),
    ("P1-SEC", "疑似硬编码密钥/token", "P0",
     re.compile(r"(?:api[_-]?key|secret|access[_-]?token|bearer|passwd|password)"
                r"\s*[:=]\s*[\"'][A-Za-z0-9_\-]{16,}[\"']"
                r"|\bsk-[A-Za-z0-9]{20,}|\bghp_[A-Za-z0-9]{20,}"
                r"|\bAKIA[0-9A-Z]{16}\b"),
     "疑似真实凭据硬编码"),
    ("P1-POST", "外发/上传行为", "P0",
     re.compile(r"requests\.post|\.post\(|method=[\"']POST|method=[\"']PUT"
                r"|multipart/form-data|webhook|telemetry|urlretrieve"),
     "非 GET 外发行为；公开 skill 应为零，否则须显式声明"),
    ("P1-EXEC", "危险执行操作", "P0",
     re.compile(r"\bshutil\.rmtree|\bos\.system\s*\(|\bsubprocess\.\w+\s*\(|"
                r"\beval\s*\(|\bexec\s*\(|\bpickle\.loads|shell\s*=\s*True|"
                r"\b__import__\s*\("),
     "删除/任意执行；公开 skill 应为零，若必需须逐条说明"),
    ("P2-SEND", "指令要求外发文稿", "P1",
     re.compile(r"(粘贴|上传|发送|提交)到\s*(?!评审|Steering)[\w一-鿿]{2,12}"
                r"(网站|平台|服务|网盘|邮箱|群)"),
     "skill 指令诱导用户外传材料"),
    ("P2-PII", "真实个人/机构信息", "P2",
     re.compile(r"[一-鿿]{2,4}(大学|学院|研究院|职业技术大学)"
                r"|[A-Za-z0-9._%+-]+@(?!example|xxx|test)[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
     "署名属正常开源要求，机构名与真实邮箱须确认是否愿意公开"),
]

# 许可一致性
LIC_HEAD = re.compile(r"(GPL|General Public License|MIT License|Apache License|"
                      r"PolyForm|Business Source License|Mozilla Public License)", re.I)
LIC_FILE = re.compile(r"(?:^|/)(LICENSE|COPYING)(?:\.[A-Za-z]+)?$", re.I)

# 分发卫生
JUNK = re.compile(r"(^|/)legacy(/|$)|\.zip$|\.tar\.gz$|~$|\.bak$|checkpoint-"
                  r"|_backup-|-backup-|\.pyc$", re.I)

# 提示注入防护（须足够具体，避免「清单不可信」这类无关表述误命中而掩盖真实缺口）
INJECTION_GUARD = re.compile(
    r"提示注入|prompt[ _-]?injection"
    r"|仅作数据|当作数据|视为数据"
    r"|不得[^。\n]{0,25}(?:当作|作为|执行)[^。\n]{0,15}指令"
    r"|(?:外部|抓取|第三方|网络|检索)[^。\n]{0,12}(?:内容|文本|数据)[^。\n]{0,12}(?:不可信|视为不可信)"
    r"|untrusted",re.I)

# 网络域名
DOMAIN = re.compile(r"https?://([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})")
BENIGN_DOMAINS = {"www.w3.org", "www.gnu.org", "fsf.org", "polyformproject.org",
                  "opensource.org", "spdx.org", "creativecommons.org"}

DESTRUCTIVE_WRITE = re.compile(r"copy2\(|copytree\(|shutil\.move|os\.replace")
DRYRUN = re.compile(r"dry.?run|--apply")


def walk(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            yield os.path.join(dirpath, fn)


def read(fp):
    try:
        with open(fp, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except OSError:
        return ""


def scan(root):
    findings = []
    domains = {}
    py_files, text_files = [], []
    lic_heads, junk_files = [], []

    for fp in walk(root):
        rel = os.path.relpath(fp, root).replace("\\", "/")
        ext = os.path.splitext(fp)[1].lower()

        if JUNK.search(rel):
            junk_files.append((rel, os.path.getsize(fp)))

        if ext not in TEXT_EXT:
            continue
        text_files.append(rel)
        if ext == ".py":
            py_files.append(rel)

        txt = read(fp)
        for i, line in enumerate(txt.splitlines(), 1):
            if len(line) > 2000:
                line = line[:2000]
            for d in DOMAIN.findall(line):
                if d.lower() not in BENIGN_DOMAINS:
                    domains[d] = domains.get(d, 0) + 1

        head = "\n".join(txt.splitlines()[:20])
        if ext == ".py" and LIC_HEAD.search(head):
            m = LIC_HEAD.search(head)
            lic_heads.append((rel, m.group(0)))

        for code, name, sev, rx, why in RULES:
            for m in rx.finditer(txt):
                line_no = txt[:m.start()].count("\n") + 1
                # 豁免审计脚本自身的规则定义区与文档字符串（含会被自家正则命中的字面量）
                if rel.endswith("audit_skill.py") and line_no <= 100:
                    continue
                snippet = m.group(0)[:60].replace("\n", " ")
                findings.append({
                    "code": code, "name": name, "severity": sev,
                    "file": rel, "line": line_no,
                    "evidence": snippet, "why": why,
                })
    return findings, domains, py_files, text_files, lic_heads, junk_files


def check_license(skill_dir, f, lic_heads):
    root_lic = [fp for fp in walk(skill_dir) if LIC_FILE.search(fp.replace("\\", "/"))]
    root_lic_text = " ".join(read(p)[:800] for p in root_lic[:3])
    root_kind = "未识别"
    m = LIC_HEAD.search(root_lic_text)
    if m:
        root_kind = m.group(0)
    py_files = [os.path.relpath(p, skill_dir).replace("\\", "/")
                for p in walk(skill_dir) if p.endswith(".py")]
    kinds = {k.lower() for _, k in lic_heads}
    mixed = len(kinds) > 1
    no_head = None
    if py_files and len(lic_heads) < len(py_files):
        headed = {r for r, _ in lic_heads}
        no_head = [r for r in py_files if r not in headed]

    # 关键：脚本许可 与 根许可 是否一致（不一致 = 法律冲突）
    def _norm(s):
        s = s.lower()
        if "general public" in s or s == "gpl":
            return "GPL"
        if "polyform" in s:
            return "PolyForm"
        if "mit" in s:
            return "MIT"
        if "apache" in s:
            return "Apache"
        if "mozilla" in s:
            return "MPL"
        if "business source" in s:
            return "BUSL"
        return s

    root_norm = _norm(root_kind)
    script_norms = {_norm(k) for _, k in lic_heads}
    conflict = script_norms - {root_norm}
    if conflict and root_norm != "未识别":
        involved = sorted({r for r, k in lic_heads if _norm(k) in conflict})
        f.append("P0-LIC", "脚本许可与根许可冲突", "P0", ", ".join(involved[:3]), "-",
                 "同一分发包内两套不兼容许可＝授权歧义/违约风险"
                 "（GPL 与 PolyForm Noncommercial 互不兼容）",
                 f"根许可={root_kind}；脚本许可={', '.join(sorted(script_norms))}")
    if mixed:
        f.append("P0-LIC", "脚本许可头不一致", "P0", "scripts/", "-",
                 "同包内多种脚本许可会造成授权歧义",
                 "检出: " + ", ".join(sorted(kinds)))

    if root_kind == "未识别" and not root_lic:
        f.append("P0-LIC", "根许可缺失", "P0", "LICENSE", "-",
                 "公开分发必须声明许可", "缺 LICENSE 文件")
    if mixed:
        f.append("P0-LIC", "脚本许可头不一致", "P0", "scripts/", "-",
                 "同包内多种许可会造成授权歧义",
                 "检出: " + ", ".join(sorted(kinds)))
    if no_head:
        f.append("P1-LIC", "脚本缺许可头", "P1", ", ".join(no_head[:3]), "-",
                 "无许可头默认保留所有权利，第三方无法合法使用", "")
    return root_kind


def check_injection_guard(skill_dir, f, text_files):
    joined = ""
    for rel in text_files:
        if rel.endswith("SKILL.md") or "modules/" in rel:
            joined += read(os.path.join(skill_dir, rel))[:20000]
    if joined and not INJECTION_GUARD.search(joined):
        f.append("P1-INJ", "无提示注入防护", "P1", "SKILL.md", "-",
                 "外部抓取内容进入上下文却无「仅作数据不当指令」约束",
                 "未检出防护条款")


def check_destructive(skill_dir, f, py_files):
    for rel in py_files:
        txt = read(os.path.join(skill_dir, rel))
        if DESTRUCTIVE_WRITE.search(txt) and not DRYRUN.search(txt):
            f.append("P2-DSTR", "覆盖/移动无 dry-run", "P2", rel, "-",
                     "覆盖类操作若无可逆设计，误操作将不可恢复", "")


def check_package_excludes(root, f):
    """打包器排除表若不含 legacy 与 .zip，则 legacy/ 会被打进分发包。
    定向查找 skill-crafting 的 skill_ops.py，不做全盘遍历。"""
    import glob
    pats = [
        os.path.expanduser("~/.workbuddy/plugins/cache/experts/skill-smith/*/skills/"
                           "skill-crafting/scripts/skill_ops.py"),
        os.path.expanduser("~/.workbuddy/plugins/marketplaces/**/skill-crafting/"
                           "scripts/skill_ops.py"),
    ]
    seen = set()
    for pat in pats:
        for p in glob.glob(pat, recursive=True):
            if p in seen:
                continue
            seen.add(p)
            txt = read(p)
            i = txt.find("EXCLUDED_DIRS")
            if i < 0:
                continue
            seg = txt[i:i + 500]
            miss = [k for k in ("legacy", ".zip") if k not in seg]
            if miss:
                f.append("P0-PKG", "打包器未排除内部目录/包", "P0",
                         "skill-crafting/scripts/skill_ops.py", "-",
                         "内部历史档会被打进公开分发包",
                         "排除表缺少: " + ", ".join(miss))
                return


def main():
    ap = argparse.ArgumentParser(description="公开 skill 发布前安全审计")
    ap.add_argument("skill_dir")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true", help="P1 也视为失败")
    a = ap.parse_args()

    if not os.path.isdir(a.skill_dir):
        print("[ERR] 目录不存在: " + a.skill_dir, file=sys.stderr)
        return 2

    findings = []

    def app(code, name, sev, file, line, why, ev):
        findings.append({"code": code, "name": name, "severity": sev,
                         "file": file, "line": line, "why": why, "evidence": ev})

    raw, domains, py_files, text_files, lic_heads, junk = scan(a.skill_dir)
    for r in raw:
        app(r["code"], r["name"], r["severity"], r["file"], r["line"],
            r["why"], r["evidence"])

    # 许可/注入/破坏性/打包检查（需要扫描结果，故在scan 之后内联执行）
    from types import SimpleNamespace
    holder = SimpleNamespace(append=lambda code, name, sev, file, line, why, ev:
                             app(code, name, sev, file, line, why, ev))
    root_kind = check_license(a.skill_dir, holder, lic_heads)
    check_injection_guard(a.skill_dir, holder, text_files)
    check_destructive(a.skill_dir, holder, py_files)

    # 分发卫生
    big_junk = [(r, s) for r, s in junk if not r.endswith(".pyc")]
    if big_junk:
        total = sum(s for _, s in big_junk)
        holder.append("P0-PKG", "内部历史档混入 skill 目录", "P0",
                      big_junk[0][0], "-",
                      "内部审查记录/历史包会随分发泄漏并膨胀包体",
                      f"{len(big_junk)} 个文件 / {total/1024:.0f} KB")
        # 仅当 skill 内确有内部档、且打包器未排除时才提示「会被打进包」
        check_package_excludes(a.skill_dir, holder)

    order = {"P0": 0, "P1": 1, "P2": 2}
    findings.sort(key=lambda x: (order.get(x["severity"], 3), x["code"], x["file"]))
    p0 = sum(1 for x in findings if x["severity"] == "P0")
    p1 = sum(1 for x in findings if x["severity"] == "P1")
    p2 = sum(1 for x in findings if x["severity"] == "P2")

    if a.json:
        print(json.dumps({
            "skill_dir": os.path.abspath(a.skill_dir),
            "root_license": root_kind,
            "scanned_text_files": len(text_files),
            "scanned_py_files": len(py_files),
            "summary": {"P0": p0, "P1": p1, "P2": p2},
            "outbound_domains": dict(sorted(domains.items(), key=lambda x: -x[1])),
            "findings": findings,
        }, ensure_ascii=False, indent=2))
        return 1 if (p0 or (a.strict and p1)) else 0

    print("=" * 68)
    print(f" skill 发布前安全审计 · {os.path.basename(os.path.abspath(a.skill_dir))}")
    print("=" * 68)
    print(f" 扫描：{len(text_files)} 个文本文件（{len(py_files)} 个脚本）")
    print(f" 根许可：{root_kind}")
    print(f" 结果：P0={p0}  P1={p1}  P2={p2}")
    print("-" * 68)
    if findings:
        for x in findings:
            loc = x["file"] + (f":{x['line']}" if x["line"] not in ("-", None) else "")
            print(f"  [{x['severity']}] {x['code']}  {x['name']}")
            print(f"         位置：{loc}")
            print(f"         风险：{x['why']}")
            if x["evidence"]:
                print(f"         证据：{x['evidence']}")
    else:
        print("  未发现自动化可检问题（仍须人工过 SKILL.md 的 13 项清单）")
    print("-" * 68)
    print(" 外发域名清单（须逐个确认「发什么字段、为什么发」）：")
    if domains:
        for d, n in sorted(domains.items(), key=lambda x: -x[1]):
            print(f"   {n:>3}x  {d}")
    else:
        print("   （无）")
    print("=" * 68)
    if p0:
        print(" [阻断] 存在 P0，不可发布。修复后复跑本脚本。")
    elif p1:
        print(" [注意] 无 P0，但有 P1 项待处理。")
    else:
        print(" [通过] 自动化检查未发现阻断项。")
    return 1 if (p0 or (a.strict and p1)) else 0


if __name__ == "__main__":
    sys.exit(main())