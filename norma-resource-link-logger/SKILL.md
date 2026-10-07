---
name: norma-resource-link-logger
version: 1.3.0
display_name: 资源链接记录器
display_name_en: Resource Link Logger
description: 把链接（GitHub 仓库、网页、教程、论文、视频等）记录到 Norma 的资源分享链接库（金山文档智能表格）。触发说法包括"记个链接""记录 + 网址""收一下 + 网址""存 + 网址""加到资源库""收藏这个网页""这些链接都记一下"，用户只给 URL 不写说明时同样触发。自动查重、按链接类型抓取元数据与简介、判断分类、追加行、回读验证，支持一次给多个链接的批量导入。
description_zh: 把链接（GitHub 仓库、网页、教程、论文、视频等）记录到 Norma 的资源分享链接库（金山文档智能表格）。触发说法包括"记个链接""记录 + 网址""收一下 + 网址""存 + 网址""加到资源库""收藏这个网页""这些链接都记一下"，用户只给 URL 不写说明时同样触发。自动查重、按链接类型抓取元数据与简介、判断分类、追加行、回读验证，支持一次给多个链接的批量导入。
description_en: Log links (GitHub repos, web pages, tutorials, papers, videos) into Norma's resource-sharing sheet (WPS/Kdocs online spreadsheet). Triggers on "save this link", "record <url>", "add <url> to my resource library", "bookmark <url>", or "log these links" for batch import; a bare URL with no description also triggers. Auto de-duplicates, fetches metadata by link type, classifies, appends rows, and reads back to verify.
agent_created: true
partner: norma
skill_type: independent
afp_spec_target: bronze
---

# 资源链接记录器

把用户给的链接记录到资源分享链接库（金山文档智能表格）。

## 资源库档案

| 项 | 值 |
|----|----|
| file_id | `560738447695` |
| 分享链接 | https://www.kdocs.cn/l/ckp3QOvJhZl1 |
| 工作表 | `sheetId=3`，名称「工作表1」，类型 et |
| 表头 | 第 1 行（row 0） |

列结构（0-based 列索引）：

| 列 | 索引 | 字段 | 说明 |
|----|------|------|------|
| A | 0 | 序号 | 数字，从 1 递增 |
| B | 1 | 资源名称 | `中文名（owner/repo 或站点名）` |
| C | 2 | 链接 | 完整 URL |
| D | 3 | 主要作用 | 2-4 句，见下方写法 |
| E | 4 | 分类 | 必须从下拉选项选 |
| F | 5 | 记录时间 | `YYYY-MM-DD`，用当天日期 |
| G | 6 | 备注 | 可选：用途规划、风险提示 |

**分类下拉选项（E 列，必须严格取自这里）**：
`工具/网站`、`教程/课程`、`论文/文献`、`开源项目`、`AI 应用`、`其他`

GitHub 开源仓库一律选 `开源项目`；在线工具/SaaS 选 `工具/网站`；教程文章选 `教程/课程`。

## 绝不做什么

- 不删除、不清空表格中已有的任何行，也不改动表头、列顺序、颜色和下拉规则。
- 不编造热度、作者、年份等抓不到的字段；拿不到就留空或标「待补充」。
- 查重失败时不得盲写，避免重复收录。
- 不把链接、表格内容或凭据发送到表格以外的任何地方。
- 不在对话中回显任何凭据。

## 环境检查（先做）

每次执行前先运行只读检查器，按结果决定走哪条路：

```bash
python scripts/check_environment.py --capability read-sheet --capability write-sheet --capability fetch-metadata
```

探测结果由宿主执行最小只读调用后写入 `--probe-results` 指向的 JSON；需要验证公网可达性时再加 `--network`。

| 结果 | 含义 | 下一步 |
|------|------|--------|
| ready | 依赖齐全 | 直接进入正常流程，不再讲配置 |
| partial | 核心可用，可选功能受限 | 继续跑，只在回报里说明受影响功能 |
| needs_setup | 必需依赖未配置 | 只展示缺失项的配置步骤，配好后重检 |
| unavailable | 已配置但授权失效、限频或服务异常 | 展示原因、恢复步骤，按降级执行 |

注意：金山文档连接器由 WorkBuddy 连接器平台托管，不写入 `~/.workbuddy/mcp.json`，因此以宿主实际的最小只读调用结果为准，不以配置文件判断。

## 执行流程

### 1. 查重（必须先做）

```json
{"name": "mcp__kdocs__sheet.get_typed_value", "arguments": {
  "file_id": "560738447695", "worksheet_id": 3, "range": "A1:G200"}}
```

检查 C 列是否已存在同一 URL：

- **已存在** → 不要重复写入。用 `AskUserQuestion` 让用户选：保持原样 / 更新该条 / 补充备注 / 仍要新增重复项。
- **不存在** → 继续。同时记下当前最大序号 N，新记录用 N+1，写入行 = 行号索引（第 N+2 行，0-based 索引 = N+1）。

### 2. 抓取资源信息

**GitHub 仓库**：用 Bash 调 GitHub API 拿准确元数据（不要靠网页抓取猜 star 数）：

```bash
curl -s -H "Accept: application/vnd.github+json" https://api.github.com/repos/{owner}/{repo}
```

关键字段：`stargazers_count`、`forks_count`、`created_at`、`pushed_at`、`license.key`、`homepage`、`description`、`topics`。

同时用 `WebFetch` 抓 README 正文，提取：项目定位、核心能力、目录/分类结构、安装使用方式。

**普通网页**：只用 `WebFetch`，提取页面标题与简介。

**网页背后有开源仓库**：很多目录站（awesome-xxx.com 之类）页面上有 GitHub 入口。此时即使链接是网站，也照样用 GitHub API 补 star/fork/建仓时间，信息量比纯网页抓取大得多。

**分类与数据口径（不必再问，直接执行）**：
- 分类按"本质是什么"判断，不看链接形式。awesome 精选列表即使挂在独立域名下，也归 `开源项目`，与同类条目保持一致；纯在线服务才选 `工具/网站`。
- 页面本身不显示 star 时，从其 GitHub 仓库取，并在主要作用里注明配套仓库数据（如插件市场另有多少 star）。

### 2.1 按链接类型选择抓取方式

先按 URL 特征判定类型，再按类型取字段。抓不到的字段留空并注明，**禁止编造**。

| 类型 | 识别特征 | 抓取方式 | 关键字段 |
|------|---------|---------|---------|
| GitHub 仓库 | `github.com/owner/repo` | `api.github.com/repos/{owner}/{repo}`（见上文） | star / fork / license / pushed_at / description / topics |
| 论文 | `arxiv.org`、`doi.org`、`ieeexplore`、`sciencedirect`、`link.springer`、`dl.acm` | WebFetch 页面；arXiv 可用 `http://export.arxiv.org/api/query?id_list={id}` | 标题、作者、年份、期刊/会议、摘要要点 |
| 视频 | `bilibili.com/video/BV...`、`youtube.com/watch`、`youtu.be` | WebFetch；B 站可 `curl -s "https://api.bilibili.com/x/web-interface/view?bvid={bvid}"` | 标题、UP 主/频道、时长、发布时间、简介 |
| 技术文章 | `mp.weixin.qq.com`、`zhihu.com`、`csdn.net`、`juejin.cn`、个人博客 | WebFetch | 标题、作者/公众号、发布时间、核心观点 |
| Hugging Face | `huggingface.co` | WebFetch；模型页可 `curl -s https://huggingface.co/api/models/{id}` | 类型（model/dataset/space）、下载量、likes、协议 |
| 在线文档 | 飞书 / 金山 / 腾讯文档 / Notion | WebFetch（需公开可读，否则抓不到 → 标"待补充"） | 文档标题、归属空间 |
| PDF / 文件直链 | 以 `.pdf` 等结尾 | 取文件名与 `Content-Length`（`curl -sI`）；需要时下载后读取 | 文件名、大小、页数 |

**抓取失败降级**：资源名称用「域名 + 路径末段」推断短名，主要作用填 `（自动抓取失败，待补充）`，分类选 `其他` 并在回报中请用户补一句说明。

**分类判定表（扩展版）**：

| 资源本质 | 分类 |
|---------|------|
| GitHub/GitLab 仓库、awesome 精选列表、HF 模型/数据集 | `开源项目` |
| 在线 SaaS、工具站、插件市场、目录站 | `工具/网站` |
| 教程、课程、教学视频、技术文章 | `教程/课程` |
| 论文、预印本、专利、标准 | `论文/文献` |
| AI 产品 / 应用演示（非代码仓库形态） | `AI 应用` |
| 无法判断 | `其他` |

判据仍是"本质是什么"：教学视频归 `教程/课程`；会议报告录像这类科研成果归 `论文/文献`。

**超长 README（> 1 MB）**：`/readme` 接口会返回 `encoding: none`、content 为空。改用两步：

```bash
# 1) 拿 sha
curl -s https://api.github.com/repos/{owner}/{repo}/readme | grep '"sha"'
# 2) 用 blob 接口取 base64 正文
curl -s https://api.github.com/repos/{owner}/{repo}/git/blobs/{sha}
```

**注意**：`raw.githubusercontent.com` 在本机 SSL 连接会失败（curl exit 35），一律走 `api.github.com`。

拿到正文后统计规模（`### ` 分类数、`- [` 条目数），这些数字写进「主要作用」比"内容很丰富"有用得多。

### 3. 撰写「主要作用」

结构：`它是什么` → `核心内容/关键数据` → `对用户有什么用`。尾部按类型补关键元数据：

- 开源仓库：`热度：X star / Y fork（YYYY-MM-DD），协议，建仓时间，官网`
- 论文：`作者，期刊/会议，年份，DOI/arXiv 号`
- 视频：`UP主/频道，时长，发布时间`
- 在线文档 / 文章：`作者或来源，发布时间`

「对用户有什么用」要结合 Norma 的实际场景（嵌入式/机器视觉/具身智能教学、科研、AI+教育社群运营）来说，不要写通用套话。

要求：
- 具体数字优先（分类数、条目数、star 数），不要写"很多""丰富"这类空词。
- **禁止编造**。抓不到的字段就不写，不要猜。star 数抓不到时明确说明未获取。
- 若网页自述与 API `description` 数字不一致，以 API 为准并在回复中说明差异。

### 4. 写入

**单格 formula 上限 1024 字节（UTF-8，约 330 个汉字）**，超限直接返回 `{"code":400001,"message":"rangeData[i].formula size N bytes exceeds limit 1024"}` 并拒绝整批写入。因此 D 列「主要作用」必须成品控：**目标 280-300 汉字以内**，精简方式是砍掉修饰语与并列举例，保留「它是什么 + 关键数字 + 对 Norma 的用途」。首次写入就按此长度写，不要写完再截断重试。其余列（B 资源名称、G 备注）保持一句话。

用 `mcp__kdocs__sheet.update_range_data`，**值写进 `formula` 字段**，坐标 0-based：

```json
{"name": "mcp__kdocs__sheet.update_range_data", "arguments": {
  "file_id": "560738447695", "worksheet_id": 3,
  "rangeData": [
    {"opType":"formula","rowFrom":1,"rowTo":1,"colFrom":0,"colTo":0,"formula":"1"},
    {"opType":"formula","rowFrom":1,"rowTo":1,"colFrom":1,"colTo":1,"formula":"资源名称"},
    ...
  ]}}
```

更新已有记录时，只传需要改的那几个单元格，不要重发整行。

### 5. 回读验证（必须）

写完后立刻用 `get_typed_value` 读回刚写的行，逐字段核对。不信任 `code: 0`。若值不符，等 2 秒重试一次，仍不符则报告用户。

注意：`记录时间` 回读会显示为 `date` 类型（如 `2026-9-8`），属正常。

## 限频与错误处理

- 金山文档对请求频率敏感：遇 `429001`（限频）立即停止调用，等待响应中的恢复时间；`429002`（熔断）在熔断时长内零请求。禁止连续重试。
- **`local_rate_limited`（本地限流）**：较常见，不是鉴权问题。`sleep 5` 后重试即可成功。经验节奏：读与写之间、写与回读之间各留 3-5 秒，不要连续无间隔调用。
- `400006` 鉴权失败 → 提示用户在连接器管理中断开金山文档连接器后重连；配置、权限与撤销方式见 `references/setup-guide.md`。
- **连接器整体不可用**：`ToolSearch` 搜不到任何 `mcp__kdocs__*` 工具（只剩 `mcp__sheetagent__*`，那是本地文件编辑器，操作不了云端文档）时，说明 kdocs MCP 掉线。此时**不要反复重试**，改为：
  1. 正常完成抓取和信息整理；
  2. 把待写入内容 + 完整 `update_range_data` 指令落盘到工作空间（如 `pending-resource-link.md`）；
  3. 告知用户连接器状态，请其在连接器管理页重连，重连后按落盘文件一键写入。

## 批量导入（一次多个链接）

触发：用户一次给出 2 个以上 URL，或说"这些链接都记一下""批量导入"。

与单条流程的三点差异：

1. **只在开头读一次全表**：`get_typed_value` 读 `A1:G200`，一次性拿到已有 URL 集合与最大序号 N。不要在每条之间反复读表。
2. **抓取并行、写入一次**：抓取阶段可并行 WebFetch / 调 API；写入阶段把所有新记录放进**同一个** `update_range_data` 的 `rangeData` 数组（按行展开 formula 操作）一次提交，降低请求数与被限频的概率。
3. **回读一次整块**：写入后读 `A{N+2}:G{N+M+1}`（M = 新增条数）核对全部字段，不逐条回读。

序号与行号：已有最大序号 N → 新记录序号 `N+1 … N+M`，0-based 行索引 `N+1 … N+M`（表格第 N+2 … N+M+1 行）。

重复与失败项处理：

- 与已有 URL 重复的条目**不写入**，汇总后用 `AskUserQuestion` 一次性询问处理方式（保持原样 / 更新该条 / 仍要新增），不要每个重复项弹一次。
- 抓取失败的条目照常写入，主要作用标 `（自动抓取失败，待补充）`，并在回报中单列清单。
- 批量过程中若触发 429 / `local_rate_limited`：立即按「限频与错误处理」停止重试，用回读确认已写入部分，剩余条目连同完整写入指令落盘，待恢复后一次性补写。

## 收尾

- 向用户回报写入结果（表格形式列出该条内容），并指出哪些字段因抓不到而未填。
- 批量导入时，回报分三块：已新增 / 重复跳过 / 抓取失败待补充。
- 若本次修正了既有记录（如补 star 数），顺带检查同一批其他记录是否也缺同类字段，一并补齐并保持格式一致。

---

© 2026 Norma（郑洪英）· 深圳信息职业技术大学 · 中德机器人学院
依据 **PolyForm Noncommercial License v1.0.0** 授权（完整条款见仓库根目录 `LICENSE`）· 可公开、可修改、可再分发，**禁止商业使用**；教育机构教学使用属许可用途。
版本许可说明：**自初始版本起**适用本协议。
