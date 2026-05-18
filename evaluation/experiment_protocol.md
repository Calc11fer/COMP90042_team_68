# Evaluation Experiment Protocol

This document defines the files and metadata needed for Xuan to evaluate each
retrieval/classification experiment consistently.

## Project Constraints To Enforce

These constraints come from the official project clarification posts and should
be checked before a result is used in the report or final submission:

- Use only open-source libraries, tools, and pretrained models.
- Do not use closed-source APIs or models.
- Do not use external datasets for training, tuning, calibration, or evaluation.
- Use only the provided train/dev data for model development.
- Treat `dev-claims.json` as the labelled development ground truth.
- Treat `dev-claims-baseline.json` only as an example prediction file, not as
  ground truth.
- Treat `evidence.json` as a mapping from evidence IDs to evidence text. Do not
  assume the numeric part of an evidence ID matches file order.
- The final system must be automatic, fixed, reproducible, and runnable in a
  free Google Colab environment.
- Do not include personal access tokens in submitted code. If a public model
  unexpectedly needs authentication, document the required setup instead.
- Saved checkpoints are acceptable only if the training procedure,
  configuration, and logs are documented well enough to reproduce comparable
  behaviour.
- The final report must describe the implemented system faithfully. If a score
  depends on gold evidence or another diagnostic-only setup, label it clearly.

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
| Result category | `end-to-end`, `retrieval-only`, `classification diagnostic`, or `format check` |
| Evidence available at inference | `retrieved evidence` or `gold evidence` |
| Open-source model names | `microsoft/deberta-v3-small`, `cross-encoder/ms-marco-MiniLM-L6-v2` |
| Saved checkpoint/log path | `checkpoints/deberta_seed42`, `wandb run URL`, or `none` |
| Hardware/runtime | `Colab T4, 2h 10m` |
| Notes | Any failure mode, truncation, or known caveat |

## Result Categories

Use these categories consistently in filenames, tables, and report text:

- `format check`: official baseline or toy output used only to verify that the
  evaluator and JSON format work.
- `retrieval-only`: evidence IDs are meaningful, but labels may be placeholders
  such as all `SUPPORTS`. These runs can support retrieval analysis, not final
  classification claims.
- `classification diagnostic`: the classifier is evaluated with gold evidence
  or another non-test-time input. These scores estimate classifier capacity, but
  are not end-to-end results.
- `end-to-end`: both evidence IDs and labels are produced automatically using
  information available at inference time. Only this category can be presented
  as final system performance.

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
- If a retrieval file uses a placeholder label such as all `SUPPORTS`, report
  its evidence F-score but describe classification accuracy as a placeholder or
  majority-label baseline.
- Retrieval and classification modules may be tuned separately, but the final
  reported pipeline must be fixed before test prediction generation.
- If dev is used for model selection or calibration, describe the selected
  configuration as dev-selected rather than as an untouched test estimate.
- Test set predictions must be generated automatically by the submitted code.
- Do not manually inspect test labels or hand-edit test predictions.
