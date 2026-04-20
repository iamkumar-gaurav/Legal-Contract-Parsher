import os

# ── Folders ────────────────────────────────────────────────────────────────────
PDF_FOLDER    = r"D:\contract_parser\inputPDF"      # Drop your PDF files here
OUTPUT_FOLDER = r"D:\contract_parser\Output"        # Formatted Excel files saved here

# ── OpenRouter API (Free) ──────────────────────────────────────────────────────
# Sign up at https://openrouter.ai → Keys → Create Key
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "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")   # paste your key here or set env var
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL   = "openai/gpt-oss-120b:free"

# ── Processing ─────────────────────────────────────────────────────────────────
CLAUSE_CHAR_LIMIT = 1000
MAX_TOKENS        = 4096
TEMPERATURE       = 0.2