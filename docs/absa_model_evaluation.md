# CXIQ Aspect-Sentiment Model — Evaluation Report

Generated: 2026-09-25 18:42 UTC

## Dataset

**MAMS-ATSA** (Aspect-Term Sentiment Analysis subset of the Multi-Aspect
Multi-Sentiment dataset). Jiang et al., 2019, EMNLP. Source:
https://github.com/siat-nlp/MAMS-for-ABSA (official repository, research use).
Sentences are drawn from restaurant reviews and are specifically curated so
most sentences contain multiple aspects with *different* sentiment polarities —
directly matching CXIQ's real-world failure case of "camera is great but battery
drains fast" type reviews.

| Split | Examples |
|---|---|
| Train | 11186 | 
| Validation | 1332 |
| Test | 1336 |

This is the dataset's own official split — not reshuffled or altered.

## Model

TF-IDF (1-3 grams) + Logistic Regression, trained on a **local context window**
(6 words on each side of the aspect term, located via the dataset's
character offsets) rather than the whole sentence — this is what lets the model
learn that the same word (e.g. "fast") can be positive or negative depending on
which aspect it's attached to, instead of a fixed per-word lexicon score.

## Hyperparameter selection (on validation split only)

| C | Validation Macro F1 |
|---|---|
| 0.5 | 0.6895 |
| 1.0 | 0.689 |
| 2.0 | 0.6937 |
| 4.0 | 0.6989 |
| 8.0 | 0.69 |

**Selected C = 4.0** (highest validation macro F1). The test split was not
used at any point during this selection.

## Final test-set results (held out, evaluated once)

| Metric | Value |
|---|---|
| Accuracy | 0.6826 |
| Precision Macro | 0.6726 |
| Recall Macro | 0.6788 |
| F1 Macro | 0.6751 |
| Precision Weighted | 0.6841 |
| Recall Weighted | 0.6826 |

Confusion matrix (rows = true label, columns = predicted label, order = ['negative', 'neutral', 'positive']):

```
[231, 67, 31]
[69, 432, 106]
[62, 89, 249]
```

Full classification report:

```
              precision    recall  f1-score   support

    negative       0.64      0.70      0.67       329
     neutral       0.73      0.71      0.72       607
    positive       0.65      0.62      0.63       400

    accuracy                           0.68      1336
   macro avg       0.67      0.68      0.68      1336
weighted avg       0.68      0.68      0.68      1336

```

## Honest limitations

- MAMS-ATSA is restaurant-domain text. CXIQ applies this model across other
  domains (electronics, e-commerce, hotel, etc.); the *linguistic* patterns it
  learned (e.g. how intensifiers and negation interact with nearby sentiment
  words) should transfer reasonably, but domain-specific vocabulary the model
  never saw in training (e.g. certain electronics jargon) will fall back to
  CXIQ's lexicon signal, which is blended in as a secondary signal.
- These are the only accuracy/F1 numbers reported anywhere in this project for
  this model, and they are exactly what this script measured on the held-out
  test split above — nothing here is estimated or rounded up.
