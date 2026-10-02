---
name: llm-wiki-ingest
description: >
  LLM Wiki 自动知识库维护技能。每次对话中产生的**任何新文件**（Write 操作生成的 .md/.py/.html/.json 等）或**用户上传的文件**（PDF/图片/文档等），都必须自动将内容摄入到位于 D 盘的 Obsidian-based 个人知识库（LLM Wiki）中。这是强制行为，不是可选操作。也支持用户手动说 ingest、记录到 wiki、加入知识库。执行 Ingest（摄入）、Query（查询）、Lint（健康检查）三种工作流。
version: 1.0.0
agent_created: true
---

# LLM Wiki Ingest 技能

## 知识库位置

知识库由多个独立的知识空间组成，**根目录不统一**（2026-09-10 实测校正，早期版本误记为全部位于 `cctest\`）：

| 空间 | 实际 Wiki 路径 | 用途 | 状态 |
|------|---------------|------|------|
| **workspace** | `D:\BaiduSyncdisk\cctest\workspace\llm-wiki\` | 工程/开发/技术研究 | ✅ 活跃（37+ 页，自适应目标检测综述知识域） |
| **teachspace** | `D:\BaiduSyncdisk\workbudy\teachspace\llm-wiki\` | 教学/课程建设/教务管理 | ⚠️ 骨架（仅 AGENTS.md + index.md，0 页） |
| **newsspace** | 尚未建立 llm-wiki（原始资料在 `cctest\newswork\`、`workbudy\newswork\`） | 新闻/资讯/行业动态 | ❌ 不存在，需先建空间 |

> **注意**：`D:\BaiduSyncdisk\cctest\teachspace\`、`D:\BaiduSyncdisk\cctest\newsspace\` 这两个路径**不存在**，切勿写入。

- **规范文件**：每个空间的 `llm-wiki/AGENTS.md`（每次会话开始时读取）
- **原始资料 PDF**：`workspace/docs/Papers/工业智能/文献/`（只读）
- **PDF 映射**：`workspace/docs/Papers/工业智能/文献/_mapping.json`

> **路由规则**：ingest 时根据内容类型自动判断目标空间——教学相关内容 → teachspace，新闻资讯 → newsspace，其他 → workspace。用户可显式指定目标空间。

---

## 触发时机（强制自动 + 手动）

### 🚨 强制自动触发（不可跳过）

每次对话中，以下操作完成后，**必须在同一轮回复中自动执行 ingest**，不允许跳过或延迟：

| 触发条件 | 说明 | 优先级 |
|----------|------|--------|
| **Write 操作** | 任何 `Write`/`Edit` 操作创建或实质性修改了非临时文件（.md / .py / .html / .json / .txt / .pptx / .docx 等） | 🔴 强制 |
| **用户上传文件** | 用户通过对话上传了 PDF、图片、Office 文档、代码文件等 | 🔴 强制 |
| **生成了可视化** | 对话中产生了图表、架构图、流程图等实质内容 | 🟡 建议 |
| **多轮讨论沉淀** | 对话中形成了明确的结论、决策或方法论洞察 | 🟡 建议 |

> **判定标准**：只要是用户会保留、打开、或后续引用的输出文件——无论是分析报告、代码脚本、课程框架、可视化图表——都必须自动 ingest。临时文件（`/tmp/` 下的 scratch work）除外。

### 手动触发（仍支持）

用户明确说以下关键词时：`ingest`、`记录到 wiki`、`加入知识库`、`更新 wiki`

> **原则**：有价值的知识不应只存在于聊天记录里，应自动沉淀到 wiki。

---

## 工作流零：Auto-Ingest（文件自动摄入）🔴 强制

当 `Write`/`Edit` 创建或修改了业务文件，或用户上传了文件后，**立即执行以下精简流程**：

### 执行步骤

**Step 0：判定是否需要 ingest**

- ✅ 需要：`.md` / `.html` / `.py` / `.json` / `.pptx` / `.docx` / `.xlsx` / `.pdf` / `.txt` 等业务文件
- ❌ 跳过：`/tmp/` 下文件、缓存文件、纯调试脚本

**Step 0.5：判断目标空间**

| 文件来源/内容 | 目标空间 |
|-------------|---------|
| 项目在 `teachrwork/` 或 `teachwork/` 下 | `teachspace` |
| 内容涉及课程/教学/教务/教材 | `teachspace` |
| 内容涉及新闻/资讯/行业动态 | `newsspace` |
| 其他（工程/技术/研究/默认） | `workspace` |

**Step 1：快速读取上下文**（无需重复读取 AGENTS.md 如果本次会话已读过）
```
Read {目标空间}/llm-wiki/wiki/index.md
```

**Step 2：创建文件摘要页**

路径：`{目标空间}/llm-wiki/wiki/sources/YYYY-MM-DD_{文件名简称}.md`

模板：
```markdown
# {文件名或主题}

## 来源信息
- **原始文件**: `{相对路径}`
- **创建时间**: YYYY-MM-DD
- **文件类型**: {Markdown/PDF/Python/HTML...}
- **所属项目**: {项目名}

## 核心内容摘要
{200-400字概括文件的核心内容和目的}

## 关键要点
- {要点1}
- {要点2}
- ...

## 相关页面
- [[concepts/{相关概念}]]
- [[entities/{相关实体}]]

## 标签
#{标签1} #{标签2} #{标签3}
```

**Step 3：更新 index.md**

在对应分类下添加：
```markdown
- [[sources/YYYY-MM-DD_{文件名简称}]] — {一句话描述}
```

**Step 4：创建或更新概念/实体页**（如有新的重要概念）

**Step 5：追加日志**

在 `{目标空间}/llm-wiki/wiki/log.md` 顶部追加：
```markdown
## [YYYY-MM-DD] auto-ingest | {文件名}

**新增页面**: [[sources/YYYY-MM-DD_{文件名简称}]]
**更新页面**: index.md
**来源**: {Write操作 / 用户上传}

---
```

### 批量文件处理

如果一次 Write 了多个文件（如多文件项目），采用批量模式：
- 为每个文件创建独立的 sources 页
- 批量更新 index.md（一次 Edit）
- 批量追加日志（一条日志记录所有文件）

---

## 工作流一：Ingest（手动/深度摄入新资料）

### 执行步骤

**Step 1：判断目标空间并读取 wiki 上下文**

先根据内容类型确定目标空间：
- 教学/课程/教务 → `D:\BaiduSyncdisk\cctest\teachspace\llm-wiki\`
- 新闻/资讯/行业动态 → `D:\BaiduSyncdisk\cctest\newsspace\llm-wiki\`
- 其他（工程/技术/研究/默认） → `D:\BaiduSyncdisk\cctest\workspace\llm-wiki\`

然后读取对应空间的上下文：
```
Read {目标空间}/llm-wiki/AGENTS.md
Read {目标空间}/llm-wiki/wiki/index.md
```
目的：了解当前知识库状态，避免创建重复页面。

**Step 2：读取原始资料**

- 若是 PDF：`Read {workspace}/docs/Papers/工业智能/文献/XX. 文件名.pdf`
- 若是 Markdown：直接 `Read` 文件路径
- 若内容来自当前对话：跳过此步，直接使用对话上下文

**Step 3：确认引用上下文（论文类）**

从主论文摘要查找该资料的引用段落：
```
Grep pattern="关键词" path="{目标空间}/llm-wiki/wiki/sources/2026-06-06_自适应目标检测综述.md"
```

**Step 4：创建源摘要页**

路径：`{目标空间}/llm-wiki/wiki/sources/YYYY-MM-DD_简写.md`

必须包含（见 `references/wiki-schema.md`）：
- `## 来源信息`
- `## 核心摘要`（200-400 字）
- `## 关键观点`（条目列表）
- `## 相关页面`（用 `[[链接]]` 关联）

**Step 5：扫描并更新相关 Concepts/Entities 页**

逻辑：
- 新论文是现有概念的代表方法 → 在现有概念页添加 `### XXX 深入分析` 章节 + 更新 `source_count`
- 新论文的主角方法尚无实体页 → 新建 `entities/方法名.md`
- 新论文引入全新学术范式 → 新建 `concepts/新概念.md`

深入分析章节结构：
```markdown
### [方法名] 深入分析（[[sources/YYYY-MM-DD_方法名]]）

**核心机制**：...
**关键数据/实验结果**：...
**适用条件与局限**：...
**与其他方法的互补关系**：...
```

**Step 6：更新 index.md**

- 在对应分类下添加新页面链接
- 更新页面总数 `共 N 个页面`

**Step 7：追加日志到 log.md**

在文件**顶部**追加（倒序，最新在上）：
```markdown
## [YYYY-MM-DD] ingest | 简述

**新增页面**: ...
**更新页面**: ...
**维基总页面**: N → N+k 页

---
```

---

## 工作流二：Query（查询知识库）

用户提问关于 wiki 中内容时：

1. 根据提问内容判断目标空间（教学→teachspace，新闻→newsspace，其他→workspace）
2. `Read {目标空间}/llm-wiki/wiki/index.md` 定位相关页面
3. `Read` 相关 sources/entities/concepts 页面
4. 综合信息，生成带引用的回答
5. 若回答具有持续价值 → 创建 `{目标空间}/llm-wiki/wiki/analysis/YYYY-MM-DD_主题.md` 页面

---

## 工作流三：Lint（健康检查）

用户说「检查 wiki 健康状态」时：

1. 扫描所有页面，检查：
   - 互相矛盾的声明
   - 孤立页面（无入链）
   - 多次提及但没有独立页面的概念/实体
   - 缺失的交叉引用
2. 生成健康报告，包含问题列表和建议操作
3. 提出 3-5 个值得深挖的后续问题或资料建议

---

## 关键约束

| 规则 | 说明 |
|------|------|
| 🔴 **强制 auto-ingest** | Write/Edit 操作或用户上传文件后，必须执行工作流零。不可跳过。 |
| `raw/` 只读 | 永远不修改 raw/ 目录下任何文件 |
| `log.md` 只追加 | 永远不修改 log.md 已有内容 |
| 交叉引用格式 | `[[sources/文件名]]`（不含 .md 扩展名） |
| 语言 | 默认中文，英文专有名词保留原文 |
| source_count | 每次向某页面添加内容时 +1 |
| 单次 ingest 规模 | 通常涉及 5-15 个页面的创建或更新 |
| 🔴 **自动空间路由** | 根据文件路径和内容自动选择 workspace/teachspace/newsspace |
| 🔴 **批量模式** | 多文件时批量创建 sources 页，避免逐文件重复读 index.md |
| 🟡 **同类主题不新建概念页** | 新材料若与既有概念页**同构**（如"TRAE 六步法需求模板"≙ 既有 ATP「目标+边界+验收」），应在既有概念页下加「同构变体 / 对照」章节并 `source_count` +1，**而非新建概念页**。该 wiki 以交叉引用优先，概念页重复即技术债。仅当新材料引入**全新范式**时才新建概念页。 |
| 🟡 **忠实转录 + 证据边界** | 截图类材料常被裁切：首行/末行残缺时，注明裁切位置并**只转录可见部分，不补全推测**。若材料无出处、无数据支撑，在页面内显式标注为"作者经验主张，不可作为有效性证据"。 |
| 🟡 **sources 与 entities 分工** | 材料若描述**一个具体产品/系统/项目/工具**且积累了多条事实 → 建 `entities/` 页（含「争议与不确定性」表，逐项列未验证内容）。**同一项目的多份材料各建一个 `sources/` 页**，共用同一 entities 页并互相双链——不合并成一个大 sources 页，保持来源可追溯。 |
| 🟡 **隐私字段** | 截图中的姓名标签、头像、账号等第三方信息：判断是否为 UI 浮层/通讯录元素；**只作客观记录并标明"归属关系不明确"，不据此推断身份**。 |

---

## 环境避坑（2026-09-21 实测）

| 现象 | 原因 | 绕过办法 |
|------|------|---------|
| Bash 报 `dirname: command not found`，随后 `cp`/`ls` 报 `command not found`（但退出码仍为 0，**易误判成功**） | shim `shell-runtime-bash-env.sh` 初始化失败，PATH 未设置 | 命令前加 `export PATH="/usr/bin:/bin:$PATH"` |
| PowerShell 工具无任何输出（连 `Write-Output` 也为空），`Copy-Item` 实际不生效 | 未知 | 改用 Bash + 显式 PATH；**PowerShell 无输出时一律换通道复核，不要当作成功** |
| 同一文件并行下发多处 `Edit` | 文件锁 | 出现 `EBUSY` 且**失败编辑静默丢失** → 单文件多处修改必须**串行**，改完回读确认 |

---

## 参考资料

- 详细 wiki 架构规范：`references/wiki-schema.md`
- 完整 ingest 示例（PDF/文章/笔记）：`references/ingest-examples.md`
- workspace 空间 AGENTS.md：`D:\BaiduSyncdisk\cctest\workspace\llm-wiki\AGENTS.md`
