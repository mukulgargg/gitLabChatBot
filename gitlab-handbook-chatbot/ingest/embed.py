import faiss, json, os, numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

def build_index(chunks, out_dir="data/index"):
    os.makedirs(out_dir, exist_ok=True)
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    texts = [c["text"] for c in chunks]
    embs = model.encode(texts, batch_size=64, show_progress_bar=True, normalize_embeddings=True)
    embs = np.asarray(embs, dtype="float32")
    index = faiss.IndexFlatIP(embs.shape[1])
    index.add(embs)
    faiss.write_index(index, os.path.join(out_dir, "faiss.index"))
    meta = [{"url": c["url"], "text": c["text"][:1000]} for c in chunks]
    json.dump(meta, open(os.path.join(out_dir, "meta.json"), "w"))
