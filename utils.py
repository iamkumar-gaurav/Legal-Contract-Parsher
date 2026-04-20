"""
utils.py
Shared utility functions for JSON extraction and file I/O.
"""

import json
import re
import os


def extract_json_blocks(raw_text: str) -> list[dict]:
    """
    Extract all top-level JSON objects from a raw string (e.g. GPT/Groq response).
    Handles nested structures like arrays and objects inside the block.
    """
    results = []
    i = 0
    text = raw_text.strip()

    while i < len(text):
        # Find next opening brace
        start = text.find('{', i)
        if start == -1:
            break

        # Walk forward tracking depth to find the matching closing brace
        depth = 0
        end = -1
        in_string = False
        escape_next = False

        for j in range(start, len(text)):
            ch = text[j]

            if escape_next:
                escape_next = False
                continue

            if ch == '\\' and in_string:
                escape_next = True
                continue

            if ch == '"':
                in_string = not in_string
                continue

            if in_string:
                continue

            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = j
                    break

        if end == -1:
            break

        block = text[start:end + 1]
        try:
            parsed = json.loads(block)
            if isinstance(parsed, dict):
                results.append(parsed)
        except json.JSONDecodeError as e:
            # Try cleaning common issues: trailing commas
            cleaned = re.sub(r',\s*([}\]])', r'\1', block)
            try:
                parsed = json.loads(cleaned)
                if isinstance(parsed, dict):
                    results.append(parsed)
            except json.JSONDecodeError:
                print(f"  ⚠️  Skipping malformed JSON block: {e}")

        i = end + 1

    return results


def append_text_to_file(path: str, text: str) -> None:
    """Append text to a file, creating it if it doesn't exist."""
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"\n{text}")


def load_json_file(path: str) -> list | dict:
    """Load and return JSON from a file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json_file(path: str, data: list | dict) -> None:
    """Save data as a formatted JSON file."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def safe_remove(*paths: str) -> None:
    """Delete files if they exist; silently skip missing ones."""
    for path in paths:
        if os.path.exists(path):
            try:
                os.remove(path)
            except PermissionError:
                print(f"  ⚠️  Could not delete {path} — file may be open.")