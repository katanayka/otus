# Homework 11: OTUS-GPT

## Structure
- `otus_gpt/` - training and chat scripts
- `data/train.jsonl` - small prompt/response dataset (legacy)
- `penguin_finetune.ipynb` - end-to-end penguin Wikipedia fine-tuning
- `LLM13_296721_4becbf-296721-7d2837.ipynb` - lecture notebook (reference)

## Requirements
- Python 3.10-3.12
- GPU is optional (CPU works for the tiny model)

Note: PyTorch and tokenizers wheels are not available for Python 3.13+ yet. If you
are on 3.13+, use a 3.12 virtualenv (for example, `py -3.12 -m venv .venv`) or
install the build dependencies (Rust + MSVC) and compile from source.

## Setup
Run from the `11/` directory.

```bash
python -m venv .venv
.venv\\Scripts\\activate
python -m pip install -r requirements.txt
python -m pip install -r dev_requirements.txt
```

If torch was skipped (Python 3.13+), install it separately:
```bash
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
```

If tokenizers fails to build from source, install Rust and MSVC build tools:
- Rust: https://rustup.rs/ (restart shell, `cargo --version` should work)
- Visual Studio Build Tools: C++ build tools

## Train (fine-tune) via notebook
Open `penguin_finetune.ipynb` and run the cells in order. The notebook downloads
Wikipedia pages about penguins, trains GPT-2, and saves the model under
`artifacts/penguin-gpt`.

## Train (fine-tune) via CLI
```bash
python -m otus_gpt.train \
  --base-model sshleifer/tiny-gpt2 \
  --data-path data/train.jsonl \
  --output-dir artifacts/otus-gpt \
  --epochs 5 \
  --batch-size 8 \
  --learning-rate 5e-4
```

## Run the bot
```bash
python -m otus_gpt.chat --model-path artifacts/penguin-gpt
```

You can also run a single prompt:
```bash
python -m otus_gpt.chat --prompt "Explain OTUS homework workflow."
```

## Lint
```bash
ruff check .
```

## Pre-commit
```bash
pre-commit install -c .pre-commit-config.yaml
pre-commit run --all-files
```

## CI
GitHub Actions runs ruff and dataset tests on every push/PR that touches `11/**`.
