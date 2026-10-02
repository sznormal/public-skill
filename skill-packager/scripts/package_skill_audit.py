#!/usr/bin/env python3
"""skill-packager · 打包前安全审计 + 压缩脚本（仅 stdlib，自包含）

用途：把某个 WorkBuddy skill 目录打成可分发 zip，并在打包前做一次安全审计：
  1) 扫描硬编码真实密钥（sk-/AKIA/ghp_/xox/JWT/明文字符串赋值等），发现即报错并拒绝打包；
  2) 扫描个人环境路径（当前用户名、BaiduSyncdisk、s2_key.txt、绝对 home 路径等），
     列出待泛化项（warning，不阻断）；
  3) 检查文档完整性（安装说明 / 使用说明 / 版权说明 / 作者说明），缺失则提示补全（warning）；
  4) 排除 __pycache__ / *.pyc 后，打成顶层带目录名的 zip。

用法：
  python package_skill_audit.py <skill_dir> [--out output.zip] [--force]
    <skill_dir>  要打包的 skill 源目录（如 ~/.workbuddy/skills/my-skill）
    --out        输出 zip 路径（默认 <skill_dir>/../<dirname>.zip）
    --force      即使发现真实密钥也强行打包（不推荐，仅审计用）

退出码：0=打包成功且无高危；2=发现真实密钥（除非 --force）；1=其它错误。
"""
from __future__ import annotations
import argparse
import getpass
import os
import re
import sys
import zipfile

# ---------- 扫描目标文本后缀 ----------
TEXT_EXT = {".md", ".py", ".json", ".yaml", ".yml", ".txt", ".toml",
            ".cfg", ".ini", ".sh", ".bat", ".js", ".ts", ".html", ".css", ".csv"}

# ---------- 1. 真实密钥模式（高危，必须删除） ----------
SECRET_PATTERNS = [
    ("OpenAI",       re.compile(r"sk-[A-Za-z0-9]{20,}")),
    ("AWS",          re.compile(r"AKIA[0-9A-Z]{16}")),
    ("GitHub",       re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}")),
    ("Slack",        re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("Google",       re.compile(r"AIza[0-9A-Za-z_-]{20,}")),
    ("GoogleOAuth",  re.compile(r"ya29\.[0-9A-Za-z_-]+")),
    ("JWT",          re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]+")),
    # 明文字符串赋值的 key/token/password（排除仅写 "环境变量" / 占位 "你的key" / "xxxx"）
    ("HardcodedKey", re.compile(r"(?i)(api[_-]?key|secret|token|password|passwd|access[_-]?token)\s*=\s*['\"](?!你的|your|xxxx|xxx|placeholder|env|环境|<|\{)[A-Za-z0-9_\-./+]{12,}['\"]")),
]

# ---------- 2. 个人环境路径模式（待泛化，warning） ----------
def _personal_patterns() -> list[tuple[str, re.Pattern]]:
    user = getpass.getuser()
    pats = [
        ("WinUserPath", re.compile(r"C:\\\\Users\\\\" + re.escape(user) + r"[\\/][^\\/\s:'\"\)]+")),
        ("UnixUserPath", re.compile(r"(/home/|/Users/)" + re.escape(user) + r"(/|$)")),
        ("BaiduSyncdisk", re.compile(r"(?i)([a-z]:\\.*baidusyncdisk|baidusyncdisk[\\/]|[a-z]:\\.*百度网盘)")),
        ("S2KeyFile", re.compile(r"(?i)s2_key\.txt")),
        ("ManagedPyPath", re.compile(r"\.workbuddy\\binaries\\python")),
    ]
    return pats

# 允许出现的"安全"字符串白名单（命中这些不算泄露）
SAFE_HINTS = ["你的key", "your key", "xxxx", "placeholder", "环境变量", "env var",
              "S2_API_KEY", "os.environ", "--api-key", "api_key=None", "api_key = None",
              "getenv", "get(\"S2_API_KEY\")", "environment variable"]


def _read_text(path: str) -> str | None:
    ext = os.path.splitext(path)[1].lower()
    if ext not in TEXT_EXT:
        return None
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return None


# ---------- 3. 文档完整性（安装/使用/版权/作者，warning） ----------
COMPLETENESS = [
    ("安装说明", re.compile(r"(?i)(安装|installation|如何安装|部署|setup)")),
    ("使用说明", re.compile(r"(?i)(使用指南|使用说明|用法|quick\s*start|快速开始|触发方式|如何触发|getting started|how to use)")),
    ("版权说明", re.compile(r"(?i)(版权|copyright|版权所有|all rights reserved|©|license|许可协议|开源协议)")),
    ("作者说明", re.compile(r"(?i)(作者|author|维护者|maintainer|created by|出品|编写者)")),
]


def completeness(skill_dir: str):
    """检查 README.md 与 SKILL.md 是否含安装/使用/版权/作者说明，返回缺失项列表。"""
    rt = _read_text(os.path.join(skill_dir, "README.md")) or ""
    st = _read_text(os.path.join(skill_dir, "SKILL.md")) or ""
    pool = rt + "\n" + st
    return [label for label, pat in COMPLETENESS if not pat.search(pool)]


def audit(skill_dir: str):
    """返回 (secrets, personal) 两个列表，元素为 (file, line_no, kind, snippet)。"""
    secrets, personal = [], []
    for root, dirs, files in os.walk(skill_dir):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for fn in files:
            if fn.endswith(".pyc"):
                continue
            full = os.path.join(root, fn)
            text = _read_text(full)
            if text is None:
                continue
            rel = os.path.relpath(full, skill_dir)
            lines = text.splitlines()
            for i, line in enumerate(lines, 1):
                low = line.lower()
                # 命中白名单则跳过（如 "os.environ.get('S2_API_KEY')"）
                if any(h.lower() in low for h in SAFE_HINTS):
                    continue
                for kind, pat in SECRET_PATTERNS:
                    m = pat.search(line)
                    if m:
                        secrets.append((rel, i, kind, line.strip()[:160]))
                        break
                for kind, pat in _personal_patterns():
                    if pat.search(line):
                        personal.append((rel, i, kind, line.strip()[:160]))
                        break
    return secrets, personal


def build_zip(skill_dir: str, out_zip: str):
    top = os.path.basename(os.path.normpath(skill_dir))
    n = 0
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(skill_dir):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for fn in files:
                if fn.endswith(".pyc"):
                    continue
                full = os.path.join(root, fn)
                rel = os.path.relpath(full, skill_dir)
                z.write(full, os.path.join(top, rel))
                n += 1
    return n


def main():
    ap = argparse.ArgumentParser(description="skill 打包前安全审计 + 压缩")
    ap.add_argument("skill_dir", help="skill 源目录")
    ap.add_argument("--out", help="输出 zip 路径")
    ap.add_argument("--force", action="store_true", help="即使发现真实密钥也打包")
    args = ap.parse_args()

    skill_dir = os.path.abspath(args.skill_dir)
    if not os.path.isdir(skill_dir):
        print(f"[错误] 目录不存在: {skill_dir}", file=sys.stderr)
        sys.exit(1)

    out_zip = args.out or os.path.join(
        os.path.dirname(skill_dir), os.path.basename(os.path.normpath(skill_dir)) + ".zip")

    print(f"== 审计 {skill_dir} ==")
    secrets, personal = audit(skill_dir)

    if secrets:
        print(f"\n[高危] 发现 {len(secrets)} 处疑似硬编码密钥 —— 必须删除后再打包：")
        for rel, ln, kind, snip in secrets:
            print(f"  - [{kind}] {rel}:{ln}  {snip}")
        if not args.force:
            print("\n打包已中止。请删除上述真实密钥，改为「用户自行提供」（见 references/audit-patterns.md）。")
            sys.exit(2)
        print("  （--force 已启用，仍打包，仅供审计。）")

    if personal:
        print(f"\n[待泛化] 发现 {len(personal)} 处个人环境路径 —— 建议改为通用描述：")
        for rel, ln, kind, snip in personal:
            print(f"  - [{kind}] {rel}:{ln}  {snip}")
        print("  建议：移除绝对路径/用户名，改为「用户自行提供 / 用环境变量」等通用表述。")
    else:
        print("\n[OK] 未发现个人环境路径泄露。")

    if not secrets:
        print("\n[OK] 未发现硬编码真实密钥。")

    missing = completeness(skill_dir)
    if missing:
        print(f"\n[待补充] 缺少说明文档：{', '.join(missing)}")
        print("  建议按 references/audit-patterns.md 第五节模板补全到 README（版权/作者建议常驻）。")
    else:
        print("\n[OK] 安装/使用/版权/作者说明齐全。")

    n = build_zip(skill_dir, out_zip)
    print(f"\n== 打包完成 ==")
    print(f"输出: {out_zip}")
    print(f"条目数: {n}")
    print(f"大小: {os.path.getsize(out_zip)} 字节")


if __name__ == "__main__":
    main()
