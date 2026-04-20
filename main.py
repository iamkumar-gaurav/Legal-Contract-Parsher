"""
main.py
Entry point — orchestrates the full PDF → Excel pipeline.
Lets the user select which PDFs to process from the input folder.
Always overwrites previously created output files silently.
"""

import os
import json
import glob

from config import PDF_FOLDER, OUTPUT_FOLDER
from pdf_loader import select_pdfs, load_pdf, extract_text
from text_parser import format_structure, parse_to_dict
from openai_client import send_to_openai
from excel_exporter import export
from utils import extract_json_blocks, append_text_to_file, save_json_file, safe_remove

# Temp file paths
RAW_TXT_PATH  = "tmp_raw_output.txt"
JSON_TMP_PATH = "tmp_parsed.json"


def clear_previous_output(pdf_name: str) -> None:
    """Silently delete the output file for this PDF if it already exists."""
    existing = os.path.join(OUTPUT_FOLDER, f"formatted_{pdf_name}.xlsx")
    if os.path.exists(existing):
        os.remove(existing)
        print(f"  🔄 Replaced previous output: formatted_{pdf_name}.xlsx")


def process_pdf(pdf_path: str) -> None:
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    print(f"\n📄 Processing: {pdf_name}")

    # Remove old output for this PDF before starting
    clear_previous_output(pdf_name)

    # Step 1 — Extract text
    pdf_data = load_pdf(pdf_path)
    raw_text = extract_text(pdf_data)
    print("  ✅ Text extracted")

    # Step 2 — Structure & parse
    structured = format_structure(raw_text)
    content    = parse_to_dict(structured)
    print(f"  ✅ Parsed {len(content)} sections")

    # Step 3 — Send each subsection to Groq
    total_blocks = 0
    safe_remove(RAW_TXT_PATH)

    for section, subsections in content.items():
        if not isinstance(subsections, dict):
            continue
        for subsection, details in subsections.items():
            if subsection == "No Subsection":
                subsection = section
            if not details:
                continue

            bullets = "\n".join(f"- {item}" for item in details)
            prompt  = (
                f"section_name: {section}\n"
                f"subsection_name: {subsection}\n"
                f"bulletpoints:\n{bullets}\n"
            )

            response = send_to_openai(prompt)
            if not response:
                continue

            blocks = extract_json_blocks(response)
            if blocks:
                for block in blocks:
                    append_text_to_file(RAW_TXT_PATH, json.dumps(block))
                total_blocks += len(blocks)

    print(f"  ✅ Groq returned {total_blocks} JSON blocks")

    # Step 4 — Load blocks and export to Excel
    if not os.path.exists(RAW_TXT_PATH):
        print("  ⚠️  No output collected, skipping Excel export.")
        return

    all_data = []
    with open(RAW_TXT_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                all_data.append(json.loads(line))
            except Exception:
                pass

    save_json_file(JSON_TMP_PATH, all_data)

    # Step 5 — Export to formatted Excel
    output_path = export(all_data, pdf_name)
    print(f"  ✅ Saved → {output_path}")

    # Cleanup temp files
    safe_remove(RAW_TXT_PATH, JSON_TMP_PATH)


def main():
    print("=" * 50)
    print("  Contract Parser — Local PDF Mode")
    print("=" * 50)

    try:
        selected_pdfs = select_pdfs(PDF_FOLDER)
    except FileNotFoundError as e:
        print(f"\n❌ {e}")
        return

    for pdf_path in selected_pdfs:
        try:
            process_pdf(pdf_path)
        except Exception as e:
            print(f"\n❌ Failed to process {pdf_path}: {e}")

    print("\n✅ All done!")


if __name__ == "__main__":
    main()