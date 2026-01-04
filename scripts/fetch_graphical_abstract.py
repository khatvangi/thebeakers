#!/usr/bin/env python3
"""
Fetch graphical abstracts from research paper DOIs
Supports: ACS, Nature, Elsevier, RSC, Wiley
"""

import requests
import re
import json
from pathlib import Path
from urllib.parse import urlparse

BEAKERS_DIR = Path(__file__).parent.parent
IMAGES_DIR = BEAKERS_DIR / "images" / "abstracts"

# User agent to avoid blocks
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}


def get_doi_metadata(doi):
    """Get metadata from CrossRef API"""
    url = f"https://api.crossref.org/works/{doi}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            return resp.json().get('message', {})
    except Exception as e:
        print(f"  CrossRef error: {e}")
    return {}


def fetch_acs_abstract(doi):
    """Fetch graphical abstract from ACS journals (JACS, etc.)"""
    # ACS pattern: https://pubs.acs.org/doi/10.1021/jacs.xxxxx
    # Graphical abstract: https://pubs.acs.org/cms/10.1021/jacs.xxxxx/asset/images/medium/jaXXXX_0001.gif

    # First get the article page to find the actual image
    article_url = f"https://pubs.acs.org/doi/{doi}"
    print(f"  Checking ACS: {article_url}")

    try:
        resp = requests.get(article_url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            # Look for graphical abstract image
            # Pattern: /cms/10.1021/xxxxx/asset/images/medium/xxxxx_0001.gif
            matches = re.findall(r'/cms/[^"]+/asset/images/[^"]+\.(?:gif|png|jpg)', resp.text)
            if matches:
                img_url = f"https://pubs.acs.org{matches[0]}"
                print(f"  Found ACS image: {img_url}")
                return img_url

            # Try TOC graphic
            toc_matches = re.findall(r'(https://pubs\.acs\.org/cms/[^"]+toc[^"]+\.(?:gif|png|jpg))', resp.text)
            if toc_matches:
                print(f"  Found ACS TOC: {toc_matches[0]}")
                return toc_matches[0]
    except Exception as e:
        print(f"  ACS error: {e}")

    return None


def fetch_nature_abstract(doi):
    """Fetch figure from Nature journals"""
    # Nature pattern: https://www.nature.com/articles/s41557-xxx
    article_id = doi.split('/')[-1]
    article_url = f"https://www.nature.com/articles/{article_id}"
    print(f"  Checking Nature: {article_url}")

    try:
        resp = requests.get(article_url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            # Look for figure images
            matches = re.findall(r'(https://media\.nature\.com/[^"]+\.(?:png|jpg|gif))', resp.text)
            if matches:
                print(f"  Found Nature image: {matches[0]}")
                return matches[0]
    except Exception as e:
        print(f"  Nature error: {e}")

    return None


def fetch_rsc_abstract(doi):
    """Fetch graphical abstract from RSC journals"""
    article_url = f"https://pubs.rsc.org/en/content/articlelanding/{doi.split('/')[-1]}"
    print(f"  Checking RSC: {article_url}")

    try:
        resp = requests.get(article_url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            matches = re.findall(r'(https://pubs\.rsc\.org/[^"]+ga\.(?:png|jpg|gif))', resp.text)
            if matches:
                print(f"  Found RSC image: {matches[0]}")
                return matches[0]
    except Exception as e:
        print(f"  RSC error: {e}")

    return None


def fetch_graphical_abstract(doi):
    """Try to fetch graphical abstract from various publishers"""
    print(f"\nFetching graphical abstract for: {doi}")

    # Get metadata to determine publisher
    metadata = get_doi_metadata(doi)
    publisher = metadata.get('publisher', '').lower()
    container = metadata.get('container-title', [''])[0].lower() if metadata.get('container-title') else ''

    print(f"  Publisher: {publisher}")
    print(f"  Journal: {container}")

    # Try publisher-specific methods
    if 'american chemical society' in publisher or '10.1021' in doi:
        result = fetch_acs_abstract(doi)
        if result:
            return {'url': result, 'source': 'ACS', 'type': 'graphical_abstract'}

    if 'nature' in publisher or 'nature' in container:
        result = fetch_nature_abstract(doi)
        if result:
            return {'url': result, 'source': 'Nature', 'type': 'figure'}

    if 'royal society of chemistry' in publisher or '10.1039' in doi:
        result = fetch_rsc_abstract(doi)
        if result:
            return {'url': result, 'source': 'RSC', 'type': 'graphical_abstract'}

    # Fallback: try Unpaywall for open access version
    print("  Trying Unpaywall...")
    try:
        unpaywall_url = f"https://api.unpaywall.org/v2/{doi}?email=thebeakerscom@gmail.com"
        resp = requests.get(unpaywall_url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('best_oa_location'):
                oa_url = data['best_oa_location'].get('url_for_pdf') or data['best_oa_location'].get('url')
                if oa_url:
                    print(f"  Found OA link: {oa_url}")
                    return {'url': oa_url, 'source': 'Unpaywall', 'type': 'open_access'}
    except Exception as e:
        print(f"  Unpaywall error: {e}")

    return None


def download_image(url, doi, output_dir=IMAGES_DIR):
    """Download image to local storage"""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create filename from DOI
    safe_doi = re.sub(r'[^a-zA-Z0-9]', '-', doi)
    ext = url.split('.')[-1].split('?')[0][:4]  # Get extension
    filename = f"{safe_doi}.{ext}"
    filepath = output_dir / filename

    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        if resp.status_code == 200:
            with open(filepath, 'wb') as f:
                f.write(resp.content)
            print(f"  Downloaded: {filepath}")
            return str(filepath.relative_to(BEAKERS_DIR))
    except Exception as e:
        print(f"  Download error: {e}")

    return None


def get_semantic_scholar_data(doi):
    """Get paper data from Semantic Scholar API (free, includes TLDR and authors)"""
    url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields=title,abstract,tldr,authors,year,venue,citationCount,openAccessPdf"
    print(f"  Checking Semantic Scholar...")

    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            result = {
                'title': data.get('title'),
                'authors': [a.get('name') for a in data.get('authors', []) if a.get('name')],
                'year': data.get('year'),
                'venue': data.get('venue'),
                'citations': data.get('citationCount'),
                'tldr': data.get('tldr', {}).get('text') if data.get('tldr') else None,
            }
            # Check for open access PDF
            if data.get('openAccessPdf', {}).get('url'):
                result['pdf_url'] = data['openAccessPdf']['url']

            print(f"  Found: {len(result['authors'])} authors, {result['citations']} citations")
            return result
    except Exception as e:
        print(f"  Semantic Scholar error: {e}")

    return None


def get_paper_metadata(doi):
    """Get comprehensive paper metadata from multiple sources"""
    print(f"\nFetching metadata for: {doi}")

    # Try Semantic Scholar first (best for authors/TLDR)
    ss_data = get_semantic_scholar_data(doi)

    # Also get CrossRef data
    cr_data = get_doi_metadata(doi)

    # Combine results
    result = {
        'doi': doi,
        'url': f"https://doi.org/{doi}",
    }

    if ss_data:
        result.update({
            'title': ss_data.get('title'),
            'authors': ss_data.get('authors', []),
            'year': ss_data.get('year'),
            'tldr': ss_data.get('tldr'),
            'citations': ss_data.get('citations'),
            'pdf_url': ss_data.get('pdf_url'),
        })

    if cr_data:
        result['publisher'] = cr_data.get('publisher')
        result['journal'] = cr_data.get('container-title', [''])[0] if cr_data.get('container-title') else None
        if not result.get('title'):
            result['title'] = cr_data.get('title', [''])[0] if cr_data.get('title') else None

    return result


def test_fetch():
    """Test with the sample article"""
    test_doi = "10.1021/jacs.5c13642"

    # Get metadata
    metadata = get_paper_metadata(test_doi)
    print(f"\n📄 Paper Metadata:")
    print(f"   Title: {metadata.get('title')}")
    print(f"   Authors: {', '.join(metadata.get('authors', [])[:3])}...")
    print(f"   Journal: {metadata.get('journal')}")
    print(f"   Citations: {metadata.get('citations')}")
    print(f"   TLDR: {metadata.get('tldr', '')[:100]}...")

    # Try to get graphical abstract
    result = fetch_graphical_abstract(test_doi)
    if result:
        print(f"\n✅ Found image: {result}")
        local_path = download_image(result['url'], test_doi)
        if local_path:
            print(f"✅ Saved locally: {local_path}")
    else:
        print("\n⚠️ No graphical abstract found (paper may require subscription)")
        print(f"   View figures at: https://doi.org/{test_doi}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        doi = sys.argv[1]
        result = fetch_graphical_abstract(doi)
        if result:
            print(f"\nResult: {json.dumps(result, indent=2)}")
            download_image(result['url'], doi)
    else:
        test_fetch()
