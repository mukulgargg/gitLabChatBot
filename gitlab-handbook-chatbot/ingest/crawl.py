import re, time, yaml, requests, logging, threading, queue
from urllib.parse import urljoin, urldefrag
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def crawl(cfg_path):
    logging.info(f"Starting crawl with config: {cfg_path}")
    cfg = yaml.safe_load(open(cfg_path))
    seeds, include, exclude = cfg["seeds"], [re.compile(x) for x in cfg["include"]], [re.compile(x) for x in cfg["exclude"]]
    max_pages = cfg.get("max_pages", 20000)
    url_queue = queue.Queue()
    for seed in seeds:
        url_queue.put(seed)
    seen = set()
    seen_lock = threading.Lock()
    out = {}
    out_lock = threading.Lock()

    def worker():
        while True:
            try:
                url = url_queue.get(timeout=1)
            except queue.Empty:
                return
            url = urldefrag(url)[0]
            with seen_lock:
                if url in seen or len(out) >= max_pages:
                    url_queue.task_done()
                    continue
                seen.add(url)
            if not any(r.search(url) for r in include) or any(r.search(url) for r in exclude):
                logging.debug(f"URL filtered out: {url}")
                url_queue.task_done()
                continue
            try:
                r = requests.get(url, timeout=15)
                if r.status_code != 200 or "text/html" not in r.headers.get("Content-Type",""):
                    logging.warning(f"Skipped non-HTML or failed request: {url} (status: {r.status_code})")
                    url_queue.task_done()
                    continue
                with out_lock:
                    if len(out) < max_pages:
                        out[url] = r.text
                        logging.info(f"Crawled: {url} (total: {len(out)})")
                soup = BeautifulSoup(r.text, "html.parser")
                for a in soup.select("a[href]"):
                    nxt = urljoin(url, a["href"])
                    if nxt.startswith("http"):
                        with seen_lock:
                            if nxt not in seen:
                                url_queue.put(nxt)
                time.sleep(0.2)
            except Exception as e:
                logging.error(f"Error crawling {url}: {e}")
            finally:
                url_queue.task_done()

    with ThreadPoolExecutor(max_workers=8) as executor:
        for _ in range(8):
            executor.submit(worker)
        url_queue.join()
    logging.info(f"Crawling finished. Total pages crawled: {len(out)}")
    return out  # {url: html}
