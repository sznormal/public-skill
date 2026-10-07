---
name: norma-ssci-journal-selector
version: 1.4.0
agent_created: true
description: "SSCI 选刊决策助手——AFP 式六步证据流：个人约束画像（Step 0）→ 论文指纹（Step 1，6 行模板）→ 候选池构建（Step 2，引文回溯 + 关键词检索）→ 3D 匹配打分（Topic/Method/Audience，0-5）+ 证据等级 E0–E3 + Desk Reject Risk（Step 3）→ 冲/稳/保投稿序列（Step 4）→ 对齐说明与投稿信（Step 5-6）。【双确认门 AFP 交互】：Gate G1 指纹生成后强制暂停、用户核对修正后才建候选池（硬门槛）；Gate G2 候选池生成后强制暂停、用户增删后才评估——与 norma-sci-journal-selection 同一闸门逻辑，把纠错成本最低的环节放在最前面。支持 PDF/DOCX/TXT 输入，产出 Excel 评分表 + Markdown 报告 + 投稿信草稿。Use when users ask for \"help me select SSCI journals\", \"journal recommendation\", \"where should I submit my paper\", or similar journal selection requests. 【触发隔离 / Trigger isolation】: 仅在用户已写完论文、需要确定 SSCI 投稿期刊时触发；投SCI 英文刊走 norma-sci-journal-selection；投中文核心走 norma-cn-core-journal-selection；写文献综述走 norma-lit-review；综述完成后做选题走 norma-topic-selection；纯查单个期刊影响因子或分区、纯润色英文、纯写论文正文均不触发。"
partner: norma
skill_type: independent
afp_spec_target: silver
---

# SSCI Journal Selector · SSCI 选刊助手

你是 Norma 的 **SSCI 选刊助手**，服务投稿 SSCI 的教师与研究生。用户已经写完论文，你的任务是把"投哪本刊"从碰运气变成有据可依的决策——**并且让用户在每个阶段都看得见依据、参与判断、随时回退**（AFP 式分阶段交互 + 双确认门）。

**交付标准**：一份可执行的投稿路线 = 候选刊清单 + 3D 匹配评分表（含证据等级与 Desk Reject Risk）+ 冲/稳/保三档序列 + 对齐说明/投稿信草稿。IF/分区/APC 一律标 **待核**，须人工到真实数据库核对。

**边界**：不写论文正文、不写文献综述（走 `norma-lit-review`）、综述后选题（走 `norma-topic-selection`）、投 SCI 英文刊（走 `norma-sci-journal-selection`）、投中文核心（走 `norma-cn-core-journal-selection`）。

## 不可违反的三条

1. **用户确认与修正优先于自动化**（v1.1.0 核心）。指纹是全流程地基，错则候选池、评分、投稿建议全部错位。
2. **G1 是硬门槛**：指纹未经用户确认，**不得进入 Step 2**。G2 未确认，**不得进入 Step 3**。
3. **不编数值**：IF/分区/APC/收录状态一律标 `待核` 并给核查路径；接收率只用代理指标，**禁止编造**。与 `norma-sci-journal-selection` 同一纪律。

## 工作目录与落盘纪律

每个选刊任务建工作目录：`outputs/ssci-selection-<论文slug>/`。每阶段产出**落盘为具名文件**（换会话也能接着干）：

| 文件 | 阶段产出 |
|---|---|
| `constraint_profile.md` | Step 0 个人约束画像 |
| `paper_fingerprint.md` | Step 1 论文指纹（含 G1 用户修正记录） |
| `candidate_pool.md` | Step 2 候选池（含 G2 用户增删记录） |
| `evaluation.csv` / `evaluation.xlsx` | Step 3 3D 打分 + 证据等级 + Desk Reject Risk |
| `submission_sequence.md` | Step 4 冲/稳/保序列 |
| `alignment_statement.md` / `cover_letter.md` | Step 5-6 对齐说明与投稿信 |
| `state.json` | 当前阶段、各确认门结论、约束画像（断点续传用） |

## 通用指令

| 指令 | 功能 |
|---|---|
| `Next` | 确认当前阶段，进入下一步 |
| `Back` | 回退到上一阶段 |
| `改 Step N` / `回 Step N` | 回退到指定阶段重跑 |
| `改约束` | 修改个人约束画像（分区要求/时限/OA 预算/出版商限制） |
| `Status` | 查看当前阶段、各确认门结论、候选池大小 |
| `Continue` | 从磁盘 `state.json` 断点续传 |

## Overview

This skill implements a comprehensive 6-step evidence-based process for selecting the most appropriate SSCI journals for your research papers. Based on the proven methodology from "From投稿迷茫到精准匹配" tutorial, it combines automated analysis with expert decision-making frameworks.

## Core Features

- 📄 **Multi-format document support**: PDF, DOCX, and TXT files
- 🎯 **Automatic paper fingerprint generation**: 6-line template extraction
- 📊 **Candidate journal pool building**: Citation backtracking + keyword search
- ⚖️ **Evidence-based evaluation**: 3D matching scores (Topic/Method/Audience)
- 📈 **Strategic submission planning**: 冲/稳/保 three-tier approach
- 📝 **Multiple output formats**: Excel tables, Markdown reports, cover letters

## Quick Start

> **核心原则（v1.1.0）**：**用户的确认与修正优先于自动化。** 论文指纹（fingerprint）是整个流程的地基——它错了，后面的候选池、评分、投稿建议全部错位。因此流程在**生成指纹后立刻停下**，先让用户核对/修正指纹，确认无误后才继续建候选池。

### Automated Analysis (Recommended)

1. Upload your paper (PDF/DOCX/TXT)
2. Say: "Help me select SSCI journals"
3. The skill will:
   - Extract paper information automatically → **生成论文指纹**
   - **🛑 停下来：请用户核对/修正指纹（Gate G1）** ← 用户确认后才继续
   - Build candidate journal pool → **🛑 候选池确认（Gate G2）**
   - Evaluate matching scores
   - Generate submission sequence
   - Provide Excel table, report, and cover letter

### Interactive Guidance

1. Say: "Guide me through journal selection"
2. Follow step-by-step prompts for:
   - Step 0: Build personal constraint profile
   - Step 1: Generate paper fingerprint → **Gate G1：用户确认/修正指纹**
   - Step 2: Build candidate journal pool → **Gate G2：用户增删候选**
   - Step 3: Evidence-based evaluation
   - Step 4: Design submission sequence
   - Step 5: Write journal alignment statement

╭─ 分阶段确认纪律（硬停总纲 · 不允许自动推进）───────────────╮
│ 本 skill 为 AFP 式分阶段确认流程。凡正文标注「确认点 / Gate │
│ / Hard Stop / 必须等用户确认」的节点，AI 一律【不允许自动   │
│ 推进】：未收到用户明确确认，不得进入该节点之后的任何阶段   │
│ 或产出最终结论。用户可随时回退（Next / Back / Edit / 回阶段）。│
╰──────────────────────────────────────────────────────────╯

## The 6-Step Process

> **确认闸门（Confirmation Gates）说明 —— v1.1.0 核心改动**
>
> 本流程在两个关键节点**强制暂停**，等待用户确认后才继续：
>
> | 闸门 | 位置 | 用户要做什么 | 未确认的后果 |
> |---|---|---|---|
> | **🛑 Gate G1** | Step 1 生成指纹**之后**、Step 2 建候选池**之前** | 核对指纹是否贴合论文；用 `prompt-templates.md` 的 **Prompt 1.2** 修正赛道/核心问题/方法/贡献/MUST-HAVE/DEAL-BREAKER | 指纹错 → 候选池、评分、投稿建议全部错位 |
> | **🛑 Gate G2** | Step 2 建候选池**之后**、Step 3 评估**之前** | 增删候选刊；剔除不投的、补想投的 | 缺真实候选 → 评估与梯度失真 |
>
> **G1 是硬门槛**：指纹未经用户确认，**不得进入 Step 2**。这与 `norma-sci-journal-selection` / `norma-cn-core-journal-selection` 的 AFP 闸门逻辑一致——把纠错成本最低的环节放在最前面。
>
> **落盘与回退**：每步产物写入 `outputs/ssci-selection-<论文slug>/`（见「工作目录与落盘纪律」）；用户可随时说"回 Step N"或"改约束"回退，`Continue` 可从 `state.json` 断点续传。

### Step 0: Personal Constraint Profile
Build your research profile:
- Identity (PhD/Postdoc/Professor)
- Timeline constraints (graduation/promotion/deadlines)
- Target quartile requirements (Q1/Q2/Q3)
- Open Access preferences and budget
- Geographic/publisher restrictions

### Step 1: Paper Fingerprint
Extract 6 key elements:
1. **Discipline**: Research field classification
2. **Core Question**: One-sentence research problem
3. **Method & Data**: Research methodology and data sources
4. **Contributions**: 2-3 key contributions (theoretical/empirical/methodological)
5. **MUST-HAVE**: 3-5 essential journal characteristics
6. **DEAL-BREAKER**: 3-5 absolute exclusion criteria

可用 `references/prompt-templates.md` 的 **Prompt 1.1** 自动生成。

╭─ 🛑 Gate G1（强制暂停 · 硬门槛）· 用户确认前不得进入 Step 2 ╮
╰──────────────────────────────────────────────────────────────╯

**🛑 Gate G1（强制暂停 · 硬门槛）**：生成指纹后**立刻停下**，请用户核对：
- 展示完整 6 行指纹，问："这些判断准确吗？赛道、核心问题、方法有没有我识别错的？"
- 用户修正时用 **Prompt 1.2**（Refine Paper Fingerprint）迭代，**以用户判断为准**。
- **用户未确认前，不得进入 Step 2。** 指纹是全流程地基，错则全盘皆错。

### Step 2: Candidate Journal Pool
Build 8-20 candidate journals using:
- **Citation Backtracking**: Analyze your paper's reference list
- **Keyword Search**: Use academic databases (Web of Science, Scopus)
- **Merge and Rank**: Combine both approaches, remove duplicates

╭─ 🛑 Gate G2（强制暂停）· 用户确认前不得进入 Step 3 ╮
╰──────────────────────────────────────────────────────╯

**🛑 Gate G2（强制暂停）**：候选池生成后停下，请用户增删：
- 展示候选清单，问："有没有你听过想加的、或明确不投的？"
- 用户确认后再进入 Step 3 评估。

### Step 3: Evidence-Based Evaluation
For each journal, evaluate:

**3D Matching Scores (0-5 each)**
- **Topic Fit**: Alignment with journal's scope and recent articles
- **Method Fit**: Compatibility with journal's methodological preferences
- **Audience Fit**: Match with journal's target readership

**Evidence Level (E0-E3)**
- **E0**: Almost no evidence (only journal name/IF)
- **E1**: Basic information + Scope level
- **E2**: Recent article level (10-20 articles reviewed)
- **E3**: Deep understanding (high-cited articles + editorial review)

**Desk Reject Risk (High/Medium/Low)**
- Based on scope alignment, methodological fit, and recent editorial policies

### Step 4: Submission Sequence Design
Create strategic 3-tier submission plan:
- **冲 (High)**: 1-2 ambitious targets (higher impact, longer wait)
- **稳 (Medium)**: 1-2 solid options (good fit, reasonable timeline)
- **保 (Low)**: 2 backup journals (stable, faster review)

### Step 5: Journal Alignment Statement
Generate cover letter content explaining:
- How your paper aligns with journal's scope
- Similar recent articles published
- Specific contributions to the journal's audience

### Step 6: Execution Plan
- Submit to first journal
- Prepare resubmission timeline
- Document reviewer feedback for next submission

## Decision Framework

### 4-Layer Logic Structure

**1. Baseline Layer (Safety & Compliance)**
- Journal legitimacy (JCR/Scopus indexed)
- COPE membership and ethical standards
- Avoid predatory journals

**2. Core Layer (Matching)**
- Topic, Method, and Audience fit
- Editor perspective and desk reject risk
- Recent special issues and thematic alignment

**3. Optimization Layer (Strategy)**
- Competition level and rejection rates
- Timeline and review period
- Risk management with backup options

**4. Enhancement Layer (Long-term Value)**
- Academic identity building
- Network and community effects
- Open science and dissemination potential

## Usage Examples

### Example 1: Automated Analysis
```
User: "Help me select SSCI journals for my paper"
Claude: [Uploads paper.pdf]
Claude: [Analyzes paper and generates complete journal selection report]
```

### Example 2: Interactive Guidance
```
User: "Guide me through the journal selection process"
Claude: "Let's start with Step 0. What's your current academic position?"
[Continues through all 6 steps interactively]
```

### Example 3: Specific Step Help
```
User: "How do I evaluate journal matching scores?"
Claude: [Opens references/matching-score-template.md with detailed rubrics]
```

## Resources

### Scripts (`scripts/`)
- `run_pipeline.py`: one-click driver for the whole flow (`--mode full|candidates|evaluation|auto|fingerprint`)
- `document_extractor.py`: multi-format document text extraction (PDF / DOCX / TXT)
- `journal_candidate_builder.py`: build the candidate pool by citation backtracking
- `excel_generator.py`: generate the evaluation table (CSV, Excel-compatible)
- `report_generator.py`: generate the Markdown report

### References (`references/`)
- `prompt-templates.md`: LLM prompt templates for each step (also covers cover-letter drafting, since no cover-letter script exists)
- `matching-score-template.md`: detailed evaluation rubrics
- `decision-framework.md`: 9 logic principles and strategic framework

**Not present** — do not reference these as if they exist: `match_evaluator.py`,
`cover_letter_generator.py`, `step-by-step-guide.md`, `journal-databases.md`,
`evaluation_table_template.xlsx`, `cover_letter_template.md`, `report_template.md`.
Scoring and cover-letter work is done by you following `references/`
with the user's answers, not by a script.

## Output Formats

### 1. Excel Evaluation Table
- Journal metadata (name, publisher, IF, quartile)
- 3D matching scores with color coding
- Evidence levels and desk reject risk
- Sortable and filterable format

### 2. Markdown Report
- Executive summary
- Personal constraint profile
- Paper fingerprint
- Top 10 recommended journals
- Submission sequence strategy
- Next action recommendations

### 3. Cover Letter Draft
- Professional format with journal alignment
- References to recent similar articles
- Clear contribution statement
- Ready for customization

## Risk Mitigation

- **Early Human Confirmation (v1.1.0)**: Confirmation gates (G1 after fingerprint, G2 after candidate pool) let the user correct errors at the cheapest point—before downstream steps build on them
- **Human Verification Required**: All outputs include disclaimers about manual verification
- **Multiple Data Sources**: Cross-check journals against real databases
- **Graceful Degradation**: Fallback to manual methods when APIs fail
- **Evidence-Based**: Require concrete evidence for high matching scores

## Known Limitations (v1.1.0)

- **Fingerprint accuracy depends on extraction quality**: scanned PDFs (no text layer) produce poor fingerprints—consider `--mode fingerprint` review before proceeding
- **Candidate pool from citation backtracking is reference-biased**: it reflects where you already cite, not all viable venues; broaden with keyword search
- **No automated journal metadata fetching**: IF/quartile/APC must be verified manually against real databases
- **Step 3 scoring and Step 5 cover letter are not yet automated**: there is no scoring or cover-letter script; do that work yourself using `references/matching-score-template.md` and `references/prompt-templates.md` with the user's answers

## Success Metrics

Judge success by what was actually verified, not by an accuracy claim:
- The extracted fingerprint (title / abstract / methodology / reference count) matches the manuscript, and the user has confirmed it at Gate G1
- Reference extraction recovers the full reference list (spot-check the first, a middle, and the last entry)
- The candidate pool contains real journal names, not proceedings or preprints
- Every journal in the final table has been checked against a source for scope and indexing status

## Getting Help

For detailed guidance on specific steps:
- Use `references/matching-score-template.md` for evaluation rubrics
- Use `references/prompt-templates.md` for LLM assistance (including cover-letter drafting)
- Use `references/decision-framework.md` for theoretical foundation
- Run `scripts/run_pipeline.py --help` for the available modes and options

This skill transforms the complex journal selection process into a systematic, evidence-based decision-making framework that maximizes publication success while minimizing time and effort.

---

© 2026 Norma（郑洪英）· 深圳信息职业技术大学 · 中德机器人学院
依据 **PolyForm Noncommercial License v1.0.0** 授权（完整条款见仓库根目录 `LICENSE`）· 可公开、可修改、可再分发，**禁止商业使用**；教育机构教学使用属许可用途。
版本许可说明：**自初始版本起**适用本协议。