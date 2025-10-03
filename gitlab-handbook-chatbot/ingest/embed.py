import os, json, numpy as np, logging
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def build_index(chunks, out_dir="data/index"):
    logging.info(f"Building Pinecone index for {len(chunks)} chunks.")
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX", "handbook-index")
    pinecone_cloud = os.getenv("PINECONE_CLOUD", "aws")
    pinecone_region = os.getenv("PINECONE_REGION", "us-west-2")
    if not pinecone_api_key:
        raise ValueError("PINECONE_API_KEY must be set in environment variables.")
    pc = Pinecone(api_key=pinecone_api_key)
    # Create or connect to index
    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=384,  # 384 for all-MiniLM-L6-v2
            metric='cosine',
            spec=ServerlessSpec(
                cloud=pinecone_cloud,
                region=pinecone_region
            )
        )
        logging.info(f"Created Pinecone index '{index_name}' in {pinecone_cloud}:{pinecone_region}")
    index = pc.Index(index_name)
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    texts = [c["text"] for c in chunks]
    urls = [c["url"] for c in chunks]
    logging.info("Encoding texts into embeddings...")
    embs = model.encode(texts, batch_size=64, show_progress_bar=True, normalize_embeddings=True)
    embs = np.asarray(embs, dtype="float32")
    logging.info(f"Embeddings shape: {embs.shape}")
    # Use URL as the vector ID for deduplication
    vectors = [(url, emb.tolist(), {"text": text, "url": url}) for url, text, emb in zip(urls, texts, embs)]
    # Remove duplicates: fetch existing IDs from Pinecone and only upsert new ones
    existing_ids = set()
    fetch_batch = 100  # Reduce batch size to avoid 414 error
    for i in range(0, len(urls), fetch_batch):
        batch_ids = urls[i:i+fetch_batch]
        try:
            res = index.fetch(ids=batch_ids)
            existing_ids.update(res.get('vectors', {}).keys())
        except Exception as e:
            logging.warning(f"Error fetching batch {i//fetch_batch+1}: {e}")
    new_vectors = [v for v in vectors if v[0] not in existing_ids]
    if not new_vectors:
        logging.info("No new vectors to upsert; all URLs are already in Pinecone.")
    else:
        batch_size = 100
        for i in range(0, len(new_vectors), batch_size):
            batch = new_vectors[i:i+batch_size]
            index.upsert(vectors=batch)
            logging.info(f"Upserted batch {i//batch_size+1} ({len(batch)} vectors)")
    # Save metadata for reference
    os.makedirs(out_dir, exist_ok=True)
    meta = [{"url": c["url"], "text": c["text"][:1000]} for c in chunks]
    json.dump(meta, open(os.path.join(out_dir, "meta.json"), "w"))
    logging.info(f"Metadata written to {os.path.join(out_dir, 'meta.json')}")
    logging.info(f"Index build complete: {len(chunks)} chunks indexed in Pinecone.")
