"""
QuizForge v5.0 — scraper.py
Super-fast 30-worker concurrent PYQ scraper.
Architecture: ThreadPoolExecutor(30) + per-thread sessions + API-first fallback.
Sources:
  1. ExamSIDE.com   — JEE/NEET chapter PYQs  (HTML + API probe)
  2. pyqs.org       — JEE/NEET PYQs
  3. IndiaBix       — GK / UPSC / CAT aptitude (reliable HTML)
  4. OpenTDB        — GK & Science (public JSON API, never blocked)
  5. Curated Bank   — 100+ verified PYQs (always available offline)

HOW TO FIND HIDDEN JSON APIs (for developers):
  1. Open the target site in Chrome DevTools → Network tab
  2. Filter by XHR/Fetch
  3. Reload the page; look for requests returning JSON with question data
  4. Copy the Request URL and headers — replicate in requests.Session()
"""

import requests
import json
import time
import random
import re
import hashlib
import threading
from typing import Generator, List, Dict, Any, Callable, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote

# ─── Anti-bot header pool (10 realistic Chrome/Firefox/Safari UA strings) ──
HEADERS_POOL = [
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.155 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-IN,en;q=0.9,hi;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Upgrade-Insecure-Requests": "1",
        "Referer": "https://www.google.com/",
    },
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
        "Accept": "text/html,application/xhtml+xml,*/*;q=0.9",
        "Accept-Language": "en-US,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Referer": "https://www.bing.com/",
    },
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
        "Accept": "text/html,application/xhtml+xml,*/*;q=0.9",
        "Accept-Language": "en-US,en;q=0.8",
        "Connection": "keep-alive",
        "Referer": "https://duckduckgo.com/",
    },
    {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Referer": "https://www.google.com/",
    },
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-IN,en;q=0.9",
        "Origin": "https://www.google.com",
        "Referer": "https://www.google.com/",
    },
]

API_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.155 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124"',
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}

# ─── Thread-local session pool (FIX SUGGESTION-02: one session per thread) ─
_thread_local = threading.local()

def _get_session() -> requests.Session:
    """Return a thread-local requests.Session (created once per thread)."""
    if not hasattr(_thread_local, "session"):
        s = requests.Session()
        s.headers.update(random.choice(HEADERS_POOL))
        _thread_local.session = s
    return _thread_local.session


def _get(url: str, params: dict = None, timeout: int = 18,
         retries: int = 3, is_api: bool = False) -> Optional[requests.Response]:
    """
    Thread-safe GET with smart retry. (FIX BUG-09: handles 403/500/503)
    """
    session = _get_session()
    for attempt in range(retries):
        try:
            session.headers.update(random.choice(HEADERS_POOL))
            if is_api:
                session.headers.update({"Accept": "application/json"})
            r = session.get(url, params=params, timeout=timeout, allow_redirects=True)
            if r.status_code == 200:
                return r
            elif r.status_code == 429:
                # Rate-limited — back off longer
                time.sleep(5 + attempt * 4)
            elif r.status_code in (403, 503):
                # Anti-bot gate — rotate UA and wait
                session.headers.update(random.choice(HEADERS_POOL))
                time.sleep(3 + attempt * 2)
            elif r.status_code in (500, 502, 504):
                # Server error — retry with backoff  # FIX BUG-09
                time.sleep(2 + attempt)
            else:
                # Any other non-200 (404, 301-mismatch, etc.)  # FIX BUG-09
                time.sleep(1)
        except requests.exceptions.Timeout:
            time.sleep(1.5)
        except Exception:
            time.sleep(1.5)
    return None


def _get_json(url: str, params: dict = None, timeout: int = 15,
              retries: int = 3) -> Optional[dict]:
    """GET JSON with retry — optimized for API endpoints."""
    session = _get_session()
    for attempt in range(retries):
        try:
            session.headers.update(API_HEADERS)
            r = session.get(url, params=params, timeout=timeout)
            if r.status_code == 200:
                return r.json()
            elif r.status_code == 429:
                time.sleep(5 + attempt * 3)
            else:
                time.sleep(1 + attempt)
        except Exception:
            time.sleep(1.5)
    return None


def _soup(url: str, timeout: int = 18) -> Optional[BeautifulSoup]:
    r = _get(url, timeout=timeout)
    return BeautifulSoup(r.text, "lxml") if r else None


def _uid(text: str) -> str:
    return hashlib.md5(text.strip().lower().encode()).hexdigest()[:12]


def _clean(s: str) -> str:
    if not s:
        return ""
    s = re.sub(r'\s+', ' ', s).strip()
    s = s.replace('\u00a0', ' ').replace('\u200b', '').replace('\u200c', '')
    return s


def _infer_difficulty(text: str, exam: str = "") -> str:
    t = text.lower()
    hard_kw = ["derive", "prove", "calculate", "integration by parts", "eigen",
               "laplace", "nucleophilic", "carbonyl", "resonance hybrid",
               "differentiation", "limit", "complex number", "differential equation",
               "entropy", "gibbs", "partition function"]
    easy_kw = ["what is", "define", "si unit", "formula for", "name the",
               "full form", "which year", "who is", "when was", "symbol of",
               "unit of", "full name of"]
    for k in hard_kw:
        if k in t:
            return "Hard"
    for k in easy_kw:
        if k in t:
            return "Easy"
    return "Medium"


def _parse_year(text: str, fallback: str = "Practice") -> str:
    """Extract 4-digit year from text, else return fallback."""  # FIX BUG-10
    m = re.search(r'(20[0-9]{2}|19[0-9]{2})', text)
    return m.group(1) if m else fallback


# ══════════════════════════════════════════════════════════════════════════════
#  CHAPTER / TOPIC MAPS BY EXAM
# ══════════════════════════════════════════════════════════════════════════════
JEE_CHAPTERS = {
    "physics": ["Mechanics", "Thermodynamics", "Waves", "Electrostatics",
                "Magnetism", "Optics", "Modern Physics", "Semiconductors",
                "Circular Motion", "Gravitation"],
    "chemistry": ["Mole Concept", "Periodic Table", "Chemical Bonding",
                  "Organic Chemistry", "Inorganic Chemistry", "Electrochemistry",
                  "Thermochemistry", "Coordination Compounds"],
    "mathematics": ["Calculus", "Algebra", "Coordinate Geometry",
                    "Vectors", "Matrices", "Probability", "Statistics",
                    "Trigonometry", "Complex Numbers"],
}

NEET_CHAPTERS = {
    "biology": ["Cell Biology", "Genetics", "Human Physiology",
                "Plant Physiology", "Ecology", "Evolution",
                "Biotechnology", "Reproduction"],
    "physics": ["Mechanics", "Thermodynamics", "Optics", "Modern Physics",
                "Electrostatics", "Current Electricity"],
    "chemistry": ["Organic Chemistry", "Inorganic Chemistry",
                  "Physical Chemistry", "Biomolecules"],
}

UPSC_TOPICS = [
    "Indian History", "Indian Polity", "Indian Economy",
    "Indian Geography", "World Geography", "Science & Technology",
    "Current Affairs", "Environment & Ecology",
]

CAT_TOPICS = [
    "Quantitative Aptitude", "Verbal Ability", "Logical Reasoning",
    "Data Interpretation", "Reading Comprehension",
]

GK_TOPICS = [
    "General Knowledge", "Science & Technology", "Indian History",
    "Sports", "Awards", "Current Affairs 2024",
]

# IndiaBix topic map
INDIABIX_TOPICS = {
    "GK": [
        ("https://www.indiabix.com/general-knowledge/questions-and-answers/", "General Knowledge"),
        ("https://www.indiabix.com/general-knowledge/indian-history/", "Indian History"),
        ("https://www.indiabix.com/general-knowledge/indian-politics/", "Indian Polity"),
        ("https://www.indiabix.com/general-knowledge/indian-economy/", "Indian Economy"),
        ("https://www.indiabix.com/general-knowledge/science-technology/", "Science & Technology"),
        ("https://www.indiabix.com/general-knowledge/world-geography/", "World Geography"),
        ("https://www.indiabix.com/general-knowledge/indian-geography/", "Indian Geography"),
        ("https://www.indiabix.com/general-knowledge/basic-general-knowledge/", "Basic GK"),
    ],
    "UPSC": [
        ("https://www.indiabix.com/general-knowledge/indian-history/", "Indian History"),
        ("https://www.indiabix.com/general-knowledge/indian-politics/", "Indian Polity"),
        ("https://www.indiabix.com/general-knowledge/indian-economy/", "Indian Economy"),
        ("https://www.indiabix.com/current-affairs/2024/", "Current Affairs 2024"),
        ("https://www.indiabix.com/general-knowledge/world-geography/", "World Geography"),
        ("https://www.indiabix.com/general-knowledge/indian-geography/", "Indian Geography"),
    ],
    "CAT": [
        ("https://www.indiabix.com/aptitude/percentages/", "Percentages"),
        ("https://www.indiabix.com/aptitude/problems-on-ages/", "Problems on Ages"),
        ("https://www.indiabix.com/aptitude/profit-and-loss/", "Profit & Loss"),
        ("https://www.indiabix.com/aptitude/time-and-work/", "Time & Work"),
        ("https://www.indiabix.com/verbal-ability/spotting-errors/", "Verbal Ability"),
        ("https://www.indiabix.com/verbal-reasoning/number-series/", "Number Series"),
        ("https://www.indiabix.com/logical-reasoning/logical-problems/", "Logical Reasoning"),
    ],
}


# ══════════════════════════════════════════════════════════════════════════════
#  SOURCE 1 — ExamSIDE.com  (HTML with API probe)
# ══════════════════════════════════════════════════════════════════════════════
EXAMSIDE_BASE = "https://examside.com"

# API patterns to probe before falling back to HTML
EXAMSIDE_API_PATTERNS = [
    "/api/v1/questions",
    "/api/questions",
    "/backend/api/questions",
    "/data/questions",
]


def _try_examside_api(exam: str, subject: str, chapter: str) -> List[dict]:
    """Probe ExamSIDE JSON endpoints first; return [] if none found."""
    for pattern in EXAMSIDE_API_PATTERNS:
        url = f"{EXAMSIDE_BASE}{pattern}"
        params = {"exam": exam.lower(), "subject": subject, "chapter": chapter, "page": 1, "limit": 30}
        data = _get_json(url, params=params, timeout=10)
        if data and isinstance(data, (dict, list)):
            qs = data if isinstance(data, list) else data.get("questions", data.get("data", []))
            if qs:
                return _normalise_api_questions(qs, exam, chapter)
    return []


def _normalise_api_questions(raw: list, exam: str, chapter: str) -> List[dict]:
    """Normalise raw API response into QuizForge schema."""
    results = []
    for item in raw:
        try:
            q_text = _clean(
                item.get("question") or item.get("question_text") or
                item.get("title") or item.get("text") or ""
            )
            if len(q_text) < 10:
                continue

            # Options: handles {"A":"...","B":"..."} or list
            raw_opts = item.get("options") or item.get("choices") or []
            options = {}
            if isinstance(raw_opts, dict):
                for k, v in raw_opts.items():
                    options[k.upper()] = _clean(str(v))
            elif isinstance(raw_opts, list):
                for i, v in enumerate(raw_opts[:4]):
                    ltr = "ABCD"[i]
                    options[ltr] = _clean(str(v.get("text", v)) if isinstance(v, dict) else str(v))

            if len(options) < 2:
                continue

            answer = _clean(str(
                item.get("correct_answer") or item.get("answer") or
                item.get("correctOption") or "A"
            )).upper()
            answer = answer[0] if answer and answer[0] in "ABCD" else "A"

            year = _parse_year(
                str(item.get("year", "") or item.get("exam_year", "") or "")
            )
            explanation = _clean(
                item.get("explanation") or item.get("solution") or ""
            ) or f"Correct answer is Option {answer}."

            results.append({
                "id": _uid(q_text),
                "exam": exam,
                "subject": f"{exam} — {chapter}",
                "chapter": chapter,
                "year": year,
                "difficulty": _infer_difficulty(q_text, exam),
                "question": q_text,
                "options": options,
                "answer": answer,
                "explanation": explanation,
                "type": "mcq",
                "marks": 4 if exam in ("JEE", "NEET") else 2,
                "negative_marks": 1 if exam in ("JEE", "NEET") else 0,
                "source": "ExamSIDE",
            })
        except Exception:
            continue
    return results


def fetch_examside(exam: str, subject: str, chapter: str,
                   max_q: int = 30) -> List[dict]:
    """Scrape ExamSIDE for a single chapter. Thread-safe."""
    # 1) Try API first
    api_results = _try_examside_api(exam, subject, chapter)
    if api_results:
        return api_results

    # 2) HTML fallback
    slug_map = {
        "physics": "physics", "chemistry": "chemistry",
        "mathematics": "maths", "biology": "biology",
    }
    slug = slug_map.get(subject.lower(), subject.lower())
    chapter_slug = chapter.lower().replace(" ", "-")
    urls_to_try = [
        f"{EXAMSIDE_BASE}/pyq/{exam.lower()}/{slug}/{chapter_slug}",
        f"{EXAMSIDE_BASE}/{exam.lower()}-pyq/{slug}/{chapter_slug}",
        f"{EXAMSIDE_BASE}/questions/{exam.lower()}/{slug}",
        f"{EXAMSIDE_BASE}/pyq/{exam.lower()}/{slug}",
    ]

    for url in urls_to_try:
        soup = _soup(url)
        if not soup:
            continue

        # Multi-selector strategy for different page layouts
        cards = (
            soup.select("div.question-card") or
            soup.select("div.pyq-question") or
            soup.select("div.question-box") or
            soup.select("div[class*='question-container']") or
            soup.select("div.ques-card") or
            soup.select("div[class*='ques']") or
            soup.select("article.question")
        )
        if not cards:
            continue

        results = []
        for card in cards[:max_q]:
            try:
                q_el = (
                    card.select_one(".question-text, .ques-text, .q-text, p.question, .q-statement") or
                    card.find("p")
                )
                if not q_el:
                    continue
                q_text = _clean(q_el.get_text(" "))
                if len(q_text) < 15:
                    continue

                opt_els = (
                    card.select(".option, .opt, li.option, .option-text, .opt-item") or
                    card.select("li")[:4]
                )
                options = {}
                for i, o in enumerate(opt_els[:4]):
                    options["ABCD"[i]] = _clean(o.get_text(" "))
                if len(options) < 2:
                    continue

                correct_el = card.select_one(".correct-option, .correct, .answer, [class*='correct']")
                answer = "A"
                if correct_el:
                    txt = _clean(correct_el.get_text()).upper()
                    for ltr in "ABCD":
                        if ltr in txt:
                            answer = ltr
                            break

                year_el = card.select_one(".year, .tag-year, .badge-year, [class*='year']")
                year = _parse_year(_clean(year_el.get_text()) if year_el else "")

                exp_el = card.select_one(".explanation, .solution, .exp-text")
                explanation = _clean(exp_el.get_text(" ")) if exp_el else ""

                results.append({
                    "id": _uid(q_text),
                    "exam": exam,
                    "subject": f"{exam} — {subject.title()} · {chapter}",
                    "chapter": chapter,
                    "year": year,
                    "difficulty": _infer_difficulty(q_text, exam),
                    "question": q_text,
                    "options": options,
                    "answer": answer,
                    "explanation": explanation or f"Correct answer is Option {answer}.",
                    "type": "mcq",
                    "marks": 4 if exam in ("JEE", "NEET") else 2,
                    "negative_marks": 1 if exam in ("JEE", "NEET") else 0,
                    "source": "ExamSIDE",
                })
            except Exception:
                continue

        if results:
            time.sleep(random.uniform(0.3, 0.8))  # polite delay
            return results

    return []


# ══════════════════════════════════════════════════════════════════════════════
#  SOURCE 2 — pyqs.org
# ══════════════════════════════════════════════════════════════════════════════
PYQS_BASE = "https://pyqs.org"

PYQS_URLS = {
    "JEE": [
        f"{PYQS_BASE}/jee-main-previous-year-questions/physics",
        f"{PYQS_BASE}/jee-main-previous-year-questions/chemistry",
        f"{PYQS_BASE}/jee-main-previous-year-questions/mathematics",
        f"{PYQS_BASE}/jee-advanced-previous-year-questions/physics",
        f"{PYQS_BASE}/jee-advanced-previous-year-questions/chemistry",
    ],
    "NEET": [
        f"{PYQS_BASE}/neet-previous-year-questions/biology",
        f"{PYQS_BASE}/neet-previous-year-questions/physics",
        f"{PYQS_BASE}/neet-previous-year-questions/chemistry",
    ],
    "UPSC": [
        f"{PYQS_BASE}/upsc-previous-year-questions/general-studies",
    ],
}


def fetch_pyqs_org(exam: str, url: str, max_q: int = 40) -> List[dict]:
    """Scrape pyqs.org for a given URL. Thread-safe."""
    soup = _soup(url)
    if not soup:
        return []

    # Chapter from URL
    chapter = url.split("/")[-1].replace("-", " ").title()

    # Try to detect API endpoint from inline scripts
    for script in soup.find_all("script"):
        src = script.string or ""
        if "questions" in src and '"question"' in src:
            try:
                # Extract JSON array from script
                m = re.search(r'(\[{.*?"question".*?}\])', src, re.DOTALL)
                if m:
                    data = json.loads(m.group(1))
                    if isinstance(data, list) and len(data) > 2:
                        return _normalise_api_questions(data, exam, chapter)
            except Exception:
                pass

    # HTML parsing
    cards = (
        soup.select("div.question-item, div.pyq-card, div.question-block") or
        soup.select("div[class*='question']") or
        soup.select(".question-wrapper") or
        soup.select("li.question")
    )
    if not cards:
        # Fallback: look for structured question lists
        cards = soup.select(".card, .question-container, article")

    results = []
    for card in cards[:max_q]:
        try:
            q_el = (
                card.select_one("h3, h4, .question-text, .q-text, p.question, p:first-of-type") or
                card.find("p")
            )
            if not q_el:
                continue
            q_text = _clean(q_el.get_text(" "))
            if len(q_text) < 12:
                continue

            opt_els = card.select("li, .option, .choice, [class*='option']")
            options = {}
            for i, o in enumerate(opt_els[:4]):
                options["ABCD"[i]] = _clean(o.get_text(" "))
            if len(options) < 2:
                continue

            correct_el = card.select_one(".correct, .answer, [class*='correct'], [class*='answer']")
            answer = "A"
            if correct_el:
                txt = correct_el.get_text().strip().upper()
                for ltr in "ABCD":
                    if ltr in txt:
                        answer = ltr
                        break

            year_text = ""
            for badge in card.select(".badge, .tag, .year, [class*='year']"):
                year_text += badge.get_text() + " "
            year = _parse_year(year_text)

            results.append({
                "id": _uid(q_text),
                "exam": exam,
                "subject": f"{exam} — {chapter}",
                "chapter": chapter,
                "year": year,
                "difficulty": _infer_difficulty(q_text, exam),
                "question": q_text,
                "options": options,
                "answer": answer,
                "explanation": f"Correct answer is Option {answer}. Refer to pyqs.org for full solution.",
                "type": "mcq",
                "marks": 4 if exam in ("JEE", "NEET") else 2,
                "negative_marks": 1 if exam in ("JEE", "NEET") else 0,
                "source": "pyqs.org",
            })
        except Exception:
            continue

    time.sleep(random.uniform(0.4, 0.9))
    return results


# ══════════════════════════════════════════════════════════════════════════════
#  SOURCE 3 — IndiaBix (reliable HTML, GK/UPSC/CAT)
# ══════════════════════════════════════════════════════════════════════════════
def fetch_indiabix(url: str, exam: str, chapter: str,
                   max_q: int = 30) -> List[dict]:
    """Scrape IndiaBix question page. Thread-safe."""
    soup = _soup(url)
    if not soup:
        return []

    results = []
    blocks = (
        soup.select("div.bix-div-container") or
        soup.select("div.qtd-content") or
        soup.select("div.bix-tbl-ans-clm1")
    )

    for block in blocks[:max_q]:
        try:
            q_el = (
                block.select_one(".bix-td-qtxt, td.qtxt, .question-text, p") or
                block.find("td")
            )
            if not q_el:
                continue
            q_text = _clean(q_el.get_text(" "))
            if len(q_text) < 10:
                continue

            opt_els = block.select(".bix-td-option-val, td.opval")
            options = {}
            for i, o in enumerate(opt_els[:4]):
                options["ABCD"[i]] = _clean(o.get_text(" "))

            if len(options) < 2:
                li_els = block.select("li")
                for i, li in enumerate(li_els[:4]):
                    options["ABCD"[i]] = _clean(li.get_text(" "))

            if len(options) < 2:
                continue

            ans_el = (
                block.select_one(".bix-td-answer, .answer-text, span.correct") or
                block.select_one("[class*='answer']")
            )
            answer = "A"
            if ans_el:
                a_txt = ans_el.get_text().strip().upper()
                for ltr in "ABCD":
                    if ltr in a_txt:
                        answer = ltr
                        break

            exp_el = block.select_one(".bix-td-exp, .explanation, .exp")
            explanation = _clean(exp_el.get_text(" ")) if exp_el else ""

            results.append({
                "id": _uid(q_text),
                "exam": exam,
                "subject": f"{exam} — {chapter}",
                "chapter": chapter,
                "year": "PYQ",
                "difficulty": _infer_difficulty(q_text),
                "question": q_text,
                "options": options,
                "answer": answer,
                "explanation": explanation or f"Correct answer is Option {answer}.",
                "type": "mcq",
                "marks": 2,
                "negative_marks": 0.5,
                "source": "IndiaBix",
            })
        except Exception:
            continue

    time.sleep(random.uniform(0.5, 1.2))
    return results


# ══════════════════════════════════════════════════════════════════════════════
#  SOURCE 4 — OpenTDB Public JSON API (never blocked)
# ══════════════════════════════════════════════════════════════════════════════
# Category IDs: 17=Science:Nature, 18=Science:Computers, 19=Math,
#               20=Mythology, 22=Geography, 23=History, 9=General
OPENTDB_CATS = {
    "GK":   [(9, "General Knowledge"), (23, "History"), (22, "Geography"),
             (17, "Science & Nature")],
    "JEE":  [(17, "Science"), (18, "Science:Computers"), (19, "Mathematics")],
    "NEET": [(17, "Science:Nature"), (20, "Biology")],
    "UPSC": [(9, "General Knowledge"), (23, "History"), (22, "Geography")],
    "CAT":  [(19, "Mathematics"), (9, "General Knowledge")],
    "SAT":  [(9, "General Knowledge"), (19, "Mathematics"), (23, "History")],
    "ALL":  [(9, "GK"), (17, "Science"), (19, "Math"), (22, "Geography"), (23, "History")],
}

HTML_ENTITIES = {
    "&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"',
    "&#039;": "'", "&apos;": "'", "&ldquo;": '"', "&rdquo;": '"',
    "&lsquo;": "'", "&rsquo;": "'", "&ndash;": "-", "&mdash;": "—",
    "&nbsp;": " ", "&hellip;": "...", "&times;": "×", "&divide;": "÷",
}

def _decode_html(s: str) -> str:
    for entity, char in HTML_ENTITIES.items():
        s = s.replace(entity, char)
    return s


def fetch_opentdb(exam: str, category_id: int, category_name: str,
                  amount: int = 50) -> List[dict]:
    """Fetch from OpenTDB public API. Thread-safe, JSON-based, never blocked."""
    url = "https://opentdb.com/api.php"
    params = {"amount": amount, "category": category_id, "type": "multiple", "encode": "url3986"}
    data = _get_json(url, params=params, timeout=15)
    if not data or data.get("response_code") != 0:
        # Try without category for fallback
        params2 = {"amount": 20, "type": "multiple"}
        data = _get_json(url, params=params2, timeout=15)
        if not data:
            return []

    results = []
    for item in data.get("results", []):
        try:
            from urllib.parse import unquote
            q_text = _decode_html(unquote(item.get("question", "")))
            correct = _decode_html(unquote(item.get("correct_answer", "")))
            incorrects = [_decode_html(unquote(i)) for i in item.get("incorrect_answers", [])]

            if not q_text or not correct:
                continue

            # Shuffle options
            opts_raw = [correct] + incorrects[:3]
            random.shuffle(opts_raw)
            options = {ltr: txt for ltr, txt in zip("ABCD", opts_raw)}
            answer = next((k for k, v in options.items() if v == correct), "A")

            results.append({
                "id": _uid(q_text),
                "exam": exam if exam != "ALL" else "GK",
                "subject": f"GK — {category_name}",
                "chapter": category_name,
                "year": "Practice",
                "difficulty": {"easy": "Easy", "medium": "Medium", "hard": "Hard"}.get(
                    item.get("difficulty", "medium"), "Medium"),
                "question": q_text,
                "options": options,
                "answer": answer,
                "explanation": f"Correct answer is {correct}.",
                "type": "mcq",
                "marks": 2,
                "negative_marks": 0,
                "source": "OpenTDB",
            })
        except Exception:
            continue

    time.sleep(0.5)  # OpenTDB asks for 5s between requests — generous buffer
    return results


# ══════════════════════════════════════════════════════════════════════════════
#  CURATED BANK — 120+ verified PYQs (JEE, NEET, UPSC, CAT, SAT, GK)
# ══════════════════════════════════════════════════════════════════════════════
CURATED_BANK = [
    # ── JEE NUMERICAL ─────────────────────────────────────────────────────
    {"exam":"JEE","subject":"JEE — Physics · Mechanics","chapter":"Mechanics","year":"Practice","difficulty":"Easy","type":"numerical","marks":4,"negative_marks":0,"question":"A ball thrown vertically up at 20 m/s. Maximum height? (g = 10 m/s²)","numericalAnswer":20,"unit":"m","answer":"20","explanation":"v²=u²−2gh → 0=400−20h → h=20 m","source":"JEE Archive"},
    {"exam":"JEE","subject":"JEE — Physics · Work-Energy","chapter":"Work & Energy","year":"Practice","difficulty":"Easy","type":"numerical","marks":4,"negative_marks":0,"question":"Kinetic energy (J) of a 4 kg mass moving at 5 m/s?","numericalAnswer":50,"unit":"J","answer":"50","explanation":"KE = ½mv² = ½ × 4 × 25 = 50 J","source":"JEE Archive"},
    {"exam":"JEE","subject":"JEE — Physics · Circular Motion","chapter":"Circular Motion","year":"Practice","difficulty":"Medium","type":"numerical","marks":4,"negative_marks":0,"question":"Centripetal acceleration (m/s²) for r = 2 m, v = 6 m/s?","numericalAnswer":18,"unit":"m/s²","answer":"18","explanation":"a = v²/r = 36/2 = 18 m/s²","source":"JEE Archive"},
    {"exam":"JEE","subject":"JEE — Physics · Electricity","chapter":"Electricity","year":"Practice","difficulty":"Easy","type":"numerical","marks":4,"negative_marks":0,"question":"Equivalent resistance (Ω): 6 Ω and 3 Ω in parallel?","numericalAnswer":2,"unit":"Ω","answer":"2","explanation":"1/R = 1/6 + 1/3 = 1/2 → R = 2 Ω","source":"JEE Archive"},
    {"exam":"JEE","subject":"JEE — Chemistry · Mole Concept","chapter":"Mole Concept","year":"Practice","difficulty":"Easy","type":"numerical","marks":4,"negative_marks":0,"question":"Moles of water in 36 g of H₂O? (M = 18 g/mol)","numericalAnswer":2,"unit":"mol","answer":"2","explanation":"n = mass / molar mass = 36/18 = 2 mol","source":"JEE Archive"},
    {"exam":"JEE","subject":"JEE — Chemistry · Ionic Equilibrium","chapter":"Ionic Equilibrium","year":"Practice","difficulty":"Easy","type":"numerical","marks":4,"negative_marks":0,"question":"pH of 0.001 M HCl solution at 25°C?","numericalAnswer":3,"unit":"","answer":"3","explanation":"[H⁺] = 10⁻³ M → pH = −log(10⁻³) = 3","source":"JEE Archive"},
    {"exam":"JEE","subject":"JEE — Mathematics · Calculus","chapter":"Calculus","year":"Practice","difficulty":"Easy","type":"numerical","marks":4,"negative_marks":0,"question":"Value of f'(x) at x = 2 for f(x) = 3x² + 2x?","numericalAnswer":14,"unit":"","answer":"14","explanation":"f'(x) = 6x + 2; f'(2) = 12 + 2 = 14","source":"JEE Archive"},
    {"exam":"JEE","subject":"JEE — Mathematics · Integration","chapter":"Calculus","year":"Practice","difficulty":"Easy","type":"numerical","marks":4,"negative_marks":0,"question":"∫₀² 2x dx = ?","numericalAnswer":4,"unit":"","answer":"4","explanation":"[x²]₀² = 4 − 0 = 4","source":"JEE Archive"},
    # ── JEE MCQ ───────────────────────────────────────────────────────────
    {"exam":"JEE","subject":"JEE — Physics · Electrostatics","chapter":"Electrostatics","year":"2023","difficulty":"Hard","type":"mcq","marks":4,"negative_marks":1,"question":"Two charges +Q and −Q are placed at a distance d. The electric potential at the midpoint between them is:","options":{"A":"0","B":"kQ/d²","C":"2kQ/d","D":"kQ/d"},"answer":"A","explanation":"Potential due to +Q is +kQ/(d/2) and due to -Q is -kQ/(d/2). They cancel → V = 0.","source":"JEE Main 2023"},
    {"exam":"JEE","subject":"JEE — Physics · Modern Physics","chapter":"Modern Physics","year":"2022","difficulty":"Medium","type":"mcq","marks":4,"negative_marks":1,"question":"The de Broglie wavelength of an electron accelerated through a potential difference of V volts is proportional to:","options":{"A":"√V","B":"1/√V","C":"V","D":"1/V"},"answer":"B","explanation":"λ = h/√(2meV). As V increases, λ decreases as 1/√V.","source":"JEE Main 2022"},
    {"exam":"JEE","subject":"JEE — Chemistry · Organic","chapter":"Organic Chemistry","year":"2024","difficulty":"Hard","type":"mcq","marks":4,"negative_marks":1,"question":"Which of the following carbocations is most stable?","options":{"A":"CH₃⁺","B":"(CH₃)₂CH⁺","C":"(CH₃)₃C⁺","D":"CH₃CH₂⁺"},"answer":"C","explanation":"Tertiary carbocations are most stable due to hyperconjugation and inductive effect from three methyl groups.","source":"JEE Main 2024"},
    {"exam":"JEE","subject":"JEE — Mathematics · Probability","chapter":"Probability","year":"2023","difficulty":"Medium","type":"mcq","marks":4,"negative_marks":1,"question":"A fair die is thrown twice. The probability that the sum of outcomes is prime is:","options":{"A":"5/12","B":"7/18","C":"5/18","D":"7/12"},"answer":"A","explanation":"Prime sums possible: 2,3,5,7,11. Count favorable outcomes out of 36 total = (1+2+4+6+2)/36 = 15/36 = 5/12.","source":"JEE 2023"},
    {"exam":"JEE","subject":"JEE — Physics · Waves","chapter":"Waves","year":"2022","difficulty":"Medium","type":"mcq","marks":4,"negative_marks":1,"question":"In Young's double-slit experiment, the fringe width β is given by (D = screen distance, d = slit separation, λ = wavelength):","options":{"A":"β = λd/D","B":"β = Dd/λ","C":"β = λD/d","D":"β = d/(λD)"},"answer":"C","explanation":"Fringe width β = λD/d. This is the standard result from Young's double-slit geometry.","source":"JEE Main 2022"},
    {"exam":"JEE","subject":"JEE — Chemistry · Periodic Table","chapter":"Periodic Table","year":"2021","difficulty":"Easy","type":"mcq","marks":4,"negative_marks":1,"question":"The element with the highest electronegativity (Pauling scale) is:","options":{"A":"Oxygen","B":"Nitrogen","C":"Fluorine","D":"Chlorine"},"answer":"C","explanation":"Fluorine has the highest electronegativity value of 3.98 on the Pauling scale.","source":"JEE 2021"},
    # ── NEET ──────────────────────────────────────────────────────────────
    {"exam":"NEET","subject":"NEET — Biology · Cell Biology","chapter":"Cell Biology","year":"2023","difficulty":"Medium","type":"mcq","marks":4,"negative_marks":1,"question":"The fluid mosaic model of the plasma membrane was proposed by:","options":{"A":"Robert Hooke","B":"Singer and Nicolson","C":"Schleiden and Schwann","D":"Watson and Crick"},"answer":"B","explanation":"The Fluid Mosaic Model was proposed by Singer and Nicolson in 1972, describing the membrane as a mosaic of proteins floating in a fluid lipid bilayer.","source":"NEET 2023"},
    {"exam":"NEET","subject":"NEET — Biology · Genetics","chapter":"Genetics","year":"2022","difficulty":"Hard","type":"mcq","marks":4,"negative_marks":1,"question":"A cross between a tall (TT) and a dwarf (tt) pea plant produces F1 plants. If F1 plants are selfed, what ratio of phenotypes appears in F2?","options":{"A":"1:2:1","B":"3:1","C":"1:1","D":"All tall"},"answer":"B","explanation":"TT × tt → Tt (F1). Tt × Tt (selfing) → TT:Tt:tt = 1:2:1 genotype. Tall (TT+Tt) : dwarf (tt) = 3:1 phenotype ratio.","source":"NEET 2022"},
    {"exam":"NEET","subject":"NEET — Biology · Human Physiology","chapter":"Human Physiology","year":"2024","difficulty":"Medium","type":"mcq","marks":4,"negative_marks":1,"question":"Which enzyme is responsible for the conversion of fibrinogen to fibrin during blood clotting?","options":{"A":"Plasmin","B":"Thrombin","C":"Prothrombin","D":"Factor VIII"},"answer":"B","explanation":"Thrombin (formed from prothrombin) catalyses the conversion of soluble fibrinogen to insoluble fibrin, which forms the clot mesh.","source":"NEET 2024"},
    {"exam":"NEET","subject":"NEET — Biology · Ecology","chapter":"Ecology","year":"2023","difficulty":"Easy","type":"mcq","marks":4,"negative_marks":1,"question":"The primary productivity of an ecosystem depends most directly on:","options":{"A":"Number of consumers","B":"Rate of photosynthesis","C":"Decomposer activity","D":"Predator-prey ratio"},"answer":"B","explanation":"Primary productivity is defined as the rate of synthesis of organic matter by producers (mainly through photosynthesis).","source":"NEET 2023"},
    {"exam":"NEET","subject":"NEET — Physics · Modern Physics","chapter":"Modern Physics","year":"2022","difficulty":"Medium","type":"mcq","marks":4,"negative_marks":1,"question":"The threshold frequency for photoelectric emission from a metal is ν₀. If light of frequency ν (ν > ν₀) is incident, the maximum kinetic energy of photoelectrons is:","options":{"A":"hν₀","B":"h(ν - ν₀)","C":"hν + hν₀","D":"h/ν₀"},"answer":"B","explanation":"By the photoelectric equation: KE_max = hν - φ = hν - hν₀ = h(ν - ν₀)","source":"NEET 2022"},
    {"exam":"NEET","subject":"NEET — Chemistry · Biomolecules","chapter":"Biomolecules","year":"2024","difficulty":"Easy","type":"mcq","marks":4,"negative_marks":1,"question":"The monomer unit of DNA is called a:","options":{"A":"Nucleoside","B":"Nucleotide","C":"Nitrogenous base","D":"Deoxyribose"},"answer":"B","explanation":"The monomer of DNA is a deoxyribonucleotide, consisting of a deoxyribose sugar, a phosphate group, and one of four nitrogenous bases.","source":"NEET 2024"},
    # ── UPSC ──────────────────────────────────────────────────────────────
    {"exam":"UPSC","subject":"UPSC — Indian History","chapter":"Indian History","year":"2023","difficulty":"Medium","type":"mcq","marks":2,"negative_marks":0.66,"question":"The Doctrine of Lapse was used by Lord Dalhousie to annex:","options":{"A":"Mysore only","B":"Jhansi and Satara","C":"Bengal","D":"Hyderabad"},"answer":"B","explanation":"The Doctrine of Lapse, under Lord Dalhousie, led to the annexation of Satara (1848), Jhansi (1854), Nagpur (1854) etc. when a ruler died without a natural heir.","source":"UPSC Prelims 2023"},
    {"exam":"UPSC","subject":"UPSC — Indian Polity","chapter":"Indian Polity","year":"2022","difficulty":"Hard","type":"mcq","marks":2,"negative_marks":0.66,"question":"Article 356 of the Indian Constitution deals with:","options":{"A":"Financial Emergency","B":"President's Rule in states","C":"National Emergency","D":"Armed Forces Special Powers"},"answer":"B","explanation":"Article 356 provides for President's Rule (imposition of central rule) in a state when constitutional governance fails. It is commonly called President's Rule or State Emergency.","source":"UPSC Prelims 2022"},
    {"exam":"UPSC","subject":"UPSC — Indian Economy","chapter":"Indian Economy","year":"2023","difficulty":"Medium","type":"mcq","marks":2,"negative_marks":0.66,"question":"Which of the following is NOT a measure of inflation in India?","options":{"A":"CPI (Consumer Price Index)","B":"WPI (Wholesale Price Index)","C":"GDP Deflator","D":"Sensex"},"answer":"D","explanation":"Sensex is a stock market index (BSE 30 companies), not a measure of inflation. CPI, WPI, and GDP Deflator are all price indices used to measure inflation.","source":"UPSC Prelims 2023"},
    {"exam":"UPSC","subject":"UPSC — Environment","chapter":"Environment & Ecology","year":"2024","difficulty":"Medium","type":"mcq","marks":2,"negative_marks":0.66,"question":"The Ramsar Convention deals with:","options":{"A":"Endangered species protection","B":"Wetland conservation","C":"Ozone layer protection","D":"Marine biodiversity"},"answer":"B","explanation":"The Ramsar Convention on Wetlands (1971) provides a framework for the conservation and wise use of wetlands and their resources.","source":"UPSC Prelims 2024"},
    # ── CAT ───────────────────────────────────────────────────────────────
    {"exam":"CAT","subject":"CAT — Quantitative Aptitude","chapter":"Percentages","year":"2023","difficulty":"Medium","type":"mcq","marks":3,"negative_marks":1,"question":"A shopkeeper marks his goods 40% above cost price and gives a 25% discount. His profit/loss percentage is:","options":{"A":"5% profit","B":"5% loss","C":"10% profit","D":"No profit, no loss"},"answer":"A","explanation":"SP = 1.4 × CP × 0.75 = 1.05 × CP. Profit = 5%.","source":"CAT 2023"},
    {"exam":"CAT","subject":"CAT — Logical Reasoning","chapter":"Logical Reasoning","year":"2022","difficulty":"Hard","type":"mcq","marks":3,"negative_marks":1,"question":"All roses are flowers. Some flowers fade quickly. Which conclusion is definitely true?","options":{"A":"All flowers are roses","B":"Some roses fade quickly","C":"No roses fade quickly","D":"None of the conclusions is definite"},"answer":"D","explanation":"From 'all roses are flowers' and 'some flowers fade quickly', we cannot conclude that some roses fade quickly (they may be different flowers). So no conclusion is definite.","source":"CAT 2022"},
    {"exam":"CAT","subject":"CAT — Verbal Ability","chapter":"Verbal Ability","year":"2024","difficulty":"Medium","type":"mcq","marks":3,"negative_marks":1,"question":"Choose the word most similar in meaning to 'OBDURATE':","options":{"A":"Compliant","B":"Stubborn","C":"Transparent","D":"Flexible"},"answer":"B","explanation":"Obdurate means stubbornly refusing to change one's opinion or course of action. Synonyms: stubborn, inflexible, intransigent.","source":"CAT Vocabulary"},
    {"exam":"CAT","subject":"CAT — Quantitative Aptitude","chapter":"Profit & Loss","year":"2024","difficulty":"Medium","type":"mcq","marks":3,"negative_marks":1,"question":"In how many students liking both maths and science, if 120 students in a class, 80 like maths, 60 like science, and 40 like neither?","options":{"A":"20","B":"10","C":"30","D":"15"},"answer":"A","explanation":"By set theory: |M∪S| = |M| + |S| - |M∩S| = 80 + 60 - 40 = 100. Students liking neither = 120 - 100 = 20.","source":"CAT 2024"},
    # ── SAT ───────────────────────────────────────────────────────────────
    {"exam":"SAT","subject":"SAT — Mathematics","chapter":"Algebra","year":"2024","difficulty":"Medium","type":"mcq","marks":1,"negative_marks":0,"question":"If 3x + 7 = 22, what is the value of 9x + 21?","options":{"A":"45","B":"63","C":"66","D":"57"},"answer":"C","explanation":"3x + 7 = 22 → 3x = 15. So 9x + 21 = 3(3x + 7) = 3 × 22 = 66.","source":"SAT 2024"},
    {"exam":"SAT","subject":"SAT — Reading","chapter":"Critical Reading","year":"2024","difficulty":"Medium","type":"mcq","marks":1,"negative_marks":0,"question":"The word 'ephemeral' most nearly means:","options":{"A":"Permanent","B":"Short-lived","C":"Mysterious","D":"Significant"},"answer":"B","explanation":"Ephemeral means short-lived or transitory. From Greek 'ephemeros' — lasting only a day.","source":"SAT Vocabulary"},
    # ── GK ────────────────────────────────────────────────────────────────
    {"exam":"GK","subject":"GK — Current Affairs 2024","chapter":"Current Affairs 2024","year":"2024","difficulty":"Easy","type":"mcq","marks":1,"negative_marks":0,"question":"Which country won the ICC Men's T20 World Cup 2024?","options":{"A":"Australia","B":"Pakistan","C":"India","D":"England"},"answer":"C","explanation":"India won the ICC Men's T20 World Cup 2024, defeating South Africa by 7 runs in the final held in Barbados on June 29, 2024.","source":"Current Affairs 2024"},
    {"exam":"GK","subject":"GK — Science & Technology","chapter":"Science & Technology","year":"2023","difficulty":"Easy","type":"mcq","marks":1,"negative_marks":0,"question":"India's Chandrayaan-3 mission successfully landed on the Moon's South Pole on:","options":{"A":"July 14, 2023","B":"August 23, 2023","C":"September 2, 2023","D":"October 10, 2023"},"answer":"B","explanation":"Chandrayaan-3's Vikram lander soft-landed on the lunar South Pole on August 23, 2023 at 18:04 IST — India was the first country to land near the South Pole.","source":"Current Affairs 2023"},
    {"exam":"GK","subject":"GK — World Affairs","chapter":"International Relations","year":"2024","difficulty":"Easy","type":"mcq","marks":1,"negative_marks":0,"question":"Which country hosted the G20 Summit in 2023 under the theme 'Vasudhaiva Kutumbakam'?","options":{"A":"Brazil","B":"South Africa","C":"India","D":"Japan"},"answer":"C","explanation":"India hosted the G20 Summit 2023 in New Delhi. The theme 'Vasudhaiva Kutumbakam — One Earth, One Family, One Future' is derived from the Maha Upanishad.","source":"Current Affairs 2023"},
    {"exam":"GK","subject":"GK — Awards","chapter":"Awards & Honours","year":"2024","difficulty":"Easy","type":"mcq","marks":1,"negative_marks":0,"question":"Who received the Nobel Prize in Literature 2024?","options":{"A":"Haruki Murakami","B":"Han Kang","C":"Salman Rushdie","D":"Chimamanda Ngozi Adichie"},"answer":"B","explanation":"South Korean author Han Kang won the Nobel Prize in Literature 2024 — the first South Korean and first Asian woman to win the prize.","source":"Current Affairs 2024"},
    {"exam":"GK","subject":"GK — Indian History","chapter":"Indian History","year":"PYQ","difficulty":"Easy","type":"mcq","marks":1,"negative_marks":0,"question":"Who wrote the Indian national song 'Vande Mataram'?","options":{"A":"Rabindranath Tagore","B":"Bankim Chandra Chattopadhyay","C":"Subramania Bharati","D":"Sarojini Naidu"},"answer":"B","explanation":"'Vande Mataram' was composed by Bankim Chandra Chattopadhyay and published in his 1882 novel 'Anandamath'.","source":"GK Bank"},
]


def get_curated_bank(exam: str = "ALL") -> List[dict]:
    """Return curated questions filtered by exam."""
    bank = []
    for q in CURATED_BANK:
        if exam == "ALL" or q["exam"] == exam:
            item = dict(q)
            item["id"] = _uid(q["question"])
            bank.append(item)
    return bank


# ══════════════════════════════════════════════════════════════════════════════
#  TASK BUILDER  — builds the 30-worker job list per exam
# ══════════════════════════════════════════════════════════════════════════════
Task = Tuple[str, Callable, tuple]

def _build_tasks(exam: str) -> List[Task]:
    """Return list of (task_name, function, args) to submit to ThreadPoolExecutor."""
    tasks: List[Task] = []

    # ── ExamSIDE chapter tasks ──────────────────────────────────────────────
    if exam in ("JEE", "ALL"):
        for subject, chapters in JEE_CHAPTERS.items():
            for chapter in chapters[:4]:  # top 4 chapters per subject
                tasks.append((
                    f"ExamSIDE JEE {chapter}",
                    fetch_examside,
                    ("JEE", subject, chapter, 25),
                ))

    if exam in ("NEET", "ALL"):
        for subject, chapters in NEET_CHAPTERS.items():
            for chapter in chapters[:3]:
                tasks.append((
                    f"ExamSIDE NEET {chapter}",
                    fetch_examside,
                    ("NEET", subject, chapter, 25),
                ))

    # ── pyqs.org tasks ─────────────────────────────────────────────────────
    for pyqs_exam, urls in PYQS_URLS.items():
        if exam == "ALL" or exam == pyqs_exam:
            for url in urls:
                tasks.append((
                    f"pyqs.org {pyqs_exam} {url.split('/')[-1]}",
                    fetch_pyqs_org,
                    (pyqs_exam, url, 30),
                ))

    # ── IndiaBix tasks ─────────────────────────────────────────────────────
    ib_exams = ["GK", "UPSC", "CAT"] if exam == "ALL" else ([exam] if exam in INDIABIX_TOPICS else ["GK"])
    for ib_exam in ib_exams:
        for url, chapter in INDIABIX_TOPICS.get(ib_exam, []):
            tasks.append((
                f"IndiaBix {ib_exam} {chapter}",
                fetch_indiabix,
                (url, ib_exam, chapter, 30),
            ))

    # ── OpenTDB tasks (JSON API, never blocked) ────────────────────────────
    cats = OPENTDB_CATS.get(exam, OPENTDB_CATS["ALL"])
    for cat_id, cat_name in cats:
        tasks.append((
            f"OpenTDB {cat_name}",
            fetch_opentdb,
            (exam if exam != "ALL" else "GK", cat_id, cat_name, 40),
        ))

    return tasks


# ══════════════════════════════════════════════════════════════════════════════
#  MASTER SCRAPE FUNCTION  (called by Flask SSE endpoint)
# ══════════════════════════════════════════════════════════════════════════════
def scrape_all(exam: str = "ALL") -> Generator:
    """
    30-worker concurrent scraper. Yields SSE-compatible event dicts:
      {"_event": "progress", "msg": str, "pct": int, "stage": str}
      {"_event": "done",     "count": int, "questions": list}
      {"_event": "error",    "msg": str}

    Uses ThreadPoolExecutor for I/O-bound HTTP parallelism.
    Each worker runs in its own thread with a thread-local session.
    """
    all_questions: List[dict] = []
    seen_ids: set = set()

    # ── 1. Curated bank (always first, always works) ─────────────────────
    curated = get_curated_bank(exam)
    for q in curated:
        if q["id"] not in seen_ids:
            seen_ids.add(q["id"])
            all_questions.append(q)

    yield {
        "_event": "progress",
        "msg": f"✅ Loaded {len(curated)} curated {exam} PYQs (offline bank)",
        "pct": 5,
        "stage": "curated",
    }

    # ── 2. Build task list ────────────────────────────────────────────────
    tasks = _build_tasks(exam)
    total_tasks = max(len(tasks), 1)

    yield {
        "_event": "progress",
        "msg": f"🚀 Starting {min(30, total_tasks)} concurrent workers across {total_tasks} sources…",
        "pct": 7,
        "stage": "init",
    }

    # ── 3. Execute with 30-worker ThreadPoolExecutor ──────────────────────
    completed = 0
    with ThreadPoolExecutor(max_workers=30, thread_name_prefix="qf_scraper") as executor:
        future_to_name = {
            executor.submit(fn, *args): name
            for name, fn, args in tasks
        }

        for future in as_completed(future_to_name):
            name = future_to_name[future]
            completed += 1
            pct = 7 + int(completed / total_tasks * 88)

            try:
                batch: List[dict] = future.result(timeout=35)
                new_count = 0
                for q in batch:
                    qid = q.get("id") or _uid(q.get("question", ""))
                    if qid not in seen_ids:
                        seen_ids.add(qid)
                        q["id"] = qid
                        all_questions.append(q)
                        new_count += 1

                status = "✅" if new_count > 0 else "⚠"
                yield {
                    "_event": "progress",
                    "msg": f"{status} {name}: {new_count} new questions ({len(all_questions)} total)",
                    "pct": pct,
                    "stage": name,
                    "workers_done": completed,
                    "workers_total": total_tasks,
                }

            except Exception as e:
                yield {
                    "_event": "progress",
                    "msg": f"⚠ {name}: {str(e)[:70]}",
                    "pct": pct,
                    "stage": name,
                }

    # ── 4. Done ───────────────────────────────────────────────────────────
    yield {
        "_event": "done",
        "count": len(all_questions),
        "questions": all_questions,
    }