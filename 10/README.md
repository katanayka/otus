# Homework 10: Logistic Regression

This assignment finishes a logistic regression classifier implemented with
stochastic gradient descent and applies it to Amazon review summaries.

## Structure
- `homework/homework.ipynb` - notebook with data prep and experiments
- `homework/dmia/classifiers/logistic_regression.py` - model implementation
- `homework/data/train.csv` - training data

## Setup
Run from the `10/` directory.

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m pip install -r dev_requirements.txt
```

## Run the notebook
Install Jupyter if needed:
```bash
python -m pip install jupyter
```

Start Jupyter:
```bash
python -m jupyter lab
```

Open `homework/homework.ipynb` and run cells in order.

## Lint
```bash
ruff check .
```

## Pre-commit
```bash
pre-commit install
pre-commit run --all-files
```

## CI
GitHub Actions runs ruff on every push/PR that touches `10/**`.
