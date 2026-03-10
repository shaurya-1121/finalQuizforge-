"""
QuizForge v5.0 — Pyq_database.py
Lightweight JSON-backed persistent question store with full-text search.

Fixes applied:
  BUG-06: load_questions() now uses a file-mtime cache so the JSON file is
          only re-read from disk when it has actually changed.
"""

import json
import os
import time
import hashlib
import re
from pathlib import Path
from typing import Optional

DB_FILE   = Path(os.environ.get("QUIZFORGE_DB", "questions.json"))
META_FILE = Path("meta.json")

# ── In-memory cache (FIX BUG-06) ────────────────────────────────────────────
_cache: list = []
_cache_mtime: float = 0.0


# ── Schema default ──────────────────────────────────────────────────────────
def _default_meta() -> dict:
    return {"scraped_at": 0, "count": 0, "sources": [], "version": "5.0"}


def _load_meta() -> dict:
    if META_FILE.exists():
        try:
            return json.loads(META_FILE.read_text())
        except Exception:
            pass
    return _default_meta()


def _save_meta(meta: dict):
    META_FILE.write_text(json.dumps(meta, ensure_ascii=False, indent=2))


# ── Core DB ops ─────────────────────────────────────────────────────────────
def load_questions() -> list:
    """
    Load all questions from disk.
    FIX BUG-06: Only re-reads the JSON file when DB_FILE mtime has changed.
    All other calls return the cached list directly (no disk I/O).
    """
    global _cache, _cache_mtime

    if not DB_FILE.exists():
        _cache = []
        _cache_mtime = 0.0
        return []

    try:
        mtime = DB_FILE.stat().st_mtime
    except OSError:
        return _cache

    if mtime == _cache_mtime:
        # File unchanged — return cached list  # FIX BUG-06
        return _cache

    # File changed (or first load) — re-read from disk
    try:
        data = json.loads(DB_FILE.read_text(encoding="utf-8"))
        if isinstance(data, list):
            _cache = data
        elif isinstance(data, dict) and "questions" in data:
            _cache = data["questions"]
        else:
            _cache = []
        _cache_mtime = mtime
    except Exception:
        _cache = []

    return _cache


def save_questions(questions: list):
    """Persist questions list to disk atomically, then invalidate cache."""
    global _cache, _cache_mtime

    tmp = DB_FILE.with_suffix(".tmp")
    payload = {
        "version": "5.0",
        "saved_at": time.time(),
        "count": len(questions),
        "questions": questions,
    }
    tmp.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    tmp.replace(DB_FILE)

    # Invalidate cache so next load_questions() re-reads the new file
    _cache_mtime = 0.0
    _cache = []

    meta = _load_meta()
    meta["scraped_at"] = time.time()
    meta["count"] = len(questions)
    sources = list({q.get("source", "") for q in questions if q.get("source")})
    meta["sources"] = sources
    _save_meta(meta)


def count_questions() -> int:
    return len(load_questions())


def clear_questions():
    global _cache, _cache_mtime
    if DB_FILE.exists():
        DB_FILE.unlink()
    _cache = []
    _cache_mtime = 0.0
    _save_meta(_default_meta())


def is_stale(max_age_hours: float = 24.0) -> bool:
    """Return True if DB is empty or older than max_age_hours."""
    meta = _load_meta()
    if meta["count"] == 0:
        return True
    age = time.time() - meta["scraped_at"]
    return age > max_age_hours * 3600


# ── Query helpers ────────────────────────────────────────────────────────────
def get_questions(
    exam: Optional[str] = None,
    chapter: Optional[str] = None,
    difficulty: Optional[str] = None,
    year: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    per_page: int = 200,
) -> dict:
    """Filter, search, and paginate questions."""
    pool = load_questions()

    if exam and exam.upper() != "ALL":
        pool = [q for q in pool if q.get("exam", "").upper() == exam.upper()]

    if chapter and chapter != "ALL":
        pool = [q for q in pool if q.get("chapter", "").lower() == chapter.lower()]

    if difficulty and difficulty != "ALL":
        pool = [q for q in pool if q.get("difficulty", "") == difficulty]

    if year and year != "ALL":
        pool = [q for q in pool if str(q.get("year", "")) == year]

    if search:
        kw = search.lower()
        pool = [q for q in pool if kw in q.get("question", "").lower()
                or kw in q.get("chapter", "").lower()]

    total = len(pool)
    start = (page - 1) * per_page
    end   = start + per_page

    return {
        "total":    total,
        "page":     page,
        "per_page": per_page,
        "questions": pool[start:end],
    }


def get_by_id(qid: str) -> Optional[dict]:
    for q in load_questions():
        if q.get("id") == qid:
            return q
    return None


def get_stats() -> dict:
    qs = load_questions()
    exams = {}
    chapters = {}
    difficulties = {}
    years = {}
    sources = {}

    for q in qs:
        e = q.get("exam", "GK")
        exams[e] = exams.get(e, 0) + 1

        c = q.get("chapter", "General")
        chapters[c] = chapters.get(c, 0) + 1

        d = q.get("difficulty", "Medium")
        difficulties[d] = difficulties.get(d, 0) + 1

        y = str(q.get("year", "Practice"))
        years[y] = years.get(y, 0) + 1

        s = q.get("source", "Unknown")
        sources[s] = sources.get(s, 0) + 1

    return {
        "total":         len(qs),
        "by_exam":       exams,
        "by_chapter":    dict(sorted(chapters.items(), key=lambda x: -x[1])[:20]),
        "by_difficulty": difficulties,
        "by_year":       dict(sorted(years.items(), reverse=True)[:15]),
        "by_source":     sources,
        "meta":          _load_meta(),
    }


def upsert_question(q: dict) -> bool:
    """Insert or update a single question by ID."""
    qs = load_questions()
    qid = q.get("id")
    if not qid:
        return False
    for i, existing in enumerate(qs):
        if existing.get("id") == qid:
            qs[i] = q
            save_questions(qs)
            return True
    qs.append(q)
    save_questions(qs)
    return True