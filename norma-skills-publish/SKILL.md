---
name: norma-skills-publish
description: 将单个 WorkBuddy skill 推送到 sznormal/norma-skills（GitHub + Gitee 双远端 monorepo）。当用户要把自建 skill 发布/同步到 norma-skills 仓库，或说"推送 skill""发布到 gitee/github""同步 norma-skills""把 skill 入库"时触发。
---

# norma-skills 双远端发布（norma-skills-publish）

## Overview

把本地补全好的单个 WorkBuddy skill 作为顶层子目录并入 `sznormal/norma-skills` monorepo，并推送到 **GitHub + Gitee 双远端**。本 skill 固化了 2026-10-02 实测的完整流程与所有踩坑点，避免重复排查。

## 关键事实（先读，避免踩坑）

- **系统代理**：git 实际走 `HTTPS_PROXY=http://127.0.0.1:62178`（不是早期记忆里的 59050）。**所有 git 网络命令必须 `dangerouslyDisableSandbox=true`**，否则沙箱拦截会误判"不可达"。
- **仓库可见性**：私有仓库。匿名可读（`clone` / `ls-remote` 不需认证），**写操作需认证**。
- **认证机制**：经 `sznormal` 账号 Basic 认证，凭证由 Windows 凭据管理器 / git `credential.helper=store` 提供（通常**无需手动 token**）。仅当 push 提示认证失败，才补 gitee / github Personal Access Token。
- **Gitee 卡顿是误报**：gitee 写时服务端 `receive-pack` 返回 `200 OK` 即已落库，但 git 客户端在读取 report-status 最后确认阶段会因代理抖动挂起（push 长时间无输出、被 timeout 杀、之后 `ls-remote` 也超时）。**这是本地确认阶段的误报，不是推送失败。**

## 标准流程（四步）

**Step 1 克隆仓库**
```bash
git clone https://gitee.com/sznormal/norma-skills.git   # 建议副本路径 D:/c/Users/29206/norma-skills
# 所有 git 网络命令加 dangerouslyDisableSandbox=true
```
仓库根目录为「一个 skill 一个顶层目录」结构。克隆后确认目标 skill 子目录尚不存在。

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

- 一个 skill 一个顶层目录；README「Skill 清单」必须同步登记（含版本号）。
- 不提交 `*.zip` 等打包产物；不提交 `__pycache__` / 构建产物（已被 .gitignore 覆盖）。
- 提交信息用 `feat: add <skill> ...` 风格，便于双端历史对齐。
