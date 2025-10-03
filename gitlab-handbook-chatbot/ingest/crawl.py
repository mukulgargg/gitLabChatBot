import re, time, yaml, requests
from urllib.parse import urljoin, urldefrag
from bs4 import BeautifulSoup

def crawl(cfg_path):
    cfg = yaml.safe_load(open(cfg_path))
    seeds, include, exclude = cfg["seeds"], [re.compile(x) for x in cfg["include"]], [re.compile(x) for x in cfg["exclude"]]
    max_pages = cfg.get("max_pages", 300)
    q, seen, out = list(seeds), set(), {}
    while q and len(out) < max_pages:
        url = urldefrag(q.pop(0))[0]
        if url in seen: continue
        seen.add(url)
        if not any(r.search(url) for r in include) or any(r.search(url) for r in exclude):
            continue
        try:
            r = requests.get(url, timeout=15)
            if r.status_code != 200 or "text/html" not in r.headers.get("Content-Type",""): continue
            out[url] = r.text
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.select("a[href]"):
                nxt = urljoin(url, a["href"])
                if nxt.startswith("http"): q.append(nxt)
            time.sleep(0.5)  # be nice
        except Exception:
            pass
    return out  # {url: html}
