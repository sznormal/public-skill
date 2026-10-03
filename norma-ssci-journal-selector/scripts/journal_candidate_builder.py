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

    def __init__(self, min_frequency: int = 1):
        # A journal cited only once is still a legitimate signal (a new or niche
        # venue is routinely cited once in a 100+ reference survey), so the default
        # keeps every hit and lets ranking do the filtering. Raise it to 2+ when
        # the reference list is large and noisy.
        self.min_frequency = min_frequency

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

        Strategy: prefer the explicit GB/T 7714 type marker, which states what the
        source actually is. Only [J] denotes a journal; [C] is a conference
        proceedings, [M] a book, [EB/OL] an online resource/preprint. Guessing the
        venue by position alone is unreliable (it silently mislabels proceedings
        and reports as journals), so marker-based matching runs first and the
        positional heuristics only serve unmarked references.
        """
        # 1) GB/T 7714 style: title[J]. Journal Name, vol...
        m = re.search(r'\[(?:J|Journal)\]\s*\.?\s*([^,.;]{3,90})', reference)
        if m:
            j = self._clean_journal(m.group(1))
            if j:
                return j

        # 2) Unmarked English author-year style (AAAI/IEEE/JAIR house styles):
        #    Author. Year. "Article Title." Journal Name, 59, 1. doi:...
        #    The venue sits after the closing quote, so none of the year-anchored
        #    patterns below can reach it. Conference papers use the same slot
        #    ("In:Proc. ACL") and are rejected later by _NON_JOURNAL.
        m = re.search(r'[”"]\s*,?\s*'
                      r'([A-Z][A-Za-z\s&,.\-]{5,70}?)'
                      r',\s*(?:\d+|vol|issue|pp)',
                      reference)
        if m:
            j = self._clean_journal(m.group(1))
            if j:
                return j

        # 3) Unmarked: "Journal Name, 2024" / "Journal Name. Year;Vol:Pages"
        for pattern in (
            r'\.\s*([A-Z][A-Za-z\s&,.\-]+?),\s*(?:vol\.?\s*)?\d{4}',
            r'([A-Z][A-Za-z\s&,.\-]+?)\s*,\s*(?:vol\.?\s*)?(?:19|20)\d{2}\s*[;:]',
            r'\.\s*([A-Z][A-Za-z\s&,.\-]+?)\.\s*(?:19|20)\d{2}\s*;',
        ):
            match = re.search(pattern, reference)
            if match:
                j = self._clean_journal(match.group(1))
                if j:
                    return j

        return ''

    # Sources that are venues-adjacent but not journals selectable as an SSCI/SCIE
    # target; used only to reject obvious false positives.
    _NON_JOURNAL = ('press', 'university', 'chapter', 'book', 'workshop', 'symposium',
                    'conference', 'proceedings', 'technical report', 'foundation',
                    'institute', 'laboratory', 'retrieved from', 'arxiv', 'preprint',
                    'editors', 'edition')

    def _clean_journal(self, raw: str) -> str:
        """Normalise whitespace/markup and reject obvious non-journals."""
        j = raw.strip().strip('*.,;: ')
        j = re.sub(r'\s+', ' ', j)
        j = j.replace('&', 'and')
        # "ACM Trans. Software Eng. ..." — a period after an abbreviation token
        # is not a field terminator, so the split below would truncate the name.
        j = re.sub(r'\b([A-Z][a-z]{1,9}|Trans|Proc|J|Int|Comput|Sci|Eng)\.\s+(?=[A-Z])',
                   r'\1 ', j)
        low = j.lower()
        # A journal name should not itself be a length/date string
        if len(j) < 6 or len(j) > 90:
            return ''
        if any(x in low for x in self._NON_JOURNAL):
            return ''
        if re.match(r'^(vol|no|issue|pp?|doi|isbn)\b', low):
            return ''
        # Reject a lone author-list fragment (many commas and initials, no words)
        if j.count(',') >= 3 and len(j.split()) > 8:
            return ''
        return j

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