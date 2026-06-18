#!/usr/bin/env python3
"""Streamlit sandbox for the Redrob candidate ranker."""

from __future__ import annotations

import tempfile
from pathlib import Path

try:
    import streamlit as st
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Install streamlit to run the demo: pip install streamlit") from exc

from rank import rank_candidates, write_submission


st.set_page_config(
    page_title="IntelliHire Candidate Ranker",
    page_icon="IH",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    :root {
        --ink: #18212f;
        --muted: #607085;
        --line: #d8e0ea;
        --paper: #ffffff;
        --soft: #f5f7fb;
        --blue: #2563eb;
        --teal: #0f9f8f;
        --amber: #d97706;
    }
    .stApp {
        background:
            radial-gradient(circle at 8% 5%, rgba(37, 99, 235, 0.10), transparent 28rem),
            linear-gradient(180deg, #f7f9fd 0%, #ffffff 42%);
        color: var(--ink);
    }
    .block-container {
        padding-top: 2rem;
        max-width: 1180px;
    }
    div[data-testid="stToolbar"] { visibility: hidden; height: 0; }
    .hero {
        border: 1px solid var(--line);
        background: rgba(255, 255, 255, 0.88);
        padding: 1.35rem 1.5rem;
        border-radius: 8px;
        box-shadow: 0 18px 45px rgba(24, 33, 47, 0.08);
        margin-bottom: 1rem;
    }
    .eyebrow {
        color: var(--teal);
        font-size: .78rem;
        font-weight: 700;
        letter-spacing: .08em;
        text-transform: uppercase;
        margin-bottom: .35rem;
    }
    .hero h1 {
        font-size: 2rem;
        line-height: 1.1;
        margin: 0;
        color: var(--ink);
    }
    .hero p {
        color: var(--muted);
        font-size: 1rem;
        max-width: 820px;
        margin: .65rem 0 0;
    }
    .metric-card {
        border: 1px solid var(--line);
        background: var(--paper);
        border-radius: 8px;
        padding: 1rem;
        min-height: 105px;
    }
    .metric-label {
        color: var(--muted);
        font-size: .78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: .04em;
    }
    .metric-value {
        color: var(--ink);
        font-size: 1.55rem;
        font-weight: 750;
        margin-top: .3rem;
    }
    .metric-note {
        color: var(--muted);
        font-size: .86rem;
        margin-top: .25rem;
    }
    .section-title {
        font-size: 1.08rem;
        font-weight: 750;
        margin: 1.1rem 0 .55rem;
        color: var(--ink);
    }
    .candidate-card {
        border: 1px solid var(--line);
        background: var(--paper);
        border-radius: 8px;
        padding: .9rem 1rem;
        margin-bottom: .55rem;
    }
    .rank-pill {
        display: inline-block;
        background: #e8f1ff;
        color: var(--blue);
        border: 1px solid #c9dcff;
        border-radius: 999px;
        padding: .16rem .52rem;
        font-size: .78rem;
        font-weight: 750;
        margin-right: .45rem;
    }
    .candidate-id {
        color: var(--ink);
        font-weight: 750;
    }
    .score {
        color: var(--teal);
        font-weight: 750;
    }
    .reason {
        color: var(--muted);
        margin-top: .45rem;
        line-height: 1.45;
    }
    div.stButton > button,
    div.stDownloadButton > button {
        border-radius: 8px;
        border: 1px solid #1d4ed8;
        background: #2563eb;
        color: white;
        font-weight: 700;
        height: 2.75rem;
    }
    div.stButton > button:hover,
    div.stDownloadButton > button:hover {
        border-color: #1e40af;
        background: #1d4ed8;
        color: white;
    }
    div[data-testid="stFileUploader"] {
        border: 1px dashed #aab8ca;
        background: rgba(255, 255, 255, .72);
        border-radius: 8px;
        padding: .65rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def save_upload(uploaded_file) -> tuple[Path, tempfile.TemporaryDirectory[str]]:
    tmp = tempfile.TemporaryDirectory()
    suffix = ".jsonl.gz" if uploaded_file.name.endswith(".gz") else Path(uploaded_file.name).suffix
    input_path = Path(tmp.name) / f"candidates{suffix}"
    input_path.write_bytes(uploaded_file.getvalue())
    return input_path, tmp


def render_metric(label: str, value: str, note: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
          <div class="metric-label">{label}</div>
          <div class="metric-value">{value}</div>
          <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_candidate(rank: int, row) -> None:
    st.markdown(
        f"""
        <div class="candidate-card">
          <span class="rank-pill">#{rank}</span>
          <span class="candidate-id">{row.candidate_id}</span>
          <span style="float:right" class="score">{row.score:.4f}</span>
          <div class="reason">{row.reasoning}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">IntelliHire Talent Intelligence</div>
      <h1>Candidate ranking for high-signal AI engineering hiring</h1>
      <p>
        Upload a candidate file and get a recruiter-ready shortlist ranked by
        production retrieval experience, trusted ML skills, behavioral signals,
        availability, and trap-aware risk checks.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

metric_cols = st.columns(4)
with metric_cols[0]:
    render_metric("Ranking mode", "Hybrid", "Career evidence + behavior")
with metric_cols[1]:
    render_metric("Runtime", "CPU only", "No hosted LLM calls")
with metric_cols[2]:
    render_metric("Target role", "Senior AI", "Search, retrieval, ranking")
with metric_cols[3]:
    render_metric("Output", "CSV", "Challenge-ready format")

st.markdown('<div class="section-title">Run a shortlist</div>', unsafe_allow_html=True)

left, right = st.columns([1.15, 0.85], gap="large")
with left:
    uploaded = st.file_uploader(
        "Candidate file",
        type=["jsonl", "json", "gz"],
        help="Use candidates.jsonl for the full run or sample_candidates.json for a quick demo.",
        label_visibility="collapsed",
    )

with right:
    limit = st.slider("Number of candidates", min_value=5, max_value=100, value=20, step=5)
    run_clicked = st.button("Rank candidates", use_container_width=True)

if "ranked_rows" not in st.session_state:
    st.session_state.ranked_rows = []
    st.session_state.csv_bytes = b""

if run_clicked:
    if uploaded is None:
        st.warning("Upload a candidate file first.")
    else:
        with st.spinner("Reading profiles, scoring evidence, and building the shortlist..."):
            input_path, tmp = save_upload(uploaded)
            try:
                rows = rank_candidates(input_path, limit=limit)
                output_path = Path(tmp.name) / "candidate_recommendations.csv"
                write_submission(rows, output_path)
                st.session_state.ranked_rows = rows
                st.session_state.csv_bytes = output_path.read_bytes()
            finally:
                tmp.cleanup()

if st.session_state.ranked_rows:
    rows = st.session_state.ranked_rows
    top_score = rows[0].score if rows else 0
    avg_score = sum(row.score for row in rows) / len(rows)

    st.markdown('<div class="section-title">Shortlist summary</div>', unsafe_allow_html=True)
    summary_cols = st.columns(3)
    with summary_cols[0]:
        render_metric("Candidates ranked", str(len(rows)), "Sorted by final fit score")
    with summary_cols[1]:
        render_metric("Top score", f"{top_score:.3f}", rows[0].candidate_id)
    with summary_cols[2]:
        render_metric("Average score", f"{avg_score:.3f}", "Across current shortlist")

    st.download_button(
        "Download candidate_recommendations.csv",
        st.session_state.csv_bytes,
        "candidate_recommendations.csv",
        "text/csv",
        use_container_width=True,
    )

    st.markdown('<div class="section-title">Top recommendations</div>', unsafe_allow_html=True)
    for idx, row in enumerate(rows[:10], start=1):
        render_candidate(idx, row)

    with st.expander("View full ranked table", expanded=False):
        st.dataframe(
            [
                {
                    "rank": idx,
                    "candidate_id": row.candidate_id,
                    "score": round(row.score, 6),
                    "reasoning": row.reasoning,
                }
                for idx, row in enumerate(rows, start=1)
            ],
            use_container_width=True,
            hide_index=True,
        )
else:
    st.info("Upload a candidate file and run the ranker to see the shortlist.")
