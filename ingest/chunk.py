def chunk_docs(docs, chunk_size=800, overlap=120):
    out = []
    for d in docs:
        t, u = d["text"], d["url"]
        i = 0
        while i < len(t):
            out.append({"url": u, "text": t[i:i+chunk_size]})
            i += (chunk_size - overlap)
    return out
