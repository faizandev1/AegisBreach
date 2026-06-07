import sys
import logging
import threading
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette

from engine.packet_crafter import AdvancedPacketCrafter
from utils.logger import logger
from reporting.pdf_generator import ReportGenerator
from database.db_manager import AttackDatabase
from plugins.plugin_manager import PluginManager
from campaigns.campaign_manager import CampaignManager
from mitre.mitre_visualizer import MITREVisualizer
from updater.auto_updater import check_for_updates, open_download_page

class PacketCrafterWorker(QThread):
    log_signal = pyqtSignal(str)
    
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            self.func(*self.args, **self.kwargs)
        except Exception as e:
            self.log_signal.emit(f"Error: {str(e)}")

class AegisMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.crafter = AdvancedPacketCrafter()
        self.report_gen = ReportGenerator()
        self.db = AttackDatabase()
        self.plugin_mgr = PluginManager()
        self.plugin_mgr.load_plugins()
        self.campaign_mgr = CampaignManager()
        self.init_ui()
        self.apply_dark_theme()
        # Check for updates on startup
        self.check_updates()

    def init_ui(self):
        self.setWindowTitle("AegisBreach - Advanced Adversarial Simulation Suite")
        self.setGeometry(100, 100, 1400, 900)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        header = QLabel("AEGIS BREACH")
        header.setAlignment(Qt.AlignCenter)
        header.setFont(QFont("Courier New", 28, QFont.Bold))
        header.setStyleSheet("color: #ff4444; margin: 10px;")
        layout.addWidget(header)
        
        tabs = QTabWidget()
        tabs.setFont(QFont("Helvetica", 11))
        tabs.addTab(self.create_network_tab(), "Network Attacks")
        tabs.addTab(self.create_wifi_tab(), "WiFi Attacks (v2)")
        tabs.addTab(self.create_web_tab(), "Web Attacks (v3)")
        tabs.addTab(self.create_ai_tab(), "AI Evasion")
        tabs.addTab(self.create_campaigns_tab(), "Campaigns")
        tabs.addTab(self.create_mitre_tab(), "MITRE ATT&CK")
        tabs.addTab(self.create_reports_tab(), "Reports")
        tabs.addTab(self.create_plugins_tab(), "Plugins")
        tabs.addTab(self.create_console_tab(), "Live Console")
        layout.addWidget(tabs)

    # ---------------- Network Tab ----------------
    def create_network_tab(self):
        tab = QWidget()
        grid = QGridLayout()
        
        grid.addWidget(QLabel("SYN Flood Target IP:"), 0, 0)
        self.syn_ip = QLineEdit("192.168.1.10")
        grid.addWidget(self.syn_ip, 0, 1)
        grid.addWidget(QLabel("Port:"), 0, 2)
        self.syn_port = QLineEdit("80")
        grid.addWidget(self.syn_port, 0, 3)
        self.syn_btn = QPushButton("Launch SYN Flood")
        self.syn_btn.clicked.connect(self.launch_syn_flood)
        grid.addWidget(self.syn_btn, 0, 4)
        
        grid.addWidget(QLabel("ARP Spoof Target:"), 1, 0)
        self.arp_target = QLineEdit("192.168.1.5")
        grid.addWidget(self.arp_target, 1, 1)
        grid.addWidget(QLabel("Gateway:"), 1, 2)
        self.arp_gw = QLineEdit("192.168.1.1")
        grid.addWidget(self.arp_gw, 1, 3)
        self.arp_btn = QPushButton("Start ARP Spoofing")
        self.arp_btn.clicked.connect(self.launch_arp_spoof)
        grid.addWidget(self.arp_btn, 1, 4)
        
        tab.setLayout(grid)
        return tab

    # ---------------- WiFi Tab ----------------
    def create_wifi_tab(self):
        from gui.wifi_attack_panel import WiFiAttackPanel
        return WiFiAttackPanel()

    # ---------------- Web Attacks Tab ----------------
    def create_web_tab(self):
        from gui.web_attack_panel import WebAttackPanel
        return WebAttackPanel()

    # ---------------- AI Evasion Tab ----------------
    def create_ai_tab(self):
        from gui.ai_evasion_panel import AIEvasionPanel
        return AIEvasionPanel()

    # ---------------- Campaigns Tab ----------------
    def create_campaigns_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        form = QFormLayout()
        self.campaign_name = QLineEdit("MyCampaign")
        form.addRow("Campaign Name:", self.campaign_name)
        layout.addLayout(form)

        self.cb_syn = QCheckBox("SYN Flood (192.168.1.10:80)")
        self.cb_arp = QCheckBox("ARP Spoof (192.168.1.5)")
        layout.addWidget(self.cb_syn)
        layout.addWidget(self.cb_arp)

        btn_layout = QHBoxLayout()
        self.start_campaign_btn = QPushButton("Start Campaign")
        self.start_campaign_btn.clicked.connect(self.launch_campaign)
        self.stop_campaign_btn = QPushButton("Stop Campaign")
        self.stop_campaign_btn.clicked.connect(self.stop_campaign)
        btn_layout.addWidget(self.start_campaign_btn)
        btn_layout.addWidget(self.stop_campaign_btn)
        layout.addLayout(btn_layout)

        self.campaign_log = QTextEdit()
        self.campaign_log.setReadOnly(True)
        layout.addWidget(self.campaign_log)
        tab.setLayout(layout)
        return tab

    # ---------------- MITRE ATT&CK Tab ----------------
    def create_mitre_tab(self):
        return MITREVisualizer()

    # ---------------- Reports Tab ----------------
    def create_reports_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        self.report_content = QTextEdit()
        self.report_content.setPlaceholderText("Enter report content...")
        layout.addWidget(QLabel("Report Content:"))
        layout.addWidget(self.report_content)
        btn = QPushButton("Generate PDF Report")
        btn.clicked.connect(self.generate_report)
        layout.addWidget(btn)
        tab.setLayout(layout)
        return tab

    # ---------------- Plugins Tab ----------------
    def create_plugins_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        self.plugin_list = QListWidget()
        for name in self.plugin_mgr.plugins.keys():
            self.plugin_list.addItem(name)
        layout.addWidget(QLabel("Loaded Plugins:"))
        layout.addWidget(self.plugin_list)
        run_btn = QPushButton("Run Selected Plugin")
        run_btn.clicked.connect(self.run_plugin)
        layout.addWidget(run_btn)
        tab.setLayout(layout)
        return tab

    # ---------------- Console Tab ----------------
    def create_console_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet("background-color: #000000; color: #00ff00; font-family: 'Courier New'; font-size: 11px;")
        layout.addWidget(self.console)
        tab.setLayout(layout)
        self.console_handler = QTextEditHandler(self.console)
        logger.addHandler(self.console_handler)
        return tab

    # ---------------- Attack & Action Methods ----------------
    def launch_syn_flood(self):
        target = self.syn_ip.text()
        port = int(self.syn_port.text())
        self.worker = PacketCrafterWorker(self.crafter.syn_flood, target, port, threads=10, count=1000)
        self.worker.log_signal.connect(self.log_to_console)
        self.worker.start()
        self.db.log_attack("SYN Flood", target, {"port": port, "count": 1000})

    def launch_arp_spoof(self):
        target = self.arp_target.text()
        gw = self.arp_gw.text()
        threading.Thread(target=self.crafter.arp_spoof_loop, args=(target, gw), daemon=True).start()
        self.log_to_console("ARP spoofing started in background")
        self.db.log_attack("ARP Spoof", f"{target} <-> {gw}", {})

    def launch_campaign(self):
        name = self.campaign_name.text()
        attacks = []
        if self.cb_syn.isChecked():
            attacks.append({'module': 'syn', 'target': '192.168.1.10', 'params': {'port': 80}})
        if self.cb_arp.isChecked():
            attacks.append({'module': 'arp_spoof', 'target': '192.168.1.5', 'params': {'gateway': '192.168.1.1'}})
        if not attacks:
            self.campaign_log.append("No attacks selected")
            return
        ok, msg = self.campaign_mgr.start_campaign(name, attacks)
        self.campaign_log.append(msg)

    def stop_campaign(self):
        name = self.campaign_name.text()
        if self.campaign_mgr.stop_campaign(name):
            self.campaign_log.append("Campaign stopped")
        else:
            self.campaign_log.append("Campaign not found or already stopped")

    def generate_report(self):
        content = self.report_content.toPlainText()
        if content.strip():
            self.report_gen.create_report("AegisBreach Attack Report", content, "report.pdf")
            self.log_to_console("Report generated: report.pdf")
        else:
            self.log_to_console("Report content empty")

    def run_plugin(self):
        item = self.plugin_list.currentItem()
        if item:
            name = item.text()
            self.plugin_mgr.run_plugin(name, "127.0.0.1")
            self.log_to_console(f"Plugin {name} executed")

    def log_to_console(self, msg):
        self.console.append(msg)

    def check_updates(self):
        has_update, version = check_for_updates()
        if has_update:
            QMessageBox.information(self, "Update Available", f"New version {version} is available. Download?")

    def apply_dark_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(30, 30, 30))
        palette.setColor(QPalette.WindowText, QColor(200, 200, 200))
        palette.setColor(QPalette.Base, QColor(20, 20, 20))
        palette.setColor(QPalette.AlternateBase, QColor(30, 30, 30))
        palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.Text, QColor(200, 200, 200))
        palette.setColor(QPalette.Button, QColor(40, 40, 40))
        palette.setColor(QPalette.ButtonText, QColor(200, 200, 200))
        palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.Highlight, QColor(255, 68, 68))
        palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
        self.setPalette(palette)

class QTextEditHandler(logging.Handler):
    def __init__(self, widget):
        super().__init__()
        self.widget = widget
        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    def emit(self, record):
        msg = self.format(record)
        self.widget.append(msg)