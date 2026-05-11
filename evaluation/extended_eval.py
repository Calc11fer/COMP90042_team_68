#!/usr/bin/env python3
"""Extended evaluator for the COMP90042 fact-checking project.

This script keeps the official metrics from eval.py, then adds the diagnostics
needed for experiment tracking, report tables, and error analysis.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LABELS = ("SUPPORTS", "REFUTES", "NOT_ENOUGH_INFO", "DISPUTED")
INVALID_LABEL = "__INVALID_OR_MISSING__"
EVIDENCE_ID_RE = re.compile(r"^evidence-\d+$")


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object keyed by claim id.")
    return data


def harmonic_mean(f_score: float, accuracy: float) -> float:
    if f_score == 0.0 and accuracy == 0.0:
        return 0.0
    return (2 * f_score * accuracy) / (f_score + accuracy)


def evidence_scores(
    predicted_evidences: Any, gold_evidences: list[str]
) -> tuple[int, float, float, float]:
    evidence_correct = 0
    evidence_recall = 0.0
    evidence_precision = 0.0
    evidence_fscore = 0.0

    if isinstance(predicted_evidences, list) and len(predicted_evidences) > 0:
        predicted_set = set(predicted_evidences)
        for gold_ev in gold_evidences:
            if gold_ev in predicted_set:
                evidence_correct += 1

        if evidence_correct > 0:
            evidence_recall = float(evidence_correct) / len(gold_evidences)
            evidence_precision = float(evidence_correct) / len(predicted_evidences)
            evidence_fscore = (
                2 * evidence_precision * evidence_recall
            ) / (evidence_precision + evidence_recall)

    return evidence_correct, evidence_precision, evidence_recall, evidence_fscore


def score_claim(claim_id: str, gold: dict[str, Any], pred: Any) -> dict[str, Any]:
    pred_is_object = isinstance(pred, dict)
    has_required_fields = (
        pred_is_object and "claim_label" in pred and "evidences" in pred
    )
    predicted_label = pred.get("claim_label") if pred_is_object else None
    predicted_evidences = pred.get("evidences") if pred_is_object else None
    predicted_evidence_count = (
        len(predicted_evidences) if isinstance(predicted_evidences, list) else 0
    )
    duplicate_evidence_count = (
        len(predicted_evidences) - len(set(predicted_evidences))
        if isinstance(predicted_evidences, list)
        else 0
    )
    invalid_evidence_id_count = (
        sum(
            1
            for ev in predicted_evidences
            if not isinstance(ev, str) or EVIDENCE_ID_RE.match(ev) is None
        )
        if isinstance(predicted_evidences, list)
        else 0
    )

    gold_evidences = gold["evidences"]
    correct_evidence, precision, recall, evidence_f1 = evidence_scores(
        predicted_evidences, gold_evidences
    )

    return {
        "claim_id": claim_id,
        "gold_label": gold["claim_label"],
        "predicted_label": predicted_label or "",
        "classification_correct": int(predicted_label == gold["claim_label"]),
        "gold_evidence_count": len(gold_evidences),
        "predicted_evidence_count": predicted_evidence_count,
        "correct_evidence_count": correct_evidence,
        "evidence_precision": precision,
        "evidence_recall": recall,
        "evidence_f1": evidence_f1,
        "has_required_fields": int(has_required_fields),
        "valid_label": int(predicted_label in LABELS),
        "evidences_is_list": int(isinstance(predicted_evidences, list)),
        "evidences_non_empty": int(
            isinstance(predicted_evidences, list) and len(predicted_evidences) > 0
        ),
        "duplicate_evidence_count": duplicate_evidence_count,
        "invalid_evidence_id_count": invalid_evidence_id_count,
    }


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def aggregate(rows: list[dict[str, Any]]) -> dict[str, float | int]:
    f_score = mean([float(row["evidence_f1"]) for row in rows])
    accuracy = mean([float(row["classification_correct"]) for row in rows])
    return {
        "num_claims": len(rows),
        "evidence_f_score": f_score,
        "classification_accuracy": accuracy,
        "harmonic_mean": harmonic_mean(f_score, accuracy),
    }


def build_label_metrics(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for label in LABELS:
        gold_rows = [row for row in rows if row["gold_label"] == label]
        pred_rows = [row for row in rows if row["predicted_label"] == label]
        true_positives = sum(
            1
            for row in rows
            if row["gold_label"] == label and row["predicted_label"] == label
        )
        precision = true_positives / len(pred_rows) if pred_rows else 0.0
        recall = true_positives / len(gold_rows) if gold_rows else 0.0
        f1 = (
            (2 * precision * recall) / (precision + recall)
            if precision + recall > 0
            else 0.0
        )
        output.append(
            {
                "label": label,
                "gold_count": len(gold_rows),
                "predicted_count": len(pred_rows),
                "classification_precision": precision,
                "classification_recall": recall,
                "classification_f1": f1,
                "label_accuracy": recall,
                "mean_evidence_f1": mean(
                    [float(row["evidence_f1"]) for row in gold_rows]
                ),
            }
        )
    return output


def build_confusion_matrix(rows: list[dict[str, Any]]) -> dict[str, Counter[str]]:
    matrix: dict[str, Counter[str]] = {label: Counter() for label in LABELS}
    for row in rows:
        predicted = row["predicted_label"]
        if predicted not in LABELS:
            predicted = INVALID_LABEL
        matrix[row["gold_label"]][predicted] += 1
    return matrix


def collect_format_issues(
    groundtruth: dict[str, Any], predictions: dict[str, Any], rows: list[dict[str, Any]]
) -> dict[str, Any]:
    gold_ids = set(groundtruth)
    pred_ids = set(predictions)
    issue_rows = [
        row
        for row in rows
        if not row["has_required_fields"]
        or not row["valid_label"]
        or not row["evidences_is_list"]
        or not row["evidences_non_empty"]
        or row["duplicate_evidence_count"] > 0
        or row["invalid_evidence_id_count"] > 0
    ]
    return {
        "missing_claims": sorted(gold_ids - pred_ids),
        "extra_prediction_claims": sorted(pred_ids - gold_ids),
        "missing_or_invalid_required_fields": sum(
            1 for row in rows if not row["has_required_fields"]
        ),
        "invalid_labels": sum(1 for row in rows if not row["valid_label"]),
        "invalid_evidence_lists": sum(1 for row in rows if not row["evidences_is_list"]),
        "empty_evidence_lists": sum(1 for row in rows if not row["evidences_non_empty"]),
        "duplicate_evidence_entries": sum(
            int(row["duplicate_evidence_count"]) for row in rows
        ),
        "invalid_evidence_id_entries": sum(
            int(row["invalid_evidence_id_count"]) for row in rows
        ),
        "sample_problem_claims": [row["claim_id"] for row in issue_rows[:20]],
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_confusion_csv(path: Path, matrix: dict[str, Counter[str]]) -> None:
    columns = list(LABELS) + [INVALID_LABEL]
    rows = []
    for gold_label in LABELS:
        row = {"gold_label": gold_label}
        for predicted_label in columns:
            row[predicted_label] = matrix[gold_label][predicted_label]
        rows.append(row)
    write_csv(path, rows, ["gold_label"] + columns)


def append_experiment_log(path: Path, run_name: str, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "timestamp_utc",
        "run_name",
        "predictions",
        "groundtruth",
        "official_num_claims",
        "official_evidence_f_score",
        "official_classification_accuracy",
        "official_harmonic_mean",
        "strict_num_claims",
        "strict_evidence_f_score",
        "strict_classification_accuracy",
        "strict_harmonic_mean",
        "notes",
    ]
    row = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "run_name": run_name,
        "predictions": summary["files"]["predictions"],
        "groundtruth": summary["files"]["groundtruth"],
        "official_num_claims": summary["official_metrics"]["num_claims"],
        "official_evidence_f_score": summary["official_metrics"][
            "evidence_f_score"
        ],
        "official_classification_accuracy": summary["official_metrics"][
            "classification_accuracy"
        ],
        "official_harmonic_mean": summary["official_metrics"]["harmonic_mean"],
        "strict_num_claims": summary["strict_metrics"]["num_claims"],
        "strict_evidence_f_score": summary["strict_metrics"]["evidence_f_score"],
        "strict_classification_accuracy": summary["strict_metrics"][
            "classification_accuracy"
        ],
        "strict_harmonic_mean": summary["strict_metrics"]["harmonic_mean"],
        "notes": "",
    }
    file_exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def maybe_write_plots(
    plots_dir: Path,
    summary: dict[str, Any],
    label_metrics: list[dict[str, Any]],
    confusion_matrix: dict[str, Counter[str]],
) -> None:
    plots_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(plots_dir / ".matplotlib"))
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib is not available; skipping plots.")
        return

    metric_names = ["evidence_f_score", "classification_accuracy", "harmonic_mean"]
    metric_labels = ["Evidence F1", "Accuracy", "H Mean"]
    values = [summary["official_metrics"][name] for name in metric_names]
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(metric_labels, values, color=["#4c78a8", "#59a14f", "#f28e2b"])
    ax.set_ylim(0, 1)
    ax.set_ylabel("Score")
    ax.set_title(summary["run_name"])
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 0.02,
            f"{value:.3f}",
            ha="center",
            va="bottom",
        )
    fig.tight_layout()
    fig.savefig(plots_dir / "summary_metrics.png", dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4))
    labels = [row["label"] for row in label_metrics]
    acc_values = [row["label_accuracy"] for row in label_metrics]
    bars = ax.bar(labels, acc_values, color="#4c78a8")
    ax.set_ylim(0, 1)
    ax.set_ylabel("Accuracy")
    ax.set_title("Label-wise Classification Accuracy")
    ax.tick_params(axis="x", rotation=20)
    for bar, value in zip(bars, acc_values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 0.02,
            f"{value:.3f}",
            ha="center",
            va="bottom",
        )
    fig.tight_layout()
    fig.savefig(plots_dir / "label_accuracy.png", dpi=200)
    plt.close(fig)

    columns = list(LABELS)
    values = [
        [confusion_matrix[gold_label][predicted_label] for predicted_label in columns]
        for gold_label in LABELS
    ]
    fig, ax = plt.subplots(figsize=(6, 5))
    image = ax.imshow(values, cmap="Blues")
    ax.set_xticks(range(len(columns)), columns, rotation=25, ha="right")
    ax.set_yticks(range(len(LABELS)), LABELS)
    ax.set_xlabel("Predicted label")
    ax.set_ylabel("Gold label")
    ax.set_title("Confusion Matrix")
    for i, row in enumerate(values):
        for j, value in enumerate(row):
            ax.text(j, i, str(value), ha="center", va="center", color="#111111")
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(plots_dir / "confusion_matrix.png", dpi=200)
    plt.close(fig)


def evaluate(args: argparse.Namespace) -> dict[str, Any]:
    predictions_path = Path(args.predictions)
    groundtruth_path = Path(args.groundtruth)
    predictions = load_json(predictions_path)
    groundtruth = load_json(groundtruth_path)

    strict_rows = []
    official_rows = []
    for claim_id, gold in sorted(groundtruth.items()):
        pred = predictions.get(claim_id)
        row = score_claim(claim_id, gold, pred)
        strict_rows.append(row)
        if row["has_required_fields"]:
            official_rows.append(row)

    label_metrics = build_label_metrics(strict_rows)
    confusion_matrix = build_confusion_matrix(strict_rows)
    summary = {
        "run_name": args.run_name,
        "files": {
            "predictions": str(predictions_path),
            "groundtruth": str(groundtruth_path),
        },
        "official_metrics": aggregate(official_rows),
        "strict_metrics": aggregate(strict_rows),
        "format_issues": collect_format_issues(groundtruth, predictions, strict_rows),
    }

    output_dir = Path(args.output_dir) if args.output_dir else None
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "summary.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8"
        )
        write_csv(
            output_dir / "per_claim_metrics.csv",
            strict_rows,
            [
                "claim_id",
                "gold_label",
                "predicted_label",
                "classification_correct",
                "gold_evidence_count",
                "predicted_evidence_count",
                "correct_evidence_count",
                "evidence_precision",
                "evidence_recall",
                "evidence_f1",
                "has_required_fields",
                "valid_label",
                "evidences_is_list",
                "evidences_non_empty",
                "duplicate_evidence_count",
                "invalid_evidence_id_count",
            ],
        )
        write_csv(
            output_dir / "label_metrics.csv",
            label_metrics,
            [
                "label",
                "gold_count",
                "predicted_count",
                "classification_precision",
                "classification_recall",
                "classification_f1",
                "label_accuracy",
                "mean_evidence_f1",
            ],
        )
        write_confusion_csv(output_dir / "confusion_matrix.csv", confusion_matrix)

    if args.experiment_log:
        append_experiment_log(Path(args.experiment_log), args.run_name, summary)

    if args.plots_dir:
        maybe_write_plots(Path(args.plots_dir), summary, label_metrics, confusion_matrix)

    return summary


def print_summary(summary: dict[str, Any]) -> None:
    official = summary["official_metrics"]
    strict = summary["strict_metrics"]
    print(f"Run name: {summary['run_name']}")
    print("Official-compatible metrics")
    print(f"  Evidence Retrieval F-score (F)    = {official['evidence_f_score']}")
    print(f"  Claim Classification Accuracy (A) = {official['classification_accuracy']}")
    print(f"  Harmonic Mean of F and A          = {official['harmonic_mean']}")
    print("Strict metrics including malformed/missing claims as zero")
    print(f"  Evidence Retrieval F-score (F)    = {strict['evidence_f_score']}")
    print(f"  Claim Classification Accuracy (A) = {strict['classification_accuracy']}")
    print(f"  Harmonic Mean of F and A          = {strict['harmonic_mean']}")
    issues = summary["format_issues"]
    print("Format checks")
    print(f"  Missing claims: {len(issues['missing_claims'])}")
    print(f"  Extra prediction claims: {len(issues['extra_prediction_claims'])}")
    print(
        "  Invalid labels / empty evidence lists / duplicate evidence entries: "
        f"{issues['invalid_labels']} / {issues['empty_evidence_lists']} / "
        f"{issues['duplicate_evidence_entries']}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extended evaluator for COMP90042 claim verification outputs."
    )
    parser.add_argument("--predictions", required=True, help="Prediction JSON file.")
    parser.add_argument("--groundtruth", required=True, help="Gold claim JSON file.")
    parser.add_argument("--run-name", default="unnamed_run", help="Experiment name.")
    parser.add_argument(
        "--output-dir",
        help="Directory for summary.json, per-claim CSV, label CSV, and confusion CSV.",
    )
    parser.add_argument(
        "--experiment-log",
        help="CSV file to append one row of experiment-level metrics.",
    )
    parser.add_argument("--plots-dir", help="Directory for PNG diagnostic plots.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = evaluate(args)
    print_summary(summary)


if __name__ == "__main__":
    main()
