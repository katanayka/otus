from pathlib import Path

import pytest

from otus_gpt.dataset import PromptExample, build_prompt, format_example, load_jsonl


def test_format_example_requires_text() -> None:
    with pytest.raises(ValueError):
        format_example(PromptExample(prompt="", response="hi"))


def test_build_prompt_format() -> None:
    prompt = build_prompt("Hello")
    assert "### User:" in prompt
    assert "Hello" in prompt
    assert "### Assistant:" in prompt


def test_load_jsonl(tmp_path: Path) -> None:
    data = tmp_path / "data.jsonl"
    data.write_text('{"prompt": "Ping", "response": "Pong"}\n', encoding="utf-8")
    examples = load_jsonl(data)
    assert examples[0].prompt == "Ping"
    assert examples[0].response == "Pong"
