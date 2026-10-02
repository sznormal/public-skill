#!/usr/bin/env python3
"""
Simplified Journal Candidate Builder for MVP

Focuses on extracting journal names from paper references
and identifying potential candidate journals.
"""

import re
import json
from typing import List, Dict, Tuple
from collections import Counter


class JournalCandidateBuilder:
    """Build candidate journal pool from paper references"""

    def __init__(self):
        self.min_frequency = 2  # Minimum times a journal must appear

    def extract_journals_from_references(self, references: List[str]) -> List[Tuple[str, int]]:
        """
        Extract journal names from reference list.

        Args:
            references: List of reference strings

        Returns:
            List of (journal_name, frequency) tuples, sorted by frequency
        """
        journal_counter = Counter()

        for ref in references:
            journal_name = self._parse_journal_from_reference(ref)
            if journal_name:
                journal_counter[journal_name] += 1

        # Filter by minimum frequency and sort
        candidates = [(journal, count) for journal, count in journal_counter.items()
                     if count >= self.min_frequency]
        candidates.sort(key=lambda x: x[1], reverse=True)

        return candidates

    def _parse_journal_from_reference(self, reference: str) -> str:
        """
        Parse journal name from a single reference.

        This is a simplified parser - may need refinement for specific formats.
        """
        # Common patterns for journal references
        patterns = [
            # Pattern 1: Journal Name. Year;Volume:Pages
            r'^([A-Z][A-Za-z\s&]+?)\.\s*\d{4}',
            # Pattern 2: Authors. Journal Name, Year
            r'\.\s*([A-Z][A-Za-z\s&]+?),\s*\d{4}',
            # Pattern 3: Journal Name (Year)
            r'^([A-Z][A-Za-z\s&]+?)\s*\(\d{4}\)',
        ]

        for pattern in patterns:
            match = re.search(pattern, reference)
            if match:
                journal = match.group(1).strip()
                # Clean up common issues
                journal = journal.replace('&', 'and')
                journal = ' '.join(journal.split())  # Normalize whitespace

                # Filter out obvious non-journals
                if len(journal) > 5 and not any(x in journal.lower() for x in
                    ['university', 'press', 'chapter', 'book', 'ed.', 'editor']):
                    return journal

        return ''

    def build_candidate_pool(self, paper_data: Dict) -> Dict:
        """
        Build complete candidate journal pool from paper data.

        Args:
            paper_data: Dictionary containing 'references' key with list of references

        Returns:
            Dictionary with candidate pool and analysis
        """
        references = paper_data.get('references', [])

        if not references:
            return {
                'status': 'error',
                'message': 'No references found in paper data',
                'candidates': []
            }

        # Extract journals from references
        journal_candidates = self.extract_journals_from_references(references)

        # Build candidate pool
        candidates = []
        for i, (journal, frequency) in enumerate(journal_candidates[:20], 1):
            candidates.append({
                'rank': i,
                'journal_name': journal,
                'frequency': frequency,
                'source': 'citation_backtracking',
                'priority': 'high' if frequency >= 3 else 'medium'
            })

        return {
            'status': 'success',
            'total_references': len(references),
            'unique_journals': len(journal_candidates),
            'candidates': candidates,
            'analysis': {
                'top_journal': journal_candidates[0] if journal_candidates else None,
                'average_frequency': sum(count for _, count in journal_candidates) / len(journal_candidates) if journal_candidates else 0
            }
        }

    def save_candidate_pool(self, result: Dict, output_path: str):
        """Save candidate pool to JSON file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    def print_summary(self, result: Dict):
        """Print summary of candidate pool"""
        print("\n" + "="*60)
        print("JOURNAL CANDIDATE POOL SUMMARY")
        print("="*60)

        if result['status'] == 'error':
            print(f"❌ Error: {result['message']}")
            return

        print(f"Total references analyzed: {result['total_references']}")
        print(f"Unique journals found: {result['unique_journals']}")
        print(f"Candidate pool size: {len(result['candidates'])}")

        if result['analysis']['top_journal']:
            top = result['analysis']['top_journal']
            print(f"\nTop journal: {top[0]} (appears {top[1]} times)")

        print(f"\nTop 10 candidates:")
        print("-" * 60)
        print(f"{'Rank':<6} {'Journal Name':<40} {'Freq':<6}")
        print("-" * 60)

        for candidate in result['candidates'][:10]:
            print(f"{candidate['rank']:<6} {candidate['journal_name'][:38]:<40} {candidate['frequency']:<6}")

        print("\n" + "="*60)


def main():
    """Test with extracted paper data"""
    import sys

    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python journal_candidate_builder.py <paper_extraction.json> [output_candidates.json]")
        print("  where paper_extraction.json is output from document_extractor.py")
        sys.exit(1)

    # Load paper data
    extraction_file = sys.argv[1]
    with open(extraction_file, 'r', encoding='utf-8') as f:
        paper_data = json.load(f)

    # Build candidate pool
    builder = JournalCandidateBuilder()
    result = builder.build_candidate_pool(paper_data)

    # Print summary
    builder.print_summary(result)

    # Save results — optional 2nd arg lets run_pipeline.py specify the output path.
    if len(sys.argv) == 3:
        output_file = sys.argv[2]
    else:
        output_file = extraction_file.replace('.extraction.json', '.candidates.json')
    builder.save_candidate_pool(result, output_file)
    print(f"\n✅ Candidate pool saved to: {output_file}")


if __name__ == "__main__":
    main()