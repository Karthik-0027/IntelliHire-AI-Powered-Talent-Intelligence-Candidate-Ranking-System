#!/usr/bin/env python3
"""Create a small PDF deck without third-party dependencies."""

from __future__ import annotations

import argparse
from pathlib import Path


SLIDES = [
    (
        "Redrob Candidate Ranker",
        [
            "Goal: identify the top 100 candidates for Redrob's Senior AI Engineer founding-team role.",
            "Built as a deterministic offline ranker: CPU-only, no network calls, no hosted LLM APIs.",
            "Optimized for recruiter trust: specific reasons, explicit concerns, and stable reproducibility.",
        ],
    ),
    (
        "What The JD Really Asks For",
        [
            "Primary need: production search, retrieval, ranking, embeddings, and evaluation systems.",
            "Strong preference for 5-9 years, hands-on coding, product-company context, and India/Pune/Noida logistics.",
            "Explicit negatives: keyword-only AI exposure, pure research, services-only careers, and CV/speech-only profiles.",
        ],
    ),
    (
        "Scoring Architecture",
        [
            "Job-fit score combines title, career narrative, trusted skills, experience band, product background, and location.",
            "Career evidence is weighted above raw skills to avoid candidates who only stuff AI keywords.",
            "Skills are trusted by proficiency, duration, endorsements, and Redrob assessment scores.",
        ],
    ),
    (
        "Behavioral Signals",
        [
            "Availability modifier uses last active date, open-to-work flag, recruiter response rate, response time, and notice period.",
            "Hireability adds interview completion, offer acceptance, recruiter saves, GitHub activity, and profile verification.",
            "Behavior adjusts the technical score without letting a weak technical fit outrank a strong role match.",
        ],
    ),
    (
        "Trap And Risk Handling",
        [
            "Penalizes non-technical titles with many AI skills but weak career evidence.",
            "Penalizes services-only histories, stale profiles, low response rates, and impossible skill-duration patterns.",
            "Downweights CV/speech-heavy specialization when NLP/IR/retrieval evidence is missing.",
        ],
    ),
    (
        "Output And Reproducibility",
        [
            "Single command: python rank.py --candidates ./candidates.jsonl --out ./submission.csv",
            "Runtime on the full 100,000-candidate dataset: about 20 seconds on local CPU.",
            "Generated CSV passes the provided challenge validator with exactly 100 ranked rows.",
        ],
    ),
]


def esc(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def wrap(text: str, width: int = 84) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        trial = " ".join(current + [word])
        if len(trial) > width and current:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines


def page_stream(title: str, bullets: list[str]) -> str:
    commands = ["BT", "/F1 28 Tf", "72 520 Td", f"({esc(title)}) Tj"]
    y_shift = 54
    for bullet in bullets:
        first = True
        for line in wrap(bullet):
            commands.extend(["/F2 14 Tf", f"0 -{y_shift if first else 22} Td"])
            prefix = "- " if first else "  "
            commands.append(f"({esc(prefix + line)}) Tj")
            first = False
        y_shift = 34
    commands.append("ET")
    return "\n".join(commands)


def build_pdf(slides: list[tuple[str, list[str]]]) -> bytes:
    objects: list[bytes] = []

    def add(obj: str) -> int:
        objects.append(obj.encode("latin-1"))
        return len(objects)

    add("<< /Type /Catalog /Pages 2 0 R >>")
    add("<< /Type /Pages /Kids [] /Count 0 >>")
    font1 = add("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")
    font2 = add("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    page_ids: list[int] = []
    for title, bullets in slides:
        stream = page_stream(title, bullets)
        content_id = add(f"<< /Length {len(stream.encode('latin-1'))} >>\nstream\n{stream}\nendstream")
        page_id = add(
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 792 612] "
            f"/Resources << /Font << /F1 {font1} 0 R /F2 {font2} 0 R >> >> "
            f"/Contents {content_id} 0 R >>"
        )
        page_ids.append(page_id)

    kids = " ".join(f"{pid} 0 R" for pid in page_ids)
    objects[1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode("latin-1")

    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{i} 0 obj\n".encode("latin-1"))
        output.extend(obj)
        output.extend(b"\nendobj\n")
    xref = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))
    output.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("latin-1")
    )
    return bytes(output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("docs/approach_deck.pdf"))
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(build_pdf(SLIDES))
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
