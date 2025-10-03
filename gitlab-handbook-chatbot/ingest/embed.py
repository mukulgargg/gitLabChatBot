import faiss, json, os, numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def build_index(chunks, out_dir="data/index"):
    logging.info(f"Building index for {len(chunks)} chunks.")
    os.makedirs(out_dir, exist_ok=True)
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    texts = [c["text"] for c in chunks]
    logging.info("Encoding texts into embeddings...")
    embs = model.encode(texts, batch_size=64, show_progress_bar=True, normalize_embeddings=True)
    embs = np.asarray(embs, dtype="float32")
    logging.info(f"Embeddings shape: {embs.shape}")
    index = faiss.IndexFlatIP(embs.shape[1])
    index.add(embs)
    faiss.write_index(index, os.path.join(out_dir, "faiss.index"))
    logging.info(f"FAISS index written to {os.path.join(out_dir, 'faiss.index')}")
    meta = [{"url": c["url"], "text": c["text"][:1000]} for c in chunks]
    json.dump(meta, open(os.path.join(out_dir, "meta.json"), "w"))
    logging.info(f"Metadata written to {os.path.join(out_dir, 'meta.json')}")
    logging.info(f"Index build complete: {len(chunks)} chunks indexed.")
