# Evaluation Experiment Protocol

This document defines the files and metadata needed for Xuan to evaluate each
retrieval/classification experiment consistently.

## Required Prediction Format

Every dev or test prediction file must be a JSON object keyed by claim id:

```json
{
  "claim-123": {
    "claim_label": "SUPPORTS",
    "evidences": ["evidence-1", "evidence-2"]
  }
}
```

Requirements:

- Include every claim from the evaluated split.
- Use exactly one of these labels:
  - `SUPPORTS`
  - `REFUTES`
  - `NOT_ENOUGH_INFO`
  - `DISPUTED`
- `evidences` must be a non-empty list of evidence IDs.
- Avoid duplicate evidence IDs.
- Do not hand-edit predictions after generation.

## Naming Convention

Use this naming pattern for development predictions:

```text
pred_dev_<retrieval>_<classifier>_top<k>_seed<seed>.json
```

Examples:

```text
pred_dev_bm25_supports_top5_seed42.json
pred_dev_bm25_dense_logreg_top5_seed42.json
pred_dev_bm25_dense_rrf_deberta_top5_seed42.json
```

For leaderboard submissions, the required file name inside the zip is:

```text
test-output.json
```

## Metadata Needed For Each Run

Please report the following with each prediction file:

| Field | Example |
| --- | --- |
| Run name | `bm25_dense_logreg_top5_seed42` |
| Prediction path | `evaluation_outputs/baselines/pred_dev_bm25_dense_logreg_top5_seed42.json` |
| Retrieval method | `BM25 + dense reranking` |
| Classifier | `logistic regression` |
| Top-k evidence | `5` |
| Candidate pool size | `100` |
| Random seed | `42` |
| Training data | `train only`, `train+dev`, or `diagnostic gold evidence` |
| Hardware/runtime | `Colab T4, 2h 10m` |
| Notes | Any failure mode, truncation, or known caveat |

## Evaluation Commands

Run official-compatible evaluation:

```bash
python evaluation/extended_eval.py \
  --predictions <prediction-json> \
  --groundtruth data/dev-claims.json \
  --run-name <run-name> \
  --output-dir evaluation/results/<run-name> \
  --experiment-log evaluation/results/experiment_log.csv \
  --plots-dir evaluation/results/<run-name>/plots
```

For ranked retrieval outputs, run top-k sweep:

```bash
python evaluation/topk_sweep.py \
  --predictions <prediction-json> \
  --groundtruth data/dev-claims.json \
  --min-k 1 \
  --max-k 10 \
  --output-csv evaluation/results/<run-name>/topk_sweep.csv
```

## Interpretation Rules

- The official diagnostic baseline is only for checking evaluation format.
- Gold-evidence classifier scores are diagnostic and must not be presented as
  end-to-end system scores.
- End-to-end scores must use retrieved evidence, not gold evidence.
- Test set predictions must be generated automatically by the submitted code.
- Do not manually inspect test labels or hand-edit test predictions.

