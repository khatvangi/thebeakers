#!/usr/bin/env python3
"""
stage0_fulltext_fetch.py - fetch full-text PDFs for triaged articles

input: triage_result rows where route in ('blurb','digest') AND frontier_flag=1 AND status='ok'
output: downloads to data/papers/<article_id>/paper.pdf, updates DB

resolution order:
1. direct DOI link (if OA)
2. Unpaywall API
3. PMC
4. skip (mark as unavailable)
"""

import argparse
import hashlib
import json
import os
import re
import sqlite3
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Tuple
from urllib.parse import urlparse, quote

# config
DB_PATH = Path(__file__).parent.parent / "data" / "articles.db"
PAPERS_DIR = Path(__file__).parent.parent / "data" / "papers"
UNPAYWALL_CACHE = Path(__file__).parent.parent / "cache" / "unpaywall"
UNPAYWALL_EMAIL = os.environ.get("UNPAYWALL_EMAIL", "thebeakerscom@gmail.com")

# headers to avoid being blocked
HEADERS = {
    "User-Agent": "TheBeakers/1.0 (educational platform; mailto:thebeakerscom@gmail.com)"
}


def article_id_from_url(url: str) -> str:
    """generate a safe directory name from article URL"""
    # extract DOI if present
    doi_match = re.search(r'10\.\d{4,}/[^\s]+', url)
    if doi_match:
        doi = doi_match.group(0)
        # clean up trailing characters
        doi = re.sub(r'[?#].*$', '', doi)
        # make filesystem-safe
        return doi.replace('/', '_').replace(':', '_')

    # fallback to URL hash
    return hashlib.md5(url.encode()).hexdigest()[:16]


def extract_doi(url: str) -> Optional[str]:
    """extract DOI from URL"""
    # common patterns
    patterns = [
        r'doi\.org/(10\.\d{4,}/[^\s?#]+)',
        r'dx\.doi\.org/(10\.\d{4,}/[^\s?#]+)',
        r'(10\.\d{4,}/[^\s?#]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            doi = match.group(1)
            # clean trailing punctuation
            doi = re.sub(r'[.,;:]+$', '', doi)
            return doi
    return None


def unpaywall_cache_path(doi: str) -> Path:
    """get cache file path for a DOI"""
    safe_doi = doi.replace("/", "_").replace(":", "_")
    return UNPAYWALL_CACHE / f"{safe_doi}.json"


def load_unpaywall_cache(doi: str) -> Optional[Dict]:
    """load cached Unpaywall response"""
    cache_file = unpaywall_cache_path(doi)
    if cache_file.exists():
        try:
            import json
            data = json.loads(cache_file.read_text())
            # cache is valid for 30 days
            cached_at = data.get("_cached_at", "")
            if cached_at:
                from datetime import datetime, timedelta
                cached_time = datetime.fromisoformat(cached_at)
                if datetime.now() - cached_time < timedelta(days=30):
                    return data
        except Exception:
            pass
    return None


def save_unpaywall_cache(doi: str, data: Dict) -> None:
    """save Unpaywall response to cache"""
    import json
    UNPAYWALL_CACHE.mkdir(parents=True, exist_ok=True)
    data["_cached_at"] = datetime.now().isoformat()
    cache_file = unpaywall_cache_path(doi)
    cache_file.write_text(json.dumps(data, indent=2))


def try_unpaywall(doi: str) -> Optional[str]:
    """query Unpaywall API for OA PDF link (with caching)"""
    # check cache first
    cached = load_unpaywall_cache(doi)
    if cached:
        best = cached.get("best_oa_location")
        if best:
            pdf_url = best.get("url_for_pdf") or best.get("url")
            if pdf_url:
                print(f"    [unpaywall/cached] found: {pdf_url[:60]}...")
                return pdf_url
        print(f"    [unpaywall/cached] no OA")
        return None

    # query API
    url = f"https://api.unpaywall.org/v2/{quote(doi, safe='')}?email={UNPAYWALL_EMAIL}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            save_unpaywall_cache(doi, data)  # cache response
            # check for best OA location
            best = data.get("best_oa_location")
            if best:
                pdf_url = best.get("url_for_pdf") or best.get("url")
                if pdf_url:
                    print(f"    [unpaywall] found: {pdf_url[:60]}...")
                    return pdf_url
        elif resp.status_code == 404:
            # DOI not found - cache as empty
            save_unpaywall_cache(doi, {"is_oa": False, "_not_found": True})
            print(f"    [unpaywall] DOI not found")
    except Exception as e:
        print(f"    [unpaywall] error: {e}")
    return None


def try_pmc(doi: str) -> Optional[str]:
    """check if article is in PMC and get PDF link"""
    # PMC ID lookup via NCBI
    url = f"https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?ids={quote(doi, safe='')}&format=json"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            records = data.get("records", [])
            if records and records[0].get("pmcid"):
                pmcid = records[0]["pmcid"]
                pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf/"
                print(f"    [pmc] found: {pdf_url}")
                return pdf_url
    except Exception as e:
        print(f"    [pmc] error: {e}")
    return None


def download_pdf(url: str, dest_path: Path) -> bool:
    """download PDF to destination"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=60, stream=True)
        if resp.status_code == 200:
            content_type = resp.headers.get("Content-Type", "")
            # check if it's actually a PDF
            if "pdf" in content_type.lower() or url.endswith(".pdf"):
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                with open(dest_path, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)
                # verify it's a valid PDF
                with open(dest_path, 'rb') as f:
                    header = f.read(5)
                    if header == b'%PDF-':
                        return True
                    else:
                        dest_path.unlink()  # not a PDF
                        print(f"    [download] not a valid PDF")
                        return False
            else:
                print(f"    [download] not PDF content-type: {content_type}")
                return False
    except Exception as e:
        print(f"    [download] error: {e}")
    return False


def fetch_fulltext(article_url: str, doi: Optional[str] = None) -> Tuple[Optional[str], str]:
    """
    attempt to fetch full text for an article

    returns: (local_path, source) or (None, 'unavailable')
    """
    article_id = article_id_from_url(article_url)
    dest_dir = PAPERS_DIR / article_id
    dest_path = dest_dir / "paper.pdf"

    # check if already downloaded
    if dest_path.exists():
        print(f"    already downloaded: {dest_path}")
        return str(dest_path), "cached"

    # try arXiv direct first (no DOI needed, no Cloudflare)
    if "arxiv.org" in article_url:
        # extract arXiv ID from URL (e.g., arxiv.org/abs/2401.00001)
        arxiv_match = re.search(r'arxiv\.org/abs/([^\s/]+)', article_url)
        if arxiv_match:
            arxiv_id = arxiv_match.group(1)
            arxiv_pdf = f"https://arxiv.org/pdf/{arxiv_id}"  # note: no .pdf extension needed
            print(f"    [arxiv] trying: {arxiv_pdf}")
            if download_pdf(arxiv_pdf, dest_path):
                return str(dest_path), "arxiv_direct"

    # try bioRxiv/medRxiv direct (may fail due to Cloudflare)
    if "biorxiv.org" in article_url or "medrxiv.org" in article_url:
        # pattern: {article_url}.full.pdf
        clean_url = re.sub(r'\?.*$', '', article_url)  # remove query params
        biorxiv_pdf = f"{clean_url}.full.pdf"
        print(f"    [biorxiv] trying: {biorxiv_pdf[:60]}...")
        if download_pdf(biorxiv_pdf, dest_path):
            return str(dest_path), "biorxiv_direct"

    # extract DOI for Unpaywall/PMC fallbacks
    if not doi:
        doi = extract_doi(article_url)
    if not doi:
        print(f"    no DOI found for fallback methods")
        return None, "no_doi"

    # try Unpaywall
    pdf_url = try_unpaywall(doi)
    if pdf_url:
        if download_pdf(pdf_url, dest_path):
            return str(dest_path), "unpaywall"
        else:
            # unpaywall found URL but download failed
            return None, "unpaywall_download_failed"

    # try PMC
    pdf_url = try_pmc(doi)
    if pdf_url:
        if download_pdf(pdf_url, dest_path):
            return str(dest_path), "pmc"
        else:
            return None, "pmc_download_failed"

    # try direct DOI redirect (some publishers serve OA directly)
    direct_url = f"https://doi.org/{doi}"
    try:
        resp = requests.head(direct_url, headers=HEADERS, timeout=10, allow_redirects=True)
        final_url = resp.url
        if "pdf" in final_url.lower():
            if download_pdf(final_url, dest_path):
                return str(dest_path), "direct"
    except Exception as e:
        print(f"    [direct] error: {e}")

    return None, "unavailable"


def run_fulltext_fetch(limit: int = 10, dry_run: bool = False) -> Dict:
    """fetch fulltext for pending triaged articles"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # ensure schema has new columns
    from db_schema_triage import ensure_triage_schema
    ensure_triage_schema(conn)

    # get candidates: frontier articles needing fulltext (not yet attempted)
    cursor = conn.execute("""
        SELECT run_id, article_url, discipline, route, score_e
        FROM triage_result
        WHERE route IN ('blurb', 'digest')
          AND frontier_flag = 1
          AND status = 'ok'
          AND (fulltext_ok IS NULL OR fulltext_ok = 0)
          AND fulltext_source IS NULL
        ORDER BY score_s DESC, score_t DESC
        LIMIT ?
    """, (limit,))

    articles = cursor.fetchall()
    print(f"=== FULLTEXT FETCH ===")
    print(f"found {len(articles)} articles needing fulltext")

    results = {"fetched": 0, "unavailable": 0, "errors": 0}

    for article in articles:
        url = article["article_url"]
        print(f"\n>>> {url[:60]}...")

        if dry_run:
            print("  [dry-run] would fetch")
            continue

        try:
            path, source = fetch_fulltext(url)

            if path:
                # update DB - PDF found and downloaded
                conn.execute("""
                    UPDATE triage_result
                    SET fulltext_path = ?,
                        fulltext_ok = 1,
                        fulltext_source = ?,
                        fulltext_fetched_at = ?,
                        access_state = 'oa_pdf_found'
                    WHERE article_url = ?
                """, (path, source, datetime.now().isoformat(), url))
                conn.commit()
                results["fetched"] += 1
                print(f"  OK: {source}")
            else:
                # determine access_state based on failure reason
                if source in ('unavailable', 'no_doi'):
                    access_state = 'paywalled'
                elif source.endswith('_download_failed'):
                    # OA location found but download failed
                    access_state = 'oa_pdf_found_but_failed'
                else:
                    access_state = 'abstract_only'

                conn.execute("""
                    UPDATE triage_result
                    SET fulltext_source = ?,
                        fulltext_fetched_at = ?,
                        access_state = ?
                    WHERE article_url = ?
                """, (source, datetime.now().isoformat(), access_state, url))
                conn.commit()
                results["unavailable"] += 1
                print(f"  UNAVAILABLE: {source} ({access_state})")

        except Exception as e:
            print(f"  ERROR: {e}")
            results["errors"] += 1

    conn.close()

    print(f"\n=== SUMMARY ===")
    print(f"fetched: {results['fetched']}")
    print(f"unavailable: {results['unavailable']}")
    print(f"errors: {results['errors']}")

    return results


def main():
    parser = argparse.ArgumentParser(description="fetch full-text PDFs for triaged articles")
    parser.add_argument("--limit", type=int, default=10, help="max articles to fetch")
    parser.add_argument("--dry-run", action="store_true", help="don't actually download")

    args = parser.parse_args()
    run_fulltext_fetch(args.limit, args.dry_run)


if __name__ == "__main__":
    main()
