#!/usr/bin/env python3
"""
society_fetcher.py - fetch papers from society journals (OA focus)

simple first: 3 research papers + 1-2 education papers per discipline
all open access, from trusted society publishers

usage:
    python society_fetcher.py              # fetch all disciplines
    python society_fetcher.py chemistry    # fetch one discipline
    python society_fetcher.py --list       # show configured sources
"""

import argparse
import json
import os
import re
import sqlite3
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from dataclasses import dataclass, asdict, field

# paths
DB_PATH = Path(__file__).parent.parent / "data" / "articles.db"
PAPERS_DIR = Path(__file__).parent.parent / "data" / "papers"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "society"
CURRICULUM_PATH = Path(__file__).parent.parent / "data" / "curriculum.json"

# education article classification patterns
# based on pedagogical criteria from curriculum.json
EDUCATION_PATTERNS = {
    "new-understanding": [
        r"new way to (understand|teach|explain)",
        r"novel approach to teaching",
        r"alternative (explanation|perspective|method)",
        r"reconceptualiz",
        r"fresh perspective",
        r"intuitive (understanding|approach)",
    ],
    "simple-experiment": [
        r"simple experiment",
        r"hands-on",
        r"demonstration",
        r"laboratory (activity|exercise)",
        r"low-cost experiment",
        r"classroom (experiment|demonstration|activity)",
        r"(easy|quick) to (perform|set up)",
        r"DIY",
    ],
    "misconception": [
        r"misconception",
        r"students (struggle|fail|difficulty|confuse)",
        r"common (error|mistake)",
        r"wrong (belief|assumption)",
        r"learning difficult",
        r"conceptual (barrier|challenge|difficulty)",
        r"misunderstand",
    ],
    "teaching-innovation": [
        r"active learning",
        r"inquiry-based",
        r"problem-based learning",
        r"flipped classroom",
        r"peer instruction",
        r"collaborative learning",
        r"game-based",
        r"simulation",
        r"virtual (lab|laboratory)",
        r"online learning",
        r"pedagogical",
    ],
}

# api keys from environment
SEMANTIC_SCHOLAR_KEY = os.environ.get("SEMANTIC_SCHOLAR_API_KEY", "")

# headers
HEADERS = {
    "User-Agent": "TheBeakers/1.0 (educational; mailto:thebeakerscom@gmail.com)"
}

# society journal sources - simple, curated list
# format: publisher -> list of journal names/ISSNs
SOURCES = {
    "chemistry": {
        "research": [
            # open access with abstracts
            {"name": "Frontiers in Chemistry", "issn": "2296-2646", "publisher": "Frontiers", "oa": True},
            {"name": "RSC Advances", "issn": "2046-2069", "publisher": "RSC", "oa": True},
            {"name": "Beilstein J. Org. Chem.", "issn": "1860-5397", "publisher": "Beilstein", "oa": True},
            {"name": "Molecules", "issn": "1420-3049", "publisher": "MDPI", "oa": True},
            {"name": "Catalysts", "issn": "2073-4344", "publisher": "MDPI", "oa": True},
            # ACS OA (may not have abstracts via API)
            {"name": "ACS Central Science", "issn": "2374-7943", "publisher": "ACS", "oa": True},
            {"name": "JACS Au", "issn": "2691-3704", "publisher": "ACS", "oa": True},
        ],
        "education": [
            {"name": "J. Chem. Education", "issn": "0021-9584", "publisher": "ACS", "oa": False},
            {"name": "Chemistry Education Research and Practice", "issn": "1756-1108", "publisher": "RSC", "oa": False},
        ]
    },
    "physics": {
        "research": [
            {"name": "Physical Review X", "issn": "2160-3308", "publisher": "APS", "oa": True},
            {"name": "PRX Quantum", "issn": "2691-3399", "publisher": "APS", "oa": True},
            {"name": "Physical Review Research", "issn": "2643-1564", "publisher": "APS", "oa": True},
        ],
        "education": [
            {"name": "Am. J. Physics", "issn": "0002-9505", "publisher": "AAPT", "oa": False},
        ]
    },
    "biology": {
        "research": [
            {"name": "PLOS Biology", "issn": "1545-7885", "publisher": "PLOS", "oa": True},
            {"name": "eLife", "issn": "2050-084X", "publisher": "eLife", "oa": True},
            {"name": "PLOS ONE", "issn": "1932-6203", "publisher": "PLOS", "oa": True},
        ],
        "education": [
            {"name": "CBE Life Sci. Education", "issn": "1931-7913", "publisher": "ASCB", "oa": True},
        ]
    },
    "engineering": {
        "research": [
            {"name": "IEEE Access", "issn": "2169-3536", "publisher": "IEEE", "oa": True},
            {"name": "ASME Open J. Engineering", "issn": "2770-3495", "publisher": "ASME", "oa": True},
            {"name": "Frontiers in Robotics and AI", "issn": "2296-9144", "publisher": "Frontiers", "oa": True},
        ],
        "education": [
            {"name": "J. Engineering Education", "issn": "1069-4730", "publisher": "ASEE", "oa": False},
        ]
    },
    "mathematics": {
        "research": [
            {"name": "Forum of Mathematics, Sigma", "issn": "2050-5094", "publisher": "Cambridge", "oa": True},
            {"name": "Forum of Mathematics, Pi", "issn": "2050-5086", "publisher": "Cambridge", "oa": True},
            {"name": "Discrete Analysis", "issn": "2397-3129", "publisher": "DA", "oa": True},
        ],
        "education": [
            {"name": "PRIMUS", "issn": "1051-1970", "publisher": "Taylor Francis", "oa": False},
        ]
    },
    "ai": {
        "research": [
            # open access with abstracts
            {"name": "Frontiers in Artificial Intelligence", "issn": "2624-8212", "publisher": "Frontiers", "oa": True},
            {"name": "Machine Learning", "issn": "1573-0565", "publisher": "Springer", "oa": False},  # some OA
            {"name": "Applied Sciences - AI Section", "issn": "2076-3417", "publisher": "MDPI", "oa": True},
            {"name": "Algorithms", "issn": "1999-4893", "publisher": "MDPI", "oa": True},
            {"name": "AI", "issn": "2673-2688", "publisher": "MDPI", "oa": True},
            # traditional
            {"name": "JMLR", "issn": "1533-7928", "publisher": "JMLR", "oa": True},
            {"name": "TMLR", "issn": "2835-8856", "publisher": "TMLR", "oa": True},
        ],
        "education": [
            {"name": "AI & Society", "issn": "1435-5655", "publisher": "Springer", "oa": False},
        ]
    },
    "agriculture": {
        "research": [
            {"name": "Agronomy", "issn": "2073-4395", "publisher": "MDPI", "oa": True},
            {"name": "Plants", "issn": "2223-7747", "publisher": "MDPI", "oa": True},
            {"name": "Agriculture", "issn": "2077-0472", "publisher": "MDPI", "oa": True},
        ],
        "education": []  # agriculture education through general sources
    }
}


@dataclass
class Paper:
    """paper metadata"""
    doi: str
    title: str
    authors: List[str]
    journal: str
    publisher: str
    discipline: str
    paper_type: str  # research or education
    abstract: str
    pub_date: str
    pdf_url: Optional[str] = None
    is_oa: bool = True
    education_tags: List[str] = field(default_factory=list)  # for education papers: new-understanding, simple-experiment, misconception, teaching-innovation
    curriculum_topics: List[str] = field(default_factory=list)  # matched curriculum topics from curriculum.json


def classify_education_article(title: str, abstract: str) -> List[str]:
    """classify education article by pedagogical type using pattern matching"""

    text = f"{title} {abstract}".lower()
    tags = []

    for tag_type, patterns in EDUCATION_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                tags.append(tag_type)
                break  # found one match for this type, move to next

    return tags


def match_curriculum_topics(title: str, abstract: str, discipline: str) -> List[str]:
    """match paper to curriculum topics based on keywords"""

    if not CURRICULUM_PATH.exists():
        return []

    try:
        with open(CURRICULUM_PATH) as f:
            curriculum = json.load(f)
    except:
        return []

    if discipline not in curriculum:
        return []

    text = f"{title} {abstract}".lower()
    matched_topics = []

    for subfield_name, subfield_data in curriculum[discipline].get("subfields", {}).items():
        for topic in subfield_data.get("topics", []):
            topic_name = topic["name"]
            keywords = topic.get("keywords", [])

            # check if any keyword matches
            for keyword in keywords:
                if keyword.lower() in text:
                    matched_topics.append(f"{subfield_name}: {topic_name}")
                    break

    return matched_topics[:5]  # limit to top 5 matches


def fetch_crossref_by_issn(issn: str, limit: int = 5, days_back: int = 90) -> List[Dict]:
    """fetch recent papers from a journal via Crossref"""

    # date filter
    from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

    url = "https://api.crossref.org/works"
    params = {
        "filter": f"issn:{issn},from-pub-date:{from_date},type:journal-article",
        "sort": "published",
        "order": "desc",
        "rows": limit,
        "mailto": "thebeakerscom@gmail.com"
    }

    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("message", {}).get("items", [])
    except Exception as e:
        print(f"  [!] crossref error for {issn}: {e}")
        return []


def crossref_to_paper(item: Dict, journal_info: Dict, discipline: str, paper_type: str) -> Optional[Paper]:
    """convert crossref item to Paper"""

    doi = item.get("DOI", "")
    if not doi:
        return None

    title = item.get("title", [""])[0] if item.get("title") else ""
    if not title:
        return None

    # authors
    authors = []
    for author in item.get("author", [])[:5]:  # first 5
        given = author.get("given", "")
        family = author.get("family", "")
        if family:
            authors.append(f"{given} {family}".strip())

    # abstract
    abstract = item.get("abstract", "")
    if abstract:
        # clean HTML tags
        abstract = re.sub(r'<[^>]+>', '', abstract)

    # pub date
    pub_date = ""
    if "published-print" in item:
        parts = item["published-print"].get("date-parts", [[]])[0]
    elif "published-online" in item:
        parts = item["published-online"].get("date-parts", [[]])[0]
    else:
        parts = []

    if parts:
        pub_date = "-".join(str(p) for p in parts)

    # pdf url (check for OA link)
    pdf_url = None
    for link in item.get("link", []):
        if link.get("content-type") == "application/pdf":
            pdf_url = link.get("URL")
            break

    # classify education articles by pedagogical type
    education_tags = []
    if paper_type == "education":
        education_tags = classify_education_article(title, abstract)

    # match curriculum topics (for both research and education)
    curriculum_topics = match_curriculum_topics(title, abstract, discipline)

    return Paper(
        doi=doi,
        title=title,
        authors=authors,
        journal=journal_info["name"],
        publisher=journal_info["publisher"],
        discipline=discipline,
        paper_type=paper_type,
        abstract=abstract,
        pub_date=pub_date,
        pdf_url=pdf_url,
        is_oa=journal_info.get("oa", False),
        education_tags=education_tags,
        curriculum_topics=curriculum_topics
    )


def fetch_pdf(paper: Paper) -> Optional[Path]:
    """download PDF for a paper, return path if successful"""

    if not paper.pdf_url:
        # try unpaywall
        paper.pdf_url = get_unpaywall_pdf(paper.doi)

    if not paper.pdf_url:
        return None

    # create directory
    safe_doi = paper.doi.replace("/", "_").replace(":", "_")
    paper_dir = PAPERS_DIR / paper.discipline / safe_doi
    paper_dir.mkdir(parents=True, exist_ok=True)

    pdf_path = paper_dir / "paper.pdf"
    if pdf_path.exists():
        return pdf_path

    try:
        resp = requests.get(paper.pdf_url, headers=HEADERS, timeout=60, allow_redirects=True)
        resp.raise_for_status()

        # verify it's actually a PDF
        if resp.content[:4] != b'%PDF':
            print(f"  [!] not a valid PDF: {paper.doi}")
            return None

        pdf_path.write_bytes(resp.content)
        print(f"  [✓] downloaded: {pdf_path.name}")
        return pdf_path

    except Exception as e:
        print(f"  [!] pdf download failed: {e}")
        return None


def get_unpaywall_pdf(doi: str) -> Optional[str]:
    """get OA PDF url from unpaywall"""

    url = f"https://api.unpaywall.org/v2/{doi}"
    params = {"email": "thebeakerscom@gmail.com"}

    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            best = data.get("best_oa_location")
            if best:
                return best.get("url_for_pdf") or best.get("url")
    except:
        pass

    return None


def save_to_db(papers: List[Paper]):
    """save papers to database"""

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # ensure table exists with education/curriculum fields
    cur.execute("""
        CREATE TABLE IF NOT EXISTS society_papers (
            doi TEXT PRIMARY KEY,
            title TEXT,
            authors TEXT,
            journal TEXT,
            publisher TEXT,
            discipline TEXT,
            paper_type TEXT,
            abstract TEXT,
            pub_date TEXT,
            pdf_url TEXT,
            is_oa INTEGER,
            education_tags TEXT,
            curriculum_topics TEXT,
            pdf_downloaded INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # add columns if they don't exist (for existing databases)
    try:
        cur.execute("ALTER TABLE society_papers ADD COLUMN education_tags TEXT")
    except sqlite3.OperationalError:
        pass  # column already exists
    try:
        cur.execute("ALTER TABLE society_papers ADD COLUMN curriculum_topics TEXT")
    except sqlite3.OperationalError:
        pass  # column already exists

    for paper in papers:
        cur.execute("""
            INSERT OR REPLACE INTO society_papers
            (doi, title, authors, journal, publisher, discipline, paper_type,
             abstract, pub_date, pdf_url, is_oa, education_tags, curriculum_topics)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            paper.doi,
            paper.title,
            json.dumps(paper.authors),
            paper.journal,
            paper.publisher,
            paper.discipline,
            paper.paper_type,
            paper.abstract,
            paper.pub_date,
            paper.pdf_url,
            1 if paper.is_oa else 0,
            json.dumps(paper.education_tags),
            json.dumps(paper.curriculum_topics)
        ))

    conn.commit()
    conn.close()


def fetch_discipline(discipline: str, download_pdfs: bool = True) -> List[Paper]:
    """fetch papers for one discipline"""

    if discipline not in SOURCES:
        print(f"[!] unknown discipline: {discipline}")
        return []

    sources = SOURCES[discipline]
    papers = []

    print(f"\n[{discipline.upper()}]")

    # research papers (limit 3)
    print("  research papers:")
    for journal in sources.get("research", []):
        print(f"    {journal['name']}...")
        items = fetch_crossref_by_issn(journal["issn"], limit=2, days_back=60)

        for item in items:
            paper = crossref_to_paper(item, journal, discipline, "research")
            if paper:
                papers.append(paper)
                print(f"      + {paper.title[:60]}...")
                if paper.curriculum_topics:
                    print(f"        curriculum: {', '.join(paper.curriculum_topics[:2])}")

        if len(papers) >= 3:
            break

    # education papers (limit 2)
    print("  education papers:")
    for journal in sources.get("education", []):
        print(f"    {journal['name']}...")
        items = fetch_crossref_by_issn(journal["issn"], limit=2, days_back=180)

        for item in items:
            paper = crossref_to_paper(item, journal, discipline, "education")
            if paper:
                papers.append(paper)
                print(f"      + {paper.title[:60]}...")
                if paper.education_tags:
                    print(f"        tags: {', '.join(paper.education_tags)}")
                if paper.curriculum_topics:
                    print(f"        curriculum: {', '.join(paper.curriculum_topics[:2])}")

    # download PDFs
    if download_pdfs:
        print("  downloading PDFs...")
        for paper in papers:
            fetch_pdf(paper)

    return papers


def list_sources():
    """print configured sources"""

    print("\n=== SOCIETY JOURNAL SOURCES ===\n")

    for discipline, sources in SOURCES.items():
        print(f"{discipline.upper()}")
        print("  Research:")
        for j in sources.get("research", []):
            oa = "✓ OA" if j.get("oa") else "  "
            print(f"    {oa} {j['name']} ({j['publisher']})")
        print("  Education:")
        for j in sources.get("education", []):
            oa = "✓ OA" if j.get("oa") else "  "
            print(f"    {oa} {j['name']} ({j['publisher']})")
        print()


def main():
    parser = argparse.ArgumentParser(description="Fetch papers from society journals")
    parser.add_argument("discipline", nargs="?", help="Discipline to fetch (or 'all')")
    parser.add_argument("--list", action="store_true", help="List configured sources")
    parser.add_argument("--no-pdf", action="store_true", help="Skip PDF downloads")
    args = parser.parse_args()

    if args.list:
        list_sources()
        return

    # ensure directories exist
    PAPERS_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    all_papers = []

    if args.discipline and args.discipline != "all":
        papers = fetch_discipline(args.discipline, not args.no_pdf)
        all_papers.extend(papers)
    else:
        for discipline in SOURCES.keys():
            papers = fetch_discipline(discipline, not args.no_pdf)
            all_papers.extend(papers)

    # save to database
    if all_papers:
        save_to_db(all_papers)
        print(f"\n=== SUMMARY ===")
        print(f"Total papers fetched: {len(all_papers)}")
        print(f"Saved to: {DB_PATH}")


if __name__ == "__main__":
    main()
