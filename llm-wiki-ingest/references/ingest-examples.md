# LLM Wiki Ingest 流程完整示例

## 场景 A：Auto-Ingest（文件自动摄入）🔴 强制

触发条件：Write/Edit 操作创建了业务文件，或用户上传了文件。

### 示例：对话中创建了一个课程框架 Markdown 文件

LLM 内部执行步骤：

#### Step 0：判定是否需要 ingest
- 文件类型：`.md` → ✅ 需要

#### Step 0.5：判断目标空间
- 文件路径含 `teachrwork/` → 目标空间：`teachspace`

#### Step 1：快速读取上下文
```
Read D:\BaiduSyncdisk\cctest\teachspace\llm-wiki\wiki\index.md
```

#### Step 2：创建文件摘要页
```
Write D:\BaiduSyncdisk\cctest\teachspace\llm-wiki\wiki\sources\2026-07-09_课程框架v3.md
```
内容：
```markdown
# 嵌入式Linux课程框架v3

## 来源信息
- **原始文件**: `嵌入式Linux操作系统应用_智慧课程框架_64学时_汇川工控版_v3.md`
- **创建时间**: 2026-07-09
- **文件类型**: Markdown
- **所属项目**: 嵌入式linux应用开发

## 核心内容摘要
v3版本课程框架在v2基础上全面改为岗位场景命名，验收标准改为功能验证+质量规范+交付物标准（5类体系），新增shellcheck质量检查。含6个项目18个任务64学时。

## 关键要点
- 项目以岗位角色命名，不以技术功能命名
- 验收标准不使用时间标准
- 新增实验项目对照表
- 总任务数18个，总学时64

## 相关页面
- [[concepts/项目化课程设计]]
- [[entities/汇川技术]]

## 标签
#课程框架 #嵌入式Linux #职业教育
```

#### Step 3：更新 index.md
在 teachspace 的 index.md 对应分类下添加：
```markdown
- [[sources/2026-07-09_课程框架v3]] — v3课程框架，6项目18任务64学时
```

#### Step 4：追加日志
在 teachspace 的 log.md 顶部追加：
```markdown
## [2026-07-09] auto-ingest | 课程框架v3

**新增页面**: [[sources/2026-07-09_课程框架v3]]
**更新页面**: index.md
**来源**: Write操作

---
```

### 批量 Auto-Ingest 示例

一次创建了17个理论测试题文件时：
- 为每个文件创建独立的 sources 页（17个）
- 批量更新 index.md（一次 Edit，添加17条链接）
- 批量追加日志（一条日志记录全部17个文件）

---

## 场景 B：手动 Ingest 一篇学术论文 PDF

用户输入：`帮我 ingest 这篇论文: 47. FDA_Fourier_Domain_Adaptation.pdf`

### Step 1：判断目标空间并读取上下文

论文属于工程/技术研究 → 目标空间：`workspace`

```
Read D:\BaiduSyncdisk\cctest\workspace\llm-wiki\AGENTS.md
Read D:\BaiduSyncdisk\cctest\workspace\llm-wiki\wiki\index.md
```
目的：了解 wiki 当前状态、已有页面、主题领域。

### Step 2：读取原始资料
```
Read D:\BaiduSyncdisk\cctest\workspace\docs\Papers\工业智能\文献\47. FDA_Fourier_Domain_Adaptation.pdf
```
如果是主论文，还需读取引用上下文：
```
Grep pattern="FDA" path="D:\BaiduSyncdisk\cctest\workspace\llm-wiki\wiki\sources\2026-06-06_自适应目标检测综述.md"
```

### Step 3：确定需要更新的现有页面
扫描 index.md，找出哪些已有概念页/实体页与新论文相关。
例如：FDA 涉及域适应 → 需要更新 `concepts/跨域适应.md`

### Step 4：创建源摘要页
```
Write D:\BaiduSyncdisk\cctest\workspace\llm-wiki\wiki\sources\2026-06-06_FDA.md
```
包含：来源信息、200-400字核心摘要、关键观点列表、相关页面链接。

### Step 5：更新相关概念/实体页
```
Read D:\BaiduSyncdisk\cctest\workspace\llm-wiki\wiki\concepts\跨域适应.md
Edit D:\BaiduSyncdisk\cctest\workspace\llm-wiki\wiki\concepts\跨域适应.md  # 新增"FDA 深入分析"小节，更新 source_count
```
深入分析章节格式：
```markdown
### FDA 深入分析（[[sources/2026-06-06_FDA]]）

**核心机制**：...
**关键数据**：...
**工业适用条件**：...
**与其他方法的互补关系**：...
```

### Step 6：更新 index.md
- 将新来源摘要页加入列表
- 更新页面总数（如 26 → 27）

### Step 7：追加日志到 log.md
按日志格式追加，记录新增页面和更新页面。

---

## 场景 C：Ingest 到 teachspace（教学类内容）

用户输入：`把课程思政评审标准记录到知识库`

### Step 1：判断目标空间
内容涉及课程/教学/教务 → 目标空间：`teachspace`

```
Read D:\BaiduSyncdisk\cctest\teachspace\llm-wiki\AGENTS.md
Read D:\BaiduSyncdisk\cctest\teachspace\llm-wiki\wiki\index.md
```

### Step 2：内容来自对话
跳过读取原始资料，直接使用对话上下文。

### Step 3：创建源摘要页
```
Write D:\BaiduSyncdisk\cctest\teachspace\llm-wiki\wiki\sources\2026-07-09_课程思政评审标准.md
```

### Step 4：创建/更新概念页
```
Write D:\BaiduSyncdisk\cctest\teachspace\llm-wiki\wiki\concepts\课程思政.md
```

### Step 5：更新 index.md
### Step 6：追加日志

---

## 场景 D：Ingest 到 newsspace（新闻/资讯类内容）

用户输入：`把今天看到的人形机器人行业动态 ingest 到 wiki`

### Step 1：判断目标空间
内容涉及新闻/资讯/行业动态 → 目标空间：`newsspace`

```
Read D:\BaiduSyncdisk\cctest\newsspace\llm-wiki\wiki\index.md
```

### Step 2-5：同上流程，写入 newsspace 目录

---

## 场景 E：用户直接告知结论后要求 ingest

用户输入：`帮我把刚才讨论的内容记录到 wiki 里`

此时主要是 Step 4-7（创建 sources 页 → 更新 index → 追加日志），内容来自当前对话，不需要重新读取 PDF。

---

## 场景 F：用户阅读非论文资料（文章、笔记等）

1. Read 资料文件
2. 在 raw/ 下保存副本（如果还没有）
3. 继续执行 Step 3-7

---

## 决策：何时需要新建实体/概念页

| 条件 | 操作 |
|------|------|
| 新论文的主角方法/模型不在现有实体页中 | 新建 `entities/新方法名.md` |
| 新论文引入全新学术概念/范式 | 新建 `concepts/新概念.md` |
| 仅补充现有概念的文献支撑 | 更新现有概念页，增加"深入分析"小节 |
| 方法是现有实体的变体 | 在现有实体页添加"变体"子章节 |

## 决策：source_count 更新规则

每次向某页面添加内容时，将 YAML front matter 中的 `source_count` +1。
例如 `source_count: 2` → `source_count: 3`

## 注意事项

- **永远不修改 raw/ 目录下的文件**
- **log.md 只追加，不修改已有内容**
- **index.md 的页面总数要准确反映实际文件数**
- **交叉引用格式**：`[[sources/文件名]]`（不含扩展名，相对路径）
- **单次 ingest 通常涉及 5-15 个 wiki 页面的创建或更新**
- **Auto-ingest 时如已读过 AGENTS.md 则无需重复读取**
