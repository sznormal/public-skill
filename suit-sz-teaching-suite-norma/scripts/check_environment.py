#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""依赖型环境自检（只读）。

只读取状态：不安装、不登录、不授权、不改配置、不启子进程、不访问网络。

用法：
    python check_environment.py                      # 人读格式
    python check_environment.py --json               # 机器可读
    python check_environment.py --capability docx-render --capability docx-parse

输出状态：
    ready        核心与当前请求所需依赖齐备 —— 跳过配置引导，直接执行
    partial      核心可用、部分可选功能不可用 —— 继续执行并标注受影响功能
    needs_setup  当前请求所需必需依赖缺失 —— 只展示缺失项的配置步骤
    unavailable  依赖存在但版本不兼容 —— 给出恢复与降级方案

退出码：ready / partial 为 0；needs_setup / unavailable 为 1（表示需降级，不代表停工）。
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

# 本技能自身要用的模板（相对本脚本所在目录的上一级）
REQUIRED_TEMPLATES = [
    "templates/课程标准.docx",
    "templates/教案模板.docx",
    "templates/课程计划-空白模板.docx",
]

# 模块名 -> 展示名 / 最低版本
MODULES = {
    "docx": ("python-docx", "0.8.11"),
    "openpyxl": ("openpyxl", "3.0.0"),
    "olefile": ("olefile", "0.46"),
}

VERSION_RE = re.compile(r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?")


def parse_version(text: str):
    match = VERSION_RE.match(str(text).strip())
    if not match:
        return None
    return tuple(int(part or 0) for part in match.groups())


def lower_than(current, minimum) -> bool:
    if current is None or minimum is None:
        return False
    return current < minimum


# --------------------------------------------------------------- 解释器发现

def _site_packages(root: Path):
    """列出一个解释器/虚拟环境可能在的 site-packages 目录。"""
    found = []
    for pattern in ("Lib/site-packages", "lib/site-packages", "lib/python*/site-packages"):
        found.extend(sorted(root.glob(pattern)))
    return [p for p in found if p.is_dir()]


def normalize_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", str(name)).strip().lower()


def module_version_in(root: Path, module: str):
    """在 site-packages 中查模块元数据，返回版本号、'unknown' 或 None。

    dist-info 目录名会把 python-docx 规范化为 python_docx，因此按 METADATA 的
    Name 字段比对，而不是按目录名猜。
    """
    project, _ = MODULES[module]
    for site in _site_packages(root):
        if not (site / module).is_dir():
            continue
        for dist in sorted(site.glob("*.dist-info")):
            metadata = dist / "METADATA"
            if not metadata.is_file():
                continue
            try:
                text = metadata.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            declared = version = None
            for line in text.splitlines():
                if not line.strip():
                    break
                if line.startswith("Name:") and declared is None:
                    declared = line.split(":", 1)[1].strip()
                elif line.startswith("Version:") and version is None:
                    version = line.split(":", 1)[1].strip()
                if declared and version:
                    break
            if declared and normalize_name(declared) == normalize_name(project):
                return version
        return "unknown"
    return None


def candidate_interpreters():
    """按优先级列出候选解释器 (标签, 可执行文件, 包根目录)。"""
    candidates = []

    current = Path(sys.executable)
    if current.is_file():
        candidates.append(("当前解释器", current, current.parent.parent))

    envs = Path.home() / ".workbuddy" / "binaries" / "python" / "envs"
    default_env = envs / "default"
    for exe in (default_env / "Scripts" / "python.exe", default_env / "bin" / "python"):
        if exe.is_file():
            candidates.append(("受管默认虚拟环境", exe, default_env))

    if envs.is_dir():
        for env in sorted(p for p in envs.iterdir() if p.is_dir() and p != default_env):
            for exe in (env / "Scripts" / "python.exe", env / "bin" / "python"):
                if exe.is_file():
                    candidates.append((f"受管虚拟环境 {env.name}", exe, env))

    versions = Path.home() / ".workbuddy" / "binaries" / "python" / "versions"
    if versions.is_dir():
        for ver in sorted(p for p in versions.iterdir() if p.is_dir()):
            for exe in (ver / "python.exe", ver / "bin" / "python"):
                if exe.is_file():
                    candidates.append((f"受管运行时 {ver.name}", exe, ver))

    return candidates


def probe_module(module: str):
    """在当前解释器内探测模块；返回 (found, version, source)。"""
    try:
        if importlib.util.find_spec(module) is not None:
            version = "unknown"
            try:
                from importlib import metadata

                version = metadata.version(MODULES.get(module, (module,))[0])
            except Exception:
                pass
            return True, version, "当前解释器"
    except (ImportError, ValueError):
        pass

    for label, exe, root in candidate_interpreters():
        version = module_version_in(root, module)
        if version:
            return True, version, f"{label}（{exe}）"

    return False, None, None


def best_interpreter():
    """挑一个能 import python-docx 的解释器，供后续所有脚本使用。"""
    for label, exe, root in candidate_interpreters():
        if module_version_in(root, "docx"):
            return label, str(exe)
    if importlib.util.find_spec("docx") is not None:
        return "当前解释器", sys.executable
    return None, None


# --------------------------------------------------------------- 检查项

def check_runtime():
    current = sys.version_info[:3]
    minimum = (3, 10, 0)
    ok = current >= minimum
    return {
        "id": "python-runtime",
        "type": "runtime",
        "required": True,
        "status": "ready" if ok else "unavailable",
        "reason_code": "ok" if ok else "version_incompatible",
        "detail": f"Python {current[0]}.{current[1]}.{current[2]}；最低要求 3.10.0",
    }


def check_module(module: str, required: bool):
    name, min_version = MODULES[module]
    found, version, source = probe_module(module)
    if not found:
        return {
            "id": name,
            "type": "local-tool",
            "required": required,
            "status": "missing",
            "reason_code": "package_missing",
            "detail": f"{name} 未安装（已检查当前解释器与受管 Python 目录）",
        }
    current = parse_version(version)
    if lower_than(current, parse_version(min_version)):
        return {
            "id": name,
            "type": "local-tool",
            "required": required,
            "status": "unavailable",
            "reason_code": "version_incompatible",
            "detail": f"{name} {version} 低于最低要求 {min_version}（来源：{source}）",
        }
    return {
        "id": name,
        "type": "local-tool",
        "required": required,
        "status": "ready",
        "reason_code": "ok",
        "detail": f"{name} {version}（来源：{source}）",
    }


def check_templates(skill_dir: Path):
    missing = [item for item in REQUIRED_TEMPLATES if not (skill_dir / item).is_file()]
    return {
        "id": "template-pack",
        "type": "file",
        "required": True,
        "status": "ready" if not missing else "missing",
        "reason_code": "ok" if not missing else "file_missing",
        "detail": "内置空白模板齐全" if not missing else f"缺少模板：{'、'.join(missing)}",
    }


# --------------------------------------------------------------- 汇总

NEXT_ACTION = {
    "ready": "跳过配置引导，直接执行主流程",
    "partial": "继续执行可用功能，只说明受影响功能与降级方式",
    "needs_setup": "只展示缺失必需项的配置步骤，配置完成后重新检查",
    "unavailable": "展示故障原因、恢复步骤与安全降级方案",
}


def summarize(checks):
    required = [c for c in checks if c["required"]]
    optional = [c for c in checks if not c["required"]]
    if any(c["status"] == "missing" for c in required):
        return "needs_setup"
    if any(c["status"] == "unavailable" for c in required):
        return "unavailable"
    if any(c["status"] != "ready" for c in optional):
        return "partial"
    return "ready"


def build_report(skill_dir: Path):
    runtime = check_runtime()
    docx_check = check_module("docx", required=True)
    openpyxl_check = check_module("openpyxl", required=False)
    olefile_check = check_module("olefile", required=False)
    templates = check_templates(skill_dir)

    checks = [runtime, docx_check, templates, openpyxl_check, olefile_check]
    status = summarize(checks)

    label, interpreter = best_interpreter()
    visible = checks if status == "ready" else [c for c in checks if c["status"] != "ready"]

    return {
        "status": status,
        "skill_dir": str(skill_dir),
        "checks": visible,
        "recommended_interpreter": interpreter,
        "recommended_interpreter_source": label,
        "runtime_level": "L1" if docx_check["status"] == "ready" else "L2",
        "next_action": NEXT_ACTION[status],
    }


def render_text(report):
    marks = {"ready": "[OK  ]", "missing": "[MISS]", "unavailable": "[FAIL]", "partial": "[PART]"}
    lines = ["=" * 62, " 教学文件写作套件 · 环境自检（只读）", "=" * 62]
    for item in report["checks"]:
        lines.append(f"  {marks.get(item['status'], '[????]')} {item['id']:<18} {item['detail']}")
    lines.append("-" * 62)
    lines.append(f"  总体状态：{report['status']}")
    if report["recommended_interpreter"]:
        lines.append(f"  推荐解释器：{report['recommended_interpreter']}")
        lines.append(f"  来源：{report['recommended_interpreter_source']}")
        lines.append(f"  运行级别：{report['runtime_level']}")
    else:
        lines.append("  推荐解释器：未找到可 import python-docx 的解释器")
        lines.append("  运行级别：L2（Markdown 降级）")
    lines.append(f"  下一步：{report['next_action']}")
    lines.append("=" * 62)
    lines.append("  提示：本检查不安装任何依赖。需要安装时按 references/setup-guide.md 的步骤操作。")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="检查本技能的依赖与运行环境（只读）")
    parser.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    parser.add_argument("--skill-dir", type=Path,
                        default=Path(__file__).resolve().parent.parent,
                        help="技能根目录，默认取本脚本的上一级")
    args = parser.parse_args()

    report = build_report(args.skill_dir)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_text(report))
    return 0 if report["status"] in {"ready", "partial"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
