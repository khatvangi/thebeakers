#!/usr/bin/env python3
"""
process_indepth.py - automated in-depth article processing with NotebookLM

designed to be run FROM Claude Code (MCP tools required for NotebookLM).
can also be run standalone to identify candidates and generate HTML from
existing assets.

usage:
    python scripts/process_indepth.py --list              # show candidates
    python scripts/process_indepth.py --process <url>     # process one article
    python scripts/process_indepth.py --process-all       # process all ready
    python scripts/process_indepth.py --build-html <url>  # build HTML from assets

flow per article:
    1. find indepth candidates with PDFs
    2. create NotebookLM notebook + upload PDF  (MCP: notebook_create, source_add)
    3. generate audio, video, report, quiz      (MCP: studio_create x4)
    4. poll until complete                      (MCP: studio_status)
    5. download assets locally                  (MCP: download_artifact x4)
    6. build deep dive HTML from canonical template
    7. update DB with notebook_id + status
"""

import argparse
import json
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

DB_PATH = Path(__file__).parent.parent / "data" / "articles.db"
DEEPDIVE_DIR = Path(__file__).parent.parent / "deepdive"
ASSETS_BASE = Path(__file__).parent.parent / "data" / "deep"
CURRICULUM_PATH = Path(__file__).parent.parent / "data" / "curriculum.json"
TEMPLATE_PATH = Path(__file__).parent.parent / "deepdive" / "solar-cell-bromine.html"


def ensure_schema(conn: sqlite3.Connection):
    """add notebooklm columns to triage_result if missing"""
    existing = {row[1] for row in conn.execute("PRAGMA table_info(triage_result)")}
    new_cols = {
        "notebook_id": "TEXT",
        "nlm_status": "TEXT DEFAULT 'pending'",  # pending | processing | complete | error
        "nlm_audio_path": "TEXT",
        "nlm_video_path": "TEXT",
        "nlm_report_path": "TEXT",
        "nlm_quiz_path": "TEXT",
        "nlm_processed_at": "TEXT",
    }
    for col, dtype in new_cols.items():
        if col not in existing:
            conn.execute(f"ALTER TABLE triage_result ADD COLUMN {col} {dtype}")
    conn.commit()


def get_candidates(conn: sqlite3.Connection, limit: int = 10) -> List[Dict]:
    """find indepth articles ready for NotebookLM processing"""
    ensure_schema(conn)
    rows = conn.execute("""
        SELECT article_url, discipline, fulltext_path, tldr,
               score_s, score_e, score_t, score_m, score_h,
               route, nlm_status, notebook_id
        FROM triage_result
        WHERE fulltext_ok = 1
          AND access_state = 'oa_pdf_found'
          AND route = 'indepth'
          AND (nlm_status IS NULL OR nlm_status = 'pending')
        ORDER BY score_t DESC, score_s DESC
        LIMIT ?
    """, (limit,)).fetchall()

    return [
        {
            "url": r[0], "discipline": r[1], "pdf_path": r[2], "tldr": r[3],
            "S": r[4], "E": r[5], "T": r[6], "M": r[7], "H": r[8],
            "route": r[9], "nlm_status": r[10], "notebook_id": r[11]
        }
        for r in rows
    ]


def get_digest_candidates(conn: sqlite3.Connection, limit: int = 20) -> List[Dict]:
    """find digest articles as fallback (if no indepth yet)"""
    ensure_schema(conn)
    rows = conn.execute("""
        SELECT article_url, discipline, fulltext_path, tldr,
               score_s, score_e, score_t, score_m, score_h,
               route, nlm_status, notebook_id
        FROM triage_result
        WHERE fulltext_ok = 1
          AND access_state = 'oa_pdf_found'
          AND route = 'digest'
          AND (nlm_status IS NULL OR nlm_status = 'pending')
        ORDER BY score_t DESC, score_s DESC
        LIMIT ?
    """, (limit,)).fetchall()

    return [
        {
            "url": r[0], "discipline": r[1], "pdf_path": r[2], "tldr": r[3],
            "S": r[4], "E": r[5], "T": r[6], "M": r[7], "H": r[8],
            "route": r[9], "nlm_status": r[10], "notebook_id": r[11]
        }
        for r in rows
    ]


def slugify(url: str) -> str:
    """convert DOI URL to filesystem-safe slug"""
    # extract DOI part
    doi = url.replace("https://doi.org/", "").replace("/", "_").replace(".", "-")
    return doi[:60]


def article_title_from_db(conn: sqlite3.Connection, url: str) -> str:
    """try to get article title from seen_articles, fall back to triage tldr"""
    row = conn.execute(
        "SELECT headline FROM seen_articles WHERE url = ?", (url,)
    ).fetchone()
    if row and row[0]:
        return row[0]
    # fall back to tldr from triage_result
    row = conn.execute(
        "SELECT tldr FROM triage_result WHERE article_url = ? LIMIT 1", (url,)
    ).fetchone()
    return row[0] if row and row[0] else url.split("/")[-1]


def get_curriculum_connection(discipline: str) -> str:
    """build curriculum connection HTML from curriculum.json"""
    if not CURRICULUM_PATH.exists():
        return ""

    with open(CURRICULUM_PATH) as f:
        curriculum = json.load(f)

    disc_data = curriculum.get(discipline, {})
    if not disc_data:
        return ""

    cards_html = ""
    count = 0
    for subfield_name, subfield_data in disc_data.get("subfields", {}).items():
        if count >= 3:
            break
        difficulty = subfield_data.get("difficulty", "sophomore")
        level_map = {"freshman": "100", "sophomore": "200", "junior": "300"}
        level = level_map.get(difficulty, "200")
        topics = subfield_data.get("topics", [])
        topic_names = [t["name"] for t in topics[:3]]
        cards_html += f'''
            <div class="course-card">
                <div class="course-code">{discipline.upper()} {level}</div>
                <div class="course-name">{subfield_name}</div>
                <p class="course-connection">This research connects to topics like {', '.join(topic_names)}.</p>
                <div class="course-concepts">
                    {''.join(f'<span class="concept-tag">{t}</span>' for t in topic_names)}
                </div>
            </div>'''
        count += 1

    return cards_html


def build_deep_dive_html(article: Dict, title: str, assets_dir: Path, conn: sqlite3.Connection) -> str:
    """build deep dive HTML page from canonical template pattern.

    embeds audio/video from local downloaded files (HTML5 players).
    no SoundCloud/YouTube upload needed.
    """
    slug = slugify(article["url"])
    discipline = article["discipline"]
    tldr = article.get("tldr", "")

    # asset paths (relative to deepdive/ dir)
    audio_rel = f"{slug}/audio.mp4"
    video_rel = f"{slug}/video.mp4"
    report_path = assets_dir / "report.md"
    quiz_path = assets_dir / "quiz.json"

    audio_exists = (assets_dir / "audio.mp4").exists()
    video_exists = (assets_dir / "video.mp4").exists()
    report_exists = report_path.exists()
    quiz_exists = quiz_path.exists()

    # load report content if available
    report_html = ""
    if report_exists:
        report_text = report_path.read_text()
        # simple markdown to HTML: paragraphs + bold + headers
        for line in report_text.split("\n"):
            line = line.strip()
            if line.startswith("# "):
                report_html += f"<h3>{line[2:]}</h3>\n"
            elif line.startswith("## "):
                report_html += f"<h4>{line[3:]}</h4>\n"
            elif line.startswith("- "):
                report_html += f"<li>{line[2:]}</li>\n"
            elif line:
                report_html += f"<p>{line}</p>\n"

    # load quiz if available
    # supports NotebookLM format (answerOptions + isCorrect) and generic format
    quiz_html = ""
    if quiz_exists:
        quiz_data = json.loads(quiz_path.read_text())
        questions = quiz_data if isinstance(quiz_data, list) else quiz_data.get("questions", [])
        for i, q in enumerate(questions[:5], 1):
            question_text = q.get("question", q.get("text", ""))
            # handle NotebookLM answerOptions format or generic options/choices
            options = q.get("answerOptions", q.get("options", q.get("choices", [])))
            options_html = ""
            for opt in options:
                if isinstance(opt, str):
                    opt_text, is_correct = opt, False
                else:
                    opt_text = opt.get("text", "")
                    is_correct = opt.get("isCorrect", False)
                options_html += f'<button class="quiz-option" data-correct="{1 if is_correct else 0}" onclick="checkAnswer(this)">{opt_text}</button>\n'
            quiz_html += f'''
                <div class="quiz-question">
                    <p class="question-number">Question {i}</p>
                    <p class="question-text">{question_text}</p>
                    <div class="quiz-options">{options_html}</div>
                </div>'''

    curriculum_html = get_curriculum_connection(discipline)

    # color accents per discipline
    colors = {
        "biology": "#22c55e", "chemistry": "#10b981", "physics": "#3b82f6",
        "ai": "#8b5cf6", "engineering": "#f59e0b", "mathematics": "#a855f7",
        "agriculture": "#84cc16"
    }
    accent = colors.get(discipline, "#10b981")

    # audio section (only if asset exists)
    audio_section = ""
    if audio_exists:
        audio_section = f'''
        <section class="podcast-section">
            <div class="podcast-header">
                <span class="podcast-badge">AI Podcast</span>
                <span style="color: var(--text-light); font-size: 0.9rem;">~15 min listen</span>
            </div>
            <h2 class="podcast-title">Deep Dive Podcast</h2>
            <p class="podcast-description">Two AI hosts break down this research in a conversational format. Perfect for your commute or study session.</p>
            <div class="audio-player">
                <audio controls preload="metadata" style="width: 100%; border-radius: 12px;">
                    <source src="{audio_rel}" type="audio/mp4">
                    Your browser does not support the audio element.
                </audio>
                <p class="audio-note">Generated by NotebookLM</p>
            </div>
        </section>'''

    # video section (only if asset exists)
    video_section = ""
    if video_exists:
        video_section = f'''
        <section class="section video-section">
            <div class="section-header">
                <div class="section-icon" style="background: var(--accent-orange);">
                    <span style="filter: grayscale(1) brightness(10);">&#x25B6;</span>
                </div>
                <h2 class="section-title">Video Explainer</h2>
            </div>
            <div class="video-container">
                <video controls preload="metadata" poster=""
                    style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;">
                    <source src="{video_rel}" type="video/mp4">
                    Your browser does not support the video element.
                </video>
            </div>
        </section>'''

    # report section
    report_section = ""
    if report_html:
        report_section = f'''
        <section class="section" style="background: var(--bg-card); border-radius: 20px; padding: 2rem; border: 1px solid var(--border-dark);">
            <div class="section-header">
                <div class="section-icon" style="background: var(--accent-cyan);">
                    <span style="filter: grayscale(1) brightness(10);">&#128214;</span>
                </div>
                <h2 class="section-title">Study Guide</h2>
            </div>
            <div style="color: var(--text-secondary); line-height: 1.8;">
                {report_html}
            </div>
        </section>'''

    # quiz section
    quiz_section = ""
    if quiz_html:
        quiz_section = f'''
        <section class="section" id="quiz">
            <span class="curriculum-badge" style="background: var(--accent-orange);">Interactive</span>
            <div class="section-header">
                <h2 class="section-title">Test Your Understanding</h2>
            </div>
            {quiz_html}
        </section>'''

    # curriculum section
    curriculum_section = ""
    if curriculum_html:
        curriculum_section = f'''
        <section class="section curriculum-section"
            style="background: linear-gradient(135deg, rgba(16,185,129,0.1), rgba(6,182,212,0.1));
                   border-radius: 20px; padding: 2rem; border: 1px solid {accent}40;">
            <span class="curriculum-badge">The Beakers Exclusive</span>
            <div class="section-header">
                <h2 class="section-title" style="color: white;">Curriculum Connection</h2>
            </div>
            <p style="color: var(--text-secondary); margin-bottom: 1.5rem;">See how concepts from your courses directly apply to this cutting-edge research.</p>
            {curriculum_html}
        </section>'''

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Deep Dive: {title} - The Beakers</title>
    <meta name="description" content="{tldr}">
    <link rel="icon" type="image/x-icon" href="../favicon.ico">
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Instrument+Serif:ital@0;1&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-dark: #0f172a;
            --bg-card: #1e293b;
            --bg-card-hover: #273549;
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --text-light: #64748b;
            --border-dark: #334155;
            --accent-green: {accent};
            --accent-blue: #3b82f6;
            --accent-purple: #8b5cf6;
            --accent-orange: #f59e0b;
            --accent-cyan: #06b6d4;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        html {{ scroll-behavior: smooth; }}
        body {{
            font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
            background: var(--bg-dark);
            color: var(--text-primary);
            line-height: 1.7;
        }}
        header {{
            padding: 1.5rem 2rem;
            max-width: 1400px;
            margin: 0 auto;
        }}
        .logo {{
            font-size: 1.5rem;
            font-weight: 800;
            text-decoration: none;
            background: linear-gradient(135deg, var(--accent-green), var(--accent-blue), var(--accent-purple));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .hero {{
            text-align: center;
            padding: 3rem 2rem 2rem;
            max-width: 900px;
            margin: 0 auto;
        }}
        .deep-dive-badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: linear-gradient(135deg, var(--accent-purple), var(--accent-blue));
            color: white;
            font-size: 0.75rem;
            font-weight: 700;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            margin-bottom: 1.5rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }}
        .hero h1 {{
            font-family: 'Instrument Serif', Georgia, serif;
            font-size: 2.75rem;
            font-weight: 400;
            line-height: 1.2;
            margin-bottom: 1rem;
        }}
        .hero .subtitle {{
            font-size: 1.25rem;
            color: var(--text-secondary);
            margin-bottom: 2rem;
        }}
        .meta-link {{
            color: var(--accent-cyan);
            text-decoration: none;
            font-size: 0.9rem;
        }}
        .meta-link:hover {{ text-decoration: underline; }}
        main {{
            max-width: 1000px;
            margin: 0 auto;
            padding: 0 2rem 4rem;
        }}
        .section {{ margin-bottom: 3rem; }}
        .section-header {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 1.5rem;
        }}
        .section-icon {{
            width: 40px; height: 40px;
            border-radius: 10px;
            display: flex; align-items: center; justify-content: center;
            font-size: 1.25rem;
        }}
        .section-title {{ font-size: 1.5rem; font-weight: 700; }}
        .podcast-section {{
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            border-radius: 24px;
            padding: 2.5rem;
            margin-bottom: 3rem;
            border: 1px solid var(--accent-purple);
            position: relative;
            overflow: hidden;
        }}
        .podcast-badge {{
            background: var(--accent-purple);
            color: white;
            font-size: 0.7rem;
            font-weight: 700;
            padding: 0.4rem 0.8rem;
            border-radius: 15px;
            text-transform: uppercase;
        }}
        .podcast-header {{ display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem; }}
        .podcast-title {{ font-family: 'Instrument Serif', Georgia, serif; font-size: 1.75rem; margin-bottom: 0.5rem; }}
        .podcast-description {{ color: var(--text-secondary); margin-bottom: 1.5rem; }}
        .audio-player {{ background: rgba(0,0,0,0.3); border-radius: 16px; padding: 1.5rem; }}
        .audio-note {{ font-size: 0.8rem; color: var(--text-light); margin-top: 1rem; text-align: center; }}
        .video-section {{
            background: var(--bg-card);
            border-radius: 20px;
            padding: 2rem;
            border: 1px solid var(--border-dark);
        }}
        .video-container {{
            position: relative;
            padding-bottom: 56.25%;
            height: 0;
            border-radius: 12px;
            overflow: hidden;
            background: #000;
        }}
        .curriculum-badge {{
            display: inline-block;
            background: var(--accent-green);
            color: var(--bg-dark);
            padding: 0.35rem 0.75rem;
            border-radius: 20px;
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 1rem;
        }}
        .course-card {{
            background: rgba(0,0,0,0.2);
            border-radius: 12px;
            padding: 1.25rem;
            margin-bottom: 1rem;
            border-left: 3px solid var(--accent-cyan);
        }}
        .course-code {{ font-size: 0.8rem; color: var(--accent-cyan); font-weight: 600; text-transform: uppercase; }}
        .course-name {{ font-size: 1.1rem; margin: 0.25rem 0 0.75rem 0; }}
        .course-connection {{ color: var(--text-secondary); font-size: 0.95rem; line-height: 1.6; }}
        .course-concepts {{ display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.75rem; }}
        .concept-tag {{
            background: rgba(6,182,212,0.1);
            border: 1px solid var(--accent-cyan);
            color: var(--accent-cyan);
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.75rem;
        }}
        .quiz-question {{
            background: var(--bg-card);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            border: 1px solid var(--border-dark);
        }}
        .question-number {{ font-size: 0.8rem; color: var(--accent-orange); font-weight: 600; margin-bottom: 0.5rem; }}
        .question-text {{ margin-bottom: 1rem; }}
        .quiz-options {{ display: flex; flex-direction: column; gap: 0.5rem; }}
        .quiz-option {{
            background: rgba(0,0,0,0.2);
            border: 1px solid var(--border-dark);
            color: var(--text-primary);
            padding: 0.75rem 1rem;
            border-radius: 8px;
            cursor: pointer;
            text-align: left;
            font-size: 0.95rem;
            transition: all 0.2s;
        }}
        .quiz-option:hover {{ border-color: var(--accent-cyan); }}
        .quiz-option.correct {{ background: rgba(16,185,129,0.2); border-color: #10b981; }}
        .quiz-option.incorrect {{ background: rgba(239,68,68,0.2); border-color: #ef4444; }}
        footer {{
            text-align: center;
            padding: 3rem 2rem;
            color: var(--text-secondary);
            font-size: 0.9rem;
            border-top: 1px solid var(--border-dark);
        }}
        footer a {{ color: var(--accent-green); text-decoration: none; }}
        @media (max-width: 600px) {{
            .hero h1 {{ font-size: 2rem; }}
            main {{ padding: 0 1rem 2rem; }}
        }}
    </style>
</head>
<body>
    <header>
        <a href="/" class="logo">The Beakers</a>
    </header>

    <div class="hero">
        <span class="deep-dive-badge">&#128300; Deep Dive</span>
        <h1>{title}</h1>
        <p class="subtitle">{tldr}</p>
        <a class="meta-link" href="{article['url']}">View original paper &rarr;</a>
    </div>

    <main>
        {audio_section}
        {video_section}
        {report_section}
        {curriculum_section}
        {quiz_section}
    </main>

    <footer>
        <p>Deep Dive for <a href="https://thebeakers.com">The Beakers</a> | {discipline.title()}</p>
        <p style="margin-top: 0.5rem; font-size: 0.8rem;">
            DOI: {article['url'].replace('https://doi.org/', '')}
        </p>
    </footer>

    <script>
        function checkAnswer(btn) {{
            const options = btn.parentElement.querySelectorAll('.quiz-option');
            options.forEach(o => {{
                o.disabled = true;
                o.style.pointerEvents = 'none';
                if (o.dataset.correct === '1') o.classList.add('correct');
            }});
            if (btn.dataset.correct !== '1') btn.classList.add('incorrect');
        }}
    </script>
</body>
</html>'''

    return html


def update_nlm_status(conn: sqlite3.Connection, url: str, **kwargs):
    """update NotebookLM processing status in triage_result"""
    sets = ", ".join(f"{k} = ?" for k in kwargs)
    vals = list(kwargs.values()) + [url]
    conn.execute(f"UPDATE triage_result SET {sets} WHERE article_url = ?", vals)
    conn.commit()


def list_candidates(conn: sqlite3.Connection):
    """print indepth and digest candidates"""
    ensure_schema(conn)

    indepth = get_candidates(conn)
    digest = get_digest_candidates(conn, limit=10)

    print(f"\n=== INDEPTH CANDIDATES ({len(indepth)}) ===")
    for a in indepth:
        title = article_title_from_db(conn, a["url"])
        pdf = "PDF" if Path(a["pdf_path"]).exists() else "NO-PDF"
        print(f"  [{a['discipline']:12s}] S={a['S']} E={a['E']} T={a['T']} M={a['M']} H={a['H']}  {pdf}  {title[:60]}")
        print(f"    {a['url']}")

    print(f"\n=== DIGEST CANDIDATES (top {len(digest)}) ===")
    for a in digest:
        title = article_title_from_db(conn, a["url"])
        pdf = "PDF" if Path(a["pdf_path"]).exists() else "NO-PDF"
        print(f"  [{a['discipline']:12s}] S={a['S']} E={a['E']} T={a['T']} M={a['M']} H={a['H']}  {pdf}  {title[:60]}")
        print(f"    {a['url']}")

    if not indepth and not digest:
        print("\n  (no candidates yet — run triage with new scoring first)")


def prepare_article(conn: sqlite3.Connection, url: str) -> Optional[Dict]:
    """prepare an article for NotebookLM processing.
    returns article dict with asset paths set up.
    """
    ensure_schema(conn)
    row = conn.execute("""
        SELECT article_url, discipline, fulltext_path, tldr,
               score_s, score_e, score_t, score_m, score_h,
               route, nlm_status, notebook_id
        FROM triage_result
        WHERE article_url = ? AND fulltext_ok = 1
    """, (url,)).fetchone()

    if not row:
        print(f"ERROR: article not found or no fulltext: {url}")
        return None

    article = {
        "url": row[0], "discipline": row[1], "pdf_path": row[2], "tldr": row[3],
        "S": row[4], "E": row[5], "T": row[6], "M": row[7], "H": row[8],
        "route": row[9], "nlm_status": row[10], "notebook_id": row[11]
    }

    slug = slugify(url)
    assets_dir = DEEPDIVE_DIR / slug
    assets_dir.mkdir(parents=True, exist_ok=True)

    title = article_title_from_db(conn, url)

    print(f"\n=== PREPARED ===")
    print(f"  title: {title}")
    print(f"  url: {url}")
    print(f"  discipline: {article['discipline']}")
    print(f"  pdf: {article['pdf_path']}")
    print(f"  assets dir: {assets_dir}")
    print(f"  scores: S={article['S']} E={article['E']} T={article['T']} M={article['M']} H={article['H']}")
    print(f"\n=== NOTEBOOKLM STEPS (run from Claude Code) ===")
    print(f"  1. notebook_create(title='{title[:60]}')")
    print(f"  2. source_add(notebook_id=NB, source_type='file', file_path='{article['pdf_path']}', wait=True)")
    print(f"  3. studio_create(notebook_id=NB, artifact_type='audio', audio_format='deep_dive', confirm=True)")
    print(f"  4. studio_create(notebook_id=NB, artifact_type='video', video_format='explainer', confirm=True)")
    print(f"  5. studio_create(notebook_id=NB, artifact_type='report', report_format='Study Guide', confirm=True)")
    print(f"  6. studio_create(notebook_id=NB, artifact_type='quiz', question_count=5, confirm=True)")
    print(f"  7. poll studio_status(notebook_id=NB) until complete")
    print(f"  8. download_artifact(notebook_id=NB, artifact_type='audio', output_path='{assets_dir}/audio.mp4')")
    print(f"  9. download_artifact(notebook_id=NB, artifact_type='video', output_path='{assets_dir}/video.mp4')")
    print(f" 10. download_artifact(notebook_id=NB, artifact_type='report', output_path='{assets_dir}/report.md')")
    print(f" 11. download_artifact(notebook_id=NB, artifact_type='quiz', output_path='{assets_dir}/quiz.json')")

    return {**article, "title": title, "slug": slug, "assets_dir": str(assets_dir)}


def build_html(conn: sqlite3.Connection, url: str):
    """build deep dive HTML from downloaded assets"""
    ensure_schema(conn)
    article = prepare_article(conn, url)
    if not article:
        return

    assets_dir = Path(article["assets_dir"])
    title = article["title"]

    html = build_deep_dive_html(article, title, assets_dir, conn)

    slug = article["slug"]
    output_path = DEEPDIVE_DIR / f"{slug}.html"
    output_path.write_text(html)
    print(f"\n  wrote: {output_path}")

    # update DB
    update_nlm_status(conn, url, nlm_status="complete", nlm_processed_at=datetime.now().isoformat())


def main():
    parser = argparse.ArgumentParser(description="process indepth articles with NotebookLM")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true", help="list candidates")
    group.add_argument("--prepare", type=str, metavar="URL", help="prepare article for processing")
    group.add_argument("--build-html", type=str, metavar="URL", help="build HTML from downloaded assets")

    args = parser.parse_args()
    conn = sqlite3.connect(DB_PATH)

    if args.list:
        list_candidates(conn)
    elif args.prepare:
        prepare_article(conn, args.prepare)
    elif args.build_html:
        build_html(conn, args.build_html)

    conn.close()


if __name__ == "__main__":
    main()
