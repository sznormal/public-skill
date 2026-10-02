---
name: skill-packager
display_name: "技能打包器"
display_name_en: "Skill Packager"
description_zh: >
  把一个 WorkBuddy skill 目录打成可分发 zip，并在打包前执行安全审计：拦截硬编码的真实 API key / token，
  提示泛化个人环境路径（用户名、云盘目录、managed Python 路径），补检 Office 模板元数据中的机器标识，
  并校验 SKILL.md 的展示名与描述字段是否齐全。
description_en: >
  Packages a WorkBuddy skill directory into a distributable zip with a pre-pack security audit: blocks
  hardcoded real API keys and tokens, flags personal environment paths for generalization, scrubs machine
  identifiers from Office template metadata, and validates the required SKILL.md display-name and
  description fields.
description: "将某个 WorkBuddy skill 目录打包为可分发 zip，并在打包前执行安全审计——扫描并拦截硬编码的真实 API key / token，发现个人环境路径（用户名、云盘同步目录、密钥文件、managed Python 路径等）则提示泛化。触发词：打包 skill / 压缩 skill / 把 skill 做成包 / package a skill / skill 发布包 / 分发 skill / 打包前安全审计 / 检查 skill 里有没有密钥。仅在用户明确要求打包、压缩、发布或分发一个 skill 文件夹时使用。"
agent_created: true
---

# Skill Packager（打包前安全审计 + 压缩）

## Overview

把一个 WorkBuddy skill 文件夹打成可分发 zip，并默认在打包前做一次安全审计，
防止把**真实密钥**或**个人环境路径**一起发出去。核心价值：可复用、零误泄露、
产出即「解压即用」的干净包。

适用场景：
- 用户说「把这个 skill 压缩成一个包 / 做成发布包 / 打包分发」
- 用户说「打包前检查下有没有 API key，有的话删掉」
- 用户想把自建 skill 分享给别人、上架或归档

## Workflow

### Step 0 · 开放平台发布质量预检（上架必做）

若用户是要**上架 / 发布到开放平台**（而非仅本地分发），先做这轮预检。
平台通常以「沙箱评测」判定，被打回的常见理由是无密钥泄露、纯属**"低质量 / 未达标准"**：

| 检查项 | 判定标准 | 不通过时的处理 |
|---|---|---|
| **零依赖可跑通**（最致命） | 在**没有第三方库**的解释器里，技能能否仍产出成果物？ | 必须有降级路径（改用 stdlib 产出 md/html/文本）。**"缺依赖就停工"在沙箱里等于零分** |
| **无本机硬编码路径** | 是否写死 `C:\Users\xxx`、`~/.workbuddy/binaries`、云盘目录、某个 venv 的绝对路径？ | 一律改为相对 SKILL.md 目录解析：`Path(__file__).resolve().parent` |
| **自包含性** | 只读 SKILL.md，模型能否知道该怎么做？ | 核心流程与关键规则内联进 SKILL.md，子文档只作深入参考 |
| **描述质量** | description 是否堆砌触发词、含"旧技能应停用删除"等内部笔记？ | 精简为「用途 + 场景 + 触发句」，内部元信息一律删除 |
| **外部程序依赖** | 是否依赖 LibreOffice / pandoc / 某个 CLI？ | 降级为可选，缺失时跳过而非阻断 |
| **适用范围** | 是否写成"仅某单位可用"？ | 改为「默认某模板 + 支持用户提供自有模板适配」 |

配套自检脚本要点：
- 临时目录用 `tempfile.mkdtemp()`；**放在工作区会被安全删除机制拦截 `rmtree`** 而中断打包。
- 冒烟测试必须**模拟零第三方库环境**，断言脚本退出码为 0 **且确实产出了文件**。
- 环境自检类脚本默认**永不阻断**（退出码 0），只输出运行级别；需要严格模式时用 `--strict`。

### Step 1 · 定位 skill 目录
确认要打包的源目录（通常为 `~/.workbuddy/skills/<name>/` 或 `{项目}/.workbuddy/skills/<name>/`）。
若用户只给了 skill 名，先用 Glob 在这两个位置查找 `**/<name>/SKILL.md` 定位。

### Step 2 · 跑安全审计脚本
直接运行自带脚本：

```bash
python scripts/package_skill_audit.py <skill_dir> [--out output.zip] [--force]
```

脚本会：
1. 扫描所有文本文件（md/py/json/yaml/txt/sh/...）中的**真实密钥模式**
   （OpenAI `sk-`、AWS `AKIA`、GitHub `ghp_`、Slack `xox`、Google `AIza`、`ya29.`、
   JWT、明文 `api_key="..."` 赋值等）。
2. 扫描**个人环境路径**（当前用户名、`BaiduSyncdisk`/`百度网盘`、`s2_key.txt`、
   managed Python 绝对路径等）。
3. 输出报告：
   - 发现真实密钥 → **报错并中止打包**（退出码 2），除非加 `--force`（仅审计用）。
   - 发现个人路径 → 列出 warning，不阻断，但应泛化后再打。

详细模式与话术见 `references/audit-patterns.md`。

### Step 2.5 · 补检 Office 二进制模板（脚本盲区，必做）

`package_skill_audit.py` 的 `TEXT_EXT` **只扫文本后缀**，不覆盖 `.docx/.xlsx/.pptx`。
凡 skill 里带 `templates/` Office 模板，必须额外查 `docProps` 元数据，否则会漏发：
- `docProps/core.xml` → `dc:creator` / `cp:lastModifiedBy`（真实姓名、工位账号）
- `docProps/app.xml` → `Application` / `Company`（**WPS 会写入机器 GUID**，如
  `WPS Office_12.1.0.28043_F1E327BC-269C-435d-A152-05C5408002CA`）
- 正文 XML（`word/*.xml`）里可能残留真实绝对路径、真实校名/人名

快速检查（仅 stdlib）：

```python
import zipfile, os, re
for fn in os.listdir(tpl_dir):                      # tpl_dir = <skill>/templates
    if not fn.lower().endswith(('.docx', '.xlsx', '.pptx')):
        continue
    with zipfile.ZipFile(os.path.join(tpl_dir, fn)) as z:
        for meta in ('docProps/core.xml', 'docProps/app.xml'):
            if meta in z.namelist():
                print(fn, meta, z.read(meta).decode('utf-8', 'ignore')[:600])
        body = ''.join(z.read(n).decode('utf-8', 'ignore')
                       for n in z.namelist() if n.startswith('word/') and n.endswith('.xml'))
        text = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', body))
        for pat in (r'C:\\Users\\admin', r'(?i)baidusyncdisk', r'\.workbuddy'):
            if re.search(pat, text):
                print('  [!] 正文命中', pat)
```

处理原则：**清洗副本，不动源目录**（copytree → 清洗 → 审计打包 → 删临时目录），
避免污染用户本地资产。剥离 WPS GUID 用
`re.sub(r"_[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}", "", xml)`
后重写 `docProps/app.xml`（保留其它 zip 条目原样写回）。

打包后回读校验：确认 zip 顶层目录名 = skill 名、`docx` 可 `testzip()`、GUID 残留为空。

### Step 3 · 处理审计发现
根据报告逐项处理，**先改源码、再打包**：

- **真实密钥**：必须删除。改为「用户自行提供」的说明（见 `references/audit-patterns.md`
  第三节标准话术），写入对应文件与 README。
- **个人路径**：泛化为通用表述——
  - `C:\Users\admin\.workbuddy\...` → `~/.workbuddy/skills/`（用户级）或 `.workbuddy/skills/`（项目级）
  - `E:\BaiduSyncdisk\...` / `百度网盘` → 删除具体路径，提示「勿放入会被云盘同步的目录」
  - `s2_key.txt` 绝对路径 → 「用环境变量临时传入」
  - managed Python 绝对路径 → 「任意 Python 3.8+ / WorkBuddy 自带 managed Python」
- **过期文档**：若 README 还停在旧版本/旧阶段数（如 v0.3、含已删目录），先更新再打包。
  确保 README 含：安装说明、使用指南、API Key 自行提供说明、文件结构（与实情对齐）。
  章节清单见 `references/audit-patterns.md` 第四节。
- **缺失的元信息（版权 / 作者 / 安装 / 使用）**：审计脚本会检测 README 与 SKILL.md 是否含
  这四类说明，缺失则报 `[待补充]`。按 `references/audit-patterns.md` **第五节**模板补全到 README 末尾：
  至少写明**作者/维护者**、**版本与日期**、**许可证/使用范围（含默认约束）**、**免责声明**。
  版权与作者说明建议常驻，每次改版只更新版本号。

### Step 4 · 重新审计 + 打包
改完后**再跑一次** `package_skill_audit.py` 确认：真实密钥 0、个人路径 0（或仅 warning 已处理）。
脚本自动排除 `__pycache__/` 与 `*.pyc`，并让 zip 顶层带 `<skill名>/` 目录，解压即用。

### Step 5 · 交付
- 将生成的 zip 用 `present_files` 交还给用户，并汇报：① 审计结果（有无高危/泛化项）；
  ② zip 路径、条目数、大小；③ 若改过源码，说明改了哪些文件。

## 关键约束

- **绝不打包真实密钥**：无论用户是否要求，发现真实密钥必须拦截并改为用户自备。
- **绝不外发个人路径**：用户名、云盘目录、密钥文件路径一律泛化。
- **不要 `--force` 绕过审计**用于正式分发；`--force` 仅供临时查看扫描结果。
- **顶层目录名 = skill 名**：保证解压后直接落进 `skills/` 即用，不多层嵌套。

## Resources

- `scripts/package_skill_audit.py` —— 审计+压缩主脚本（仅 stdlib，自包含）
- `references/audit-patterns.md` —— 密钥/路径模式表、用户自备密钥话术、README 章节清单
