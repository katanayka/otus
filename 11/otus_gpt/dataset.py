from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

CHAT_TEMPLATE = "### User:\n{prompt}\n\n### Assistant:\n{response}\n"


@dataclass(frozen=True)
class PromptExample:
    prompt: str
    response: str


def load_jsonl(path: Path) -> list[PromptExample]:
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    examples: list[PromptExample] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        item = json.loads(raw)
        if "prompt" not in item or "response" not in item:
            raise ValueError(f"Missing prompt/response at line {line_number}")
        examples.append(PromptExample(prompt=str(item["prompt"]).strip(), response=str(item["response"]).strip()))
    if not examples:
        raise ValueError("Dataset is empty")
    return examples


def format_example(example: PromptExample) -> str:
    if not example.prompt or not example.response:
        raise ValueError("Prompt and response must be non-empty")
    return CHAT_TEMPLATE.format(prompt=example.prompt, response=example.response)


def build_prompt(message: str) -> str:
    cleaned = message.strip()
    if not cleaned:
        raise ValueError("Message must be non-empty")
    return CHAT_TEMPLATE.format(prompt=cleaned, response="")
