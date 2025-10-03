import google.generativeai as genai
import json
import os

from dotenv import load_dotenv
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

from prompts import SYSTEM, ANSWER_TEMPLATE

load_dotenv()


class RAG:
    def __init__(self, index_dir="data/index", k=5):
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        self.meta = {m["url"]: m for m in json.load(open(f"{index_dir}/meta.json"))}
        # Pinecone setup
        pinecone_api_key = os.getenv("PINECONE_API_KEY")
        index_name = os.getenv("PINECONE_INDEX", "handbook-index")
        if not pinecone_api_key:
            raise ValueError("PINECONE_API_KEY must be set in environment variables.")
        self.pc = Pinecone(api_key=pinecone_api_key)
        self.index = self.pc.Index(index_name)
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.llm = genai.GenerativeModel("gemini-2.5-pro")
        self.k = k

    def retrieve(self, q):
        qv = self.model.encode([q], normalize_embeddings=True)[0].tolist()
        # Query Pinecone for top-k most similar vectors
        res = self.index.query(vector=qv, top_k=self.k, include_metadata=True)
        ctx = []
        for match in res.get('matches', []):
            url = match['id']
            meta = self.meta.get(url)
            if meta:
                ctx.append(f"[{meta['url']}]\n{meta['text']}")
            else:
                # fallback if meta not found
                ctx.append(f"[{url}]\n(No metadata found)")
        return ctx

    def answer(self, question):
        ctx = self.retrieve(question)
        src_list = [c.split("\n", 1)[0].strip("[]") for c in ctx]
        prompt = SYSTEM + "\n\n" + ANSWER_TEMPLATE.format(
            question=question,
            sources="\n\n".join(ctx)
        )
        resp = self.llm.generate_content(prompt)
        text = resp.text
        # Append URL footnotes if missing
        foot = "\n\n" + "\n".join([f"[^{i + 1}]: {u}" for i, u in enumerate(src_list[:4])])
        return text + foot, src_list[:4]
