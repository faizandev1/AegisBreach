from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from engine.wifi_scanner import AdvancedWiFiScanner
from engine.wifi_attacks import WiFiAttacker
import threading

class ScanWorker(QThread):
    result_signal = pyqtSignal(list)
    log_signal = pyqtSignal(str)

    def __init__(self, scanner):
        super().__init__()
        self.scanner = scanner

    def run(self):
        nets = self.scanner.scan()
        self.result_signal.emit(nets)

class AttackWorker(QThread):
    log_signal = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        self.func(*self.args, **self.kwargs)
        self.finished.emit()

class WiFiAttackPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scanner = AdvancedWiFiScanner()
        self.attacker = WiFiAttacker()
        self.networks = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Scan button
        btn_layout = QHBoxLayout()
        self.scan_btn = QPushButton("🔍 Scan Networks")
        self.scan_btn.clicked.connect(self.start_scan)
        btn_layout.addWidget(self.scan_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Network list
        self.net_list = QTableWidget()
        self.net_list.setColumnCount(5)
        self.net_list.setHorizontalHeaderLabels(['SSID', 'BSSID', 'Signal (dBm)', 'Channel', 'Security'])
        self.net_list.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.net_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.net_list.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.net_list)

        # Attack controls
        attack_group = QGroupBox("Attack Configuration")
        attack_layout = QGridLayout()

        attack_layout.addWidget(QLabel("Target BSSID:"), 0, 0)
        self.bssid_entry = QLineEdit()
        attack_layout.addWidget(self.bssid_entry, 0, 1)

        self.deauth_btn = QPushButton("💥 Deauth Attack")
        self.deauth_btn.clicked.connect(self.launch_deauth)
        attack_layout.addWidget(self.deauth_btn, 0, 2)

        self.beacon_btn = QPushButton("📡 Beacon Flood")
        self.beacon_btn.clicked.connect(self.launch_beacon_flood)
        attack_layout.addWidget(self.beacon_btn, 1, 0)

        self.pmkid_btn = QPushButton("🔑 Capture PMKID")
        self.pmkid_btn.clicked.connect(self.launch_pmkid_capture)
        attack_layout.addWidget(self.pmkid_btn, 1, 1)

        self.stop_btn = QPushButton("⏹ Stop All")
        self.stop_btn.clicked.connect(self.stop_attacks)
        attack_layout.addWidget(self.stop_btn, 1, 2)

        attack_group.setLayout(attack_layout)
        layout.addWidget(attack_group)

        # Log area
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(100)
        layout.addWidget(self.log_area)

        self.setLayout(layout)

        # Connect list selection to fill BSSID
        self.net_list.itemSelectionChanged.connect(self.on_network_select)

    def start_scan(self):
        self.log_area.append("Scanning...")
        self.scan_btn.setEnabled(False)
        self.worker = ScanWorker(self.scanner)
        self.worker.result_signal.connect(self.update_network_list)
        self.worker.log_signal.connect(self.log_area.append)
        self.worker.finished.connect(lambda: self.scan_btn.setEnabled(True))
        self.worker.start()

    def update_network_list(self, networks):
        self.networks = networks
        self.net_list.setRowCount(len(networks))
        for i, net in enumerate(networks):
            self.net_list.setItem(i, 0, QTableWidgetItem(net['ssid']))
            self.net_list.setItem(i, 1, QTableWidgetItem(net['bssid']))
            self.net_list.setItem(i, 2, QTableWidgetItem(str(net['rssi'])))
            self.net_list.setItem(i, 3, QTableWidgetItem(str(net['channel'])))
            self.net_list.setItem(i, 4, QTableWidgetItem(net['security']))

    def on_network_select(self):
        row = self.net_list.currentRow()
        if row >= 0:
            bssid = self.networks[row]['bssid']
            self.bssid_entry.setText(bssid)

    def launch_deauth(self):
        bssid = self.bssid_entry.text()
        if bssid:
            self.log_area.append(f"Starting deauth on {bssid}")
            self.deauth_btn.setEnabled(False)
            self.worker = AttackWorker(self.attacker.deauth_attack, bssid, count=500)
            self.worker.log_signal.connect(self.log_area.append)
            self.worker.finished.connect(lambda: self.deauth_btn.setEnabled(True))
            self.worker.start()

    def launch_beacon_flood(self):
        self.log_area.append("Starting beacon flood...")
        self.beacon_btn.setEnabled(False)
        self.worker = AttackWorker(self.attacker.beacon_flood, count=2000)
        self.worker.finished.connect(lambda: self.beacon_btn.setEnabled(True))
        self.worker.start()

    def launch_pmkid_capture(self):
        bssid = self.bssid_entry.text()
        if bssid:
            self.log_area.append(f"Capturing PMKID from {bssid}")
            self.pmkid_btn.setEnabled(False)
            def capture():
                pmkid = self.attacker.capture_pmkid(bssid, timeout=30)
                self.log_area.append(f"PMKID: {pmkid}")
            threading.Thread(target=capture, daemon=True).start()
            self.pmkid_btn.setEnabled(True)

    def stop_attacks(self):
        self.attacker.stop_all()
        self.log_area.append("All attacks stopped")
        self.deauth_btn.setEnabled(True)
        self.beacon_btn.setEnabled(True)
        self.pmkid_btn.setEnabled(True)