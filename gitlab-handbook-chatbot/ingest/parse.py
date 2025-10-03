import trafilatura, re
def clean_text(html):
    txt = trafilatura.extract(html, include_comments=False, include_tables=True) or ""
    txt = re.sub(r'\n{3,}', '\n\n', txt).strip()
    return txt

def parse_pages(pages):
    docs = []
    for url, html in pages.items():
        text = clean_text(html)
        if len(text) < 300: continue
        docs.append({"url": url, "text": text})
    return docs
