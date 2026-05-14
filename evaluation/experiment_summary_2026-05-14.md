# Experiment Summary as of 2026-05-14

This summary records the current state of the team branches and the experiment
results that are already visible from committed notebooks or prediction files.
Numbers copied from notebook outputs should be treated as provisional until the
corresponding prediction JSON is exported and re-evaluated with
`evaluation/extended_eval.py`.

## Branch Status

| Branch | Latest commit | Owner/source | Status |
| --- | --- | --- | --- |
| `origin/main` | `7686696` | shared | Latest main; contains evaluation tooling |
| `origin/Retrieval` | `f398f47` | Peixue Wu | Retrieval work; branch is based on older main and should sync latest main before merge |
| `origin/Classification` | `fad0a52` | Calcifer account | Classification transformer work; contains evaluation tooling |

There are currently no open GitHub pull requests.

## Important Merge Risk

`origin/Retrieval` appears to be based on an older `main`. Directly merging it
may remove the `evaluation/` folder and weaken `.gitignore` / `requirements.txt`.
Before merging, the retrieval branch should merge or rebase latest `main`.

Suggested message to retrieval owner:

```text
Your Retrieval branch seems to be based on an older main and does not include
the current evaluation/ folder. Before merging, please merge or rebase the
latest main to avoid accidentally removing the evaluation tools.
```

## Verified Retrieval Prediction Files

The `origin/Retrieval` branch contains four dev prediction JSON files. These
files use `SUPPORTS` for every `claim_label`, so their accuracy is a majority
label baseline and the main useful signal is evidence retrieval F-score.

| Run | Retrieval | Classifier | Top-k | F | A | H |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| `dev_predictions_tfidf_k5.json` | TF-IDF | SUPPORTS-only | 5 | 0.0551 | 0.4416 | 0.0979 |
| `dev_predictions_bm25_k5.json` | BM25 | SUPPORTS-only | 5 | 0.1053 | 0.4416 | 0.1701 |
| `dev_predictions_tfidf_dense_k5.json` | TF-IDF + dense rerank | SUPPORTS-only | 5 | 0.1434 | 0.4416 | 0.2164 |
| `dev_predictions_bm25_dense_k5.json` | BM25 + dense rerank | SUPPORTS-only | 5 | 0.1452 | 0.4416 | 0.2185 |

Current retrieval trend:

- BM25 improves over TF-IDF.
- Dense reranking improves both sparse retrieval baselines.
- Best verified retrieval-only prediction so far is BM25 + dense rerank.

## Classification Branch Results Seen in Notebook Output

The `origin/Classification` branch contains transformer classifier work using
`microsoft/deberta-v3-small`, plus logistic regression baselines. These results
are visible in notebook output but should be re-run from exported prediction JSON
before being used as final report numbers.

| Run | Retrieval | Classifier | F | A | H | Caveat |
| --- | --- | --- | ---: | ---: | ---: | --- |
| gold-evidence DeBERTa diagnostic | Gold evidence | DeBERTa-v3-small | n/a | 0.6558 | n/a | Diagnostic only; not end-to-end |
| retrieved-evidence classifier diagnostic | Retrieved evidence | DeBERTa-v3-small | n/a | 0.4805 | n/a | Needs exported prediction JSON |
| `bm25_logistic_regression` | BM25 | logistic regression | 0.1053 | 0.4740 | 0.1723 | From notebook output |
| `bm25_dense_logistic_regression` | BM25 + dense | logistic regression | 0.1485 | 0.4870 | 0.2276 | From notebook output |
| `bm25_dense_rrf_logistic_regression` | BM25 + dense + RRF | logistic regression | 0.1511 | 0.4416 | 0.2251 | From notebook output |
| `bm25_dense_deberta_gold` | BM25 + dense | DeBERTa trained on gold evidence | 0.1485 | 0.2857 | 0.1955 | Diagnostic caveat |

Current interpretation:

- The strongest visible end-to-end score so far is approximately `H=0.2276`
  from BM25 + dense retrieval with logistic regression.
- Gold-evidence DeBERTa accuracy is much higher than end-to-end accuracy, which
  suggests retrieval quality is currently a major bottleneck.
- The final report should clearly separate gold-evidence diagnostic results
  from real end-to-end retrieved-evidence results.

## What Evaluation Needs Next

Classification owner should export dev prediction JSON files for:

```text
bm25_logistic_regression
bm25_dense_logistic_regression
bm25_dense_rrf_logistic_regression
bm25_dense_deberta_gold
```

Preferred location:

```text
evaluation_outputs/baselines/
```

Once exported, Xuan will run:

```bash
python evaluation/extended_eval.py --predictions <prediction-json> --groundtruth data/dev-claims.json ...
```

and update the official experiment log and report tables.

## Report Implications

Likely findings to validate:

- Retrieval is the current bottleneck.
- Dense reranking improves sparse retrieval.
- Better classifier accuracy does not automatically improve end-to-end score if
  retrieval evidence is weak or noisy.
- Gold-evidence results should be framed as an upper-bound or diagnostic
  classification experiment, not final system performance.

