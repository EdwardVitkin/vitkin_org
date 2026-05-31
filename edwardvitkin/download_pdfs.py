import os
import re
import json
import time
import requests
from bs4 import BeautifulSoup
import sys

_print = print
def print(*args, **kwargs):
    try:
        _print(*args, **kwargs)
    except UnicodeEncodeError:
        safe_args = []
        for arg in args:
            if isinstance(arg, str):
                try:
                    safe_args.append(arg.encode(sys.stdout.encoding or 'ascii', errors='replace').decode(sys.stdout.encoding or 'ascii'))
                except Exception:
                    safe_args.append(arg.encode('ascii', errors='replace').decode('ascii'))
            else:
                safe_args.append(arg)
        _print(*safe_args, **kwargs)

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def slugify(title):
    title = title.lower()
    title = re.sub(r'[^a-z0-9\s-]', '', title)
    title = re.sub(r'[\s-]+', '_', title)
    return title.strip('_')[:60] # Limit filename length

def is_valid_pdf(file_path):
    try:
        with open(file_path, 'rb') as f:
            header = f.read(4)
            return header == b'%PDF'
    except Exception:
        return False

def fetch_publication_titles():
    url = "https://scholar.google.com/citations?hl=en&user=kE-Ral4AAAAJ&view_op=list_works&cstart=0&pagesize=100"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    print("Fetching publication list from Google Scholar...")
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch Google Scholar page: {response.status_code}")
        
    soup = BeautifulSoup(response.text, 'html.parser')
    pub_rows = soup.select('tr.gsc_a_tr')
    
    publications = []
    for row in pub_rows:
        title_link = row.select_one('td.gsc_a_t a')
        if not title_link:
            continue
        title = clean_text(title_link.text)
        
        year_elem = row.select_one('td.gsc_a_y span')
        year = clean_text(year_elem.text) if year_elem else ""
        
        publications.append({
            "title": title,
            "year": year
        })
    return publications

def clean_title_for_query(title):
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', ' ', title)
    return ' '.join(cleaned.split())

def search_openalex_pdf(title):
    url = "https://api.openalex.org/works"
    search_query = clean_title_for_query(title)
    params = {
        "filter": f"title.search:{search_query}",
        "select": "id,display_name,open_access,best_oa_location,locations",
        "per_page": 3
    }
    headers = {
        "User-Agent": "mailto:dr.edwardv@gmail.com"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"  OpenAlex search error: {response.status_code}")
            return None
            
        data = response.json()
        results = data.get("results", [])
        if not math_results_exist(results):
            return None
            
        # Try to find a match where the title is very similar
        cleaned_search_title = clean_text(title).lower()
        
        for work in results:
            work_title = clean_text(work.get("display_name", "")).lower()
            # Simple check: either titles are close in length and overlap, or one contains the other
            # Let's clean punctuation and compare
            w_title_clean = re.sub(r'[^a-z0-9]', '', work_title)
            s_title_clean = re.sub(r'[^a-z0-9]', '', cleaned_search_title)
            
            # Allow slight prefix/suffix match or high similarity
            if w_title_clean in s_title_clean or s_title_clean in w_title_clean or len(set(w_title_clean.split()) & set(s_title_clean.split())) > 0.7:
                # Found a potential match, check PDF locations
                pdf_urls = []
                
                # Check best OA location
                best_oa = work.get("best_oa_location")
                if best_oa and best_oa.get("pdf_url"):
                    pdf_urls.append(best_oa.get("pdf_url"))
                    
                # Check open_access.oa_url
                oa = work.get("open_access")
                if oa and oa.get("oa_url") and oa.get("oa_url").endswith(".pdf"):
                    pdf_urls.append(oa.get("oa_url"))
                    
                # Check all locations
                for loc in work.get("locations", []):
                    if loc and loc.get("pdf_url"):
                        pdf_urls.append(loc.get("pdf_url"))
                        
                # Filter out duplicates and keep order
                unique_urls = []
                for u in pdf_urls:
                    if u not in unique_urls:
                        unique_urls.append(u)
                        
                if unique_urls:
                    return unique_urls[0]
                    
    except Exception as e:
        print(f"  Exception during search: {e}")
        
    return None

def math_results_exist(results):
    return len(results) > 0

def download_pdf(url, output_path):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/"
    }
    try:
        response = requests.get(url, headers=headers, timeout=30, stream=True)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        else:
            print(f"  Download failed: HTTP {response.status_code}")
    except Exception as e:
        print(f"  Download exception: {e}")
    return False

def main():
    os.chdir(r"c:\Users\Edward\Documents\Projects\AI\about me\edwardvitkin")
    os.makedirs("pdfs", exist_ok=True)
    
    # Load existing mapping if it exists
    mapping_file = "pdf_mapping.json"
    mapping = {}
    if os.path.exists(mapping_file):
        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                mapping = json.load(f)
        except Exception:
            mapping = {}
            
    pubs = fetch_publication_titles()
    print(f"Found {len(pubs)} publications to process.")
    
    new_downloads = 0
    for i, pub in enumerate(pubs, 1):
        title = pub["title"]
        year = pub["year"]
        
        print(f"\n[{i}/{len(pubs)}] Processing: {title}")
        
        # Check if already successfully downloaded
        if title in mapping and os.path.exists(mapping[title]):
            print(f"  Already downloaded: {mapping[title]}")
            continue
            
        print("  Searching on OpenAlex...")
        pdf_url = search_openalex_pdf(title)
        if not pdf_url:
            print("  No open-access PDF URL found on OpenAlex.")
            continue
            
        print(f"  Found PDF URL: {pdf_url}")
        
        # Generate filename
        year_str = year if year else "no_year"
        safe_title = slugify(title)
        filename = f"pdfs/{year_str}_{safe_title}.pdf"
        
        print(f"  Downloading to {filename}...")
        success = download_pdf(pdf_url, filename)
        if success:
            if is_valid_pdf(filename):
                print("  Download successful and PDF is valid!")
                mapping[title] = filename
                new_downloads += 1
            else:
                print("  Downloaded file is not a valid PDF (validation failed). Deleting.")
                try:
                    os.remove(filename)
                except Exception:
                    pass
        else:
            print("  Failed to download PDF.")
            
        # Polite delay
        time.sleep(0.3)
        
    # Write updated mapping
    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)
        
    print(f"\nPDF download run complete. Total active PDF links: {len(mapping)} (New downloads: {new_downloads})")

if __name__ == "__main__":
    main()
