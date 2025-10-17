"""
prepare_dataset.py

This module combines multiple financial sentiment datasets into a single,
clean dataset ready for model training. It supports:

    1. Financial PhraseBank
    2. FiQA 2018
    3. Forex News Dataset

Outputs:
    - A cleaned CSV at src/model_building/training_data/cleaned_dataset.csv
"""

import json
import logging
from pathlib import Path
from typing import Literal

import pandas as pd

# -------------------------------------------------------------------------
# Configuration and Logging
# -------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

CURRENT_FILE = Path(__file__).resolve()
CURRENT_DIR = CURRENT_FILE.parent
TRAINING_DATA_DIRECTORY = CURRENT_DIR / "training_data"

# Input dataset paths
PHRASEBANK_DIR = TRAINING_DATA_DIRECTORY / "financial_phrasebank_dataset"
FIQA_DIR = TRAINING_DATA_DIRECTORY / "fiqa_2018_task_1_dataset"
FOREX_FILE = (
    TRAINING_DATA_DIRECTORY / "forex_news_dataset/sentiment_annotated_with_texts.csv"
)

PHRASEBANK_FILES = [
    PHRASEBANK_DIR / "Sentences_50Agree.txt",
    PHRASEBANK_DIR / "Sentences_66Agree.txt",
    PHRASEBANK_DIR / "Sentences_75Agree.txt",
    PHRASEBANK_DIR / "Sentences_AllAgree.txt",
]

FIQA_FILES = [
    FIQA_DIR / "task1_headline_ABSA_train.json",
    FIQA_DIR / "task1_post_ABSA_train.json",
]

LABEL_MAP_3CLASS = {"negative": 0, "neutral": 1, "positive": 2}
NEUTRAL_THRESHOLD = 0.1
OUTPUT_FILE = TRAINING_DATA_DIRECTORY / "cleaned_dataset.csv"

COLUMNS = ["text", "label", "source", "original_label"]


# -------------------------------------------------------------------------
# Dataset Preparation Functions
# -------------------------------------------------------------------------
def prepare_phrasebank_data() -> pd.DataFrame:
    """Loads and processes all versions of the Financial PhraseBank dataset."""

    def _process_file(dataset_path: Path) -> pd.DataFrame:
        lines = []
        with open(dataset_path, "r", encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f, 1):
                parts = line.strip().split("@")
                if len(parts) != 2:
                    logging.warning(f"Malformed line {i} in {dataset_path}")
                    continue
                text, label_str = parts
                text = _clean_text(text)
                label_str = label_str.strip().lower()
                label = LABEL_MAP_3CLASS.get(label_str)
                if label is None:
                    logging.warning(f"Unknown label '{label_str}' in {dataset_path}")
                    continue
                lines.append(
                    {
                        "text": text,
                        "label": label,
                        "source": str(dataset_path),
                        "original_label": label_str,
                    }
                )
        return pd.DataFrame(lines, columns=COLUMNS)

    logging.info("Processing Financial PhraseBank datasets...")
    dfs = [_process_file(p) for p in PHRASEBANK_FILES if p.exists()]
    return pd.concat(dfs, ignore_index=True)


def prepare_fiqa_data() -> pd.DataFrame:
    """Loads and processes the FiQA 2018 datasets."""

    def _process_file(dataset_path: Path) -> pd.DataFrame:
        with open(dataset_path, "r", encoding="utf-8", errors="replace") as f:
            json_data = json.load(f)

        lines = []
        for _, data in json_data.items():
            text = _clean_text(data.get("sentence", ""))
            score_str = str(data["info"][0]["sentiment_score"]).strip()
            try:
                score = float(score_str)
            except ValueError:
                logging.warning(
                    f"Invalid sentiment score '{score_str}' in {dataset_path}"
                )
                continue

            if abs(score) < NEUTRAL_THRESHOLD:
                label = 1
            elif score > 0:
                label = 2
            else:
                label = 0

            lines.append(
                {
                    "text": text,
                    "label": label,
                    "source": str(dataset_path),
                    "original_label": score_str,
                }
            )
        return pd.DataFrame(lines, columns=COLUMNS)

    logging.info("Processing FiQA datasets...")
    dfs = [_process_file(p) for p in FIQA_FILES if p.exists()]
    return pd.concat(dfs, ignore_index=True)


def prepare_forex_data() -> pd.DataFrame:
    """Loads and processes the Forex news dataset."""
    logging.info("Processing Forex dataset...")
    df = pd.read_csv(FOREX_FILE, encoding="utf-8", on_bad_lines="skip")

    df["text"] = df["text"].astype(str).apply(_clean_text)
    df["true_sentiment"] = df["true_sentiment"].str.lower().str.strip()
    df["label"] = df["true_sentiment"].map(LABEL_MAP_3CLASS)
    df["original_label"] = df["true_sentiment"]
    df["source"] = str(FOREX_FILE)

    df = df.drop(columns=["true_sentiment"])
    return df[COLUMNS]


# -------------------------------------------------------------------------
# Main
# -------------------------------------------------------------------------
def main() -> None:
    """Combines and saves all datasets into one CSV."""
    logging.info("Preparing combined dataset...")

    phrasebank = prepare_phrasebank_data()
    fiqa = prepare_fiqa_data()
    forex = prepare_forex_data()

    combined_df = pd.concat([phrasebank, fiqa, forex], ignore_index=True)
    combined_df.dropna(subset=["text", "label"], inplace=True)

    combined_df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
    logging.info(f"Combined dataset saved to {OUTPUT_FILE}")
    logging.info(f"Total samples: {len(combined_df):,}")


if __name__ == "__main__":
    main()
