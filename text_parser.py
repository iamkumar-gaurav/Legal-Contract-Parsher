"""
text_parser.py
Cleans raw PDF text and parses it into a nested section → subsection → bullets structure.
"""

import re


# ── Patterns ───────────────────────────────────────────────────────────────────

REMOVAL_PATTERN = re.compile(
    r"\b\d{7,}\.\d{2}\b"
    r"|\b\d{5,}-\d{5,}\b"
    r"|\b\d+\s+Master Services Agreement\b"
    r"|Customer and Vendor Confidential Execution Version\b"
    r"|DocuSign Envelope ID: [A-Z0-9-]+\b"
    r"|Caterpillar File No\.: COM-\d+-\d+ CONFIDENTIAL.*"
    r"|Caterpillar Document No\.: \d+\b"
)

SECTION_PATTERN    = re.compile(r"^(\d+\.)\s+(.*)",     re.MULTILINE)
SUBSECTION_PATTERN = re.compile(r"^(\d+\.\d+)\s+(.*)", re.MULTILINE)
BULLET_PATTERN     = re.compile(r"^\(([a-z])\)\s+(.*)", re.MULTILINE)


# ── Public functions ───────────────────────────────────────────────────────────

def format_structure(text: str) -> str:
    """
    Remove boilerplate noise and re-indent lines by type:
      - Section headers  → no indent
      - Subsection lines → no indent
      - Bullet points    → 4-space indent
      - Body text        → 8-space indent
    """
    formatted = ""
    for line in text.splitlines():
        clean = REMOVAL_PATTERN.sub("", line).strip()
        if re.match(r"^\d+\.\s+[A-Z]", clean):
            formatted += f"\n{clean}\n"
        elif re.match(r"^\d+\.\d+\s+", clean):
            formatted += f"{clean}\n"
        elif re.match(r"^\(([a-z])\)\s+", clean):
            formatted += f"    {clean}\n"
        else:
            formatted += f"        {clean}\n"
    return formatted


def parse_to_dict(text: str) -> dict:
    """
    Parse structured text into:
      { "1. SECTION TITLE": { "1.1 Subsection": ["bullet", ...], ... }, ... }
    """
    content: dict = {}
    current_section: str | None = None
    current_section_number: str | None = None
    current_subsection: str | None = None
    current_subsection_number: str | None = None
    accumulated: str = ""

    def flush():
        if not accumulated:
            return
        sec_key = f"{current_section_number} {current_section}"
        if current_subsection:
            sub_key = f"{current_subsection_number} {current_subsection}"
            content[sec_key][sub_key].append(accumulated)
        else:
            content[sec_key].setdefault("No Subsection", []).append(accumulated)

    for line in text.splitlines():
        line = line.strip()

        sec_match = SECTION_PATTERN.match(line)
        if sec_match:
            flush()
            accumulated = ""
            current_section_number = sec_match.group(1)
            current_section = sec_match.group(2).strip()
            content[f"{current_section_number} {current_section}"] = {}
            current_subsection = None
            current_subsection_number = None
            continue

        sub_match = SUBSECTION_PATTERN.match(line)
        if sub_match and current_section:
            flush()
            accumulated = ""
            current_subsection_number = sub_match.group(1)
            current_subsection = sub_match.group(2).strip()
            sub_key = f"{current_subsection_number} {current_subsection}"
            content[f"{current_section_number} {current_section}"][sub_key] = []
            continue

        bullet_match = BULLET_PATTERN.match(line)
        if bullet_match:
            flush()
            accumulated = f"({bullet_match.group(1)}) {bullet_match.group(2).strip()}"
        elif current_section:
            accumulated += " " + line

    flush()
    return content
