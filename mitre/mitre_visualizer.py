import json
import os
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt

class MITREVisualizer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.mapping = {}
        self.load_mapping()
        self.init_ui()

    def load_mapping(self):
        path = os.path.join(os.path.dirname(__file__), "mitre_mapping.json")
        if os.path.exists(path):
            with open(path, 'r') as f:
                self.mapping = json.load(f)

    def init_ui(self):
        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Attack Technique", "MITRE ATT&CK ID"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.populate_table()
        layout.addWidget(self.table)

        # Simple label showing total techniques mapped
        self.info_label = QLabel(f"Total mapped techniques: {len(self.mapping)}")
        layout.addWidget(self.info_label)

        self.setLayout(layout)

    def populate_table(self):
        self.table.setRowCount(len(self.mapping))
        for row, (attack, technique_id) in enumerate(self.mapping.items()):
            self.table.setItem(row, 0, QTableWidgetItem(attack))
            self.table.setItem(row, 1, QTableWidgetItem(technique_id))
            # Color rows based on severity (optional)
            if row % 2 == 0:
                self.table.item(row, 0).setBackground(QColor(40, 40, 40))
                self.table.item(row, 1).setBackground(QColor(40, 40, 40))