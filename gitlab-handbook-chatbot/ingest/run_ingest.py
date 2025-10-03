# python -m ingest.run_ingest
from ingest.crawl import crawl
from ingest.parse import parse_pages
from ingest.chunk import chunk_docs
from ingest.embed import build_index

if __name__ == "__main__":
    pages = crawl("ingest/domains.yaml")
    docs = parse_pages(pages)
    chunks = chunk_docs(docs, chunk_size=800, overlap=120)  # tuned for Q&A
    build_index(chunks, out_dir="data/index")
    print(f"✅ Ingested {len(docs)} docs -> {len(chunks)} chunks")
