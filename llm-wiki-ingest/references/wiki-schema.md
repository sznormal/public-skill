# LLM Wiki 架构与规范参考

## 目录结构

```
llm-wiki/
├── AGENTS.md              ← Wiki 操作规范（每次会话首先读取）
├── raw/                   ← 原始资料（只读，绝对不修改）
│   ├── assets/
│   └── *.md / *.pdf / *.txt
└── wiki/                  ← LLM 全权维护
    ├── index.md           ← 全库索引（每次 ingest 后更新）
    ├── log.md             ← 操作日志（只追加）
    ├── overview.md        ← 综合综述
    ├── sources/           ← 文件名: YYYY-MM-DD_来源简写.md
    ├── entities/          ← 文件名: 实体名称.md
    ├── concepts/          ← 文件名: 概念名称.md
    └── analysis/          ← 文件名: YYYY-MM-DD_分析主题.md
```

## Front Matter 模板

```yaml
---
title: "页面标题"
type: source | entity | concept | analysis | overview
tags: [tag1, tag2]
created: YYYY-MM-DD
updated: YYYY-MM-DD
source_count: N
---
```

## 页面结构规范

### Sources 页（wiki/sources/YYYY-MM-DD_简写.md）
- `## 来源信息`：标题、作者、日期、链接
- `## 核心摘要`：200-400 字，提炼最重要论点与数据
- `## 关键观点`：条目列表，每条 1-2 句
- `## 相关页面`：链接到受此来源影响的 wiki 页面

### Entities 页（wiki/entities/实体名.md）
- `## 基本信息`：身份、背景、核心属性
- `## 关键事实`：带来源引用的重要事实列表
- `## 相关关系`：与其他实体/概念的关联，用 `[[链接]]`
- `## 争议与不确定性`：不同来源之间的分歧
- `## 参考文献`：支撑本页面的来源列表

### Concepts 页（wiki/concepts/概念名.md）
- `## 定义`：简明定义（1-3 句）
- `## 深度解析`：详细解释，含例子
- `## 相关概念`：与其他概念的关系，链接
- `## 实例`：具体案例或应用
- `## 参考文献`

### Analysis 页（wiki/analysis/YYYY-MM-DD_主题.md）
- `## 问题/背景`
- `## 分析`：正文
- `## 结论`
- `## 相关页面`
- `## 参考文献`

## 日志条目格式（追加到 wiki/log.md）

```markdown
## [YYYY-MM-DD] ingest | 操作描述

**操作类型**: 批量 Ingest 参考文献  
**源文件**: 文件路径或来源说明

**新增页面**:

| 页面 | 类型 | 说明 |
|------|------|------|
| `sources/YYYY-MM-DD_XXX.md` | 来源摘要 | 一行描述 |

**更新页面**:

| 页面 | 更新内容 |
|------|---------|
| `concepts/XXX.md` | 新增 XXX 深入分析 |

**维基总页面**: N → N+k 页

---
```

## 交叉引用规范

- 引用其他 wiki 页面：`[[sources/2026-06-06_SWDA]]`
- 引用实体：`[[entities/Faster R-CNN]]`
- 引用概念：`[[concepts/跨域适应]]`
- 链接格式始终使用相对 wiki 内部路径

## 语言约定

- 默认使用**中文**撰写
- 英文专有名词保留原文（首次出现时括号注中文）
- 来源引用格式：`[[sources/文件名]]`（无扩展名）
