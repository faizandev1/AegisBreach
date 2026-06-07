import subprocess
import re
import threading
from scapy.all import *
from utils.logger import logger
from config.settings import config

class AdvancedWiFiScanner:
    def __init__(self):
        self.interface = config.get('network.interface', 'en0')
        self.networks = []
        self.scanning = False

    def scan_airport(self):
        """Use macOS airport utility for reliable scanning"""
        try:
            result = subprocess.run(
                ['/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport', '-s'],
                capture_output=True, text=True, timeout=15
            )
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            networks = []
            for line in lines:
                # Split by whitespace, but SSID may contain spaces -> tricky
                # Better: use regex to extract columns
                match = re.match(r'^\s*(.+?)\s+([0-9a-fA-F:]{17})\s+([-+]?\d+)\s+(\d+).*?\s+(OPEN|WEP|WPA[2]?.*)$', line)
                if match:
                    ssid = match.group(1).strip()
                    bssid = match.group(2)
                    rssi_str = match.group(3).replace('+', '')
                    rssi = int(rssi_str)
                    channel = match.group(4)
                    security = match.group(5).strip()
                    networks.append({
                        'ssid': ssid,
                        'bssid': bssid,
                        'rssi': rssi,
                        'channel': channel,
                        'security': security
                    })
                else:
                    # Fallback simple splitting
                    parts = line.strip().split()
                    if len(parts) >= 3:
                        ssid = parts[0]
                        bssid = parts[1]
                        rssi_str = parts[2].replace('+', '')
                        try:
                            rssi = int(rssi_str)
                        except ValueError:
                            continue
                        channel = parts[3] if len(parts) > 3 else '?'
                        security = 'WPA2' if 'WPA2' in line else 'WPA' if 'WPA' in line else 'WEP' if 'WEP' in line else 'OPEN'
                        networks.append({
                            'ssid': ssid,
                            'bssid': bssid,
                            'rssi': rssi,
                            'channel': channel,
                            'security': security
                        })
            return networks
        except Exception as e:
            logger.error(f"Airport scan failed: {e}")
            return []

    def scan_scapy(self):
        """Scapy-based scanning – requires root"""
        networks = []
        def packet_handler(pkt):
            if pkt.haslayer(Dot11Beacon):
                try:
                    ssid = pkt[Dot11Elt].info.decode('utf-8', errors='ignore')
                except:
                    ssid = 'Hidden'
                bssid = pkt[Dot11].addr3
                try:
                    rssi = pkt.dBm_AntSignal
                except:
                    rssi = -100
                # Extract channel from DSset (third Dot11Elt usually)
                channel = '?'
                elt = pkt.getlayer(Dot11Elt, 3)
                if elt and elt.ID == 3:  # DSset
                    channel = ord(elt.info) if isinstance(elt.info, bytes) else elt.info
                security = 'OPEN'
                if pkt.haslayer(Dot11EltRSN):
                    security = 'WPA2'
                elif pkt.haslayer(Dot11EltWPA):
                    security = 'WPA'
                networks.append({
                    'ssid': ssid,
                    'bssid': bssid,
                    'rssi': rssi,
                    'channel': str(channel),
                    'security': security
                })
        try:
            sniff(iface=self.interface, prn=packet_handler, timeout=5, store=0)
        except Exception as e:
            logger.error(f"Scapy sniff failed (need root?): {e}")
        return networks

    def scan(self):
        """Perform a scan and return deduplicated list"""
        self.scanning = True
        logger.info("Starting WiFi scan...")
        nets = self.scan_airport()
        if not nets:
            logger.info("Airport scan empty, trying Scapy (needs sudo)...")
            nets = self.scan_scapy()
        seen = set()
        unique = []
        for n in nets:
            if n['bssid'] not in seen:
                seen.add(n['bssid'])
                unique.append(n)
        self.networks = sorted(unique, key=lambda x: x['rssi'], reverse=True)
        self.scanning = False
        logger.info(f"Scan complete: {len(self.networks)} networks found")
        return self.networks