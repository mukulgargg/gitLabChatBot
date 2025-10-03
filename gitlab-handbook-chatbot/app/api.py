import os, json, faiss, numpy as np, google.generativeai as genai
from sentence_transformers import SentenceTransformer
from .prompts import SYSTEM, ANSWER_TEMPLATE

class RAG:
    def __init__(self, index_dir="data/index", k=5):
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        self.index = faiss.read_index(f"{index_dir}/faiss.index")
        self.meta = json.load(open(f"{index_dir}/meta.json"))
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.llm = genai.GenerativeModel("gemini-1.5-flash")

        self.k = k

    def retrieve(self, q):
        qv = self.model.encode([q], normalize_embeddings=True).astype("float32")
        D, I = self.index.search(qv, self.k)
        ctx = []
        for idx in I[0]:
            m = self.meta[int(idx)]
            ctx.append(f"[{m['url']}]\n{m['text']}")
        return ctx

    def answer(self, question):
        ctx = self.retrieve(question)
        src_list = [c.split("\n",1)[0].strip("[]") for c in ctx]
        prompt = SYSTEM + "\n\n" + ANSWER_TEMPLATE.format(
            question=question,
            sources="\n\n".join(ctx)
        )
        resp = self.llm.generate_content(prompt)
        text = resp.text
        # Append URL footnotes if missing
        foot = "\n\n" + "\n".join([f"[^{i+1}]: {u}" for i,u in enumerate(src_list[:4])])
        return text + foot, src_list[:4]
