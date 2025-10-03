import re, time, yaml, requests, logging, threading, queue, csv, os
from urllib.parse import urljoin, urldefrag
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

CRAWL_CSV = 'crawl_status.csv'

# Thread-safe CSV writer
class ThreadSafeCSVWriter:
    def __init__(self, filename):
        self.filename = filename
        self.lock = threading.Lock()
        # Create file with header if it doesn't exist
        if not os.path.exists(filename):
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['url', 'status', 'reason'])

    def write(self, url, status, reason=None):
        with self.lock:
            # Read all rows and update or append
            rows = []
            found = False
            if os.path.exists(self.filename):
                with open(self.filename, 'r', newline='') as f:
                    reader = csv.reader(f)
                    header = next(reader, None)
                    for row in reader:
                        if row and row[0] == url:
                            rows.append([url, status, reason or ''])
                            found = True
                        else:
                            rows.append(row)
            if not found:
                rows.append([url, status, reason or ''])
            # Write back all rows
            with open(self.filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['url', 'status', 'reason'])
                writer.writerows(rows)

def crawl(cfg_path, urls_to_crawl=None):
    logging.info(f"Starting crawl with config: {cfg_path}")
    cfg = yaml.safe_load(open(cfg_path))
    seeds, include, exclude = cfg["seeds"], [re.compile(x) for x in cfg["include"]], [re.compile(x) for x in cfg["exclude"]]
    max_pages = cfg.get("max_pages", 20000)
    url_queue = queue.Queue()
    if urls_to_crawl is not None:
        for url in urls_to_crawl:
            url_queue.put(url)
    else:
        for seed in seeds:
            url_queue.put(seed)
    seen = set()
    seen_lock = threading.Lock()
    out = {}
    out_lock = threading.Lock()
    csv_writer = ThreadSafeCSVWriter(CRAWL_CSV)

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
                reason = "URL filtered by include/exclude rules"
                logging.debug(f"URL filtered out: {url}")
                csv_writer.write(url, 'failed', reason)
                url_queue.task_done()
                continue
            try:
                r = requests.get(url, timeout=15)
                if r.status_code != 200:
                    reason = f"HTTP status {r.status_code}"
                    logging.warning(f"Skipped non-HTML or failed request: {url} (status: {r.status_code})")
                    csv_writer.write(url, 'failed', reason)
                    url_queue.task_done()
                    continue
                if "text/html" not in r.headers.get("Content-Type",""):
                    reason = f"Content-Type not HTML: {r.headers.get('Content-Type','')}"
                    logging.warning(f"Skipped non-HTML or failed request: {url} (content-type: {r.headers.get('Content-Type','')})")
                    csv_writer.write(url, 'failed', reason)
                    url_queue.task_done()
                    continue
                with out_lock:
                    if len(out) < max_pages:
                        out[url] = r.text
                        logging.info(f"Crawled: {url} (total: {len(out)})")
                        csv_writer.write(url, 'success', '')
                soup = BeautifulSoup(r.text, "html.parser")
                for a in soup.select("a[href]"):
                    nxt = urljoin(url, a["href"])
                    if nxt.startswith("http"):
                        with seen_lock:
                            if nxt not in seen:
                                url_queue.put(nxt)
                time.sleep(0.2)
            except Exception as e:
                reason = f"Exception: {e}"
                logging.error(f"Error crawling {url}: {e}")
                csv_writer.write(url, 'failed', reason)
            finally:
                url_queue.task_done()

    with ThreadPoolExecutor(max_workers=8) as executor:
        for _ in range(8):
            executor.submit(worker)
        url_queue.join()
    logging.info(f"Crawling finished. Total pages crawled: {len(out)}")
    return out  # {url: html}
