# 2026-05-07 Evaluation 会议简报

## 已完成内容

- 已确认 `data/evidence.json` 现在存在于本地目录中。
- 已使用官方 `eval.py` 跑通 dev baseline。
- 已新增 `evaluation/extended_eval.py`，用于更细的 evaluation 和错误分析。
- 已在 `evaluation/results/official_baseline/` 下生成 baseline 的分析结果。

## 官方 baseline 在 dev set 上的结果

| Run | Evidence F | Accuracy | H_FA |
| --- | ---: | ---: | ---: |
| official_baseline | 0.3378 | 0.3506 | 0.3441 |

这个 baseline 只适合作为诊断参考。它的 label 是随机生成的，evidence 也包含部分人工构造的 gold evidence，因此不能把它当成真正有意义的建模 baseline。

## Baseline 的 label 级别诊断

| Label | Gold count | Label accuracy | Mean evidence F1 |
| --- | ---: | ---: | ---: |
| SUPPORTS | 68 | 0.3382 | 0.3161 |
| REFUTES | 27 | 0.4074 | 0.2383 |
| NOT_ENOUGH_INFO | 41 | 0.3902 | 0.4612 |
| DISPUTED | 18 | 0.2222 | 0.2875 |

## Baseline 的 top-k sweep

官方提供的 baseline 每条 claim 都返回 6 个 predicted evidence IDs。如果我们把这个 evidence list 截断成不同的 top-k，dev set 上的 retrieval 分数变化如下：

| Top-k | Evidence F | Accuracy | H_FA |
| ---: | ---: | ---: | ---: |
| 1 | 0.1303 | 0.3506 | 0.1900 |
| 2 | 0.2213 | 0.3506 | 0.2714 |
| 3 | 0.2677 | 0.3506 | 0.3036 |
| 4 | 0.2938 | 0.3506 | 0.3197 |
| 5 | 0.3147 | 0.3506 | 0.3317 |
| 6 | 0.3378 | 0.3506 | 0.3441 |

对于我们自己的 retrieval model，最终输出几个 evidence 不应该直接假设为 6，而应该在 dev set 上通过 top-k sweep 来决定。

## 需要队友提供的 prediction 格式

每个 dev prediction 文件都应该是一个以 claim id 为 key 的 JSON object：

```json
{
  "claim-123": {
    "claim_label": "SUPPORTS",
    "evidences": ["evidence-1", "evidence-2"]
  }
}
```

每一条 dev claim 都必须包含：

- 一个 `claim_label`
- 一个非空的 `evidences` list
- 尽量不要包含重复的 evidence IDs

## 建议统一的文件命名方式

```text
pred_dev_<retrieval>_<classifier>_top<k>_seed<seed>.json
```

例如：

```text
pred_dev_bm25_majority_top5_seed42.json
pred_dev_bm25_transformer_top5_seed42.json
pred_dev_bm25_rerank_transformer_top5_seed42.json
```

这样后面做实验对比和报告表格会清楚很多。

## 我需要 retrieval 负责人提供什么

- 第一版 dev prediction JSON，即使只是 TF-IDF 或 BM25 baseline 也可以。
- 使用的 top-k 数值。
- 返回的 evidence list 是否是按相关性排序的。
- 如果有 retrieval 或 reranking score，也可以一起保留，方便后续错误分析。

## 我需要 classification 负责人提供什么

- 第一版包含所有 dev claims 的 label prediction JSON。
- 明确说明 classifier 的输入格式，例如 `claim [SEP] top-k evidence`。
- 使用的模型、random seed 和主要 hyperparameters。
- 说明分类阶段使用的是 gold evidence 还是 retrieved evidence。

## 我可以为每个实验提供的 evaluation 输出

只要队友给我一个 dev prediction JSON，我就可以输出：

- 官方 F / Accuracy / H_FA
- prediction 格式检查
- per-claim 错误分析 CSV
- per-label classification metrics
- confusion matrix
- 报告中可直接使用的 PNG 图表
- 自动追加一行到 `evaluation/results/experiment_log.csv`

## 今天会议可以重点讨论的问题

- 当前系统的主要瓶颈是 retrieval 还是 classification？
- top-k 取多少在 dev set 上效果最好？
- 哪些 labels 最容易被混淆？
- classifier 使用 retrieved evidence 时，相比使用 gold evidence 会下降多少？
- reranking 是否显著提升 evidence F-score，值得增加复杂度吗？

