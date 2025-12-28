from __future__ import annotations

import argparse
from pathlib import Path

from otus_gpt.dataset import build_prompt, format_example, load_jsonl


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fine-tune a tiny GPT-style model.")
    parser.add_argument("--base-model", default="sshleifer/tiny-gpt2")
    parser.add_argument("--data-path", type=Path, default=Path("data/train.jsonl"))
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/otus-gpt"))
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=5e-4)
    parser.add_argument("--max-length", type=int, default=128)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    import torch
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        DataCollatorForLanguageModeling,
        Trainer,
        TrainingArguments,
        set_seed,
    )

    set_seed(args.seed)
    examples = load_jsonl(args.data_path)
    texts = [format_example(example) for example in examples]
    tokenizer = AutoTokenizer.from_pretrained(args.base_model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    tokenized = tokenizer(
        texts,
        truncation=True,
        max_length=args.max_length,
        padding="max_length",
        return_tensors="pt",
    )

    class TokenizedDataset(torch.utils.data.Dataset):
        def __init__(self, batch):
            self.batch = batch

        def __len__(self) -> int:
            return self.batch["input_ids"].shape[0]

        def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
            return {
                "input_ids": self.batch["input_ids"][idx],
                "attention_mask": self.batch["attention_mask"][idx],
            }

    dataset = TokenizedDataset(tokenized)

    model = AutoModelForCausalLM.from_pretrained(args.base_model)
    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    training_args = TrainingArguments(
        output_dir=str(args.output_dir),
        per_device_train_batch_size=args.batch_size,
        num_train_epochs=args.epochs,
        learning_rate=args.learning_rate,
        logging_steps=10,
        save_strategy="no",
        report_to=[],
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        data_collator=data_collator,
    )

    trainer.train()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)

    sample_prompt = build_prompt("Explain OTUS homework workflow in one sentence.")
    inputs = tokenizer(sample_prompt, return_tensors="pt")
    outputs = model.generate(**inputs, max_new_tokens=20)
    print(tokenizer.decode(outputs[0], skip_special_tokens=True))


if __name__ == "__main__":
    main()
