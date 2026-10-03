#!/usr/bin/env python3
"""
Simplified Report Generator for MVP

Generates Markdown report for journal selection analysis.
"""

import json
from typing import Dict, List
from datetime import datetime


class ReportGenerator:
    """Generate Markdown report for journal selection"""

    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def generate_report(self,
                       paper_fingerprint: Dict,
                       candidates_data: Dict,
                       user_constraints: Dict = None) -> str:
        """
        Generate comprehensive Markdown report.

        Args:
            paper_fingerprint: Paper's 6-line fingerprint
            candidates_data: Candidate journals data from journal_candidate_builder
            user_constraints: Optional user constraints (identity, timeline, etc.)

        Returns:
            Markdown report as string
        """
        report = []

        # Header
        report.append("# SSCI Journal Selection Report")
        report.append(f"\n**Generated**: {self.timestamp}")
        report.append("\n---\n")

        # Executive Summary
        report.append("## Executive Summary")
        if candidates_data.get('status') == 'success':
            report.append(f"\nAnalyzed {candidates_data['total_references']} references and identified "
                        f"{len(candidates_data['candidates'])} candidate journals.")
            if candidates_data['candidates']:
                top = candidates_data['candidates'][0]
                report.append(f"\n**Top candidate**: {top['journal_name']} (appears {top['frequency']} times in references)")
        report.append("\n---\n")

        # User Constraints (if provided)
        if user_constraints:
            report.append("## Personal Constraints")
            report.append(f"\n**Identity**: {user_constraints.get('identity', 'Not specified')}")
            report.append(f"\n**Timeline**: {user_constraints.get('timeline', 'Not specified')}")
            report.append(f"\n**Target Quartile**: {user_constraints.get('quartile', 'Not specified')}")
            report.append(f"\n**OA Preference**: {user_constraints.get('oa_preference', 'Not specified')}")
            report.append("\n---\n")

        # Paper Fingerprint
        report.append("## Paper Fingerprint")
        if paper_fingerprint:
            report.append(f"\n**Discipline**: {paper_fingerprint.get('discipline', 'Not extracted')}")
            report.append(f"\n**Core Question**: {paper_fingerprint.get('core_question', 'Not extracted')}")
            report.append(f"\n**Method & Data**: {paper_fingerprint.get('method_data', 'Not extracted')}")
            report.append(f"\n**Contributions**: {paper_fingerprint.get('contributions', 'Not extracted')}")
            report.append(f"\n**MUST-HAVE**: {paper_fingerprint.get('must_have', 'Not extracted')}")
            report.append(f"\n**DEAL-BREAKER**: {paper_fingerprint.get('deal_breaker', 'Not extracted')}")
        report.append("\n---\n")

        # Candidate Journals
        report.append("## Candidate Journals")
        report.append("\n### Top 10 Candidates\n")

        candidates = candidates_data.get('candidates', [])
        if candidates:
            # Table header
            report.append("| Rank | Journal Name | Frequency | Priority |")
            report.append("|------|--------------|-----------|----------|")

            # Table rows
            for candidate in candidates[:10]:
                report.append(f"| {candidate['rank']} | {candidate['journal_name']} | "
                            f"{candidate['frequency']} | {candidate['priority']} |")
        else:
            report.append("\nNo candidates identified from references.")

        report.append("\n---\n")

        # Next Steps
        report.append("## Recommended Next Steps")
        report.append("\n### Step 1: Evaluate Top Candidates")
        report.append("\nFor each of the top 5-10 journals:")
        report.append("1. Visit the journal website and read the Aims & Scope")
        report.append("2. Review 5-10 recent articles to assess fit")
        report.append("3. Use the matching score template to evaluate Topic/Method/Audience fit (0-5 each)")
        report.append("4. Assign Evidence Level (E0-E3) based on your research depth")
        report.append("5. Estimate Desk Reject Risk (High/Medium/Low)")

        report.append("\n### Step 2: Design Submission Strategy")
        report.append("\nCreate a 3-tier submission plan:")
        report.append("- **冲 (Ambitious)**: 1-2 higher-impact journals")
        report.append("- **稳 (Stable)**: 1-2 well-matched journals")
        report.append("- **保 (Safe)**: 2 reliable backup journals")

        report.append("\n### Step 3: Use LLM Assistance")
        report.append("\nFor detailed journal evaluation, use the prompt templates in:")
        report.append("- `references/prompt-templates.md` - LLM prompts for each step")
        report.append("- `references/matching-score-template.md` - Detailed scoring rubrics")
        report.append("- `references/decision-framework.md` - 9 logic principles for decisions")

        report.append("\n### Step 4: Generate Outputs")
        report.append("\n1. Fill in the Excel evaluation table (generated by excel_generator.py)")
        report.append("2. Create cover letter using prompt templates")
        report.append("3. Document your submission sequence and timeline")

        report.append("\n---\n")

        # Resources
        report.append("## Resources")
        report.append("\n### Reference Documents")
        report.append("- `SKILL.md` - Complete workflow and usage guide")
        report.append("- `references/decision-framework.md` - Decision logic framework")
        report.append("- `references/matching-score-template.md` - Scoring guidelines")
        report.append("- `references/prompt-templates.md` - LLM prompts for assistance")

        report.append("\n### Scripts")
        report.append("- `document_extractor.py` - Extract paper information")
        report.append("- `journal_candidate_builder.py` - Build candidate pool")
        report.append("- `excel_generator.py` - Generate evaluation table")
        report.append("- `report_generator.py` - Generate this report")

        report.append("\n---\n")

        # Footer
        report.append("## Notes")
        report.append("\nThis report provides initial candidate journals based on citation backtracking.")
        report.append("For comprehensive analysis, combine with keyword-based search and LLM-assisted evaluation.")
        report.append("\n**Remember**: Always verify journal legitimacy and matching before submission.")

        return '\n'.join(report)

    def save_report(self, report: str, output_path: str):
        """Save Markdown report to file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)

    def generate_from_files(self,
                          extraction_file: str,
                          candidates_file: str,
                          constraints_file: str = None) -> str:
        """
        Generate report from extraction and candidates files.

        Args:
            extraction_file: Path to paper extraction JSON
            candidates_file: Path to candidates JSON
            constraints_file: Optional path to user constraints JSON

        Returns:
            Markdown report as string
        """
        # Load paper extraction
        with open(extraction_file, 'r', encoding='utf-8') as f:
            extraction_data = json.load(f)

        # Create basic paper fingerprint from extraction
        paper_fingerprint = {
            'discipline': 'To be determined',
            'core_question': 'To be extracted',
            'method_data': extraction_data.get('methodology', 'Not found'),
            'contributions': 'To be identified',
            'must_have': 'To be specified',
            'deal_breaker': 'To be specified'
        }

        # Load candidates
        with open(candidates_file, 'r', encoding='utf-8') as f:
            candidates_data = json.load(f)

        # Load user constraints (if provided)
        user_constraints = None
        if constraints_file:
            try:
                with open(constraints_file, 'r', encoding='utf-8') as f:
                    user_constraints = json.load(f)
            except FileNotFoundError:
                pass

        return self.generate_report(paper_fingerprint, candidates_data, user_constraints)


def main():
    """Generate report from command line"""
    import sys

    if len(sys.argv) < 3:
        print("Usage: python report_generator.py <extraction.json> <candidates.json> [constraints.json]")
        sys.exit(1)

    extraction_file = sys.argv[1]
    candidates_file = sys.argv[2]
    constraints_file = sys.argv[3] if len(sys.argv) > 3 else None

    # Generate report
    generator = ReportGenerator()
    report = generator.generate_from_files(extraction_file, candidates_file, constraints_file)

    # Save report — derive _report.md path robustly (candidates file may be
    # named paper_candidates.json OR paper.extraction.candidates.json).
    if candidates_file.endswith('.candidates.json'):
        output_file = candidates_file[:-len('.candidates.json')] + '_report.md'
    else:
        stem = candidates_file[:-5] if candidates_file.endswith('.json') else candidates_file
        output_file = stem + '_report.md'
    generator.save_report(report, output_file)

    print("\n" + "="*60)
    print("JOURNAL SELECTION REPORT GENERATED")
    print("="*60)
    print(f"✅ Report saved to: {output_file}")
    print("\nThe report includes:")
    print("  - Executive summary of candidate journals")
    print("  - Paper fingerprint (basic)")
    print("  - Top 10 candidate journals table")
    print("  - Recommended next steps")
    print("  - Links to reference documentation")
    print("\nNext steps:")
    print("  1. Open the Markdown report")
    print("  2. Review the candidate journals")
    print("  3. Use prompt templates for detailed evaluation")
    print("  4. Fill in the Excel evaluation table")
    print("  5. Design your submission strategy")
    print("\n" + "="*60)


if __name__ == "__main__":
    main()