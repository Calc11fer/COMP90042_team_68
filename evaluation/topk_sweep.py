#!/usr/bin/env python3
"""Evaluate a ranked prediction file after truncating evidences to top-k."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from extended_eval import aggregate, load_json, score_claim


def truncate_prediction(pred: Any, k: int) -> Any:
    if not isinstance(pred, dict):
        return pred
    if not isinstance(pred.get("evidences"), list):
        return pred
    truncated = dict(pred)
    truncated["evidences"] = pred["evidences"][:k]
    return truncated


def evaluate_at_k(
    predictions: dict[str, Any], groundtruth: dict[str, Any], k: int
) -> dict[str, Any]:
    strict_rows = []
    official_rows = []
    for claim_id, gold in sorted(groundtruth.items()):
        pred = truncate_prediction(predictions.get(claim_id), k)
        row = score_claim(claim_id, gold, pred)
        strict_rows.append(row)
        if row["has_required_fields"]:
            official_rows.append(row)

    official = aggregate(official_rows)
    strict = aggregate(strict_rows)
    return {
        "k": k,
        "official_num_claims": official["num_claims"],
        "official_evidence_f_score": official["evidence_f_score"],
        "official_classification_accuracy": official["classification_accuracy"],
        "official_harmonic_mean": official["harmonic_mean"],
        "strict_num_claims": strict["num_claims"],
        "strict_evidence_f_score": strict["evidence_f_score"],
        "strict_classification_accuracy": strict["classification_accuracy"],
        "strict_harmonic_mean": strict["harmonic_mean"],
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "k",
        "official_num_claims",
        "official_evidence_f_score",
        "official_classification_accuracy",
        "official_harmonic_mean",
        "strict_num_claims",
        "strict_evidence_f_score",
        "strict_classification_accuracy",
        "strict_harmonic_mean",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run evidence top-k evaluation sweep.")
    parser.add_argument("--predictions", required=True, help="Prediction JSON file.")
    parser.add_argument("--groundtruth", required=True, help="Gold claim JSON file.")
    parser.add_argument("--min-k", type=int, default=1, help="Smallest top-k value.")
    parser.add_argument("--max-k", type=int, default=10, help="Largest top-k value.")
    parser.add_argument("--output-csv", help="Optional CSV path for sweep results.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.min_k < 1 or args.max_k < args.min_k:
        raise ValueError("Require 1 <= min-k <= max-k.")

    predictions = load_json(Path(args.predictions))
    groundtruth = load_json(Path(args.groundtruth))
    rows = [
        evaluate_at_k(predictions, groundtruth, k)
        for k in range(args.min_k, args.max_k + 1)
    ]

    print("k,official_evidence_f_score,official_classification_accuracy,official_harmonic_mean")
    for row in rows:
        print(
            f"{row['k']},"
            f"{row['official_evidence_f_score']},"
            f"{row['official_classification_accuracy']},"
            f"{row['official_harmonic_mean']}"
        )

    if args.output_csv:
        write_csv(Path(args.output_csv), rows)


if __name__ == "__main__":
    main()
