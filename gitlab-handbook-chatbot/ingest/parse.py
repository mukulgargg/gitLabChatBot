import trafilatura, re
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def clean_text(html):
    txt = trafilatura.extract(html, include_comments=False, include_tables=True) or ""
    txt = re.sub(r'\n{3,}', '\n\n', txt).strip()
    return txt

def parse_pages(pages, max_workers=6):
    docs = []
    total = len(pages)
    logging.info(f"Starting to parse {total} pages using {max_workers} processes.")
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(clean_text, html): url for url, html in pages.items()}
        for idx, future in enumerate(as_completed(future_to_url), 1):
            url = future_to_url[future]
            try:
                text = future.result()
                if len(text) < 300:
                    logging.debug(f"Skipped short page: {url} (length: {len(text)})")
                    continue
                docs.append({"url": url, "text": text})
                logging.info(f"Parsed page {idx}/{total}: {url} (length: {len(text)})")
            except Exception as e:
                logging.error(f"Error parsing {url}: {e}")
    logging.info(f"Parsing finished. Total documents parsed: {len(docs)} out of {total} pages.")
    return docs
