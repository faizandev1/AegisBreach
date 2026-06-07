import time
import random
import threading
import numpy as np
from utils.logger import logger

class RateLimitEnv:
    """Simulated environment: server blocks if rate > threshold, otherwise 200 OK."""
    def __init__(self, threshold=50):
        self.threshold = threshold
        self.rate = 10
        self.delay = 0.1
        self.ua_rotate = False

    def step(self, rate, delay, ua_rotate):
        # Simulate sending requests
        if rate > self.threshold:
            # blocked
            reward = -1
            blocked = True
        else:
            reward = 1
            blocked = False
        return reward, blocked

class QLearningAgent:
    """Simple Q‑learning agent with discrete state/action."""
    def __init__(self, actions, alpha=0.1, gamma=0.9, epsilon=0.1):
        self.actions = actions
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.q_table = {}  # state -> action values

    def get_state_key(self, state):
        # state = (rate_bucket, delay_bucket, ua_bool)
        return f"{state[0]}_{state[1]}_{state[2]}"

    def choose_action(self, state):
        key = self.get_state_key(state)
        if key not in self.q_table:
            self.q_table[key] = np.zeros(len(self.actions))
        if np.random.random() < self.epsilon:
            return np.random.randint(len(self.actions))
        else:
            return np.argmax(self.q_table[key])

    def update(self, state, action, reward, next_state):
        key = self.get_state_key(state)
        next_key = self.get_state_key(next_state)
        if next_key not in self.q_table:
            self.q_table[next_key] = np.zeros(len(self.actions))
        current_q = self.q_table[key][action]
        max_next_q = np.max(self.q_table[next_key])
        self.q_table[key][action] = current_q + self.alpha * (reward + self.gamma * max_next_q - current_q)

class AIEvasionController:
    """Orchestrates the learning loop."""
    def __init__(self, target_url, update_callback=None):
        self.target = target_url
        self.env = RateLimitEnv(threshold=30)  # example threshold
        self.actions = [
            "increase_rate", "decrease_rate",
            "increase_delay", "decrease_delay",
            "toggle_ua"
        ]
        self.agent = QLearningAgent(self.actions)
        self.running = False
        self.update_callback = update_callback

        # Discrete buckets for state
        self.rate_buckets = [10, 20, 30, 40, 50]
        self.delay_buckets = [0.05, 0.1, 0.2, 0.5]

    def discretize(self, rate, delay, ua):
        rate_idx = min(range(len(self.rate_buckets)), key=lambda i: abs(self.rate_buckets[i]-rate))
        delay_idx = min(range(len(self.delay_buckets)), key=lambda i: abs(self.delay_buckets[i]-delay))
        return (rate_idx, delay_idx, int(ua))

    def run(self, episodes=100, steps_per_episode=20):
        self.running = True
        rate = 20
        delay = 0.1
        ua = False
        total_rewards = []
        for ep in range(episodes):
            if not self.running:
                break
            episode_reward = 0
            for step in range(steps_per_episode):
                state = self.discretize(rate, delay, ua)
                action_idx = self.agent.choose_action(state)
                # Apply action
                if self.actions[action_idx] == "increase_rate":
                    rate = min(50, rate + 10)
                elif self.actions[action_idx] == "decrease_rate":
                    rate = max(10, rate - 10)
                elif self.actions[action_idx] == "increase_delay":
                    delay = min(0.5, delay * 2)
                elif self.actions[action_idx] == "decrease_delay":
                    delay = max(0.05, delay / 2)
                elif self.actions[action_idx] == "toggle_ua":
                    ua = not ua

                reward, blocked = self.env.step(rate, delay, ua)
                next_state = self.discretize(rate, delay, ua)
                self.agent.update(state, action_idx, reward, next_state)
                episode_reward += reward

                if self.update_callback:
                    self.update_callback(rate, delay, ua, reward, ep, step, blocked)

                time.sleep(0.01)  # simulate real time

            total_rewards.append(episode_reward)
            logger.info(f"Episode {ep+1}/{episodes} reward: {episode_reward}")

        self.running = False
        if self.update_callback:
            self.update_callback(rate, delay, ua, 0, episodes, 0, False)  # final update
        return total_rewards

    def stop(self):
        self.running = False