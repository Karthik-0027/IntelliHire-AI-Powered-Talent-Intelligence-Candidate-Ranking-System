#!/usr/bin/env python3
"""Small Streamlit sandbox for the Redrob ranker."""

from __future__ import annotations

import tempfile
from pathlib import Path

try:
    import streamlit as st
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Install streamlit to run the demo: pip install streamlit") from exc

from rank import rank_candidates, write_submission


st.set_page_config(page_title="Redrob Candidate Ranker", layout="wide")
st.title("Redrob Candidate Ranker")

uploaded = st.file_uploader("Upload candidates.jsonl, candidates.json, or candidates.jsonl.gz", type=["jsonl", "json", "gz"])
limit = st.slider("Rows to rank", min_value=5, max_value=100, value=20, step=5)

if uploaded and st.button("Run ranker"):
    suffix = ".jsonl.gz" if uploaded.name.endswith(".gz") else Path(uploaded.name).suffix
    with tempfile.TemporaryDirectory() as tmp:
        input_path = Path(tmp) / f"candidates{suffix}"
        output_path = Path(tmp) / "ranked_candidates.csv"
        input_path.write_bytes(uploaded.getvalue())
        rows = rank_candidates(input_path, limit=limit)
        write_submission(rows, output_path)
        csv_bytes = output_path.read_bytes()

    st.success(f"Ranked {len(rows)} candidates.")
    st.dataframe(
        [{"rank": i + 1, "candidate_id": row.candidate_id, "score": round(row.score, 6), "reasoning": row.reasoning} for i, row in enumerate(rows)],
        use_container_width=True,
    )
    st.download_button("Download CSV", csv_bytes, "ranked_candidates.csv", "text/csv")
