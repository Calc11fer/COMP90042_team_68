# 2026-05-07 本地目录与团队 GitHub Repo 同步说明

团队 repo 已克隆到：

```text
team_repo/
```

远程地址：

```text
https://github.com/Calc11fer/COMP90042_team_68.git
```

当前分支：

```text
main
```

## 同步前的主要发现

- 团队 repo 是一个独立 Git repo，可以作为之后小组同步代码的主目录。
- 团队 repo 已包含核心数据文件和官方 `eval.py`。
- 团队 repo 原本没有本地已完成的 `evaluation/` 工具和会议材料。
- 团队 repo 没有 `data/evidence.json`，这是合理的，因为该文件很大且不应提交到 Git。
- 团队 repo 的 `.gitignore` 原本较弱，尚未忽略 `data/evidence.json`、模型 checkpoints、evaluation results 等大文件或生成文件。

## 已同步进团队 repo 的内容

已新增：

```text
evaluation/extended_eval.py
evaluation/topk_sweep.py
evaluation/README.md
evaluation/meeting_brief_2026-05-07.md
evaluation/repo_comparison_2026-05-07.md
```

已更新：

```text
.gitignore
requirements.txt
```

没有同步：

```text
evaluation/results/
evaluation/__pycache__/
data/evidence.json
```

这些是生成文件、缓存文件或大型本地数据文件，不应该提交到 GitHub。

## 两边一致的核心文件

以下文件内容一致：

```text
eval.py
data/dev-claims.json
data/train-claims.json
data/dev-claims-baseline.json
data/test-claims-unlabelled.json
data/evidence.md
```

这说明官方 evaluation 脚本和小型数据文件已经同步。

## 团队 repo 中仍需要注意的文件

```text
assignment.md
Group68__COMP90042_Project_2026.ipynb
backend/__init__.py
build.sh
requirements.txt
```

说明：

- `Group68__COMP90042_Project_2026.ipynb` 基本来自原始 `ipynb_template.ipynb`，只有 Colab metadata 的很小差异。
- `build.sh` 用于安装 `requirements.txt` 里的依赖。
- `backend/__init__.py` 目前是空文件，像是预留目录。
- `requirements.txt` 当前只加入了 evaluation 所需的最小依赖：`numpy` 和 `matplotlib`。后续 retrieval/classification 模块需要的依赖应该继续追加。

## `assignment.md` 需要注意的问题

团队 repo 的 `assignment.md` 大体来自官方 README，但对比本地原始 `README.md` 后发现有几处疑似误删或编辑错误：

```text
Submissions that rely solely...
```

在团队 repo 中变成：

```text
s that rely solely...
```

还有几处类似问题：

```text
project report and code submission
```

变成：

```text
project report and code
```

以及：

```text
After the project submission
```

变成：

```text
After the project
```

建议后续用本地 `README.md` 或官方 GitHub README 重新覆盖 `assignment.md`，或者直接把它改名为 `README.md` 并保持官方原文。

## 已验证命令

在 `team_repo/` 中已验证：

```bash
python -m py_compile evaluation/extended_eval.py evaluation/topk_sweep.py
python eval.py --predictions data/dev-claims-baseline.json --groundtruth data/dev-claims.json
python evaluation/extended_eval.py --predictions data/dev-claims-baseline.json --groundtruth data/dev-claims.json --run-name official_baseline --output-dir evaluation/results/official_baseline --experiment-log evaluation/results/experiment_log.csv --plots-dir evaluation/results/official_baseline/plots
python evaluation/topk_sweep.py --predictions data/dev-claims-baseline.json --groundtruth data/dev-claims.json --min-k 1 --max-k 6 --output-csv evaluation/results/official_baseline/topk_sweep.csv
```

官方 baseline 结果：

```text
Evidence Retrieval F-score (F)    = 0.3377705627705628
Claim Classification Accuracy (A) = 0.35064935064935066
Harmonic Mean of F and A          = 0.3440894901357093
```

