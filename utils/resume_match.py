import io
import re
from typing import Dict, List, Tuple

from pypdf import PdfReader


def _decode_pdf_literal_string(literal: bytes) -> str:
    text = literal
    if text.startswith(b"(") and text.endswith(b")"):
        text = text[1:-1]

    decoded = []
    i = 0
    while i < len(text):
        if text[i:i + 1] == b"\\" and i + 1 < len(text):
            nxt = text[i + 1:i + 2]
            if nxt in {b"n", b"r", b"t", b"b", b"f", b"(", b")", b"\\"}:
                mapping = {
                    b"n": "\n",
                    b"r": "\r",
                    b"t": "\t",
                    b"b": "\b",
                    b"f": "\f",
                    b"(": "(",
                    b")": ")",
                    b"\\": "\\",
                }
                decoded.append(mapping[nxt])
                i += 2
                continue
            if nxt in b"01234567":
                octal = text[i + 1:i + 4]
                try:
                    decoded.append(chr(int(octal, 8)))
                    i += 4
                    continue
                except ValueError:
                    pass
            if nxt == b"x" and i + 3 < len(text):
                hex_bytes = text[i + 2:i + 4]
                try:
                    decoded.append(chr(int(hex_bytes, 16)))
                    i += 4
                    continue
                except ValueError:
                    pass
            if nxt.isdigit():
                digits = []
                j = i + 1
                while j < len(text) and text[j:j + 1].isdigit() and len(digits) < 3:
                    digits.append(text[j:j + 1].decode("latin1"))
                    j += 1
                if digits:
                    decoded.append(chr(int("".join(digits), 8)))
                    i = j
                    continue
            decoded.append(chr(int(nxt, 16))) if nxt and nxt not in {b"n", b"r", b"t", b"b", b"f", b"(", b")", b"\\"} and nxt.isascii() else None
            if nxt and nxt.isascii() and nxt not in {b"n", b"r", b"t", b"b", b"f", b"(", b")", b"\\"}:
                try:
                    decoded.append(chr(int(nxt, 8)))
                    i += 2
                    continue
                except ValueError:
                    pass
            decoded.append("\\")
            i += 1
            continue
        decoded.append(chr(text[i]))
        i += 1

    return "".join(decoded)


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """Extract readable text from a PDF file byte stream."""
    if not pdf_bytes:
        return ""

    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        pages = []
        for page in reader.pages:
            text = page.extract_text() or ""
            if text:
                pages.append(text)
        extracted = "\n".join(pages).strip()
        if extracted:
            return extracted
    except Exception:
        pass

    raw_matches = re.findall(rb"\((?:\\.|[^()\\])*\)", pdf_bytes)
    text_parts = []
    for match in raw_matches:
        decoded = _decode_pdf_literal_string(match)
        if decoded.strip():
            text_parts.append(decoded.strip())

    fallback = " ".join(text_parts)
    if fallback.strip():
        return fallback.strip()

    return ""


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_keywords(text: str) -> set[str]:
    tokens = normalize_text(text).split()
    stop_words = {
        "the", "and", "or", "with", "for", "to", "of", "in", "on", "a", "an",
        "is", "are", "be", "as", "at", "by", "from", "we", "our", "your", "you",
        "experience", "skills", "job", "role", "work", "team", "using", "used",
        "years", "year", "strong", "good", "excellent", "developer", "candidate"
    }
    return {token for token in tokens if token and token not in stop_words and len(token) > 2}


def extract_required_skills(job_description: str) -> List[str]:
    keywords = extract_keywords(job_description)
    normalized_keywords = set()
    for key in keywords:
        if key == "apis":
            normalized_keywords.add("api")
        else:
            normalized_keywords.add(key)

    priority = ["python", "django", "flask", "sql", "rest", "api", "postgresql", "mysql", "git", "agile", "teamwork", "aws", "docker", "redis", "javascript", "react", "node", "java"]
    required = []
    for term in priority:
        if term in normalized_keywords:
            required.append(term)
    if not required:
        required = sorted(normalized_keywords)[:10]
    return required


def extract_years_of_experience(text: str) -> float:
    text = normalize_text(text)
    pattern = r"(\d+(?:\.\d+)?)\s*(?:year|years)"
    matches = re.findall(pattern, text)
    if not matches:
        return 0.0
    return round(sum(float(m) for m in matches), 2)


def score_resume_against_job(resume_text: str, job_description: str) -> float:
    resume_keywords = extract_keywords(resume_text)
    required_skills = extract_required_skills(job_description)
    job_keywords = extract_keywords(job_description)
    if not job_keywords:
        return 0.0

    matches = resume_keywords & set(required_skills)
    all_matches = resume_keywords & job_keywords
    required_ratio = len(matches) / max(len(required_skills), 1)
    coverage = len(all_matches) / max(len(job_keywords), 1)
    exp_bonus = min(15.0, extract_years_of_experience(resume_text) * 5)
    score = (required_ratio * 75) + (coverage * 25)
    score *= 100
    score += min(10, len(matches) * 2)
    score += exp_bonus
    return round(max(0.0, min(100.0, score)), 2)


def rank_candidates(candidates: Dict[str, str], job_description: str) -> List[Tuple[str, float]]:
    ranked = []
    for name, resume in candidates.items():
        ranked.append((name, score_resume_against_job(resume, job_description)))
    return sorted(ranked, key=lambda item: item[1], reverse=True)


def build_candidate_summary(name: str, resume_text: str, job_description: str) -> str:
    score = score_resume_against_job(resume_text, job_description)
    required_skills = extract_required_skills(job_description)
    resume_keywords = extract_keywords(resume_text)
    matched = sorted(set(required_skills) & resume_keywords)
    missing = [skill for skill in required_skills if skill not in resume_keywords]
    experience_years = extract_years_of_experience(resume_text)

    if score >= 80:
        fit = "Strong fit"
        recommendation = "Shortlist"
    elif score >= 60:
        fit = "Good fit"
        recommendation = "Interview"
    elif score >= 40:
        fit = "Possible fit"
        recommendation = "Review manually"
    else:
        fit = "Low fit"
        recommendation = "Reject"

    match_text = ", ".join(matched) if matched else "none"
    missing_text = ", ".join(missing[:5]) if missing else "none"
    preview = resume_text.strip().replace("\n", " ")
    preview = re.sub(r"\s+", " ", preview)[:160]

    return (
        "\n" + "-" * 36 + "\n"
        f"Candidate: {name}\n"
        f"Fit: {fit} ({score:.2f}/100)\n"
        f"Recommendation: {recommendation}\n"
        f"Experience: {experience_years} years\n"
        f"Matched required skills: {match_text}\n"
        f"Missing skills: {missing_text}\n"
        f"Resume preview: {preview}\n"
        f"Job description: {job_description}\n"
        + "-" * 36
    )


def build_shortlist_report(candidate_scores: List[Tuple[str, float]], job_description: str) -> str:
    if not candidate_scores:
        return "No shortlisted candidates yet."

    lines = [
        "=" * 36,
        "Shortlist Results",
        f"Job: {job_description}",
        "=" * 36,
    ]
    for index, (name, score) in enumerate(candidate_scores[:10], start=1):
        lines.append(f"{index}. {name} — {score:.2f}/100")
    lines.append("=" * 36)
    return "\n".join(lines)
