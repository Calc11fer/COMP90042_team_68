# Evaluation Playbook

This folder contains helper material for the evaluation and visualisation part
of the COMP90042 project. The official script is still `eval.py`; the extended
script here adds diagnostics for experiment tracking and report writing.

## Minimum command for every dev experiment

```bash
python evaluation/extended_eval.py \
  --predictions data/dev-claims-baseline.json \
  --groundtruth data/dev-claims.json \
  --run-name official_baseline \
  --output-dir evaluation/results/official_baseline \
  --experiment-log evaluation/results/experiment_log.csv \
  --plots-dir evaluation/results/official_baseline/plots
```

## Top-k sweep for ranked evidence lists

When a retrieval system returns ranked evidence IDs, run:

```bash
python evaluation/topk_sweep.py \
  --predictions data/dev-claims-baseline.json \
  --groundtruth data/dev-claims.json \
  --min-k 1 \
  --max-k 6 \
  --output-csv evaluation/results/official_baseline/topk_sweep.csv
```

Use this to decide whether the final output should return top 3, top 5, top 6,
or another value. The best top-k should be chosen on dev only.

The prediction file must be a JSON object keyed by claim id:

```json
{
  "claim-123": {
    "claim_label": "SUPPORTS",
    "evidences": ["evidence-1", "evidence-2"]
  }
}
```

Allowed labels:

```text
SUPPORTS
REFUTES
NOT_ENOUGH_INFO
DISPUTED
```

## Outputs

For each run, the script can produce:

- `summary.json`: official-compatible metrics, strict metrics, and format checks.
- `per_claim_metrics.csv`: one row per dev claim for error analysis.
- `label_metrics.csv`: per-label classification and retrieval diagnostics.
- `confusion_matrix.csv`: gold label by predicted label counts.
- `plots/summary_metrics.png`: F, accuracy, and harmonic mean.
- `plots/label_accuracy.png`: label-wise classification accuracy.
- `plots/confusion_matrix.png`: visual confusion matrix.
- `experiment_log.csv`: one appended row per experiment.

## Metrics to report

The main official metrics are:

- Evidence retrieval F-score (`F`)
- Claim classification accuracy (`A`)
- Harmonic mean of F and A (`H_FA`)

For internal analysis, also track:

- Per-label classification precision, recall, and F1
- Per-label mean evidence F1
- Confusion matrix
- Missing or malformed prediction entries
- Empty evidence lists
- Duplicate evidence IDs

## Meeting checklist

Ask the retrieval owner to provide:

- A dev prediction JSON with retrieved evidence IDs for every dev claim.
- The retrieval method name, top-k value, and any reranking method.
- Whether the retrieval output is ranked and whether duplicates are possible.
- Candidate pool size, RRF constant if used, dense model name, and cross-encoder
  model name if used.
- Whether any label in the file is only a placeholder, for example all
  `SUPPORTS`.

Ask the classification owner to provide:

- A dev prediction JSON with `claim_label` for every dev claim.
- The exact input format used for classification.
- Model name, random seed, key hyperparameters, and training split.
- Whether the classifier used gold evidence, retrieved evidence, or both.
- Runtime/hardware, saved checkpoint location if any, and training logs.

Before adding a run to the report, classify it as one of:

- `format check`
- `retrieval-only`
- `classification diagnostic`
- `end-to-end`

Shared naming convention:

```text
pred_dev_<retrieval>_<classifier>_top<k>_seed<seed>.json
```

Example:

```text
pred_dev_bm25_roberta_top5_seed42.json
```

## Report-ready experiment table

Use one row per system variant:

| Run | Retrieval | Classifier | Top-k | F | A | H_FA | Notes |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| official_baseline | provided baseline | random | 6 | 0.338 | 0.351 | 0.344 | diagnostic only |

For report planning and interpretation rules, see
`evaluation/report_evaluation_notes.md`.
