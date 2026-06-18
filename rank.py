#!/usr/bin/env python3
"""Deterministic offline ranker for the Redrob candidate discovery challenge."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterator, TextIO


REFERENCE_DATE = date(2026, 6, 1)
TOP_N = 100

SERVICE_COMPANIES = {
    "tcs",
    "infosys",
    "wipro",
    "accenture",
    "cognizant",
    "capgemini",
    "hcl",
    "tech mahindra",
    "mphasis",
    "mindtree",
    "genpact ai",
}

PRODUCT_COMPANIES = {
    "swiggy",
    "zomato",
    "razorpay",
    "cred",
    "flipkart",
    "meesho",
    "inmobi",
    "nykaa",
    "zoho",
    "freshworks",
    "vedantu",
    "ola",
    "dream11",
    "yellow.ai",
    "haptik",
    "wysa",
    "apple",
    "google",
    "microsoft",
    "amazon",
    "netflix",
}

TIER1_LOCATION_TERMS = (
    "pune",
    "noida",
    "delhi",
    "gurgaon",
    "mumbai",
    "hyderabad",
    "bangalore",
    "bengaluru",
)

TITLE_WEIGHTS = {
    "senior ai engineer": 1.00,
    "recommendation systems engineer": 0.98,
    "search engineer": 0.96,
    "applied ml engineer": 0.94,
    "machine learning engineer": 0.90,
    "senior software engineer (ml)": 0.88,
    "ai engineer": 0.86,
    "ml engineer": 0.82,
    "senior data scientist": 0.78,
    "data scientist": 0.66,
    "data engineer": 0.50,
    "senior data engineer": 0.52,
    "backend engineer": 0.45,
    "analytics engineer": 0.36,
    "software engineer": 0.33,
}

CORE_SKILL_WEIGHTS = {
    "embeddings": 1.00,
    "semantic search": 1.00,
    "vector search": 1.00,
    "information retrieval": 0.98,
    "recommendation systems": 0.98,
    "sentence transformers": 0.95,
    "learning to rank": 0.94,
    "bm25": 0.90,
    "faiss": 0.86,
    "pinecone": 0.84,
    "qdrant": 0.82,
    "weaviate": 0.82,
    "milvus": 0.80,
    "opensearch": 0.80,
    "elasticsearch": 0.78,
    "pgvector": 0.76,
    "python": 0.74,
    "machine learning": 0.70,
    "mlops": 0.66,
    "mlflow": 0.62,
    "bentoml": 0.58,
    "kubeflow": 0.56,
    "hugging face transformers": 0.54,
    "llms": 0.52,
    "rag": 0.50,
    "fine-tuning llms": 0.48,
    "lora": 0.44,
    "qlora": 0.44,
    "peft": 0.42,
    "nlp": 0.40,
    "feature engineering": 0.36,
    "pytorch": 0.34,
    "tensorflow": 0.30,
    "scikit-learn": 0.30,
}

NEGATIVE_SPECIALIZATION_SKILLS = {
    "computer vision",
    "opencv",
    "image classification",
    "object detection",
    "yolo",
    "cnn",
    "gans",
    "diffusion models",
    "speech recognition",
    "asr",
    "tts",
    "robotics",
}

CAREER_PATTERNS = {
    "hybrid retrieval": 1.15,
    "dense vector": 1.05,
    "embedding-based retrieval": 1.05,
    "semantic search": 1.00,
    "vector search": 0.95,
    "information retrieval": 0.92,
    "recommendation": 0.92,
    "ranking": 0.90,
    "learning-to-rank": 0.90,
    "bm25": 0.86,
    "faiss": 0.82,
    "candidate profiles": 0.80,
    "retrieval-quality": 0.78,
    "offline/online evaluation": 0.78,
    "evaluation framework": 0.76,
    "ndcg": 0.74,
    "mrr": 0.68,
    "map": 0.58,
    "a/b testing": 0.70,
    "ab testing": 0.70,
    "production ml": 0.68,
    "deployed": 0.52,
    "real users": 0.50,
    "llm": 0.38,
    "fine-tun": 0.36,
    "python": 0.34,
}


@dataclass(frozen=True)
class CandidateScore:
    candidate_id: str
    score: float
    reasoning: str


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        year, month, day = (int(part) for part in value.split("-"))
        return date(year, month, day)
    except Exception:
        return None


def norm_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.lower())


def skill_lookup(candidate: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {s.get("name", "").lower(): s for s in candidate.get("skills", [])}


def candidate_text(candidate: dict[str, Any]) -> str:
    profile = candidate["profile"]
    chunks = [
        profile.get("headline", ""),
        profile.get("summary", ""),
        profile.get("current_title", ""),
        profile.get("current_industry", ""),
    ]
    for job in candidate.get("career_history", []):
        chunks.extend([job.get("title", ""), job.get("industry", ""), job.get("description", "")])
    chunks.extend(s.get("name", "") for s in candidate.get("skills", []))
    return norm_text(" ".join(chunks))


def experience_score(years: float) -> float:
    if 5.0 <= years <= 9.0:
        return 1.0
    if 4.0 <= years < 5.0:
        return 0.82 + 0.18 * (years - 4.0)
    if 9.0 < years <= 11.0:
        return 0.88 - 0.12 * (years - 9.0) / 2.0
    if 3.0 <= years < 4.0:
        return 0.55 + 0.20 * (years - 3.0)
    if 11.0 < years <= 14.0:
        return 0.65 - 0.15 * (years - 11.0) / 3.0
    return 0.35


def title_score(title: str) -> float:
    title_l = title.lower()
    for key, weight in TITLE_WEIGHTS.items():
        if key in title_l:
            return weight
    if any(term in title_l for term in ("marketing", "sales", "accountant", "hr", "graphic", "mechanical", "civil")):
        return 0.04
    return 0.12


def trusted_skill_score(candidate: dict[str, Any]) -> tuple[float, list[str], float]:
    skills = skill_lookup(candidate)
    total = 0.0
    max_total = sum(sorted(CORE_SKILL_WEIGHTS.values(), reverse=True)[:14])
    hits: list[tuple[str, float]] = []
    suspicious = 0
    for name, weight in CORE_SKILL_WEIGHTS.items():
        skill = skills.get(name)
        if not skill:
            continue
        prof = skill.get("proficiency", "beginner")
        duration = float(skill.get("duration_months") or 0)
        endorsements = float(skill.get("endorsements") or 0)
        prof_mult = {"beginner": 0.45, "intermediate": 0.72, "advanced": 0.93, "expert": 1.05}.get(prof, 0.55)
        duration_mult = clamp(duration / 36.0, 0.25, 1.0)
        endorse_mult = clamp(math.log1p(endorsements) / math.log(31), 0.35, 1.0)
        total += weight * prof_mult * duration_mult * endorse_mult
        hits.append((name, weight))
        if prof in {"advanced", "expert"} and duration < 6:
            suspicious += 1
        if prof == "expert" and endorsements == 0:
            suspicious += 1
    score = clamp(total / max_total)

    assessments = candidate["redrob_signals"].get("skill_assessment_scores", {})
    assessed_core = [
        v
        for k, v in assessments.items()
        if k.lower() in CORE_SKILL_WEIGHTS and isinstance(v, (int, float))
    ]
    if assessed_core:
        score *= 0.88 + 0.24 * clamp(sum(assessed_core) / (100 * len(assessed_core)))

    risk = clamp(suspicious / 5.0)
    top_hits = [name for name, _ in sorted(hits, key=lambda item: item[1], reverse=True)[:5]]
    return clamp(score), top_hits, risk


def career_evidence_score(text: str) -> tuple[float, list[str]]:
    total = 0.0
    hits: list[tuple[str, float]] = []
    for pattern, weight in CAREER_PATTERNS.items():
        if pattern in text:
            total += weight
            hits.append((pattern, weight))
    return clamp(total / 5.8), [h for h, _ in sorted(hits, key=lambda item: item[1], reverse=True)[:4]]


def product_company_score(candidate: dict[str, Any]) -> tuple[float, bool]:
    jobs = candidate.get("career_history", [])
    companies = [j.get("company", "").lower() for j in jobs]
    industries = [j.get("industry", "").lower() for j in jobs]
    product_hits = sum(c in PRODUCT_COMPANIES for c in companies)
    service_hits = sum(c in SERVICE_COMPANIES or "services" in i or "consulting" in i for c, i in zip(companies, industries))
    product = product_hits > 0 or any(i in {"software", "saas", "ai/ml", "fintech", "e-commerce", "food delivery", "gaming", "conversational ai", "healthtech ai"} for i in industries)
    if product_hits:
        score = 0.9
    elif product:
        score = 0.72
    else:
        score = 0.40
    services_only = bool(jobs) and service_hits == len(jobs)
    if services_only:
        score *= 0.55
    return clamp(score), services_only


def location_score(candidate: dict[str, Any]) -> float:
    profile = candidate["profile"]
    loc = profile.get("location", "").lower()
    country = profile.get("country", "").lower()
    signals = candidate["redrob_signals"]
    if "pune" in loc or "noida" in loc:
        base = 1.0
    elif any(term in loc for term in TIER1_LOCATION_TERMS):
        base = 0.86
    elif country == "india":
        base = 0.68
    else:
        base = 0.35
    if signals.get("willing_to_relocate"):
        base += 0.12
    if signals.get("preferred_work_mode") in {"hybrid", "flexible", "onsite"}:
        base += 0.04
    return clamp(base)


def behavior_score(candidate: dict[str, Any]) -> float:
    s = candidate["redrob_signals"]
    last_active = parse_date(s.get("last_active_date"))
    days_inactive = (REFERENCE_DATE - last_active).days if last_active else 365
    recency = clamp(1.0 - days_inactive / 180.0)
    response = clamp(float(s.get("recruiter_response_rate") or 0))
    response_time = clamp(1.0 - float(s.get("avg_response_time_hours") or 240) / 240.0)
    notice = clamp(1.0 - max(0, float(s.get("notice_period_days") or 0) - 30) / 120.0)
    interview = clamp(float(s.get("interview_completion_rate") or 0))
    offer = s.get("offer_acceptance_rate", -1)
    offer_score = 0.55 if offer == -1 else clamp(float(offer))
    github = s.get("github_activity_score", -1)
    github_score = 0.40 if github == -1 else clamp(float(github) / 100.0)
    saved = clamp(math.log1p(float(s.get("saved_by_recruiters_30d") or 0)) / math.log(51))
    completeness = clamp(float(s.get("profile_completeness_score") or 0) / 100.0)
    verified = 0.0
    verified += 0.34 if s.get("verified_email") else 0.0
    verified += 0.33 if s.get("verified_phone") else 0.0
    verified += 0.33 if s.get("linkedin_connected") else 0.0
    open_to_work = 1.0 if s.get("open_to_work_flag") else 0.45
    return clamp(
        0.18 * recency
        + 0.17 * response
        + 0.10 * response_time
        + 0.12 * open_to_work
        + 0.11 * notice
        + 0.10 * interview
        + 0.06 * offer_score
        + 0.07 * github_score
        + 0.05 * saved
        + 0.02 * completeness
        + 0.02 * verified
    )


def risk_penalty(
    candidate: dict[str, Any],
    text: str,
    top_skills: list[str],
    skill_risk: float,
    career_score_value: float,
    services_only: bool,
) -> tuple[float, list[str]]:
    profile = candidate["profile"]
    title = profile.get("current_title", "").lower()
    signals = candidate["redrob_signals"]
    penalty = 0.0
    reasons: list[str] = []

    non_technical_title = any(
        t in title
        for t in ("marketing", "sales", "accountant", "hr", "graphic", "mechanical", "civil", "customer support")
    )
    ai_skill_count = sum(1 for s in top_skills if s in CORE_SKILL_WEIGHTS)
    if non_technical_title and ai_skill_count >= 3:
        penalty += 0.18
        reasons.append("AI skills are not backed by an AI engineering title")
    if ai_skill_count >= 5 and career_score_value < 0.22:
        penalty += 0.14
        reasons.append("skills look stronger than career evidence")
    if services_only:
        penalty += 0.10
        reasons.append("services-only career history")
    if float(signals.get("recruiter_response_rate") or 0) < 0.15:
        penalty += 0.08
        reasons.append("low recruiter response rate")
    last_active = parse_date(signals.get("last_active_date"))
    if last_active and (REFERENCE_DATE - last_active).days > 120:
        penalty += 0.10
        reasons.append("stale platform activity")
    if skill_risk > 0:
        penalty += 0.08 * skill_risk
        reasons.append("some impossible skill-duration signals")

    neg_count = sum(1 for s in candidate.get("skills", []) if s.get("name", "").lower() in NEGATIVE_SPECIALIZATION_SKILLS)
    ir_count = sum(1 for s in candidate.get("skills", []) if s.get("name", "").lower() in CORE_SKILL_WEIGHTS)
    if neg_count >= 5 and ir_count < 4 and "information retrieval" not in text and "semantic search" not in text:
        penalty += 0.11
        reasons.append("CV/speech-heavy profile with limited IR evidence")

    return clamp(penalty, 0.0, 0.55), reasons[:2]


def score_candidate(candidate: dict[str, Any]) -> CandidateScore:
    profile = candidate["profile"]
    text = candidate_text(candidate)

    t_score = title_score(profile.get("current_title", ""))
    s_score, top_skills, skill_risk = trusted_skill_score(candidate)
    c_score, career_hits = career_evidence_score(text)
    exp_score = experience_score(float(profile.get("years_of_experience") or 0))
    product_score, services_only = product_company_score(candidate)
    loc_score = location_score(candidate)
    beh_score = behavior_score(candidate)

    base = (
        0.23 * t_score
        + 0.25 * c_score
        + 0.18 * s_score
        + 0.11 * exp_score
        + 0.10 * product_score
        + 0.07 * loc_score
        + 0.06 * beh_score
    )
    penalty, risk_reasons = risk_penalty(candidate, text, top_skills, skill_risk, c_score, services_only)

    # Availability should modify, but not dominate, the job-fit score.
    availability_multiplier = 0.84 + 0.28 * beh_score
    raw_score = clamp(base * availability_multiplier - penalty)

    reasoning = make_reasoning(
        candidate,
        raw_score,
        career_hits,
        top_skills,
        beh_score,
        risk_reasons,
        c_score,
        product_score,
    )
    return CandidateScore(candidate["candidate_id"], raw_score, reasoning)


def make_reasoning(
    candidate: dict[str, Any],
    score: float,
    career_hits: list[str],
    top_skills: list[str],
    behavior: float,
    risk_reasons: list[str],
    career_score_value: float,
    product_score_value: float,
) -> str:
    profile = candidate["profile"]
    signals = candidate["redrob_signals"]
    years = profile.get("years_of_experience")
    title = profile.get("current_title")
    location = profile.get("location")
    skill_phrase = ", ".join(top_skills[:3]) if top_skills else "limited explicit core skills"
    career_phrase = ", ".join(career_hits[:2]) if career_hits else "adjacent ML/software experience"
    response = signals.get("recruiter_response_rate", 0)
    notice = signals.get("notice_period_days", 0)
    active = signals.get("last_active_date", "unknown")

    if score >= 0.70:
        opener = (
            f"{title} with {years} years in {location}; profile shows {career_phrase} "
            f"and trusted skills in {skill_phrase}."
        )
    elif career_score_value >= 0.35:
        opener = (
            f"{title} with {years} years; has useful JD evidence around {career_phrase}, "
            f"with skills including {skill_phrase}."
        )
    else:
        opener = (
            f"{title} with {years} years; fit is more adjacent, with {skill_phrase} "
            f"but less direct retrieval/ranking career evidence."
        )

    concern_bits: list[str] = []
    if product_score_value < 0.45:
        concern_bits.append("limited product-company signal")
    if notice and notice > 60:
        concern_bits.append(f"{notice}-day notice")
    if response < 0.35:
        concern_bits.append(f"{response:.2f} recruiter response rate")
    concern_bits.extend(risk_reasons)

    if concern_bits:
        closer = f"Behavioral score is {behavior:.2f} with last activity {active}; concern: {', '.join(concern_bits[:2])}."
    else:
        closer = f"Behavioral score is {behavior:.2f}: last active {active}, response rate {response:.2f}, notice {notice} days."
    return f"{opener} {closer}"


def open_text(path: Path) -> TextIO:
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open("r", encoding="utf-8")


def iter_candidates(candidates_path: Path) -> Iterator[dict[str, Any]]:
    with open_text(candidates_path) as fh:
        if candidates_path.name.endswith(".json") and not candidates_path.name.endswith(".jsonl"):
            data = json.load(fh)
            if isinstance(data, list):
                yield from data
            else:
                yield data
            return
        for line in fh:
            if line.strip():
                yield json.loads(line)


def rank_candidates(candidates_path: Path, limit: int = TOP_N) -> list[CandidateScore]:
    scored: list[CandidateScore] = []
    for candidate in iter_candidates(candidates_path):
        scored.append(score_candidate(candidate))
    scored.sort(key=lambda item: (-item.score, item.candidate_id))
    return scored[:limit]


def write_submission(rows: list[CandidateScore], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        for rank, row in enumerate(rows, start=1):
            writer.writerow([row.candidate_id, rank, f"{row.score:.6f}", row.reasoning])


def main() -> None:
    parser = argparse.ArgumentParser(description="Rank Redrob candidates for the Senior AI Engineer JD.")
    parser.add_argument("--candidates", required=True, type=Path, help="Path to candidates.jsonl")
    parser.add_argument("--out", required=True, type=Path, help="Path to output CSV")
    parser.add_argument("--limit", type=int, default=TOP_N, help="Number of candidates to output")
    args = parser.parse_args()

    rows = rank_candidates(args.candidates, args.limit)
    write_submission(rows, args.out)
    print(f"Wrote {len(rows)} ranked candidates to {args.out}")


if __name__ == "__main__":
    main()
