---
name: norma-skills-publish
description: 将单个 WorkBuddy skill 推送到 sznormal/norma-skills（GitHub + Gitee 双远端 monorepo）。当用户要把自建 skill 发布/同步到 norma-skills 仓库，或说"推送 skill""发布到 gitee/github""同步 norma-skills""把 skill 入库"时触发。
version: 1.0.0
---

# norma-skills 双远端发布（norma-skills-publish）

## Overview

把本地补全好的单个 WorkBuddy skill 作为顶层子目录并入 `sznormal/norma-skills` monorepo，并推送到 **GitHub + Gitee 双远端**；**反向（从仓库拉取 / 安装 / 升级 skill）**见下方同名章节。本 skill 固化了 2026-10-02 实测的完整流程与所有踩坑点，避免重复排查。

## 关键事实（先读，避免踩坑）

- **本机仓库位置 = `C:\Users\admin\.workbuddy\skills`**：这个目录**同时**是 `norma-skills` monorepo 的本地克隆**与** WorkBuddy 用户级技能目录（一个 skill 一个顶层目录）。所以**「同步仓库」＝「装机/升级 skill」**，不需要再往别处拷贝。（若在别处看到 `D:/c/Users/<其他用户名>/norma-skills` 之类的克隆路径，那是模板残留，忽略。）
- **系统代理端口随会话变化，不要硬编码**：用 `env | grep -i proxy` 现取（2026-10-02 实测 `http://127.0.0.1:56159`；历史值 59050 / 62178 均已失效）。**所有 git 网络命令必须 `dangerouslyDisableSandbox=true`**，否则沙箱拦截会误判"不可达"。
- **双远端可能不同步**：`gitee` 与 `origin`(GitHub) 会各自领先（2026-10-02 实测 Gitee 领先 GitHub 1 个提交）。**核对/同步前两个远端都要 `fetch` 再比**，只看一边会得出错误结论。读操作用 `timeout 60` 包一层防挂起。
- **仓库可见性**：私有仓库。匿名可读（`clone` / `ls-remote` 不需认证），**写操作需认证**。
- **认证机制**：经 `sznormal` 账号 Basic 认证，凭证由 Windows 凭据管理器 / git `credential.helper=store` 提供（通常**无需手动 token**）。仅当 push 提示认证失败，才补 gitee / github Personal Access Token。
- **Gitee 卡顿是误报**：gitee 写时服务端 `receive-pack` 返回 `200 OK` 即已落库，但 git 客户端在读取 report-status 最后确认阶段会因代理抖动挂起（push 长时间无输出、被 timeout 杀、之后 `ls-remote` 也超时）。**这是本地确认阶段的误报，不是推送失败。**

## 标准流程（四步）

**Step 1 仓库就位**
本机仓库已固定在 `C:\Users\admin\.workbuddy\skills`（＝技能目录），**不要重复克隆**；远端未就绪时按下列方式补：
```bash
git clone https://gitee.com/sznormal/norma-skills.git   # 仅当该目录还不是 git 仓库时
# 所有 git 网络命令加 dangerouslyDisableSandbox=true
```
仓库根目录为「一个 skill 一个顶层目录」结构。并入前确认目标 skill 子目录尚不存在。

**Step 2 并入并登记**
- 复制 skill 目录到仓库根：`cp -r <src>/<skill> <repo>/<skill>`
- **删除 `*.zip`**（`.gitignore` 已忽略 `*.zip` 打包产物，但别留在工作区）；`!**/legacy/*.zip` 是历史留档例外，普通 skill 不提交 zip。
- 更新 `README.md` 的「Skill 清单」分类表，加一行：分类 / 名称 / 版本号 / 说明。漏登记视为不完整。

**Step 3 提交**
```bash
git add <skill> README.md
git commit -m "feat: add <skill> skill (<一句话说明>)"
```

**Step 4 配置双远端并推送**
```bash
git remote add github https://github.com/sznormal/norma-skills.git   # origin 已是 gitee
GIT_TERMINAL_PROMPT=0 git push origin main     # gitee
GIT_TERMINAL_PROMPT=0 git push github main     # github
```

## 反向：从仓库拉取 / 安装 skill（2026-10-02 实测）

目标：把远端已发布（常在另一台机器上改的）skill 同步到本机 —— 因为仓库目录＝技能目录，**拉取即"安装/升级"**。

**Step 0 体检（必做，唯一目的＝不覆盖本地未提交的工作）**
```bash
cd /c/Users/admin/.workbuddy/skills
git status --short                                   # 列出未提交改动（含 ?? untracked）
git log --oneline -1                                 # 本地 HEAD
git rev-parse --short HEAD origin/main gitee/main    # 三处对比，谁领先一眼看出
```

**Step 1 定方向**
- 远端领先 → 拉取；本地领先 → 走上面的发布流程推送；**两端点各领一部分 → 先停下说明，别自动合并**。

**Step 2 安全快进（红线：先证明零重叠）**
```bash
git diff --name-only > /tmp/_local.txt                                   # 本地未提交文件
git show --name-only --format="" <远端提交sha> | sed '/^$/d' > /tmp/_remote.txt
comm -12 <(sort /tmp/_local.txt) <(sort /tmp/_remote.txt)                # 输出为空 = 安全
git merge --ff-only gitee/main                                           # 本地无独有提交时 FF 成功
```
有重叠 → **停下来问用户**，绝不 `stash` / `reset` / `checkout --` 硬来。`--ff-only` 的价值：本地一旦有独有提交会直接失败，不会悄悄产生合并提交。

**Step 3 装机验证（拉完必做）**
1. `grep -E "^name|^version" <skill>/SKILL.md` —— 版本号已变；
2. `find <skill> -type f | sort` —— 远端新增的 references / scripts 都到位；
3. `git status --short` —— 原有未提交改动**一条不少**（逐条比对 Step 0）；
4. **技能缓存自动刷新**：`.skill-list-cache.json` 会在拉取后自行更新为新版 description（实测），无需手改。

**Step 4 补 README 版本**
远端提交常漏改 README（实测 `4821cf5` 把 SCI skill 升到 v1.3.0 却未动 README）。拉取后**必跑版本一致性核对**：
```bash
"C:\Users\admin\.workbuddy\binaries\python\versions\3.13.12\python.exe" \
  C:\Users\admin\.workbuddy\skills\norma-skills-publish\scripts\check_readme_versions.py
```
输出 A/B/C/D/E 五段：A=README 与 frontmatter 版本不一致、B=登记了但目录没了、C=frontmatter 无 version 字段、D=入库了但 README 未登记、E=磁盘有目录但 README 未登记（含第三方未入仓者，可忽略）。修 README 后**建议单独一个提交**，别混进上游提交。

## 确认落库（必须做，否则无法判定成功）

- **GitHub 成功标志**：push 输出 `main -> main`。
- **Gitee 已落库的最强证据**：再跑一次 `git push origin main` 返回 **`Everything up-to-date`**（退出码 0）。只要出现这句，远端必已含本次提交，之前的卡顿纯属客户端确认问题。
- **卡顿误判时诊断**：
  ```bash
  GIT_CURL_VERBOSE=1 GIT_TERMINAL_PROMPT=0 git push origin main 2>&1 | grep -iE "proxy|401|200|Powered by GITEE"
  ```
  链路出现 `CONNECT ... 200 Connection Established` → `GET ... 401` → `Authorization: Basic` → `POST ... 200 OK` → `remote: Powered by GITEE.COM`，即服务端已接收。
- 若 `ls-remote` 复核超时，不要慌——改用"再 push 一次看是否 up-to-date"判定，或开 gitee 网页核对 `<skill>/` 目录是否出现。

## 仓库约定（红线）

- 一个 skill 一个顶层目录；README「Skill 清单」必须同步登记（含版本号）。**每次推送/拉取后跑 `scripts/check_readme_versions.py` 核对**（远端提交漏改 README 是高频现象）。
- 不提交 `*.zip` 等打包产物；不提交 `__pycache__` / 构建产物（已被 .gitignore 覆盖）。
- 提交信息用 `feat: add <skill> ...` 风格，便于双端历史对齐。
- 操作前后**都要报出 `git status --short` 的未提交改动清单**：本地常有别人（或上一轮会话）留下的未提交工作，既不吞掉也不擅自提交。

---

© 2026 Norma（郑洪英）· 深圳信息职业技术大学 · 中德机器人学院
依据 **PolyForm Noncommercial License v1.0.0** 授权（完整条款见仓库根目录 `LICENSE`）· 可公开、可修改、可再分发，**禁止商业使用**；教育机构教学使用属许可用途。
版本许可说明：**自初始版本起**适用本协议。
