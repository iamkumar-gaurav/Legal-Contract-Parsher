"""
openai_client.py
Sends parsed contract subsections to OpenRouter and returns structured JSON.
OpenRouter uses the same OpenAI-compatible API — just a different base URL and key.
"""

import re
import requests

from config import OPENROUTER_API_KEY, OPENROUTER_API_URL, OPENROUTER_MODEL, MAX_TOKENS, TEMPERATURE

HEADERS = {
    "Content-Type":  "application/json",
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "HTTP-Referer":  "https://contract-parser.local",   # required by OpenRouter
    "X-Title":       "Contract Parser",                 # shows up in OpenRouter dashboard
}

SYSTEM_PROMPT = '''You are an AI assistant that parses legal contract subsections into JSON format.

Return ONLY a raw JSON object. No markdown, no code fences, no explanation.

Use exactly this structure:
{
    "Major Area": "MSA",
    "Reference": "<first-level section header only, e.g. 1. BACKGROUND>",
    "Task Description": "<brief description of what this clause requires>",
    "Manager": "TBD",
    "Owner": "NA",
    "Status": "Green",
    "Risk": "<Low | Medium | High>",
    "Frequency": "<Per Contract | As Required | Weekly | Bi-Monthly | Monthly | Quarterly | Semi-Annually | Annually>",
    "Category": "<one of: Service Management | Operations | Service Levels | Deliverable | DR/BCP | Contract Administration | Reports | 3rd Party Vendor | Security | PMO | Asset Management | Governance | Cross Functional | Services | Event Monitoring | Software Licensing | Transition | Financials | Termination | Infrastructure | Metrics | Backup/Tape/Restore | Management | Financial Implications | SLA Reports | Patch Management | Audits | Legal Compliance | BPO | Applications | Resources | Transformation | Warranty/Licensing | Documentation | Customer Task | Audit Compliance | New Business | Survey>",
    "Clause Text": ["<subsection name e.g. 1.1 Background>", "<(a) first bullet>", "<(b) second bullet>"],
    "Notes": "",
    "Assigned To": "NA"
}

Return only ONE JSON object per subsection. No extra text outside the JSON.'''


def strip_markdown(text: str) -> str:
    """Remove markdown code fences and extra whitespace."""
    text = re.sub(r'```(?:json)?', '', text)
    return text.strip()


def send_to_openai(prompt_text: str) -> str | None:
    """
    Send a subsection prompt to OpenRouter.
    Returns cleaned response text, or None on failure.
    """
    if not OPENROUTER_API_KEY:
        raise EnvironmentError(
            "OPENROUTER_API_KEY is not set.\n"
            "Get a free key at https://openrouter.ai then set it in config.py"
        )

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt_text},
        ],
        "max_tokens":        MAX_TOKENS,
        "temperature":       TEMPERATURE,
        "top_p":             0.95,
        "frequency_penalty": 0,
        "presence_penalty":  0,
    }

    try:
        response = requests.post(OPENROUTER_API_URL, headers=HEADERS, json=payload, timeout=60)
        response.raise_for_status()
        raw = response.json()["choices"][0]["message"]["content"]
        return strip_markdown(raw)
    except requests.exceptions.HTTPError:
        print(f"  ⚠️  OpenRouter error {response.status_code}: {response.text}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"  ⚠️  Request failed: {e}")
        return None