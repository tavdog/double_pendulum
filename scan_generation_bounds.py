#!/usr/bin/env python3
"""Scan generation JSON files for bounds exceeding a threshold."""

import argparse
import json
from pathlib import Path

GENERATIONS_DIR = Path("generations")


def iter_generation_files():
    files = list(GENERATIONS_DIR.glob("*.json"))
    files.sort(key=lambda p: int(p.stem))
    return files


def main():
    parser = argparse.ArgumentParser(
        description="Scan generations/ for bounds y_min / y_max greater than X"
    )
    parser.add_argument(
        "threshold",
        type=float,
        help="Threshold X (adjust comparison in exceeds_threshold if needed)",
    )
    args = parser.parse_args()
    X = args.threshold

    for path in iter_generation_files():
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        # bounds = data.get("bounds")
        # if not bounds:
        #     continue

        # y_min = bounds["y_min"]
        # y_max = bounds["y_max"]
        for quad in data.get("trajectory"):
            (a,b,c,d) = quad
            if exceeds_threshold(a,b,c,d, X):
                print(path)


def exceeds_threshold(a: float, b: float,c,d, x: float) -> bool:
    if (x > 0):
        return a > x or b > x or c > x or d > x
    else:
        return a < x or b < x or c < x or d < x


if __name__ == "__main__":
    main()
