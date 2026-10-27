"""
train_sentiment_model.py

Standalone script to (re)train the TF-IDF + Logistic Regression sentiment
classifier from backend/data/training/sentiment_train.csv and save it to
backend/app/models/sentiment_lr.joblib.

This is the same training logic the backend runs automatically on first use
if no cached model file is found — this script just lets you retrain
deliberately (e.g. after editing the training data) and inspect accuracy.

Usage (from the backend/ directory, with the virtual environment active):
    python scripts/train_sentiment_model.py

To fine-tune with your own labeled data, replace or extend
data/training/sentiment_train.csv (columns: text,label where label is one
of positive/neutral/negative) and re-run this script.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAIN_DATA_PATH = os.path.join(BASE_DIR, "data", "training", "sentiment_train.csv")
MODEL_PATH = os.path.join(BASE_DIR, "app", "models", "sentiment_lr.joblib")


def main():
    df = pd.read_csv(TRAIN_DATA_PATH).dropna(subset=["text", "label"])
    X_train, X_test, y_train, y_test = train_test_split(
        df["text"].astype(str), df["label"].astype(str), test_size=0.15, random_state=42, stratify=df["label"]
    )

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_features=8000, sublinear_tf=True)),
        ("clf", LogisticRegression(max_iter=1000, C=4.0, class_weight="balanced")),
    ])
    pipeline.fit(X_train, y_train)

    preds = pipeline.predict(X_test)
    print("Held-out evaluation on the bundled dataset (NOT a substitute for real production data):")
    print(classification_report(y_test, preds))

    # refit on all data for the shipped model
    pipeline.fit(df["text"].astype(str), df["label"].astype(str))
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")


if __name__ == "__main__":
    main()
