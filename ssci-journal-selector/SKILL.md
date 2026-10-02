---
name: ssci-journal-selector
version: 1.1.0
agent_created: true
description: Comprehensive SSCI journal selection skill that helps researchers select appropriate journals for their papers. Implements a 6-step evidence-based process with EARLY USER CONFIRMATION GATES - paper fingerprint must be reviewed and corrected by the user (Gate G1) before any candidate journal pool is built, and the candidate pool must be confirmed (Gate G2) before evaluation. Supports multiple document formats (PDF/DOCX/TXT) and generates Excel evaluation tables, Markdown reports, and cover letter drafts. Use when users ask for "help me select SSCI journals", "journal recommendation", "where should I submit my paper", or similar journal selection requests.
---

# SSCI Journal Selector

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
> **G1 是硬门槛**：指纹未经用户确认，**不得进入 Step 2**。这与 SCI 选刊的 AFP 闸门逻辑一致——把纠错成本最低的环节放在最前面。

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

**🛑 Gate G1（强制暂停 · 硬门槛）**：生成指纹后**立刻停下**，请用户核对：
- 展示完整 6 行指纹，问："这些判断准确吗？赛道、核心问题、方法有没有我识别错的？"
- 用户修正时用 **Prompt 1.2**（Refine Paper Fingerprint）迭代，**以用户判断为准**。
- **用户未确认前，不得进入 Step 2。** 指纹是全流程地基，错则全盘皆错。

### Step 2: Candidate Journal Pool
Build 8-20 candidate journals using:
- **Citation Backtracking**: Analyze your paper's reference list
- **Keyword Search**: Use academic databases (Web of Science, Scopus)
- **Merge and Rank**: Combine both approaches, remove duplicates

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

### Scripts
- `document_extractor.py`: Multi-format document text extraction
- `journal_candidate_builder.py`: Build candidate journal pool
- `match_evaluator.py`: LLM-based matching evaluation
- `excel_generator.py`: Generate Excel evaluation table
- `report_generator.py`: Generate Markdown report
- `cover_letter_generator.py`: Generate cover letter draft

### References
- `prompt-templates.md`: LLM prompt templates for each step
- `matching-score-template.md`: Detailed evaluation rubrics
- `decision-framework.md`: 9 logic principles and strategic framework
- `step-by-step-guide.md`: Complete manual SOP
- `journal-databases.md`: Database search strategies

### Assets
- `evaluation_table_template.xlsx`: Pre-formatted Excel template
- `cover_letter_template.md`: Professional cover letter structure
- `report_template.md`: Report structure template

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
- **Step 3 scoring and Step 5 cover letter are not yet automated**: `match_evaluator.py` and `cover_letter_generator.py` are documented but not implemented; use `prompt-templates.md` with LLM assistance

## Success Metrics

- 85% accuracy vs. expert manual selection
- Complete workflow in <10 minutes
- Professional quality cover letters
- Full automation in <2 minutes

## Getting Help

For detailed guidance on specific steps:
- Use `references/step-by-step-guide.md` for manual SOP
- Use `references/matching-score-template.md` for evaluation rubrics
- Use `references/prompt-templates.md` for LLM assistance
- Use `references/decision-framework.md` for theoretical foundation

This skill transforms the complex journal selection process into a systematic, evidence-based decision-making framework that maximizes publication success while minimizing time and effort.