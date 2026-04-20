"""
pdf_loader.py
Handles reading PDF files from local disk and extracting raw text.
"""

import os
from io import BytesIO
import pdfplumber

from config import PDF_FOLDER


def get_pdf_files(folder: str = PDF_FOLDER) -> list[str]:
    """Return full paths of all PDF files found in the given folder."""
    if not os.path.isdir(folder):
        raise FileNotFoundError(f"PDF folder not found: '{folder}'")

    files = [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.lower().endswith(".pdf")
    ]

    if not files:
        raise FileNotFoundError(f"No PDF files found in '{folder}'")

    return files


def select_pdfs(folder: str = PDF_FOLDER) -> list[str]:
    """
    Interactively prompt the user to select one or more PDFs from the folder.
    Returns a list of selected file paths.
    """
    all_files = get_pdf_files(folder)

    print(f"\n📂 PDFs found in: {folder}\n")
    for i, path in enumerate(all_files, 1):
        size_kb = os.path.getsize(path) / 1024
        print(f"  [{i}] {os.path.basename(path)}  ({size_kb:.1f} KB)")

    print(f"\n  [A] Process ALL PDFs")
    print(f"  [Q] Quit\n")

    while True:
        choice = input("Enter number(s) to select (e.g. 1 or 1,3,5): ").strip().upper()

        if choice == "Q":
            print("Exiting.")
            exit(0)

        if choice == "A":
            print(f"\n✅ Selected all {len(all_files)} PDF(s).")
            return all_files

        try:
            indices = [int(x.strip()) for x in choice.split(",")]
            selected = []
            for idx in indices:
                if 1 <= idx <= len(all_files):
                    selected.append(all_files[idx - 1])
                else:
                    print(f"  ⚠️  '{idx}' is out of range, skipping.")

            if not selected:
                print("  ❌ No valid selections. Try again.")
                continue

            print(f"\n✅ Selected {len(selected)} PDF(s):")
            for f in selected:
                print(f"   - {os.path.basename(f)}")
            return selected

        except ValueError:
            print("  ❌ Invalid input. Enter numbers like: 1  or  1,2,3")


def load_pdf(pdf_path: str) -> BytesIO:
    """Load a PDF from disk into an in-memory buffer."""
    with open(pdf_path, "rb") as f:
        buffer = BytesIO(f.read())
    return buffer


def extract_text(pdf_data: BytesIO) -> str:
    """Extract all text from a PDF buffer, page by page."""
    text = ""
    with pdfplumber.open(pdf_data) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text