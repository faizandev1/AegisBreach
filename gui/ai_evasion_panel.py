from PyQt5.QtWidgets import *
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from engine.ai_evasion import AIEvasionController

class EvasionWorker(QThread):
    # Signals: (rate, delay, ua, reward, ep, step, blocked)
    update_signal = pyqtSignal(int, float, bool, float, int, int, bool)
    episode_done = pyqtSignal(int, float)   # episode, total_reward
    finished = pyqtSignal()

    def __init__(self, target, episodes=50):
        super().__init__()
        self.target = target
        self.episodes = episodes
        self.controller = None
        self.current_ep = 0
        self.episode_reward = 0

    def run(self):
        def callback(rate, delay, ua, reward, ep, step, blocked):
            self.update_signal.emit(rate, delay, ua, reward, ep, step, blocked)
            # Track episode total
            if ep != self.current_ep:
                if self.current_ep > 0:
                    self.episode_done.emit(self.current_ep, self.episode_reward)
                self.current_ep = ep
                self.episode_reward = reward
            else:
                self.episode_reward += reward

        self.controller = AIEvasionController(self.target, update_callback=callback)
        self.controller.run(episodes=self.episodes)
        # Emit last episode
        if self.current_ep > 0:
            self.episode_done.emit(self.current_ep, self.episode_reward)
        self.finished.emit()

    def stop(self):
        if self.controller:
            self.controller.stop()

class AIEvasionPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.episode_rewards = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Target and episodes
        form = QFormLayout()
        self.target_url = QLineEdit("https://example.com")
        form.addRow("Target URL:", self.target_url)
        self.episodes_spin = QSpinBox()
        self.episodes_spin.setRange(10, 500)
        self.episodes_spin.setValue(50)
        form.addRow("Episodes:", self.episodes_spin)

        btn_row = QHBoxLayout()
        self.start_btn = QPushButton("Start AI Evasion Learning")
        self.start_btn.clicked.connect(self.start_evasion)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_evasion)
        self.stop_btn.setEnabled(False)
        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.stop_btn)
        form.addRow(btn_row)
        layout.addLayout(form)

        # Live parameters
        self.param_label = QLabel("Current: Rate=20, Delay=0.1, UA=False")
        self.param_label.setStyleSheet("font-weight: bold; color: #00aaff;")
        layout.addWidget(self.param_label)

        # Progress bar for episodes
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Episode reward table (list widget)
        self.reward_list = QListWidget()
        self.reward_list.setMaximumHeight(200)
        layout.addWidget(QLabel("Episode Rewards:"))
        layout.addWidget(self.reward_list)

        # Log area
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        layout.addWidget(self.log_area)

        self.setLayout(layout)

    def start_evasion(self):
        target = self.target_url.text()
        episodes = self.episodes_spin.value()
        self.log_area.append(f"Starting AI evasion on {target} for {episodes} episodes")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.episode_rewards = []
        self.reward_list.clear()
        self.progress_bar.setMaximum(episodes)
        self.progress_bar.setValue(0)

        self.worker = EvasionWorker(target, episodes)
        self.worker.update_signal.connect(self.update_params)
        self.worker.episode_done.connect(self.on_episode_done)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def stop_evasion(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.log_area.append("AI evasion stopped")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def update_params(self, rate, delay, ua, reward, ep, step, blocked):
        self.param_label.setText(
            f"Rate={rate}, Delay={delay:.2f}, UA={ua}, "
            f"Reward={reward:.1f}, Ep={ep}, Step={step}, "
            f"{'BLOCKED' if blocked else 'OK'}"
        )

    def on_episode_done(self, ep, total_reward):
        self.episode_rewards.append(total_reward)
        self.progress_bar.setValue(ep)
        self.reward_list.addItem(f"Episode {ep}: Total Reward = {total_reward:.1f}")
        self.reward_list.scrollToBottom()
        self.log_area.append(f"Episode {ep} finished with total reward: {total_reward:.1f}")

    def on_finished(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setValue(self.progress_bar.maximum())
        self.log_area.append("AI evasion learning completed!")