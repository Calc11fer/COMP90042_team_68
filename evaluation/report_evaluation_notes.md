# Report Evaluation Notes

This note converts the current Miro experiment plan and official Ed
clarifications into report-ready evaluation structure.

## Evaluation Scope

The official task score combines two components:

- Evidence retrieval F-score (`F`): whether predicted evidence IDs match the
  gold evidence IDs.
- Claim classification accuracy (`A`): whether the predicted claim label is
  correct.
- Harmonic mean (`H_FA`): the official combined score balancing retrieval and
  classification.

The report should separate stage-level diagnostics from end-to-end results. A
classifier evaluated with gold evidence can show whether the classification
model is capable, but it is not a final system score because gold evidence is
not available at test time.

## Planned Experiment Progression

The report can frame the system development as a staged ablation:

| Stage | Retrieval component | Classification component | Purpose |
| --- | --- | --- | --- |
| Format baseline | Provided baseline predictions | Provided baseline labels | Verify evaluator and JSON format |
| Lexical retrieval | TF-IDF or BM25 | Placeholder or simple baseline | Establish interpretable retrieval baselines |
| Hybrid retrieval | BM25/TF-IDF plus dense retrieval | Placeholder or simple baseline | Test whether semantic retrieval improves evidence coverage |
| Rank fusion | Reciprocal Rank Fusion | Same classifier as previous stage | Test whether lexical and dense rankings are complementary |
| Reranking | Optional cross-encoder | Same classifier as previous stage | Test whether joint claim-evidence scoring improves top-k evidence |
| Classification diagnostic | Gold or retrieved evidence | Fine-tuned transformer classifier | Estimate classification capacity under different evidence quality |
| Final pipeline | Selected automatic retriever | Selected automatic classifier | Report final end-to-end dev and optional test performance |

## Main Tables To Produce

Use these tables when final prediction files are available:

1. Main development results:

| Run | Retrieval | Reranker | Classifier | Top-k | F | A | H_FA | Result type |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| official_baseline | provided | none | provided | 6 | 0.338 | 0.351 | 0.344 | format check |
| final_system | TBD | TBD | TBD | TBD | TBD | TBD | TBD | end-to-end |

2. Retrieval ablation:

| Retrieval | Candidate k | Final top-k | RRF k | Reranker | F | Notes |
| --- | ---: | ---: | ---: | --- | ---: | --- |
| TF-IDF | TBD | TBD | - | none | TBD | lexical baseline |
| BM25 | TBD | TBD | - | none | TBD | lexical baseline |
| BM25 + dense + RRF | TBD | TBD | TBD | none | TBD | hybrid retrieval |
| BM25 + dense + RRF + cross-encoder | TBD | TBD | TBD | cross-encoder | TBD | reranked retrieval |

3. Classification evidence-quality diagnostic:

| Classifier | Evidence source | Top-k | Accuracy | Macro F1 | Notes |
| --- | --- | ---: | ---: | ---: | --- |
| DeBERTa v3 small | gold evidence | - | TBD | TBD | diagnostic upper bound |
| DeBERTa v3 small | retrieved evidence | TBD | TBD | TBD | realistic inference setting |

## Figures To Produce

Recommended figures:

- Compact pipeline diagram: claim preprocessing, lexical/dense retrieval, RRF,
  optional cross-encoder reranking, transformer classifier, final prediction.
- Top-k sweep plot: evidence F-score and harmonic mean as top-k changes.
- Confusion matrix: final classifier predictions on the dev set.

The pipeline figure should describe our implemented system. Avoid including a
generation/RAG step unless the final system actually generates text.

## Report Interpretation Rules

- Retrieval-only files with all labels set to `SUPPORTS` are valid for evidence
  F-score analysis, but the classification accuracy is only a placeholder or
  majority-label baseline.
- Gold-evidence classifier scores should be described as diagnostic capacity
  estimates, not final end-to-end performance.
- If retrieved evidence improves classification but not official evidence
  F-score, explain that official retrieval scoring requires exact gold evidence
  ID matches.
- If dev is used to select top-k, model, thresholds, or calibration, state that
  the final configuration was selected on dev.
- Test leaderboard results, if used, should be final evaluation only and should
  not drive repeated model selection.

## Minimum Evidence For Each Reported Run

For every result included in the report, keep:

- Prediction JSON path.
- Exact evaluation command.
- Result category.
- Retrieval method, candidate pool size, final top-k, and RRF constant if used.
- Classifier model name and key hyperparameters.
- Training split and whether gold evidence was used.
- Random seed.
- Runtime/hardware.
- Training logs or checkpoint notes if a saved checkpoint is used.
