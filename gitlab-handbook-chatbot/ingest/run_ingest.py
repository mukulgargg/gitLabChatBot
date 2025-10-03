import logging
import sys
import csv
# python -m ingest.run_ingest
from ingest.crawl import crawl
from ingest.parse import parse_pages
from ingest.chunk import chunk_docs
from ingest.embed import build_index

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

CRAWL_CSV = 'crawl_status.csv'

def get_failed_urls():
    failed = set()
    success = set()
    try:
        with open(CRAWL_CSV, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['status'] == 'success':
                    success.add(row['url'])
                elif row['status'] == 'failed':
                    failed.add(row['url'])
    except FileNotFoundError:
        return []
    # Only retry those that are failed and not already successful
    return list(failed - success)

if __name__ == "__main__":
    retry_failed = '--retry-failed' in sys.argv
    if retry_failed:
        logging.info("Retrying only failed URLs from crawl_status.csv.")
        urls_to_crawl = get_failed_urls()
        if not urls_to_crawl:
            logging.info("No failed URLs to retry. Exiting.")
            sys.exit(0)
        pages = crawl("ingest/domains.yaml", urls_to_crawl=urls_to_crawl)
    else:
        logging.info("Starting ingestion pipeline for all seed URLs.")
        pages = crawl("ingest/domains.yaml")
    logging.info(f"Crawled {len(pages)} pages.")
    docs = parse_pages(pages)
    logging.info(f"Parsed {len(docs)} documents.")
    chunks = chunk_docs(docs, chunk_size=800, overlap=120)  # tuned for Q&A
    logging.info(f"Chunked into {len(chunks)} segments.")
    build_index(chunks, out_dir="data/index")
    logging.info(f"Index built and saved to data/index.")
    logging.info(f"Ingested {len(docs)} docs -> {len(chunks)} chunks.")
    print(f"Ingested {len(docs)} docs -> {len(chunks)} chunks")
