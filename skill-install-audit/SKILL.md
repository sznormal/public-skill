---
name: skill-install-audit
version: 1.0.0
agent_created: true
description: 从本地 .zip 或 GitHub 仓库安全安装 WorkBuddy skill 的标准流程——先做安全审计（P0/P1/P2 分级），再安装到用户级 skills 目录。当用户说"安装这个skill""装一下这个技能""从 GitHub 装 skill"或提供 .zip / 仓库 URL 时使用。本机实测：skills-security-check 技能未安装，需走本文件手动审计。
---

# Skill 安装安全审计 + 安装流程

## 适用场景
- 来源：本地 `.zip`（如 `E:\xxx.zip`）或 GitHub 仓库 URL（`https://github.com/owner/repo`）。
- 目标：用户级 `~/.workbuddy/skills/<name>/`（用户明确要项目级时才放项目 `.workbuddy/skills/`）。

## 关键环境坑（本机实测，先读避免踩）
- **`skills-security-check` 技能在本地未安装** → 不要因找不到它而中断，直接按本文件手动审计。
- **Bash 的 `/tmp` 在两次工具调用间不持久**（每次调用是独立沙箱，且 `/tmp` 会被解析成 `d:\tmp`）。因此：克隆/解压与列举**必须在同一条 Bash 命令内**完成，或直接使用工作区路径（如 `D:\BaiduSyncdisk\.skill_audit_<name>`），装完再清理。
- **`find` 在 Windows Git Bash 下对长路径 / `-printf` 会报"参数格式不正确"**，改用 `ls -la` 或 Glob / Read 工具。
- **管道 `| head` 会吞掉真实退出码**：克隆后用 `REAL_EXIT=${PIPESTATUS[0]}` 取真实码，不要只看 `EXIT=$?`。
- **计数 bug 提醒**：`sum(len(f) for ...)` 计的是文件名字符长度而非文件数；正确做法用 `len(list(os.walk(d)))` 或逐目录 `sum(1 for _ in fs)`。

## 安全审计（安装前必做，P0 / P1 / P2 分级）
1. **取内容**
   - zip：`python -c "import zipfile; zipfile.ZipFile(r'<path>').extractall(r'<tmp>')"`
   - git：同一条 Bash 命令内 `git clone --depth 1 <url> <workspace_tmp> && ls -la <workspace_tmp>`
2. **通读** `SKILL.md` 与所有 `scripts/`、`tools/` 下的可执行文件（`.py`/`.sh`/`.js`/`.bat`/`.ps1`）。
3. **危险模式扫描**（用 Grep 跨仓库）：
   `subprocess|os\.system|os\.popen|eval\(|exec\(|__import__|compile\(|marshal|pickle|shutil\.rmtree|os\.remove|socket\.|requests\.|urllib|ctypes|win32|keylogger|base64\.b64decode|curl |wget |reverse.?shell`
   命中 ≠ 危险，逐条看上下文。
4. **网络目标核验**：若含 `requests` / `urllib`，读取 URL 与请求头，确认是厂商官方域名（如剪映 `ulikecam.com`），无硬编码 token / 密码；检查下载是否限大小、是否校验 URL scheme 防 SSRF。
5. **删除 / 路径越权核验**：若有 `shutil.rmtree` / `os.remove`，确认作用域——是否用 `os.path.commonpath` 之类手段限制在用户可控目录内、拒绝删根 / 越界。
6. **命令注入核验**：`subprocess` 是否用 list 参数而非 `shell=True`（Grep `shell=True` 应为 0 命中）。
7. **分级**：
   - **P0（阻断）**：反向 shell、凭据外传、无差别删除、混淆代码 → 强烈警告，**不安装**。
   - **P1（警告）**：有网络出口 / 有删除但属核心功能、无恶意 → 向用户披露后安装。
   - **P2（安全）**：无上述 → 直接安装。

## 安装
```
python -c "import shutil,os; s=r'<src>'; d=os.path.expanduser(r'~/.workbuddy/skills/<name>'); assert not os.path.exists(d); shutil.copytree(s,d,ignore=shutil.ignore_patterns('.git'))"
```
- 目录名建议取 SKILL.md frontmatter 的 `name` 字段。
- 排除 `.git`，其余（README / examples / tests / assets 等）一并复制。
- 安装后回读确认 `SKILL.md` 存在。
- 最后清理工作区临时目录（如 `D:\BaiduSyncdisk\.skill_audit_<name>`）。

## 安装后依赖就绪性核验（强烈建议，本机实测踩过）
装完文件不等于能跑。务必再核验运行时依赖，否则会像 `jianying-editor` 那样卡在核心 import（缺 `uiautomation` 直接 `import_failed`）：
1. 读仓库根的 `requirements.txt` / `pyproject.toml`，列出依赖。
2. 用 `importlib.metadata.version(pkg)`（模块名含 `-` 或 `opencv-python`→`cv2` 等需做映射）逐个探测，区分 OK / MISSING。
3. 实跑 skill 自带的 validator（若有，如 `scripts/api_validator.py --json`）拿结构化结果——它会在日志里暴露真正的缺失项。
4. **媒体类 skill 另查二进制**：如 `ffmpeg` / `ffprobe` 是否在 PATH（`shutil.which`），缺失则导出/转码会失败。
5. 汇报：已装清单 + 缺失清单 + 是否阻塞核心 import。缺失依赖的安装需用户另行确认（改托管 Python 环境、联网下载），不要静默 `pip install`。

## 交付
- 向用户汇报：审计分级结论 + 关键说明（如网络出口域名、删除作用域、运行前置依赖如 ffmpeg / 剪映专业版）。

---

© 2026 Norma（郑洪英）· 深圳信息职业技术大学 · 中德机器人学院
依据 **PolyForm Noncommercial License v1.0.0** 授权（完整条款见仓库根目录 `LICENSE`）· 可公开、可修改、可再分发，**禁止商业使用**；教育机构教学使用属许可用途。
版本许可说明：**自初始版本起**适用本协议。
