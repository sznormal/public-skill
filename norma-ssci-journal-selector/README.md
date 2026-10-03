# norma-ssci-journal-selector · SSCI Journal Selector (MVP Version)

Minimum Viable Product for automated SSCI journal selection.

> **v1.3.0 — PDF/DOCX 通道实测修复**（装齐依赖后用真实 29 页 PDF 跑通全链路发现）:
> ① **`extract()` 对 PDF/DOCX 直接 return，绕过了章节识别** —— 全文虽抽出 10 万字符，但 title/abstract/methodology/references 全为空。现三种格式统一走识别（PDF 0 → 118 条参考文献）；
> ② 新增 PDF 参考文献切分：PDF 抽文本没有空行，一条文献被拆成多行，且 AAAI 等用「作者. 年份.」而非 `[1]` 编号制。以「句点+年份+句点」为条目起始标志，其余行回并 —— **118 行 → 118 条，与正文实际引用数一致**（判据经真实数据标定：限定搜索前 80/100 字符会漏计，长作者列表会把年份挤出窗口）；
> ③ 过滤 PDF 每页重复的刊眉/收稿行（"Journal of ..., Vol. 4, Article 6. Publication date: ..."、"Received 2 October 2026"）并按原文去重保序；
> ④ 刊名解析补英文作者-年制模式（`... "Title." Journal Name, 59, 1.`）—— 此前只认 GB/T 7714 `[J]` 标记，PDF 路径候选池为 0，现为 9 本；会议论文同槽位（`In:Proc. ACL`）由 `_NON_JOURNAL` 拦下。
> 回归：TXT 路径 118/118 与候选池不受影响；`py_compile` 全通过。
> ⚠️ 遗留：`title` 字段从未被任何格式填充（预置空串），属既有功能缺口；AAAI 稿件本身无 `Abstract` 标题行，abstract 为空是正确的。

> **v1.2.0 — 脚本层修复**（经真实稿件回归验证，116 篇参考文献样本）:
> ① `chardet` 由硬依赖改为软依赖，缺失时不再导致脚本无法启动；
> ② 参考文献提取从"遇到空行即截断"改为按标题定位 + 逐条累积，116 条 → **116/116 精确提取**（原仅 1 条）；
> ③ 刊名解析改为以 GB/T 7714 类型标记为准（**只有 `[J]` 是期刊**，`[C]` 会议 / `[M]` 图书 / `[EB/OL]` 预印本一律排除），候选池从 0 → 20 本真实期刊；
> ④ 摘要与方法章节改为锚定标题行提取，不再误抓修订说明里的同名字样；
> ⑤ 修正一处死代码（`if 'methodology' not in result` 因键始终存在而永不执行回退分支）；
> ⑥ 清理 SKILL.md 中 7 个不存在的文件引用，"85% 准确率"等未验证数字已删除。

> **v1.1.0 — 用户确认前置**：本流程在**生成论文指纹后立即暂停**（Gate G1），让用户先核对/修正指纹；候选池生成后再暂停一次（Gate G2）让用户增删。**确认后才继续**，避免错误指纹污染后续全部步骤。可用 `--mode fingerprint` 只跑到指纹，核对修正后再 `--mode candidates` 继续。

## Quick Start (5 Steps)

### Step 1: Extract Paper Information
```bash
python scripts/document_extractor.py your_paper.pdf
```
Output: `your_paper.pdf.extraction.json`

### Step 1.5: 🛑 Confirm Fingerprint (Gate G1)
Review the extracted 6-line fingerprint. Correct it if needed (use Prompt 1.2 in `references/prompt-templates.md`). **Do not proceed until confirmed.**

### Step 2: Build Candidate Journal Pool
```bash
python scripts/journal_candidate_builder.py your_paper.pdf.extraction.json
```
Output: `your_paper.pdf.candidates.json`

### Step 2.5: 🛑 Confirm Candidate Pool (Gate G2)
Add/remove candidate journals before evaluation.

### Step 3: Generate Excel Evaluation Table
```bash
python scripts/excel_generator.py your_paper.pdf.candidates.json
```
Output: `your_paper.pdf_evaluation.csv`

### Step 4: Generate Markdown Report
```bash
python scripts/report_generator.py your_paper.pdf.extraction.json your_paper.pdf.candidates.json
```
Output: `your_paper.pdf_report.md`

### Step 5: Manual Evaluation with LLM Assistance
1. Open the Excel CSV file
2. Use `references/prompt-templates.md` to evaluate each journal with LLM
3. Fill in Topic/Method/Audience scores (0-5 each)
4. Assign Evidence Level (E0-E3) and Desk Risk (H/M/L)

## What's Included in MVP

### ✅ Core Scripts
- `document_extractor.py` - Multi-format document extraction (PDF/DOCX/TXT)
- `journal_candidate_builder.py` - Extract journals from references
- `excel_generator.py` - Generate evaluation table
- `report_generator.py` - Generate analysis report

### ✅ Reference Documentation
- `SKILL.md` - Complete workflow guide
- `references/decision-framework.md` - 9 logic principles for journal selection
- `references/matching-score-template.md` - Detailed 3D scoring rubrics
- `references/prompt-templates.md` - All LLM prompts for evaluation

## Workflow Overview

```
Upload Paper (PDF/DOCX/TXT)
        ↓
[document_extractor.py]
        ↓
Paper Extraction JSON (6-line fingerprint)
        ↓
   ╔══════════════════╗
   ║ 🛑 GATE G1        ║  ← 用户核对/修正指纹（Prompt 1.2）
   ║ Confirm Fingerprint║     未确认不得继续
   ╚══════════════════╝
        ↓
[journal_candidate_builder.py]
        ↓
Candidate Journals JSON
        ↓
   ╔══════════════════╗
   ║ 🛑 GATE G2        ║  ← 用户增删候选刊
   ║ Confirm Candidates ║     确认后才评估
   ╚══════════════════╝
        ↓
[excel_generator.py] + [report_generator.py]
        ↓
CSV Table + Markdown Report
        ↓
[Manual with LLM Assistance]
        ↓
Complete Journal Evaluation
```

## Example Usage

### Example 1: Process a PDF paper
```bash
# Step 1: Extract
python scripts/document_extractor.py research_paper.pdf
# Output: Document extraction summary + JSON file

# 🛑 GATE G1: Review the 6-line fingerprint; correct if needed
#   (edit the .extraction.json, or use Prompt 1.2 with your LLM)
#   Confirm before continuing!

# Step 2: Build candidates
python scripts/journal_candidate_builder.py research_paper.pdf.extraction.json
# Output: Top journals from references + JSON file

# 🛑 GATE G2: Review candidate list; remove journals you won't target

# Step 3: Generate Excel
python scripts/excel_generator.py research_paper.pdf.candidates.json
# Output: CSV evaluation table

# Step 4: Generate report
python scripts/report_generator.py research_paper.pdf.extraction.json research_paper.pdf.candidates.json
# Output: Comprehensive Markdown report

# Step 5: Manual evaluation with LLM
# Use the prompt templates in references/prompt-templates.md
# Fill in the Excel table with your scores
```

### Example 2: Process a DOCX file
```bash
# Same process, just different input file
python scripts/document_extractor.py manuscript.docx
# Continue with same steps...
```

### Example 3: Process a TXT file
```bash
# Works with plain text files too
python scripts/document_extractor.py paper_text.txt
# Continue with same steps...
```

## LLM-Assisted Evaluation

After generating the initial candidates, use these resources for detailed evaluation:

### For Paper Fingerprint (Step 1)
```
Use: references/prompt-templates.md → Prompt 1.1
Purpose: Generate accurate 6-line paper fingerprint
```

### For Journal Evaluation (Step 3)
```
Use: references/prompt-templates.md → Prompt 3.1
Purpose: Evaluate Topic/Method/Audience fit for each journal
Guide: references/matching-score-template.md for scoring criteria
```

### For Submission Strategy (Step 4)
```
Use: references/prompt-templates.md → Prompt 4.1
Purpose: Design 冲/稳/保 3-tier submission plan
```

### For Cover Letter (Step 5)
```
Use: references/prompt-templates.md → Prompt 5.1 & 5.2
Purpose: Generate journal alignment statement and cover letter
```

## Understanding the Output

### Extraction JSON
Contains:
- Title, abstract, methodology sections
- References list
- Full text
- Metadata (format, extraction quality)

### Candidates JSON
Contains:
- List of journals from references
- Frequency counts
- Priority ranking (high/medium)

### Evaluation CSV
Template with columns for:
- Topic Fit (0-5)
- Method Fit (0-5)
- Audience Fit (0-5)
- Total Score (0-15)
- Evidence Level (E0-E3)
- Desk Risk (H/M/L)

### Report Markdown
Includes:
- Executive summary
- Paper fingerprint
- Top 10 candidates table
- Next steps recommendations

## Troubleshooting

### Issue: "No references found"
**Solution**: The document extractor couldn't identify the references section.
- Try manual input: Provide references as a list in JSON format
- Check if PDF has selectable text (not scanned image)

### Issue: "No candidate journals identified"
**Solution**: References were found but no journal patterns matched.
- Increase min_frequency in journal_candidate_builder.py (change `self.min_frequency = 1`)
- Manually review references for journal names

### Issue: "Extraction quality is low"
**Solution**: Document format is challenging.
- Try different PDF/DOCX file
- Use TXT format if available
- Manually copy-paste text into a TXT file

### Issue: "Journal names are incorrect"
**Solution**: Reference parsing is imperfect.
- Manually correct the journal names in candidates.json
- Use the corrected file for subsequent steps

## Dependencies

All three are **optional** — the skill degrades gracefully without them:

| Package | Needed for | If missing |
|---|---|---|
| `PyPDF2` | PDF extraction | falls back to `pdfplumber`, then to text-layer heuristics |
| `pdfplumber` | PDF table/layout extraction | falls back to `PyPDF2` |
| `python-docx` | DOCX extraction | DOCX input is rejected |
| `chardet` | encoding guess for TXT | falls back to the built-in `utf-8 → gbk → gb2312 → latin1` chain |

Only TXT input works with zero packages installed. Install what you need:
```bash
pip install PyPDF2 pdfplumber python-docx chardet
```

On this machine they are installed in the isolated venv (do **not** install
into the system Python):
```bash
C:/Users/admin/.workbuddy/binaries/python/envs/default/Scripts/python.exe scripts/document_extractor.py paper.pdf
```

Verified working on `manuscript.pdf` (29 pages, 118 refs): text layer 107,845
chars, 118/118 references, DOCX title extraction OK.

## What's NOT in MVP (Coming Later)

- Automatic journal metadata fetching (IF, quartile, scope)
- LLM-based automatic matching evaluation — ⚠️ `match_evaluator.py` is referenced in SKILL.md but **not yet implemented**; use `references/prompt-templates.md` (Prompt 3.1/3.2) with LLM assistance
- Cover letter generator script — ⚠️ `cover_letter_generator.py` is referenced in SKILL.md but **not yet implemented**; use Prompt 5.1/5.2 manually
- Advanced Excel formatting with formulas
- Keyword-based journal search (in addition to citation backtracking)

> **v1.1.0 note**: Step 3 (scoring) and Step 5 (cover letter) are LLM-assisted manual steps by design. The confirmation gates (G1/G2) intentionally keep the user in the loop early, so the pipeline does NOT run fully unattended end-to-end.

## Getting Help

1. Read `SKILL.md` for complete workflow
2. Check `references/decision-framework.md` for decision logic
3. Use `references/prompt-templates.md` for LLM assistance
4. Review `references/matching-score-template.md` for scoring criteria

## Next Steps After MVP

1. Test with your own papers (PDF/DOCX/TXT)
2. Provide feedback on:
   - Extraction accuracy
   - Journal candidate relevance
   - Usefulness of reports
   - Missing features
3. Prioritize features for full version:
   - Automatic metadata fetching
   - LLM-based evaluation
   - Keyword search integration
   - Advanced output formatting

## License

This skill is provided for academic research purposes.

---

**Remember**: This is an MVP to get you started quickly. For comprehensive journal selection, combine automated tools with manual analysis and LLM assistance using the provided prompt templates.

---

© 2026 Norma（郑洪英）· 深圳信息职业技术大学 · 中德机器人学院
依据 **PolyForm Noncommercial License v1.0.0** 授权（完整条款见仓库根目录 `LICENSE`）· 可公开、可修改、可再分发，**禁止商业使用**；教育机构教学使用属许可用途。
版本许可说明：**自初始版本起**适用本协议。
