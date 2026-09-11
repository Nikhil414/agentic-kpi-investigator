"""Explain deterministic investigation findings with Claude; no database access."""

from __future__ import annotations

import json
import os
from pathlib import Path

import anthropic

from investigator import EXPORTS


def run() -> str:
    findings_path = EXPORTS / "investigation_results.json"
    findings = json.loads(findings_path.read_text(encoding="utf-8"))
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    response = client.messages.create(
        model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
        max_tokens=2000,
        system=(
            "You are a finance operations investigator. Use only the supplied JSON. "
            "Do not invent facts, execute SQL, or recommend changing financial records. "
            "Return concise Markdown with: finding, evidence, likely explanation, "
            "recommended human review, confidence, and approval_required."
        ),
        messages=[
            {
                "role": "user",
                "content": "Explain these approved investigation findings:\n" + json.dumps(findings),
            }
        ],
    )
    text = "\n".join(
        block.text for block in response.content if block.type == "text")
    output = EXPORTS / "ai_investigation.md"
    output.write_text(text, encoding="utf-8")
    return text


if __name__ == "__main__":
    print(run())
