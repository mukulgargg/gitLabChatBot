import logging
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

if __name__ == "__main__":
    logging.info("Starting ingestion pipeline.")
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
