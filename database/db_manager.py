import sqlite3
import datetime
from utils.logger import logger

class AttackDatabase:
    def __init__(self, db_path="data/attacks.db"):
        import os
        os.makedirs("data", exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS attack_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                attack_type TEXT,
                target TEXT,
                parameters TEXT,
                status TEXT
            )
        """)
        self.conn.commit()

    def log_attack(self, attack_type, target, parameters, status="success"):
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute(
            "INSERT INTO attack_log (timestamp, attack_type, target, parameters, status) VALUES (?,?,?,?,?)",
            (ts, attack_type, target, str(parameters), status)
        )
        self.conn.commit()
        logger.info(f"Logged {attack_type} on {target}")

    def get_all_logs(self):
        self.cursor.execute("SELECT * FROM attack_log ORDER BY timestamp DESC")
        return self.cursor.fetchall()