#!/usr/bin/env python3
"""Challenge CSV format validator."""

import csv
import re
import sys
from pathlib import Path

REQUIRED_HEADER = ["candidate_id", "rank", "score", "reasoning"]
CANDIDATE_ID_PATTERN = re.compile(r"^CAND_[0-9]{7}$")
EXPECTED_DATA_ROWS = 100


def validate_submission(csv_path):
    errors = []
    path = Path(csv_path)
    if path.suffix.lower() != ".csv":
        errors.append("Filename must use a .csv extension.")

    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            try:
                header = next(reader)
            except StopIteration:
                return ["Row 1 must be the header row; file is empty."]
            if header != REQUIRED_HEADER:
                errors.append(f"Header must be exactly: {','.join(REQUIRED_HEADER)}")
            data_rows = [row for row in reader if any(cell.strip() for cell in row)]
    except OSError as exc:
        return [f"Cannot read file: {exc}"]

    if len(data_rows) != EXPECTED_DATA_ROWS:
        errors.append(f"Expected {EXPECTED_DATA_ROWS} data rows; found {len(data_rows)}.")

    seen_ids = set()
    seen_ranks = set()
    by_rank = []
    for i, cells in enumerate(data_rows, start=2):
        if len(cells) != len(REQUIRED_HEADER):
            errors.append(f"Row {i}: expected {len(REQUIRED_HEADER)} columns, got {len(cells)}.")
            continue
        cid, rank_s, score_s, _ = cells
        if not CANDIDATE_ID_PATTERN.match(cid.strip()):
            errors.append(f"Row {i}: bad candidate_id.")
        if cid in seen_ids:
            errors.append(f"Row {i}: duplicate candidate_id {cid}.")
        seen_ids.add(cid)
        try:
            rank = int(rank_s)
            if not 1 <= rank <= 100 or rank in seen_ranks:
                errors.append(f"Row {i}: invalid or duplicate rank.")
            seen_ranks.add(rank)
        except ValueError:
            errors.append(f"Row {i}: rank must be an integer.")
            rank = -1
        try:
            score = float(score_s)
        except ValueError:
            errors.append(f"Row {i}: score must be a float.")
            score = float("nan")
        by_rank.append((rank, score, cid))

    missing = set(range(1, 101)) - seen_ranks
    if missing:
        errors.append(f"Missing ranks: {sorted(missing)}")

    by_rank.sort()
    for (r1, s1, c1), (r2, s2, c2) in zip(by_rank, by_rank[1:]):
        if s1 < s2:
            errors.append(f"score must be non-increasing: rank {r1} < rank {r2}.")
        if s1 == s2 and c1 > c2:
            errors.append(f"tie-break requires candidate_id ascending at ranks {r1}, {r2}.")
    return errors


def main():
    if len(sys.argv) != 2:
        print("Usage: python validate_submission.py <participant_id>.csv")
        raise SystemExit(1)
    errors = validate_submission(sys.argv[1])
    if errors:
        print(f"Validation failed ({len(errors)} issue(s)):")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)
    print("Submission is valid.")


if __name__ == "__main__":
    main()
