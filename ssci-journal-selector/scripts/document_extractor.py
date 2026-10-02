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
import chardet
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                encoding_info = chardet.detect(raw_data)
                encoding = encoding_info['encoding'] or 'utf-8'

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

    def _identify_sections_from_text(self, result: Dict):
        """Identify sections (abstract, methodology, references) from full text"""
        text = result['full_text']
        lines = text.split('\n')

        # Find abstract
        abstract_patterns = [
            r'abstract[:\s]*(.*?)(?=\n\n|introduction|1\s|$)',
            r'摘要[:\s]*(.*?)(?=\n\n|引言|1\s|$)'
        ]

        for pattern in abstract_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                result['abstract'] = match.group(1).strip()
                break

        # Find methodology/research method section
        method_patterns = [
            r'(methodology|method|methods|research method|研究方法|方法论)[:\s]*(.*?)(?=\n\n|results|discussion|conclusion|references|参考文献|$)',
        ]

        for pattern in method_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                result['methodology'] = match.group(2).strip()
                break

        # Find references
        ref_patterns = [
            r'(references|bibliography|参考文献|参考资料|引用文献)[:\s]*\n(.*?)(?=\n\n|appendix|附录|$)',
        ]

        for pattern in ref_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                ref_text = match.group(2).strip()
                # Split references into individual items
                ref_lines = [line.strip() for line in ref_text.split('\n')
                           if line.strip() and not line.strip().startswith('(')]
                result['references'] = ref_lines[:20]  # Limit to first 20 references
                break

    def extract(self, file_path: str) -> Dict:
        """Main extraction method - auto-detects format and extracts content"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_format = self.detect_file_format(file_path)
        if not file_format:
            raise ValueError(f"Unsupported file format. Supported formats: {self.supported_formats}")

        print(f"Detected format: {file_format}")

        if file_format == '.pdf':
            return self.extract_from_pdf(file_path)
        elif file_format == '.docx':
            return self.extract_from_docx(file_path)
        elif file_format == '.txt':
            return self.extract_from_txt(file_path)
        else:
            raise ValueError(f"Format {file_format} not implemented")

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