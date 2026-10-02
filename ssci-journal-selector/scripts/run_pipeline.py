#!/usr/bin/env python3
"""
One-click pipeline runner for SSCI Journal Selector MVP

Runs all steps automatically: extraction → candidates → excel → report
Supports both automated and interactive modes.
"""

import sys
import os
import subprocess
import argparse
import json
from pathlib import Path

def validate_file(file_path: str) -> bool:
    """Validate input file exists and has supported format."""
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found: {file_path}")
        return False

    supported_formats = ['.pdf', '.docx', '.txt']
    file_ext = Path(file_path).suffix.lower()

    if file_ext not in supported_formats:
        print(f"❌ Error: Unsupported file format: {file_ext}")
        print(f"Supported formats: {', '.join(supported_formats)}")
        return False

    return True

def run_step(step_name: str, script_path: Path, *args) -> tuple[bool, str]:
    """Run a pipeline step with error handling."""
    print(f"\n{'-'*70}")
    print(f"STEP {step_name}: {script_path.name}...")
    print(f"{'-'*70}")

    if not script_path.exists():
        error_msg = f"Script not found: {script_path}"
        print(f"❌ {error_msg}")
        return False, error_msg

    try:
        cmd = [sys.executable, str(script_path)] + list(args)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode != 0:
            error_msg = f"Step failed: {result.stderr}"
            print(f"❌ {error_msg}")
            return False, error_msg

        print(result.stdout)
        return True, "Success"

    except subprocess.TimeoutExpired:
        error_msg = f"Step timed out after 5 minutes"
        print(f"❌ {error_msg}")
        return False, error_msg
    except Exception as e:
        error_msg = f"Step error: {str(e)}"
        print(f"❌ {error_msg}")
        return False, error_msg

def run_pipeline(document_path: str, output_dir: str = None, mode: str = "full"):
    """
    Run complete MVP pipeline on a document.

    Args:
        document_path: Path to PDF/DOCX/TXT file
        output_dir: Output directory (default: same as input file)
        mode: Pipeline mode ("full", "fingerprint", "candidates", "evaluation", "auto")
    """
    print("\n" + "="*70)
    print("SSCI JOURNAL SELECTOR - MVP PIPELINE")
    print("="*70)
    print(f"\nInput document: {document_path}")
    print(f"Mode: {mode}")

    if mode == "full":
        print("\n" + "!"*70)
        print("NOTICE: 'full' mode now STOPS after fingerprint extraction (Gate G1).")
        print("Review and confirm the 6-line fingerprint before building candidates.")
        print("After confirming, re-run with --mode candidates (or 'auto' to finish).")
        print("!"*70 + "\n")

    # Validate input file
    if not validate_file(document_path):
        return False

    # Set output directory
    if output_dir is None:
        output_dir = Path(document_path).parent
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

    # Get script directory
    script_dir = Path(__file__).parent

    # Track generated files
    generated_files = []

    try:
        # Step 1: Extract document (if needed)
        extraction_json = output_dir / f"{Path(document_path).stem}_extraction.json"

        if mode in ["full", "fingerprint", "candidates", "evaluation", "auto"]:
            success, msg = run_step("1", script_dir / "document_extractor.py", document_path, str(extraction_json))
            if not success:
                return False
            generated_files.append(extraction_json)

        # 🛑 Gate G1: 'full' mode stops here so the user can review/confirm the
        # 6-line fingerprint before any downstream step builds on it.

        # Step 2: Build candidate pool (skip in 'full' mode — gated at G1)
        candidates_json = output_dir / f"{Path(document_path).stem}_candidates.json"

        if mode in ["candidates", "evaluation", "auto"]:
            if not extraction_json.exists():
                print("❌ Extraction file not found for candidate building")
                return False

            success, msg = run_step("2", script_dir / "journal_candidate_builder.py", str(extraction_json), str(candidates_json))
            if not success:
                return False
            generated_files.append(candidates_json)

        # Step 3: Generate Excel evaluation table (if needed)
        excel_file = output_dir / f"{Path(document_path).stem}_evaluation.csv"

        if mode in ["evaluation", "auto"]:
            if not candidates_json.exists():
                print("❌ Candidates file not found for evaluation")
                return False

            success, msg = run_step("3", script_dir / "excel_generator.py", str(candidates_json), str(excel_file))
            if not success:
                return False
            generated_files.append(excel_file)

        # Step 4: Generate comprehensive report (if needed)
        report_file = output_dir / f"{Path(document_path).stem}_report.md"

        if mode in ["evaluation", "auto"]:
            if not (extraction_json.exists() and candidates_json.exists()):
                print("❌ Required files not found for report generation")
                return False

            success, msg = run_step("4", script_dir / "report_generator.py", str(extraction_json), str(candidates_json), str(report_file))
            if not success:
                return False
            generated_files.append(report_file)

        # Success summary
        print("\n" + "="*70)
        print("PIPELINE COMPLETE! ✅")
        print("="*70)

        print("\nGenerated files:")
        for i, file_path in enumerate(generated_files, 1):
            print(f"  {i}. 📄 {file_path.name}")

        print("\nNext steps:")
        if mode == "full":
            print("  🛑 GATE G1: Review the 6-line fingerprint in the extraction JSON")
            print("     1. Correct it if needed (edit JSON or use Prompt 1.2 with your LLM)")
            print("     2. Confirm the fingerprint is accurate")
            print("  🔄 Then run: --mode candidates  (or --mode auto to finish end-to-end)")
        elif mode == "auto":
            print("  1. 📊 Open the Excel CSV file to review journal candidates")
            print("  2. 📝 Read the Markdown report for detailed analysis")
            print("  3. 🔍 Use LLM prompts for detailed journal evaluation")
            print("  4. 📋 Design your 3-tier submission strategy")
            print("  ⚠️  'auto' assumes the fingerprint was ALREADY confirmed (G1) and the candidate pool reviewed (G2)")
        elif mode == "fingerprint":
            print("  1. 📄 Review extracted paper fingerprint")
            print("  2. 🔄 Run with --mode candidates to build journal pool")
        elif mode == "candidates":
            print("  1. 📊 Review candidate journals (Gate G2: add/remove before evaluation)")
            print("  2. 🔄 Run with --mode evaluation for full analysis")
        elif mode == "evaluation":
            print("  1. 📈 Review evaluation table and report")
            print("  2. 📋 Plan your submission strategy")

        print("\nResources:")
        resources_dir = script_dir.parent / "references"
        print(f"  - 📚 {resources_dir / 'decision-framework.md'} - Decision logic")
        print(f"  - 📊 {resources_dir / 'matching-score-template.md'} - Scoring rubrics")
        print(f"  - 🤖 {resources_dir / 'prompt-templates.md'} - LLM prompts")
        print(f"  - 📖 {script_dir.parent.parent / 'SKILL.md'} - Complete guide")

        print("\n" + "="*70)
        return True

    except Exception as e:
        print(f"❌ Pipeline error: {str(e)}")
        return False

def interactive_mode():
    """Run interactive guided mode."""
    print("\n" + "="*70)
    print("SSCI JOURNAL SELECTOR - INTERACTIVE MODE")
    print("="*70)

    print("\nWelcome to the interactive journal selection assistant!")
    print("I'll guide you through the complete process step by step.\n")

    # Get input file
    while True:
        doc_path = input("📄 Enter path to your paper (PDF/DOCX/TXT): ").strip()
        if validate_file(doc_path):
            break
        print("Please try again with a valid file path.\n")

    # Choose mode
    print("\n🔧 Choose analysis mode:")
    print("  1. Full analysis (extract + fingerprint, then STOP for Gate G1 confirmation)")
    print("  2. Fingerprint only (extract paper characteristics)")
    print("  3. Build candidates (from existing fingerprint)")
    print("  4. Generate evaluation (from existing candidates)")
    print("  5. Auto finish (assumes fingerprint/candidates already confirmed)")

    mode_map = {
        "1": "full",
        "2": "fingerprint",
        "3": "candidates",
        "4": "evaluation",
        "5": "auto"
    }

    while True:
        choice = input("\nEnter choice (1-5): ").strip()
        if choice in mode_map:
            mode = mode_map[choice]
            break
        print("Please enter 1, 2, 3, 4, or 5")

    # Get output directory
    output_dir = input("\n📁 Output directory (press Enter for current directory): ").strip()
    if not output_dir:
        output_dir = None

    print(f"\n🚀 Starting analysis in {mode} mode...")
    return run_pipeline(doc_path, output_dir, mode)

def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="SSCI Journal Selector Pipeline - Automated journal selection and evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full analysis (extract + fingerprint, then STOP at Gate G1 for confirmation)
  python run_pipeline.py paper.pdf

  # Specific mode
  python run_pipeline.py paper.pdf --mode fingerprint

  # After confirming the fingerprint (Gate G1), build candidates
  python run_pipeline.py paper.pdf --mode candidates

  # After reviewing candidates (Gate G2), finish end-to-end
  python run_pipeline.py paper.pdf --mode auto

  # Custom output directory
  python run_pipeline.py paper.pdf --output results/

  # Interactive mode
  python run_pipeline.py --interactive

  # Show help
  python run_pipeline.py --help
        """
    )

    parser.add_argument(
        "document_path",
        nargs="?",
        help="Path to input document (PDF/DOCX/TXT)"
    )

    parser.add_argument(
        "--mode",
        choices=["full", "fingerprint", "candidates", "evaluation", "auto"],
        default="full",
        help="Pipeline mode (default: full — stops at Gate G1 for fingerprint confirmation)"
    )

    parser.add_argument(
        "--output",
        "-o",
        help="Output directory (default: same as input file)"
    )

    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Run in interactive mode"
    )

    parser.add_argument(
        "--version",
        action="version",
        version="SSCI Journal Selector v1.1.0 (confirmation gates G1/G2)"
    )

    args = parser.parse_args()

    # Handle interactive mode
    if args.interactive:
        success = interactive_mode()
        sys.exit(0 if success else 1)

    # Handle file-based mode
    if not args.document_path:
        print("❌ Error: Document path is required")
        print("\nUse --interactive for guided mode or provide a document path")
        parser.print_help()
        sys.exit(1)

    success = run_pipeline(args.document_path, args.output, args.mode)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()