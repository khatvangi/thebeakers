#!/usr/bin/env python3
"""
render_digest_page.py - render daily/weekly digest HTML for email

reads from issue table, joins with archive/triage_result for metadata,
outputs email-compatible HTML

usage:
  python render_digest_page.py --week 2026-01-16 --output data/digest_2026-01-16.html
  python render_digest_page.py --week 2026-01-16 --slot blurb  # only blurbs
"""

import argparse
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from html import escape

DB_PATH = Path(__file__).parent.parent / "data" / "articles.db"
OUTPUT_DIR = Path(__file__).parent.parent / "data"

# site colors (from design tokens)
COLORS = {
    "bg_dark": "#0f172a",
    "bg_card": "#1e293b",
    "text_primary": "#f1f5f9",
    "text_secondary": "#94a3b8",
    "accent_green": "#10b981",
    "accent_blue": "#3b82f6",
    "accent_purple": "#8b5cf6",
    "accent_orange": "#f59e0b",
}

# discipline accent colors
DISCIPLINE_COLORS = {
    "biology": "#10b981",
    "chemistry": "#10b981",
    "physics": "#10b981",
    "agriculture": "#10b981",
    "ai": "#3b82f6",
    "engineering": "#f59e0b",
    "mathematics": "#8b5cf6",
}


def get_issue_articles(conn: sqlite3.Connection, week_of: str, slot: str = None) -> List[Dict]:
    """get articles from issue table with metadata"""

    # join issue with archive and triage_result for full metadata
    query = """
        SELECT
            i.week_of,
            i.discipline,
            i.article_url,
            i.slot,
            i.rank_score,
            i.access_state,
            a.headline,
            a.teaser,
            a.source,
            t.tldr,
            t.difficulty,
            t.frontier_flag
        FROM issue i
        LEFT JOIN archive a ON i.article_url = a.url
        LEFT JOIN triage_result t ON i.article_url = t.article_url
        WHERE i.week_of = ?
    """
    params = [week_of]

    if slot:
        query += " AND i.slot = ?"
        params.append(slot)

    query += " ORDER BY i.discipline, i.slot, i.rank_score DESC"

    cursor = conn.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]


def format_article_url(article_url: str, discipline: str) -> str:
    """convert DOI or URL to thebeakers.com article link"""
    # for now, link to discipline page
    # in future, could link to specific explain page
    return f"https://thebeakers.com/{discipline}.html"


def render_digest_html(articles: List[Dict], week_of: str, title: str = None) -> str:
    """render articles as email-friendly HTML"""

    if not title:
        title = f"The Beakers — Daily Digest ({week_of})"

    # group by discipline
    by_discipline: Dict[str, List[Dict]] = {}
    for a in articles:
        d = a.get("discipline", "other")
        if d not in by_discipline:
            by_discipline[d] = []
        by_discipline[d].append(a)

    # count by slot
    slot_counts = {}
    for a in articles:
        slot = a.get("slot", "unknown")
        slot_counts[slot] = slot_counts.get(slot, 0) + 1

    html_parts = []

    # email header
    html_parts.append(f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(title)}</title>
</head>
<body style="margin: 0; padding: 0; background-color: {COLORS['bg_dark']}; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: {COLORS['bg_dark']};">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table role="presentation" width="600" cellspacing="0" cellpadding="0" style="max-width: 600px;">

                    <!-- Header -->
                    <tr>
                        <td style="padding: 20px 30px; text-align: center;">
                            <h1 style="margin: 0; font-size: 28px; font-weight: 800; color: {COLORS['text_primary']};">
                                <span style="background: linear-gradient(135deg, {COLORS['accent_green']}, {COLORS['accent_blue']}, {COLORS['accent_purple']}); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">The Beakers</span>
                            </h1>
                            <p style="margin: 10px 0 0; font-size: 14px; color: {COLORS['text_secondary']};">
                                Research, Rewritten for Students
                            </p>
                        </td>
                    </tr>

                    <!-- Date & Stats -->
                    <tr>
                        <td style="padding: 10px 30px; text-align: center;">
                            <p style="margin: 0; font-size: 12px; color: {COLORS['text_secondary']};">
                                {week_of} — {len(articles)} articles across {len(by_discipline)} disciplines
                            </p>
                        </td>
                    </tr>
''')

    # render each discipline
    for discipline in sorted(by_discipline.keys()):
        disc_articles = by_discipline[discipline]
        accent = DISCIPLINE_COLORS.get(discipline, COLORS['accent_green'])

        html_parts.append(f'''
                    <!-- {discipline.upper()} -->
                    <tr>
                        <td style="padding: 20px 30px 10px;">
                            <h2 style="margin: 0; font-size: 18px; font-weight: 700; color: {accent}; text-transform: capitalize; border-bottom: 2px solid {accent}; padding-bottom: 8px;">
                                {escape(discipline)}
                            </h2>
                        </td>
                    </tr>
''')

        for article in disc_articles:
            headline = article.get("headline") or "Untitled"
            tldr = article.get("tldr") or article.get("teaser") or ""
            source = article.get("source") or ""
            slot = article.get("slot") or ""
            frontier = article.get("frontier_flag") or 0
            article_url = format_article_url(article.get("article_url", ""), discipline)

            # slot badge
            slot_color = {
                "indepth": COLORS['accent_purple'],
                "digest": COLORS['accent_blue'],
                "blurb": COLORS['accent_green'],
            }.get(slot, COLORS['text_secondary'])

            # frontier label
            frontier_label = ' <span style="color: #f59e0b; font-size: 10px;">(Frontier)</span>' if frontier else ''

            html_parts.append(f'''
                    <tr>
                        <td style="padding: 10px 30px;">
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: {COLORS['bg_card']}; border-radius: 8px;">
                                <tr>
                                    <td style="padding: 16px;">
                                        <p style="margin: 0 0 8px; font-size: 10px; text-transform: uppercase; letter-spacing: 1px; color: {slot_color};">
                                            {escape(slot)}{frontier_label}
                                        </p>
                                        <h3 style="margin: 0 0 8px; font-size: 16px; font-weight: 600; color: {COLORS['text_primary']};">
                                            <a href="{escape(article_url)}" style="color: {COLORS['text_primary']}; text-decoration: none;">{escape(headline[:80])}{'...' if len(headline) > 80 else ''}</a>
                                        </h3>
                                        <p style="margin: 0 0 8px; font-size: 14px; color: {COLORS['text_secondary']}; line-height: 1.5;">
                                            {escape(tldr[:200])}{'...' if len(tldr) > 200 else ''}
                                        </p>
                                        <p style="margin: 0; font-size: 11px; color: {COLORS['text_secondary']};">
                                            Source: {escape(source)}
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
''')

    # footer
    html_parts.append(f'''
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 30px; text-align: center;">
                            <p style="margin: 0 0 10px; font-size: 12px; color: {COLORS['text_secondary']};">
                                <a href="https://thebeakers.com" style="color: {COLORS['accent_green']}; text-decoration: none;">thebeakers.com</a>
                            </p>
                            <p style="margin: 0; font-size: 11px; color: {COLORS['text_secondary']}; font-style: italic;">
                                "Knowledge always grows when shared"
                            </p>
                            <p style="margin: 15px 0 0; font-size: 10px; color: {COLORS['text_secondary']};">
                                <a href="{{{{ unsubscribe_url }}}}" style="color: {COLORS['text_secondary']};">Unsubscribe</a>
                            </p>
                        </td>
                    </tr>

                </table>
            </td>
        </tr>
    </table>
</body>
</html>
''')

    return "".join(html_parts)


def render_digest(
    week_of: str,
    slot: str = None,
    output_path: str = None,
    title: str = None
) -> str:
    """render digest and optionally save to file"""

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    articles = get_issue_articles(conn, week_of, slot)
    conn.close()

    if not articles:
        print(f"no articles found for week {week_of}")
        return None

    print(f"found {len(articles)} articles for {week_of}")

    # count by slot
    slot_counts = {}
    for a in articles:
        s = a.get("slot", "unknown")
        slot_counts[s] = slot_counts.get(s, 0) + 1
    print(f"  slots: {slot_counts}")

    # render
    html = render_digest_html(articles, week_of, title)

    # save if output path specified
    if output_path:
        Path(output_path).write_text(html)
        print(f"saved to {output_path}")

    return html


def main():
    parser = argparse.ArgumentParser(description="render daily digest HTML")
    parser.add_argument("--week", default=datetime.now().strftime("%Y-%m-%d"),
                        help="week to render (YYYY-MM-DD)")
    parser.add_argument("--slot", choices=["indepth", "digest", "blurb"],
                        help="only render specific slot type")
    parser.add_argument("--output", help="output HTML file path")
    parser.add_argument("--title", help="custom email title")

    args = parser.parse_args()

    output = args.output or str(OUTPUT_DIR / f"digest_{args.week}.html")

    render_digest(args.week, args.slot, output, args.title)


if __name__ == "__main__":
    main()
