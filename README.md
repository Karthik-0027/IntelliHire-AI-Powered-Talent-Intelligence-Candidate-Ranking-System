# IntelliHire – AI-Powered Candidate Ranking System

 **Live Demo:**
https://intellihire-candidate-ranker.streamlit.app/

**GitHub Repository:**
https://github.com/Karthik-0027/IntelliHire-AI-Powered-Talent-Intelligence-Candidate-Ranking-System

An AI-powered talent intelligence platform that analyzes job descriptions, evaluates candidate profiles beyond keyword matching, and generates explainable candidate rankings using semantic matching, behavioral analytics, and hybrid scoring techniques.

Built for the **Redrob Intelligent Candidate Discovery & Ranking Challenge**.

---

## Overview

Hiring is more than matching keywords on a resume.

IntelliHire understands the requirements of a role, evaluates candidate experience, technical expertise, career progression, and behavioral signals, then produces a transparent and explainable ranking of the most suitable candidates.

The system is designed to operate efficiently on large-scale candidate datasets while remaining fully reproducible, CPU-only, and free from external API dependencies.

---

## Dataset

The challenge dataset (`candidates.jsonl`) is **not included** in this repository due to dataset size constraints and challenge distribution policies.

The ranking pipeline expects the official dataset provided by the challenge organizers.

---

## Problem Statement

Traditional hiring systems often rely heavily on keyword matching, resulting in:

* High-quality candidates being overlooked
* Keyword-stuffed profiles ranking highly
* Poor consideration of real-world experience
* Limited insight into candidate engagement and reliability

IntelliHire addresses these challenges through a hybrid ranking framework that combines semantic understanding with candidate quality signals.

---

## Key Features

### Semantic Candidate Matching

Understands the meaning of a job description and compares it against a candidate's complete professional profile.

### Hybrid Ranking Engine

Combines multiple signals into a unified ranking score.

### Behavioral Intelligence

Evaluates candidate engagement using recruiter interaction and activity metrics.

### Explainable Recommendations

Generates transparent reasoning for every ranked candidate.

### Risk & Anomaly Detection

Identifies suspicious profiles, keyword stuffing, and inconsistent career patterns.

### Scalable Processing

Supports datasets containing 100,000+ candidate profiles.

### CPU-Only Execution

Designed to run within challenge constraints without requiring GPUs, hosted LLMs, or external APIs.

---

## System Architecture

```text
                    Job Description
                           │
                           ▼
                 JD Understanding Layer
                           │
                           ▼
                  Candidate Processing
                           │
      ┌────────────────────┼────────────────────┐
      ▼                    ▼                    ▼
 Semantic Match     Experience Analysis   Behavioral Signals
      │                    │                    │
      └────────────────────┼────────────────────┘
                           ▼
                  Hybrid Scoring Engine
                           │
                           ▼
                  Risk & Quality Checks
                           │
                           ▼
                 Explainable Recommendations
                           │
                           ▼
                    Ranked Candidates
```

---

## Technology Stack

### Programming

* Python

### Data Processing

* Pandas
* NumPy

### Machine Learning & NLP

* Scikit-Learn
* Semantic Similarity Techniques

### Application Layer

* Streamlit

---

## Repository Structure

```text
IntelliHire-AI-Powered-Talent-Intelligence-Candidate-Ranking-System/

├── app.py
├── rank.py
├── validate_submission.py
├── requirements.txt
├── submission_metadata.yaml
├── README.md
│
├── outputs/
│   └── candidate_recommendations.csv
│
├── docs/
│   └── methodology_deck.pdf
```

---

## Installation

Clone the repository:

```bash
git clone https://github.com/Karthik-0027/IntelliHire-AI-Powered-Talent-Intelligence-Candidate-Ranking-System.git

cd IntelliHire-AI-Powered-Talent-Intelligence-Candidate-Ranking-System
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Usage

### Generate Candidate Rankings

```bash
python rank.py --candidates ./candidates.jsonl --out ./submission.csv
```

### Validate Submission

```bash
python validate_submission.py ./submission.csv
```

### Run Streamlit Application

```bash
streamlit run app.py
```

---

## Sandbox Note

The Streamlit application is intended for demonstration and testing using small candidate samples.

For full-scale ranking on the official challenge dataset (~100k candidates), use the offline ranking pipeline:

```bash
python rank.py --candidates ./candidates.jsonl --out ./submission.csv
```

---

## Live Demo

**Streamlit Sandbox**

https://intellihire-candidate-ranker.streamlit.app/

The demo allows users to:

* Upload sample candidate datasets
* Execute the ranking workflow
* Review candidate scores
* Explore ranking explanations
* Download ranked recommendations
* Understand the evaluation methodology

---

## Output Format

The system generates:

```text
submission.csv
```

Containing:

* Candidate ID
* Rank
* Score
* Recommendation Reasoning

---

## Performance

* Handles 100,000+ candidate profiles
* CPU-only execution
* Memory-efficient processing
* Deterministic ranking
* Reproducible results
* No hosted LLM APIs required

---

## Design Principles

* Transparency over black-box ranking
* Explainable candidate recommendations
* Scalable architecture
* Reproducible evaluation
* Practical hiring intelligence

---

## Author

**Karthik Gollapudi**

B.Tech Data Science | AI/ML | NLP | Information Retrieval | Software Engineering

📧 [karthikgollapudi33@gmail.com](mailto:karthikgollapudi33@gmail.com)

🔗 https://www.linkedin.com/in/karthik-gollapudi

---

## License

This project was developed for educational, research, and hackathon purposes.
