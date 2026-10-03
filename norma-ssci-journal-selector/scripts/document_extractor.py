#!/usr/bin/env python3
"""
Multi-format Document Extractor for SSCI Journal Selection

Supports extraction of key information from:
- PDF files (.pdf) using PyPDF2 and pdfplumber
- DOCX files (.docx) using python-docx
- TXT files (.txt) with encoding detection

Extracts: title, abstract, methodology section, references, and full text
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# chardet 仅用于"猜一个编码作提示"，其后已有 utf-8 -> gbk -> gb2312 -> latin1 兜底链。
# 因此按软依赖处理：缺失时直接走兜底链，不应让整个脚本无法启动。
try:
    import chardet
    CHARDET_AVAILABLE = True
except ImportError:
    CHARDET_AVAILABLE = False

try:
    import PyPDF2
    PYPYPDF2_AVAILABLE = True
except ImportError:
    PYPYPDF2_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


class DocumentExtractor:
    """Multi-format document extractor for academic papers"""

    def __init__(self):
        self.supported_formats = ['.pdf', '.docx', '.txt']
        self.extraction_quality = 'high'  # high/medium/low

    def detect_file_format(self, file_path: str) -> Optional[str]:
        """Detect file format based on extension and content"""
        path = Path(file_path)

        # Check file extension
        if path.suffix.lower() in self.supported_formats:
            return path.suffix.lower()

        # Try to detect from MIME type or content if extension not reliable
        try:
            with open(file_path, 'rb') as f:
                header = f.read(1024)

            # PDF detection
            if header.startswith(b'%PDF'):
                return '.pdf'

            # DOCX detection (ZIP file with specific structure)
            if header.startswith(b'PK'):
                return '.docx'

        except Exception:
            pass

        return None

    def extract_from_pdf(self, file_path: str) -> Dict:
        """Extract text from PDF using multiple libraries"""
        result = {
            'title': '',
            'abstract': '',
            'methodology': '',
            'references': [],
            'full_text': '',
            'metadata': {
                'format': 'pdf',
                'extraction_quality': 'medium'
            }
        }

        # Try PyPDF2 first
        if PYPYPDF2_AVAILABLE:
            try:
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ''
                    for page in pdf_reader.pages:
                        text += page.extract_text() + '\n'

                    if text.strip():
                        result['full_text'] = text
                        result['metadata']['extraction_quality'] = 'high'
                        return result

            except Exception as e:
                print(f"PyPDF2 extraction failed: {e}")

        # Fallback to pdfplumber
        if PDFPLUMBER_AVAILABLE:
            try:
                with pdfplumber.open(file_path) as pdf:
                    text = ''
                    for page in pdf.pages:
                        text += page.extract_text() + '\n'

                    if text.strip():
                        result['full_text'] = text
                        result['metadata']['extraction_quality'] = 'high'
                        return result

            except Exception as e:
                print(f"pdfplumber extraction failed: {e}")

        # If both fail, try to read as text
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                result['full_text'] = f.read()
                result['metadata']['extraction_quality'] = 'low'
        except Exception as e:
            print(f"Fallback text extraction failed: {e}")

        return result

    def extract_from_docx(self, file_path: str) -> Dict:
        """Extract text from DOCX file"""
        result = {
            'title': '',
            'abstract': '',
            'methodology': '',
            'references': [],
            'full_text': '',
            'metadata': {
                'format': 'docx',
                'extraction_quality': 'high'
            }
        }

        if not DOCX_AVAILABLE:
            print("python-docx not available")
            return result

        try:
            doc = docx.Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]

            # Extract title (usually first paragraph or heading)
            for i, para in enumerate(paragraphs[:5]):
                if len(para) > 10 and len(para) < 200:
                    result['title'] = para
                    break

            # Build full text
            result['full_text'] = '\n'.join(paragraphs)

            # Try to identify sections
            self._identify_sections_from_text(result)

        except Exception as e:
            print(f"DOCX extraction failed: {e}")
            result['metadata']['extraction_quality'] = 'low'

        return result

    def extract_from_txt(self, file_path: str) -> Dict:
        """Extract text from TXT file with encoding detection"""
        result = {
            'title': '',
            'abstract': '',
            'methodology': '',
            'references': [],
            'full_text': '',
            'metadata': {
                'format': 'txt',
                'extraction_quality': 'medium'
            }
        }

        # Detect encoding
        try:
            encoding = 'utf-8'
            if CHARDET_AVAILABLE:
                with open(file_path, 'rb') as f:
                    raw_data = f.read()
                encoding_info = chardet.detect(raw_data)
                encoding = encoding_info['encoding'] or 'utf-8'
            else:
                result['metadata']['chardet_available'] = False

            # Try common encodings
            for enc in [encoding, 'utf-8', 'gbk', 'gb2312', 'latin1']:
                try:
                    with open(file_path, 'r', encoding=enc) as f:
                        text = f.read()
                        result['full_text'] = text
                        result['metadata']['encoding'] = enc

                        # Try to identify sections
                        self._identify_sections_from_text(result)

                        # Extract title (first line or first substantial line)
                        lines = text.split('\n')
                        for line in lines[:5]:
                            line = line.strip()
                            if len(line) > 10 and len(line) < 200:
                                result['title'] = line
                                break

                        result['metadata']['extraction_quality'] = 'high'
                        break

                except UnicodeDecodeError:
                    continue

        except Exception as e:
            print(f"TXT extraction failed: {e}")
            result['metadata']['extraction_quality'] = 'low'

        return result

    def _starts_new_bib_entry(self, line):
        """Whether a PDF-extracted line begins a new reference entry.

        In author-year styles an entry opens with the author list terminated by
        "Surname, A. 2019." — a period, the year, another period. Continuation
        lines (titled venue, DOI, bare URL) carry no such marker; note that
        "Proc. ACL 2024. doi:..." would false-positive on a bare year, so the
        preceding period is required.

        Calibrated on manuscript.pdf: matching this pattern across the whole
        line yields 118 starts, exactly the number of references cited in the
        body; restricting the search to the first 80/100 characters
        undercounts (107/116) because long author lists push the year past the
        window.
        """
        return bool(re.search(r'\.\s(19|20)\d{2}\.', line))

    def _looks_like_pdf_bib_block(self, lines_in):
        """Decide whether a blank-line-free block is a PDF-extracted reference
        list (one entry per line) rather than a single wrapped reference.

        PDF text extraction drops the blank lines that separate entries in
        Markdown/txt, and many venues (AAAI and friends) print
        "Author. Year. Title." instead of "[12] Author...", so neither the
        numbered-entry test nor the wrap test can tell the two cases apart.

        Empirical basis (manuscript.pdf, 228 lines): 60% of lines carry a
        4-digit year, median line length 117 chars, and wrapped URL/DOI
        fragments run short (<40 chars). Requiring a majority of year-bearing
        lines therefore separates the two shapes without guessing.
        """
        if len(lines_in) < 5:
            return False
        with_year = sum(1 for l in lines_in if re.search(r'(19|20)\d{2}', l))
        return with_year >= len(lines_in) * 0.4

    def _identify_sections_from_text(self, result: Dict):
        """Identify sections (abstract, methodology, references) from full text"""
        text = result['full_text']
        lines = text.split('\n')

        # Find abstract.
        # A bare "abstract" word also occurs in revision notes ("Abstract and
        # Section 1 ... are updated"), which yields a garbage abstract. Prefer an
        # explicit heading/bold label and require a plausible minimum length.
        head = re.search(
            r'^\s*(?:#{1,6}\s*|\*\*|__)?\s*(abstract|摘要)\s*(?:\*\*|__)?\s*[:：]?\s*$',
            text, re.IGNORECASE | re.MULTILINE)
        if head:
            tail = text[head.end():]
            stop = re.search(r'^\s*(?:#{1,6}\s+\S|\d+(?:\.\d+)*[.)]\s+\S)', tail,
                             re.MULTILINE)
            body = (tail[:stop.start()] if stop else tail).strip()
            if len(body) > 80:
                result['abstract'] = re.sub(r'\s+', ' ', body)[:2500]

        if not result.get('abstract'):
            # Run-in label: "Abstract: ..." or "**Abstract:** ..."
            m = re.search(
                r'(?:\*\*|__)?\s*(abstract|摘要)\s*(?:\*\*|__)?\s*[:：]\s*'
                r'([^\n]{80,2500})', text, re.IGNORECASE)
            if m:
                result['abstract'] = re.sub(r'\s+', ' ', m.group(2).strip())[:2500]

        # Find methodology/research method section.
        # Anchor on a heading line: a bare "method" occurring mid-paragraph (e.g.
        # "...research method. We ...") otherwise matches and then swallows the rest
        # of the document, which poisons the fingerprint.
        method_head = re.search(
            r'^\s*(?:#{1,6}\s*|\d+(?:\.\d+)*[.)]?\s+)'
            r'(?:\d+(?:\.\d+)*[.)]?\s+)?'
            r'(?:methodology|methods?|research method|materials and methods|'
            r'研究方法|方法论)\b[^\n]*$',
            text, re.IGNORECASE | re.MULTILINE)
        if method_head:
            tail = text[method_head.end():]
            stop = re.search(r'^\s*(?:#{1,6}\s+\S|\d+(?:\.\d+)*[.)]\s+\S)', tail,
                             re.MULTILINE)
            body = (tail[:stop.start()] if stop else tail).strip()
            if len(body) > 40:
                result['methodology'] = re.sub(r'\s+', ' ', body)[:1200]
        # Note: test the *value*, not key presence — result is pre-seeded with
        # methodology='' on every code path, so `not in result` is never true and
        # the inline fallback would be dead code.
        if not result.get('methodology'):
            # Fallback: an inline "Methodology: ..." run-in paragraph.
            m = re.search(
                r'(methodology|research method|研究方法|方法论)\s*[:：]\s*([^\n]{40,600})',
                text, re.IGNORECASE)
            if m:
                result['methodology'] = m.group(2).strip()[:1200]

        # Find references
        # 参考文献在 Markdown/txt 中常以空行分隔条目，若用 (?=\n\n) 截断只会抓到第 1 条。
        # 因此先定位标题行，再向后扫描到下一个章节标题为止，逐条累积。
        ref_header = re.search(
            r'^\s*(?:#{1,6}\s*)?(references|bibliography|参考文献|参考资料|引用文献)\s*[:：]?\s*$',
            text, re.IGNORECASE | re.MULTILINE)
        if ref_header:
            tail = text[ref_header.end():]
            # 截断到下一个 Markdown 章节标题
            stop = re.search(r'^\s*(?:#{1,6}\s+\S|appendix|附录|acknowledg)', tail,
                             re.IGNORECASE | re.MULTILINE)
            ref_text = tail[:stop.start()] if stop else tail

            # 以空行切分成块：一块可能是一条完整文献（含折行），也可能多行属于同一条
            blocks = [b.strip() for b in re.split(r'\n\s*\n', ref_text) if b.strip()]
            items = []
            for b in blocks:
                lines_in = [l.strip() for l in b.split('\n') if l.strip()]
                if len(lines_in) == 1:
                    if not lines_in[0].startswith('('):
                        items.append(lines_in[0])
                else:
                    # 多行块：若每行都像独立编号条目则逐条收，否则视为一条折行文献
                    numbered = sum(1 for l in lines_in if re.match(r'^\[?\d+[\].]', l))
                    if numbered >= max(1, len(lines_in) // 2):
                        items.extend(l for l in lines_in
                                     if not l.startswith('('))
                    elif self._looks_like_pdf_bib_block(lines_in):
                        # PDF 抽取的文本没有空行，一条文献会被拆成多行
                        # （作者行 / 标题折行 / 刊名 / DOI / URL），且不少期刊
                        # （AAAI 等）用「作者. 年份. 标题.」而非 [1] 编号制，
                        # 上面两条件都不满足，会把整段 200+ 行并成一条。
                        # 以「句点 + 年份 + 句点」作为条目起始标志，其余行回并。
                        for l in lines_in:
                            if l.startswith('('):
                                continue
                            if (items and not self._starts_new_bib_entry(l)):
                                items[-1] = items[-1] + ' ' + l
                            else:
                                items.append(l)
                    else:
                        items.append(' '.join(lines_in))
            # 过滤非文献条目：分隔线（---）、参考文献段之后的声明性文字
            # （如 "*Type declaration:* ..."），它们会被上面的分段逻辑一并吞进来。
            # PDF 还会把每页重复的刊眉/收稿行抽进来（"Journal of ..., Vol. 4,
            # Article 6. Publication date: ..."、"Received 2 October 2026"），
            # 这些行不含作者-年-标题结构，需按前缀剔除。
            items = [x for x in items
                     if x.strip() and not re.fullmatch(r'-{3,}|\*{3,}', x.strip())
                     and not x.lstrip('*_ ').lower().startswith(
                         ('type declaration', 'note:', '声明'))
                     and not re.match(
                         r'^(received|accepted|submitted|published|revised|'
                         r'journal of|proceedings of|transactions on|'
                         r'copyright|issn|isbn|this article|article '
                         r'information|publication date|vol\.|volume \d)',
                         x.lstrip('*_ '), re.IGNORECASE)]
            # PDF 每页重复的刊眉会产生同一条目的多个副本，按原文去重并保序。
            seen = set()
            deduped = []
            for x in items:
                key = re.sub(r'\s+', ' ', x.strip().lower())
                if key not in seen:
                    seen.add(key)
                    deduped.append(x)
            result['references'] = deduped[:200]

    def extract(self, file_path: str) -> Dict:
        """Main extraction method - auto-detects format and extracts content"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_format = self.detect_file_format(file_path)
        if not file_format:
            raise ValueError(f"Unsupported file format. Supported formats: {self.supported_formats}")

        print(f"Detected format: {file_format}")

        # All three branches must go through section identification; otherwise
        # title/abstract/methodology/references stay empty for PDF and DOCX
        # even though the full text was extracted correctly.
        if file_format == '.pdf':
            result = self.extract_from_pdf(file_path)
        elif file_format == '.docx':
            result = self.extract_from_docx(file_path)
        elif file_format == '.txt':
            result = self.extract_from_txt(file_path)
        else:
            raise ValueError(f"Format {file_format} not implemented")

        if result.get('full_text'):
            self._identify_sections_from_text(result)
        return result

    def save_extraction(self, extraction_result: Dict, output_path: str):
        """Save extraction result to JSON file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(extraction_result, f, ensure_ascii=False, indent=2)

    def print_summary(self, extraction_result: Dict):
        """Print a summary of the extraction results"""
        print("\n" + "="*50)
        print("DOCUMENT EXTRACTION SUMMARY")
        print("="*50)

        metadata = extraction_result['metadata']
        print(f"Format: {metadata['format'].upper()}")
        print(f"Extraction Quality: {metadata['extraction_quality'].upper()}")
        if 'encoding' in metadata:
            print(f"Encoding: {metadata['encoding']}")

        print(f"\nTitle: {extraction_result['title'][:100]}...")
        print(f"Abstract: {extraction_result['abstract'][:200]}...")
        print(f"Methodology: {extraction_result['methodology'][:200]}...")
        print(f"References found: {len(extraction_result['references'])}")
        print(f"Full text length: {len(extraction_result['full_text'])} characters")

        print("\n" + "="*50)


def main():
    """Command line interface"""
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python document_extractor.py <file_path> [output_json]")
        sys.exit(1)

    file_path = sys.argv[1]
    # Optional second arg lets run_pipeline.py specify the output path.
    # Default keeps backward-compatible behavior: <file_path>.extraction.json
    if len(sys.argv) == 3:
        output_path = sys.argv[2]
    else:
        output_path = file_path + '.extraction.json'

    extractor = DocumentExtractor()

    try:
        result = extractor.extract(file_path)
        extractor.print_summary(result)

        # Save to JSON
        extractor.save_extraction(result, output_path)
        print(f"\nExtraction saved to: {output_path}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()