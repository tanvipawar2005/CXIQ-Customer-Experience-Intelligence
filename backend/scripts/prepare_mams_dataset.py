"""
prepare_mams_dataset.py

Downloads and cleans the MAMS-ATSA dataset for training CXIQ's aspect-
sentiment model (see scripts/train_absa_model.py).

Source: https://github.com/siat-nlp/MAMS-for-ABSA (official repository)
Paper: Jiang et al., 2019, "A Challenge Dataset and Effective Models for
Aspect-Based Sentiment Analysis", EMNLP 2019.

This script is idempotent — re-run it any time to refresh
backend/data/training/mams/{train,val,test}.csv from the official source.
The raw GitHub clone is downloaded to a temporary directory and removed
afterward; only the cleaned CSVs are kept in the repo.

Usage:
    python scripts/prepare_mams_dataset.py
"""
import os
import csv
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE_DIR, "data", "training", "mams")
REPO_URL = "https://github.com/siat-nlp/MAMS-for-ABSA.git"


def parse_split(raw_dir: str, split: str):
    tree = ET.parse(os.path.join(raw_dir, f"{split}.xml"))
    root = tree.getroot()
    rows = []
    for sentence in root.findall("sentence"):
        text = sentence.find("text").text
        aspect_terms = sentence.find("aspectTerms")
        if aspect_terms is None:
            continue
        for at in aspect_terms.findall("aspectTerm"):
            polarity = at.get("polarity")
            if polarity not in ("positive", "negative", "neutral"):
                continue  # skip "conflict"-labeled examples; not part of our 3-class scheme
            rows.append({
                "sentence": text,
                "aspect_term": at.get("term"),
                "from_idx": int(at.get("from")),
                "to_idx": int(at.get("to")),
                "polarity": polarity,
            })
    return rows


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        clone_dir = os.path.join(tmp, "MAMS-for-ABSA")
        print(f"Cloning {REPO_URL} ...")
        subprocess.run(["git", "clone", "--depth", "1", REPO_URL, clone_dir], check=True)

        raw_dir = os.path.join(clone_dir, "data", "MAMS-ATSA", "raw")
        total = 0
        for split, fname in [("train", "train.csv"), ("val", "val.csv"), ("test", "test.csv")]:
            rows = parse_split(raw_dir, split)
            total += len(rows)
            out_path = os.path.join(OUT_DIR, fname)
            with open(out_path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=["sentence", "aspect_term", "from_idx", "to_idx", "polarity"])
                w.writeheader()
                w.writerows(rows)
            print(f"  {split}: {len(rows)} aspect-term examples -> {out_path}")

    print(f"Done. {total} total labeled aspect-term examples.")
    print("Next: run `python scripts/train_absa_model.py` to (re)train the model.")


if __name__ == "__main__":
    main()
