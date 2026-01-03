#!/usr/bin/env python3
"""
The Beakers Telegram Curator
Sends collected STEM articles to Telegram for weekly curation
"""

import json
import requests
import time
import sqlite3
from pathlib import Path
from datetime import datetime

# Telegram Bot Configuration
BOT_TOKEN = "8059001447:AAEqUzCwmxbvI8apmu50vAtk2Q9nMJAsHPw"
CHAT_ID = "5314021805"  # Same curator as SPS Daily
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Paths
BEAKERS_DIR = Path("/storage/thebeakers")
DATA_DIR = BEAKERS_DIR / "data"
PENDING_FILE = DATA_DIR / "pending_articles.json"
APPROVED_FILE = DATA_DIR / "approved_articles.json"
DB_PATH = DATA_DIR / "articles.db"

# Disciplines
DISCIPLINES = ["chemistry", "physics", "biology", "mathematics", "engineering", "agriculture", "ai"]

def send_message(text, reply_markup=None):
    """Send a message to the curator"""
    data = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)

    response = requests.post(f"{API_URL}/sendMessage", data=data)
    return response.json()

def send_article_for_review(article, discipline, source_type, index):
    """Send an article with approve/reject/pick buttons"""

    # Emoji based on source type
    type_emoji = "🔬" if source_type == "research" else "📚"

    text = f"""{type_emoji} <b>{discipline.upper()}</b> ({source_type})

<b>{article['headline']}</b>

{article.get('teaser', '')[:300]}

<i>Source: {article['source']}</i>
<a href="{article['url']}">Read full article</a>"""

    keyboard = {
        "inline_keyboard": [
            [
                {"text": "✅ Quick Link", "callback_data": f"quick:{discipline}:{source_type}:{index}"},
                {"text": "📝 Rewrite", "callback_data": f"rewrite:{discipline}:{source_type}:{index}"},
            ],
            [
                {"text": "⭐ Editor's Pick", "callback_data": f"pick:{discipline}:{source_type}:{index}"},
                {"text": "❌ Skip", "callback_data": f"skip:{discipline}:{source_type}:{index}"},
            ]
        ]
    }

    return send_message(text, keyboard)

def get_updates(offset=None):
    """Get updates from Telegram"""
    params = {"timeout": 30}
    if offset:
        params["offset"] = offset
    response = requests.get(f"{API_URL}/getUpdates", params=params)
    return response.json()

def load_pending():
    """Load pending articles"""
    if PENDING_FILE.exists():
        return json.load(open(PENDING_FILE))
    return {}

def load_approved():
    """Load approved articles"""
    if APPROVED_FILE.exists():
        return json.load(open(APPROVED_FILE))

    # Initialize empty structure
    approved = {"week": "", "disciplines": {}}
    for d in DISCIPLINES:
        approved["disciplines"][d] = {
            "editorsPick": None,
            "rewrite": [],
            "quickLinks": []
        }
    return approved

def save_approved(approved):
    """Save approved articles"""
    with open(APPROVED_FILE, 'w') as f:
        json.dump(approved, f, indent=2)

def add_to_archive(article, discipline, article_type):
    """Add approved article to archive database"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS archive (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            headline TEXT,
            teaser TEXT,
            source TEXT,
            discipline TEXT,
            article_type TEXT,
            week TEXT,
            approved_date DATE DEFAULT CURRENT_DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    week = datetime.now().strftime("%Y-W%W")
    conn.execute('''
        INSERT OR REPLACE INTO archive (url, headline, teaser, source, discipline, article_type, week, approved_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (article['url'], article['headline'], article.get('teaser', ''),
          article.get('source', ''), discipline, article_type, week, datetime.now().strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()

def publish_discipline(discipline):
    """Publish approved articles for a discipline to its JSON file"""
    approved = load_approved()
    disc_data = approved["disciplines"].get(discipline, {})

    output = {
        "lastUpdated": datetime.now().strftime("%Y-%m-%d"),
        "week": datetime.now().strftime("%Y-W%W"),
        "editorsPick": disc_data.get("editorsPick"),
        "rewrite": disc_data.get("rewrite", []),
        "quickLinks": disc_data.get("quickLinks", [])
    }

    output_path = DATA_DIR / f"{discipline}.json"
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    return output_path

def git_push():
    """Commit and push changes to GitHub"""
    import subprocess
    try:
        subprocess.run(["git", "add", "data/"], cwd=BEAKERS_DIR, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "📰 Weekly update"], cwd=BEAKERS_DIR, check=True, capture_output=True)
        subprocess.run(["git", "push"], cwd=BEAKERS_DIR, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        return False

def send_articles_for_review():
    """Send all collected articles for review"""
    pending = load_pending()

    if not pending or "disciplines" not in pending:
        send_message("❌ No pending articles. Run the collector first.")
        return

    week = pending.get("week", "Unknown")
    send_message(f"🧪 <b>The Beakers - Week {week}</b>\n\nReview articles below:\n✅ Quick Link = add to links\n📝 Rewrite = mark for AI rewrite\n⭐ Editor's Pick = featured article\n❌ Skip = ignore")
    time.sleep(1)

    for discipline in DISCIPLINES:
        disc_data = pending["disciplines"].get(discipline, {})
        research = disc_data.get("research", [])
        education = disc_data.get("education", [])

        if not research and not education:
            continue

        total = len(research) + len(education)
        send_message(f"\n📂 <b>{discipline.upper()}</b> ({total} articles)")
        time.sleep(0.5)

        # Send research articles
        for i, article in enumerate(research[:10]):  # Limit to 10
            send_article_for_review(article, discipline, "research", i)
            time.sleep(0.3)

        # Send education articles
        for i, article in enumerate(education[:10]):  # Limit to 10
            send_article_for_review(article, discipline, "education", i)
            time.sleep(0.3)

    send_message("✅ All articles sent!\n\nWhen done, send /publish to generate JSON files.")

def handle_callback(callback_data, pending, approved):
    """Handle button callbacks"""
    parts = callback_data.split(":")
    if len(parts) < 4:
        return "Invalid callback"

    action = parts[0]
    discipline = parts[1]
    source_type = parts[2]
    index = int(parts[3])

    # Get article from pending
    disc_data = pending.get("disciplines", {}).get(discipline, {})
    articles = disc_data.get(source_type, [])

    if index >= len(articles):
        return "Article not found"

    article = articles[index]

    # Initialize discipline in approved if needed
    if discipline not in approved["disciplines"]:
        approved["disciplines"][discipline] = {
            "editorsPick": None,
            "rewrite": [],
            "quickLinks": []
        }

    if action == "quick":
        # Add to quick links
        if article not in approved["disciplines"][discipline]["quickLinks"]:
            approved["disciplines"][discipline]["quickLinks"].append(article)
            add_to_archive(article, discipline, "quickLink")
            save_approved(approved)
            return f"✅ Added to {discipline} quick links"
        return "Already added"

    elif action == "rewrite":
        # Mark for AI rewrite
        if article not in approved["disciplines"][discipline]["rewrite"]:
            approved["disciplines"][discipline]["rewrite"].append(article)
            add_to_archive(article, discipline, "rewrite")
            save_approved(approved)
            return f"📝 Marked for rewrite ({discipline})"
        return "Already marked"

    elif action == "pick":
        # Set as editor's pick
        approved["disciplines"][discipline]["editorsPick"] = article
        add_to_archive(article, discipline, "editorsPick")
        save_approved(approved)
        return f"⭐ Set as {discipline} Editor's Pick!"

    elif action == "skip":
        return "⏭ Skipped"

    return "Unknown action"

def run_curator():
    """Main curator loop"""
    print("🧪 The Beakers STEM Curator Bot started")
    print(f"   Bot: @thebeakers_stem_bot")
    print(f"   Listening for commands...")

    offset = None
    pending = {}
    approved = load_approved()

    while True:
        try:
            updates = get_updates(offset)

            if not updates.get("ok"):
                print(f"Error: {updates}")
                time.sleep(5)
                continue

            for update in updates.get("result", []):
                offset = update["update_id"] + 1

                # Handle messages (commands)
                if "message" in update:
                    msg = update["message"]
                    text = msg.get("text", "")

                    if text == "/start" or text == "/review":
                        pending = load_pending()
                        send_articles_for_review()

                    elif text == "/publish":
                        for discipline in DISCIPLINES:
                            path = publish_discipline(discipline)
                            send_message(f"📄 Published {discipline}.json")
                        if git_push():
                            send_message("🚀 Pushed to GitHub!")
                        else:
                            send_message("⚠️ Git push failed (run manually)")

                    elif text == "/status":
                        approved = load_approved()
                        status = "📊 <b>Status</b>\n\n"
                        for d in DISCIPLINES:
                            disc = approved["disciplines"].get(d, {})
                            pick = "✓" if disc.get("editorsPick") else "✗"
                            rw = len(disc.get("rewrite", []))
                            ql = len(disc.get("quickLinks", []))
                            status += f"{d}: Pick {pick} | Rewrite {rw} | Links {ql}\n"
                        send_message(status)

                    elif text == "/help":
                        send_message("""<b>The Beakers Curator Commands</b>

/review - Send articles for review
/status - Show approved counts
/publish - Generate JSON files
/help - Show this help""")

                # Handle callbacks (button presses)
                elif "callback_query" in update:
                    callback = update["callback_query"]
                    callback_data = callback.get("data", "")

                    pending = load_pending()
                    approved = load_approved()

                    result = handle_callback(callback_data, pending, approved)

                    requests.post(f"{API_URL}/answerCallbackQuery", data={
                        "callback_query_id": callback["id"],
                        "text": result
                    })

        except KeyboardInterrupt:
            print("\nStopping curator...")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "send":
            send_articles_for_review()
        elif sys.argv[1] == "publish":
            for discipline in DISCIPLINES:
                publish_discipline(discipline)
    else:
        run_curator()
