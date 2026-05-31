import os
import requests
from bs4 import BeautifulSoup
import re
import sys
import json

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def fetch_publications():
    url = "https://scholar.google.com/citations?hl=en&user=kE-Ral4AAAAJ&view_op=list_works&cstart=0&pagesize=100"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    print("Fetching publications from Google Scholar...")
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch Google Scholar page: {response.status_code}")
        
    soup = BeautifulSoup(response.text, 'html.parser')
    
    if "captcha" in response.text.lower() or "not a robot" in response.text.lower():
        raise Exception("Blocked by Google Scholar CAPTCHA. Please try again later or use proxies.")
        
    pub_rows = soup.select('tr.gsc_a_tr')
    print(f"Found {len(pub_rows)} publication rows on Google Scholar.")
    
    publications = []
    for row in pub_rows:
        title_link = row.select_one('td.gsc_a_t a')
        if not title_link:
            continue
        title = clean_text(title_link.text)
        
        # Get citations for secondary sort
        citations_elem = row.select_one('td.gsc_a_c a')
        citations_str = clean_text(citations_elem.text) if citations_elem else "0"
        try:
            citations = int(citations_str) if citations_str else 0
        except ValueError:
            citations = 0
            
        # Get year
        year_elem = row.select_one('td.gsc_a_y span')
        year_str = clean_text(year_elem.text) if year_elem else ""
        
        publications.append({
            "title": title,
            "citations": citations,
            "year": year_str
        })
        
    # Sort: 1. Year descending, 2. Citations descending, 3. Title ascending
    def get_sort_key(pub):
        try:
            y = int(pub["year"]) if pub["year"] else 0
        except ValueError:
            y = 0
        return (-y, -pub["citations"], pub["title"])
        
    publications.sort(key=get_sort_key)
    return publications

def generate_html(publications, pdf_mapping):
    lines = []
    lines.append('            <ol class="pub-list" style="margin-bottom: 1rem; padding-left: 0; list-style: none;">')
    
    for i, pub in enumerate(publications, 1):
        year = pub["year"] if pub["year"] else "—"
        title = pub["title"]
        title_escaped = title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # Check if we have a PDF mapping
        pdf_path = None
        cleaned_title = clean_text(title).lower()
        for pub_title, path in pdf_mapping.items():
            w_title_clean = re.sub(r'[^a-z0-9]', '', pub_title.lower())
            s_title_clean = re.sub(r'[^a-z0-9]', '', cleaned_title)
            if w_title_clean == s_title_clean or w_title_clean in s_title_clean or s_title_clean in w_title_clean:
                pdf_path = path
                break
                
        pdf_link_html = ""
        if pdf_path:
            pdf_link_html = f'\n                    <a href="{pdf_path}" class="pub-pdf-link" target="_blank" title="View PDF"><i class="fa-solid fa-file-pdf"></i><span>PDF</span></a>'
            
        item_html = (
            f'                <li class="pub-item">\n'
            f'                    <span class="pub-year-badge">{year}</span>\n'
            f'                    <div class="pub-info">\n'
            f'                        <span class="pub-title"><span class="pub-index-num">{i}.</span> {title_escaped}</span>\n'
            f'                    </div>{pdf_link_html}\n'
            f'                </li>'
        )
        lines.append(item_html)
        
    lines.append('            </ol>')
    return '\n'.join(lines)

def update_selected_publications(html_block, pdf_mapping):
    soup = BeautifulSoup(html_block, 'html.parser')
    pub_items = soup.select('.pub-item')
    updated_count = 0
    for item in pub_items:
        # Clean out any old pdf link
        existing = item.select_one('.pub-pdf-link')
        if existing:
            existing.decompose()
            
        title_elem = item.select_one('.pub-title')
        if not title_elem:
            continue
        title = clean_text(title_elem.text)
        
        pdf_path = None
        cleaned_title = clean_text(title).lower()
        for pub_title, path in pdf_mapping.items():
            w_title_clean = re.sub(r'[^a-z0-9]', '', pub_title.lower())
            s_title_clean = re.sub(r'[^a-z0-9]', '', cleaned_title)
            if w_title_clean == s_title_clean or w_title_clean in s_title_clean or s_title_clean in w_title_clean:
                pdf_path = path
                break
                
        if pdf_path:
            link_html = f'<a href="{pdf_path}" class="pub-pdf-link" target="_blank" title="View PDF"><i class="fa-solid fa-file-pdf"></i><span>PDF</span></a>'
            link_soup = BeautifulSoup(link_html, 'html.parser')
            item.append(link_soup.a)
            updated_count += 1
            
    print(f"Added {updated_count} PDF links to Selected Publications.")
    ul_elem = soup.select_one('.pub-list')
    if ul_elem:
        return str(ul_elem)
    return str(soup)

def update_index_html(html_list_content, pdf_mapping):
    html_path = r"c:\Users\Edward\Documents\Projects\AI\about me\edwardvitkin\index.html"
    
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Replace All Publications
    pattern_all = r'<!-- START_GOOGLE_SCHOLAR_PUBLICATIONS -->.*?<!-- END_GOOGLE_SCHOLAR_PUBLICATIONS -->'
    replacement_all = f'<!-- START_GOOGLE_SCHOLAR_PUBLICATIONS -->\n{html_list_content}\n            <!-- END_GOOGLE_SCHOLAR_PUBLICATIONS -->'
    
    content, count = re.subn(pattern_all, replacement_all, content, flags=re.DOTALL)
    if count == 0:
        raise Exception("Could not find All Publications markers in index.html")
        
    # Replace Selected Publications if markers exist
    pattern_sel = r'<!-- START_SELECTED_PUBLICATIONS -->(.*?)<!-- END_SELECTED_PUBLICATIONS -->'
    match_sel = re.search(pattern_sel, content, flags=re.DOTALL)
    if match_sel:
        original_block = match_sel.group(1)
        updated_block = update_selected_publications(original_block, pdf_mapping)
        # Beautify padding for replacement
        replacement_sel = f'<!-- START_SELECTED_PUBLICATIONS -->\n            {updated_block.strip()}\n            <!-- END_SELECTED_PUBLICATIONS -->'
        content = content.replace(match_sel.group(0), replacement_sel)
        print("Selected Publications updated!")
    else:
        print("Selected Publications markers not found in index.html, skipping update of that section.")
        
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print("index.html updated successfully!")

if __name__ == "__main__":
    os.chdir(r"c:\Users\Edward\Documents\Projects\AI\about me\edwardvitkin")
    
    # Load pdf mapping
    mapping_file = "pdf_mapping.json"
    pdf_mapping = {}
    if os.path.exists(mapping_file):
        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                pdf_mapping = json.load(f)
        except Exception as e:
            print(f"Error loading PDF mapping: {e}")
            
    try:
        pubs = fetch_publications()
        if not pubs:
            print("No publications found.")
            sys.exit(1)
        html = generate_html(pubs, pdf_mapping)
        update_index_html(html, pdf_mapping)
        print("Done!")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
