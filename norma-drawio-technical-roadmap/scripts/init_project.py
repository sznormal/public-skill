#!/usr/bin/env python3
"""创建技术路线图项目目录与状态文件 manifest.json。

用法：
    python init_project.py --name <图名> [--root <父目录>]

父目录默认取当前工作目录下的 drawio-projects。同名目录已存在时不覆盖，
避免覆盖既有成果。

退出码：
    0  创建成功
    1  目录已存在，未做任何修改
    2  参数错误
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

UNSAFE_CHARS = set('/\\:*?"<>|')


def build_manifest(name: str) -> dict:
    return {
        "skill": "norma-drawio-technical-roadmap",
        "diagram_name": name,
        "created": datetime.now().astimezone().isoformat(timespec="seconds"),
        "inputs": {"reference_image": "", "sources": []},
        "stage_status": {
            "s1": "done",
            "s2": "pending",
            "s3": "pending",
            "s4": "pending",
            "s5": "pending",
            "s6": "pending",
        },
        "artifacts": {
            "spec": "01-版式规格.md",
            "content": "02-内容结构.md",
            "layout": "03-坐标布局.md",
            "drawio": "",
        },
        "validation": {"ran": False, "errors": 0, "warnings": 0},
        "notes": "",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="初始化 draw.io 技术路线图项目")
    parser.add_argument("--name", required=True, help="图名，用作项目目录名")
    parser.add_argument("--root", default=None, help="父目录，默认为当前目录下的 drawio-projects")
    args = parser.parse_args()

    name = args.name.strip()
    if not name or any(char in UNSAFE_CHARS for char in name):
        print(
            json.dumps(
                {"error": '图名不能为空，且不能包含 / \\ : * ? " < > | 这些字符'},
                ensure_ascii=False,
            )
        )
        return 2

    root = Path(args.root).expanduser() if args.root else Path.cwd() / "drawio-projects"
    project = root / name

    if project.exists():
        print(
            json.dumps(
                {
                    "error": f"目录已存在，未做任何修改：{project}",
                    "hint": "要继续该项目，在新对话里说 Continue <项目路径>",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    project.mkdir(parents=True)
    manifest_path = project / "manifest.json"
    manifest_path.write_text(
        json.dumps(build_manifest(name), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "ok": True,
                "project": str(project),
                "manifest": str(manifest_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
