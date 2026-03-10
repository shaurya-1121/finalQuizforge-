"""
QuizForge v5.0 — app.py
Flask backend with SSE scrape streaming, REST API, and PDF export.

Fixes applied:
  BUG-04: index() uses Path(__file__).parent so it works from any CWD
  BUG-05: _scrape_running=False wrapped in _scrape_lock (thread safety)
  BUG-12: is_stale() checked at startup with a console warning
  NEW:    /api/scrape accepts {"exam":"JEE"} body param
"""

import json
import threading
import time
import queue
import os
from pathlib import Path

from flask import (Flask, jsonify, render_template, request,
                   Response, send_file, send_from_directory)
from flask_compress import Compress

import Pyq_database as db
from scraper import scrape_all
from Pdf_generator import generate_pdf

# ─── App setup ─────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent  # FIX BUG-04: absolute path to this file's dir

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static",
)
app.config["COMPRESS_ALGORITHM"] = "gzip"
app.config["COMPRESS_LEVEL"] = 6
Compress(app)

# Global scrape state
_scrape_lock    = threading.Lock()
_scrape_q: queue.Queue = queue.Queue(maxsize=2000)
_scrape_running = False
_scrape_exam    = "ALL"   # tracks which exam is being scraped


# ─── Startup check ──────────────────────────────────────────────────────────
def _startup_check():
    """FIX BUG-12: warn if DB is empty or stale so operators know to scrape."""
    if db.is_stale(max_age_hours=24.0):
        print("⚠  QuizForge: Question DB is empty or stale — "
              "click 'Fetch Live PYQ Questions' in the browser to populate it.")
    else:
        count = db.count_questions()
        print(f"✅ QuizForge: Loaded {count} cached questions from DB.")


# ─── Static files ───────────────────────────────────────────────────────────
@app.route("/")
def index():
    # FIX BUG-04: use BASE_DIR so this works regardless of CWD at runtime
    return send_from_directory(str(BASE_DIR), "index.html")


@app.route("/static/<path:path>")
def static_files(path):
    return send_from_directory(str(BASE_DIR / "static"), path)


# ─── Questions API ──────────────────────────────────────────────────────────
@app.route("/api/questions")
def api_questions():
    """Return filtered, paginated questions."""
    exam       = request.args.get("exam")
    chapter    = request.args.get("chapter")
    difficulty = request.args.get("difficulty")
    year       = request.args.get("year")
    search     = request.args.get("q")
    page       = int(request.args.get("page", 1))
    per_page   = min(int(request.args.get("per_page", 200)), 500)

    result = db.get_questions(
        exam=exam, chapter=chapter,
        difficulty=difficulty, year=year,
        search=search, page=page, per_page=per_page,
    )
    return jsonify(result)


@app.route("/api/question/<qid>")
def api_question(qid):
    q = db.get_by_id(qid)
    if not q:
        return jsonify({"error": "Not found"}), 404
    return jsonify(q)


@app.route("/api/stats")
def api_stats():
    return jsonify(db.get_stats())


# ─── Scrape API ─────────────────────────────────────────────────────────────
@app.route("/api/scrape", methods=["POST"])
def api_scrape_start():
    global _scrape_running, _scrape_exam
    with _scrape_lock:
        if _scrape_running:
            return jsonify({"status": "already_running"}), 202
        _scrape_running = True

        # Read requested exam from POST body (NEW: exam-specific scraping)
        body = request.get_json(force=True, silent=True) or {}
        exam = body.get("exam", "ALL").upper()
        _scrape_exam = exam

        # Drain old queue
        while not _scrape_q.empty():
            try:
                _scrape_q.get_nowait()
            except queue.Empty:
                break

        def _run():
            global _scrape_running
            all_questions = []
            try:
                for event in scrape_all(exam=exam):
                    _scrape_q.put(event)
                    if event.get("_event") == "done":
                        all_questions = event.get("questions", [])
            except Exception as e:
                _scrape_q.put({"_event": "error", "msg": str(e)})
            finally:
                if all_questions:
                    db.save_questions(all_questions)
                # FIX BUG-05: acquire lock before clearing flag (thread safety)
                with _scrape_lock:
                    _scrape_running = False

        t = threading.Thread(target=_run, daemon=True)
        t.start()

    return jsonify({"status": "started", "exam": exam}), 202


@app.route("/api/scrape/stream")
def api_scrape_stream():
    """SSE endpoint — streams scrape progress to the browser."""

    def event_stream():
        timeout = 600  # 10 minutes max (30-worker scrape can take a while)
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                event = _scrape_q.get(timeout=2)
            except queue.Empty:
                yield "event: heartbeat\ndata: {}\n\n"
                if not _scrape_running:
                    break
                continue

            etype = event.get("_event", "progress")
            payload = json.dumps({k: v for k, v in event.items() if k != "_event"})

            if etype == "progress":
                yield f"event: progress\ndata: {payload}\n\n"
            elif etype == "done":
                yield "event: progress\ndata: {\"pct\":100,\"msg\":\"Finalising…\"}\n\n"
                yield f"event: done\ndata: {payload}\n\n"
                break
            elif etype == "error":
                yield f"event: error\ndata: {payload}\n\n"
                break

    return Response(
        event_stream(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@app.route("/api/scrape/status")
def api_scrape_status():
    return jsonify({
        "running": _scrape_running,
        "count": db.count_questions(),
        "exam": _scrape_exam,
    })


# ─── PDF Export API ─────────────────────────────────────────────────────────
@app.route("/api/export/pdf", methods=["POST"])
def api_export_pdf():
    """Generate and serve a PDF question paper."""
    data       = request.get_json(force=True, silent=True) or {}
    exam       = data.get("exam", "All Exams")
    chapter    = data.get("chapter")
    difficulty = data.get("difficulty")

    result = db.get_questions(
        exam=exam if exam != "ALL" else None,
        chapter=chapter,
        difficulty=difficulty,
        per_page=500,
    )
    questions = result.get("questions", [])
    if not questions:
        return jsonify({"error": "No questions matched the filters."}), 404

    try:
        pdf_bytes = generate_pdf(questions, exam=exam)
        safe_name = f"QuizForge_{exam.replace(' ', '_')}.pdf"
        from io import BytesIO
        return send_file(
            BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=safe_name,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── Health check ───────────────────────────────────────────────────────────
@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "questions": db.count_questions(),
        "scraping": _scrape_running,
        "scrape_exam": _scrape_exam,
        "version": "5.0",
    })


if __name__ == "__main__":
    _startup_check()  # FIX BUG-12: warn if DB is empty/stale
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    print(f"🎯 QuizForge v5.0 — http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug, threaded=True)