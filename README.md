# COMP90042 Project 2026 - Group 68

This repository contains the notebook pipeline for the COMP90042 climate fact-checking project. The system retrieves evidence passages for each claim, predicts one of the four claim labels, and writes outputs in the official evaluation/submission format.

The current main pipeline is:

```text
data files
-> gold-evidence DeBERTa warm start
-> BM25 + dense retrieval candidate caches
-> weighted RRF retrieval tuning
-> retrieved-evidence DeBERTa tuning
-> dev baseline comparison and final model selection
-> optional test-output.json/test-output.zip generation
```

## Project Stage

The project is at the dev-set tuning and final submission generation stage. Local model selection is performed on `dev-claims.json`. The unlabelled `test-claims-unlabelled.json` split is used only to generate a Codabench submission file; no local test performance can be computed because the labels and gold evidence are hidden.

## Pipeline Stages

1. **Data processing**
   - Checks that assignment files are present.
   - Loads `train-claims.json`, `dev-claims.json`, `test-claims-unlabelled.json`, and `evidence.json`.
   - Builds gold-evidence supervised fine-tuning JSONL files under `processed/deberta_gold_sft`.

2. **Gold-evidence classifier training**
   - Fine-tunes `microsoft/deberta-v3-small` on claim text plus gold evidence.
   - Saves the warm-start checkpoint under `models/deberta_gold_sft/best`.

3. **Retrieval implementation**
   - Uses simple BM25 tokenization.
   - Uses `sentence-transformers/all-MiniLM-L6-v2` for dense retrieval.
   - Caches BM25 and dense top candidates under `processed/retrieval`.
   - Cross-encoder reranking is kept as an optional diagnostic path and is off by default.

4. **Weighted RRF tuning**
   - Searches weighted reciprocal rank fusion settings from cached BM25 and dense candidates.
   - Selects the best retrieval configuration on dev evidence F-score.
   - Writes `evaluation_outputs/tuning/best_retrieval_config.json`.

5. **Retrieved-evidence classifier tuning**
   - Generates retrieved-evidence SFT rows using the best weighted-RRF config.
   - Fine-tunes small DeBERTa variants from the gold-evidence checkpoint.
   - Selects the best variant by official dev harmonic mean.
   - Saves the selected checkpoint under `models/deberta_best_rrf_retrieved_sft/best`.

6. **Testing and evaluation**
   - Computes dev evidence F-score, claim classification accuracy, and harmonic mean.
   - Runs baseline comparisons for logistic regression and available DeBERTa checkpoints.
   - Writes the final model-selection table to `evaluation_outputs/tuning/final_model_selection.csv`.

7. **Final test submission generation**
   - Uses the selected weighted-RRF retrieval config and selected DeBERTa checkpoint.
   - Generates predictions for `test-claims-unlabelled.json`.
   - Writes `evaluation_outputs/submission/test-output.json`.
   - Packages `evaluation_outputs/submission/test-output.zip` with exactly one internal file named `test-output.json`.

## Important Artifacts

- `processed/retrieval/*candidate_cache.json`: cached BM25 and dense candidates for train/dev/test splits.
- `processed/deberta_gold_sft/*.jsonl`: gold-evidence classifier training rows.
- `processed/deberta_best_rrf_retrieved_sft/*.jsonl`: retrieved-evidence classifier tuning rows from the best weighted-RRF retriever.
- `evaluation_outputs/tuning/retrieval_tuning_summary.json`: full weighted-RRF tuning results.
- `evaluation_outputs/tuning/best_retrieval_config.json`: selected retrieval configuration.
- `evaluation_outputs/tuning/final_model_selection.csv`: ranked dev systems by harmonic mean.
- `models/deberta_best_rrf_retrieved_sft/best`: selected final classifier checkpoint.
- `evaluation_outputs/submission/test-output.zip`: Codabench-ready submission archive.

## How To Run In Colab

1. Upload the assignment data files into the notebook working directory:
   - `train-claims.json`
   - `dev-claims.json`
   - `test-claims-unlabelled.json`
   - `dev-claims-baseline.json`
   - `evidence.md`
   - `evidence.json` if already downloaded

2. For a quick structure check, start with smoke mode:
   ```python
   EXPERIMENT_MODE = "smoke"
   FORCE_REBUILD_CANDIDATE_CACHE = True
   ```
   Run the notebook top to bottom to verify structure, dependencies, and artifact writing.

3. Choose one of the configuration recipes below in the central config cell, then run the relevant notebook sections.

## Configuration Recipes

### Fresh First Full Run / Artifacts Missing

Use this when running in a new Colab session, or when `processed/`, `models/`, and `evaluation_outputs/` do not already contain the needed artifacts.

```python
EXPERIMENT_MODE = "full"
RUN_GOLD_CLASSIFIER_TRAINING = True
RUN_FULL_RETRIEVAL_PIPELINE = True
RUN_RETRIEVAL_TUNING = True
RUN_BEST_RRF_SFT_GENERATION = True
RUN_BEST_RRF_CLASSIFIER_TUNING = True
RUN_BASELINE_COMPARISON = True
RUN_TEST_PREDICTION_GENERATION = False
RUN_CROSS_ENCODER_STAGE = False
FORCE_REBUILD_CANDIDATE_CACHE = True
```

This builds full retrieval caches, tunes weighted RRF, trains retrieved-evidence DeBERTa variants, and writes dev evaluation outputs.

### Already Ran Once And Artifacts Still Exist

Use this when the slow artifacts are still available in the same Colab session or in your configured `ARTIFACT_ROOT`.

```python
EXPERIMENT_MODE = "full"
RUN_GOLD_CLASSIFIER_TRAINING = False
RUN_FULL_RETRIEVAL_PIPELINE = True
RUN_RETRIEVAL_TUNING = False
RUN_BEST_RRF_SFT_GENERATION = False
RUN_BEST_RRF_CLASSIFIER_TUNING = False
RUN_BASELINE_COMPARISON = True
RUN_TEST_PREDICTION_GENERATION = False
RUN_CROSS_ENCODER_STAGE = False
FORCE_REBUILD_CANDIDATE_CACHE = False
```

Required artifacts for this rerun recipe:

- `processed/retrieval/*candidate_cache.json`
- `evaluation_outputs/tuning/best_retrieval_config.json`
- `processed/deberta_best_rrf_retrieved_sft/*.jsonl`
- `models/deberta_best_rrf_retrieved_sft/best`

### Only Generate Final Test Submission

Use this after model selection when the artifacts above already exist and you only need the Codabench archive.

```python
EXPERIMENT_MODE = "full"
RUN_GOLD_CLASSIFIER_TRAINING = False
RUN_FULL_RETRIEVAL_PIPELINE = True
RUN_RETRIEVAL_TUNING = False
RUN_BEST_RRF_SFT_GENERATION = False
RUN_BEST_RRF_CLASSIFIER_TUNING = False
RUN_BASELINE_COMPARISON = False
RUN_TEST_PREDICTION_GENERATION = True
RUN_CROSS_ENCODER_STAGE = False
FORCE_REBUILD_CANDIDATE_CACHE = False
```

The notebook writes `evaluation_outputs/submission/test-output.zip`.

If Colab restarted and artifacts were not saved to Drive, treat the run as a fresh first full run. If using Drive persistence, set `ARTIFACT_ROOT` to the mounted Drive folder before the notebook creates output paths.

## Notes

- Test predictions are for leaderboard submission only. The notebook intentionally does not compute test metrics.
- The final decision criterion is highest dev harmonic mean.
- The main system should be interpreted as best weighted RRF plus retrieved-evidence DeBERTa unless a later dev run proves otherwise.
- Hard negatives are used only in the optional cross-encoder diagnostic path: they are high-ranked retrieved passages that are not gold evidence for the claim.
