# SSCI Journal Selector - MVP Version

Minimum Viable Product for automated SSCI journal selection.

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

Install required packages:
```bash
pip install PyPDF2 pdfplumber python-docx chardet
```

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