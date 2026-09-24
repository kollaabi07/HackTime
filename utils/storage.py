import sqlite3
from typing import List, Tuple

from utils.resume_match import score_resume_against_job

DB_PATH = "candidates.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            resume TEXT NOT NULL,
            job_description TEXT NOT NULL,
            score REAL NOT NULL
        )
        """
    )
    return conn


def save_candidate(name: str, resume: str, job_description: str) -> float:
    score = score_resume_against_job(resume, job_description)
    conn = get_connection()
    conn.execute(
        "INSERT INTO candidates (name, resume, job_description, score) VALUES (?, ?, ?, ?)",
        (name, resume, job_description, score),
    )
    conn.commit()
    conn.close()
    return score


def get_ranked_candidates(job_description: str) -> List[Tuple[str, float]]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT name, score FROM candidates WHERE job_description = ? ORDER BY score DESC",
        (job_description,),
    ).fetchall()
    conn.close()
    return [(name, float(score)) for name, score in rows]
