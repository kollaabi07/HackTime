from utils.resume_match import (
    build_candidate_summary,
    extract_required_skills,
    extract_text_from_pdf_bytes,
    extract_years_of_experience,
)


def test_extract_text_from_pdf_bytes_reads_text():
    pdf_bytes = (
        b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 300] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
        b"4 0 obj\n<< /Length 52 >>\nstream\nBT\n/F1 18 Tf\n72 720 Td\n(Python developer with Django and SQL) Tj\nET\nendstream\nendobj\n"
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
    )

    text = extract_text_from_pdf_bytes(pdf_bytes)
    assert "Python developer" in text
    assert "Django" in text
    assert "SQL" in text


def test_extract_required_skills_keeps_important_terms():
    jd = "Need Python developer with Django SQL REST APIs and teamwork"
    skills = extract_required_skills(jd)

    assert "python" in skills
    assert "django" in skills
    assert "sql" in skills
    assert "api" in skills


def test_build_candidate_summary_lists_missing_skills():
    jd = "Need Python developer with Django SQL REST APIs and teamwork"
    resume = "Python developer with SQL and teamwork experience"

    summary = build_candidate_summary("Alice", resume, jd)

    assert "Missing skills" in summary
    assert "django" in summary.lower()
    assert "api" in summary.lower()


def test_extract_years_of_experience_and_summary_has_experience_section():
    jd = "Need Python developer with Django SQL REST APIs and teamwork"
    resume = "Python developer with 3 years of Django and SQL experience and REST APIs work"

    years = extract_years_of_experience(resume)
    summary = build_candidate_summary("Alice", resume, jd)

    assert years >= 3
    assert "Experience:" in summary
    assert "Recommendation:" in summary
