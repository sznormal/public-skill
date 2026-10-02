#!/usr/bin/env python3
"""
Simplified Excel Generator for MVP

Generates basic Excel evaluation table for journal candidates.
"""

import json
import csv
from typing import List, Dict
from pathlib import Path


class ExcelGenerator:
    """Generate Excel-compatible CSV for journal evaluation"""

    def __init__(self):
        self.headers = [
            'Rank',
            'Journal Name',
            'Frequency',
            'Priority',
            'Topic Fit (0-5)',
            'Method Fit (0-5)',
            'Audience Fit (0-5)',
            'Total Score (0-15)',
            'Evidence Level (E0-E3)',
            'Desk Risk (H/M/L)',
            'Notes'
        ]

    def generate_evaluation_table(self, candidates: List[Dict]) -> str:
        """
        Generate CSV content for evaluation table.

        Args:
            candidates: List of candidate journals from journal_candidate_builder

        Returns:
            CSV content as string
        """
        lines = []

        # Add headers
        lines.append(','.join(self.headers))

        # Add candidate rows
        for candidate in candidates:
            row = [
                str(candidate.get('rank', '')),
                f'"{candidate.get("journal_name", "")}"',  # Quote for CSV safety
                str(candidate.get('frequency', '')),
                candidate.get('priority', ''),
                '',  # Topic Fit - to be filled by user
                '',  # Method Fit - to be filled by user
                '',  # Audience Fit - to be filled by user
                '',  # Total Score - to be calculated
                '',  # Evidence Level - to be filled by user
                '',  # Desk Risk - to be filled by user
                ''   # Notes
            ]
            lines.append(','.join(row))

        return '\n'.join(lines)

    def save_csv(self, csv_content: str, output_path: str):
        """Save CSV to file"""
        with open(output_path, 'w', encoding='utf-8-sig') as f:  # utf-8-sig for Excel compatibility
            f.write(csv_content)

    def generate_from_candidates_file(self, candidates_file: str) -> str:
        """
        Generate CSV from candidates JSON file.

        Args:
            candidates_file: Path to candidates.json from journal_candidate_builder

        Returns:
            CSV content as string
        """
        with open(candidates_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        candidates = data.get('candidates', [])
        return self.generate_evaluation_table(candidates)


def main():
    """Test with candidates file"""
    import sys

    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python excel_generator.py <candidates.json> [output_evaluation.csv]")
        print("  where candidates.json is output from journal_candidate_builder.py")
        sys.exit(1)

    candidates_file = sys.argv[1]

    # Generate CSV
    generator = ExcelGenerator()
    csv_content = generator.generate_from_candidates_file(candidates_file)

    # Save to file — optional 2nd arg lets run_pipeline.py specify the output path.
    if len(sys.argv) == 3:
        output_file = sys.argv[2]
    else:
        output_file = candidates_file.replace('.candidates.json', '_evaluation.csv')
    generator.save_csv(csv_content, output_file)

    print("\n" + "="*60)
    print("EXCEL EVALUATION TABLE GENERATED")
    print("="*60)
    print(f"✅ CSV file saved to: {output_file}")
    print("\nThe CSV file includes:")
    print("  - Journal names and frequency from references")
    print("  - Empty columns for you to fill in evaluation scores")
    print("  - Topic/Method/Audience fit scores (0-5 each)")
    print("  - Evidence level (E0-E3)")
    print("  - Desk reject risk (High/Medium/Low)")
    print("\nNext steps:")
    print("  1. Open CSV in Excel")
    print("  2. Fill in Topic/Method/Audience scores (0-5)")
    print("  3. Calculate Total Score (=Topic+Method+Audience)")
    print("  4. Assign Evidence Level (E0-E3)")
    print("  5. Estimate Desk Risk (H/M/L)")
    print("  6. Add notes for each journal")
    print("\n" + "="*60)


if __name__ == "__main__":
    main()