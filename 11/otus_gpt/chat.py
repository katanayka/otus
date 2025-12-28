from __future__ import annotations

import argparse
from pathlib import Path

from otus_gpt.dataset import build_prompt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a CLI bot for OTUS-GPT.")
    parser.add_argument("--model-path", type=Path, default=Path("artifacts/otus-gpt"))
    parser.add_argument("--base-model", default="sshleifer/tiny-gpt2")
    parser.add_argument("--max-new-tokens", type=int, default=80)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--prompt", default=None)
    return parser.parse_args()


def load_model(model_path: Path, base_model: str):
    from transformers import AutoModelForCausalLM, AutoTokenizer

    if model_path.exists():
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForCausalLM.from_pretrained(model_path)
    else:
        tokenizer = AutoTokenizer.from_pretrained(base_model)
        model = AutoModelForCausalLM.from_pretrained(base_model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    return model, tokenizer


def generate_reply(model, tokenizer, message: str, max_new_tokens: int, temperature: float) -> str:
    prompt = build_prompt(message)
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id,
    )
    text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return text[len(prompt) :].strip()


def run_chat(args: argparse.Namespace) -> None:
    model, tokenizer = load_model(args.model_path, args.base_model)
    if args.prompt:
        print(generate_reply(model, tokenizer, args.prompt, args.max_new_tokens, args.temperature))
        return

    print("OTUS-GPT ready. Type ':quit' to exit.")
    while True:
        try:
            message = input("> ").strip()
        except KeyboardInterrupt:
            print()
            break
        if not message:
            continue
        if message == ":quit":
            break
        reply = generate_reply(model, tokenizer, message, args.max_new_tokens, args.temperature)
        print(reply)


def main() -> None:
    args = parse_args()
    run_chat(args)


if __name__ == "__main__":
    main()
