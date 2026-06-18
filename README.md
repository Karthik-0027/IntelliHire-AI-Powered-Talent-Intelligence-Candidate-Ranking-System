# Redrob Candidate Ranker

Offline, CPU-only candidate ranking system for the Redrob Intelligent Candidate
Discovery & Ranking Challenge.

## What it does

The ranker reads `candidates.jsonl`, scores every candidate against the released
Senior AI Engineer JD, and writes the required top-100 CSV:

```bash
python rank.py --candidates ./candidates.jsonl --out ./submission.csv
```

The method is a transparent hybrid scorer:

- JD fit from career narrative, current title, production search/retrieval/ranking
  evidence, Python/ML systems skills, and product-company background.
- Behavioral multiplier from Redrob signals: recency, open-to-work, response
  rate, notice period, verification, recruiter saves, interview reliability, and
  GitHub activity.
- Risk penalties for known traps: keyword stuffing without matching career
  evidence, pure services-consulting history, stale/unresponsive candidates,
  impossible skill-duration patterns, and CV/speech-only profiles without IR/NLP.

No network calls, hosted LLM APIs, GPU inference, or external model downloads are
used during ranking.

## Setup

Python 3.10+ is enough. The core ranker uses only the Python standard library.

```bash
python --version
python rank.py --candidates ./candidates.jsonl --out ./submission.csv
python validate_submission.py ./submission.csv
```

## Sandbox Demo

For the required hosted sandbox, deploy this repo to Streamlit Cloud and set:

```bash
streamlit run app.py
```

After deployment, paste the public Streamlit URL into `submission_metadata.yaml`
under `sandbox_link`.

## Files

- `rank.py` - full ranking pipeline and CLI.
- `app.py` - optional Streamlit sandbox demo for small uploaded samples.
- `validate_submission.py` - challenge validator copied for local checks.
- `submission_metadata.yaml` - metadata template to fill before portal upload.
- `outputs/candidate_recommendations.csv` - generated ranked candidates.
- `docs/methodology_deck.pdf` - concise PDF deck explaining the approach.

## Reproducibility

The scorer is deterministic. Ties are broken by candidate id. On the 100,000-row
dataset it streams JSONL line by line and stores only compact score/reasoning
records, so it fits comfortably inside the challenge's 5 minute / 16 GB /
CPU-only constraint.
