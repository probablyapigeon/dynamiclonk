# ============================================================
# DYNAMIC LONK CIVILIZATION SIMULATOR
# Pure Python - No external dependencies
# Features: Neural learning, emotional dynamics, composable actions,
#           factions, religion, trading, gossip, memory, lifecycle
# ============================================================

import random
import math
import time
import os
import json
import sys
from collections import deque
import numpy as np

# ============================================================
# CONFIGURATION
# ============================================================

# Learning parameters
LEARNING_RATE = 0.01
GAMMA = 0.99  # Discount factor
BATCH_SIZE = 32
MEMORY_CAPACITY = 500
HIDDEN_SIZE = 16
INPUT_SIZE = 32
OUTPUT_SIZE = 6  # Must match len(Lonk.ACTIONS)

# World parameters
MAX_HEALTH = 100
FIGHT_DAMAGE = 5
MAX_VERBS = 20  # Cap verb inventory per agent
MAX_GOSSIP = 20
STARTING_POPULATION = 5

# Toggles
TOGGLES = {
    "violence": True,
    "shinywars": True,
    "dreams": True,
    "religion": True,
    "trading": True,
    "gossip": True
}

# ============================================================
# XEMBRA EMOTIONS (50+ rich emotional states)
# ============================================================

XEMBRA_EMOTIONS = {
    # Core emotions
    "peaceful": {"valence": 0.8, "arousal": 0.2, "dominance": 0.5},
    "zen": {"valence": 0.7, "arousal": 0.1, "dominance": 0.4},
    "happy": {"valence": 0.9, "arousal": 0.6, "dominance": 0.5},
    "joyful": {"valence": 1.0, "arousal": 0.7, "dominance": 0.4},
    "excited": {"valence": 0.8, "arousal": 0.9, "dominance": 0.6},
    "sad": {"valence": 0.2, "arousal": 0.3, "dominance": 0.3},
    "angry": {"valence": 0.3, "arousal": 0.9, "dominance": 0.8},
    "afraid": {"valence": 0.1, "arousal": 0.8, "dominance": 0.2},
    "calm": {"valence": 0.7, "arousal": 0.2, "dominance": 0.5},
    "anxious": {"valence": 0.3, "arousal": 0.7, "dominance": 0.3},

    # Xembra-specific emotions (alien, cosmic, dreamlike)
    "xenic": {"valence": 0.6, "arousal": 0.5, "dominance": 0.4},
    "xenowarm": {"valence": 0.8, "arousal": 0.4, "dominance": 0.3},
    "xenofear": {"valence": 0.2, "arousal": 0.8, "dominance": 0.2},
    "xenoshy": {"valence": 0.4, "arousal": 0.6, "dominance": 0.2},
    "xenophilous": {"valence": 0.7, "arousal": 0.5, "dominance": 0.4},
    "xenoanger": {"valence": 0.3, "arousal": 0.8, "dominance": 0.7},
    "xenojoy": {"valence": 0.9, "arousal": 0.6, "dominance": 0.4},
    "xenolove": {"valence": 0.95, "arousal": 0.5, "dominance": 0.3},
    "xenolethargic": {"valence": 0.4, "arousal": 0.1, "dominance": 0.2},

    # Dream states
    "floating": {"valence": 0.7, "arousal": 0.3, "dominance": 0.3},
    "opaline": {"valence": 0.6, "arousal": 0.4, "dominance": 0.4},
    "iridescent calm": {"valence": 0.8, "arousal": 0.2, "dominance": 0.4},
    "soft stillness": {"valence": 0.7, "arousal": 0.1, "dominance": 0.3},
    "holy-soft awe": {"valence": 0.8, "arousal": 0.4, "dominance": 0.3},
    "nectar-soft": {"valence": 0.9, "arousal": 0.3, "dominance": 0.2},
    "honey-warm": {"valence": 0.85, "arousal": 0.3, "dominance": 0.3},
    "numinous": {"valence": 0.8, "arousal": 0.5, "dominance": 0.4},
    "astral": {"valence": 0.6, "arousal": 0.4, "dominance": 0.5},
    "curling inward": {"valence": 0.3, "arousal": 0.5, "dominance": 0.2},
    "pulling back": {"valence": 0.4, "arousal": 0.6, "dominance": 0.3},
    "in a zen state": {"valence": 0.75, "arousal": 0.2, "dominance": 0.4},
    "slow sweetness": {"valence": 0.85, "arousal": 0.3, "dominance": 0.3},

    # Combat emotions
    "combat energy": {"valence": 0.5, "arousal": 0.9, "dominance": 0.8},
    "with combat energy": {"valence": 0.5, "arousal": 0.9, "dominance": 0.8},
    "violent": {"valence": 0.2, "arousal": 0.9, "dominance": 0.9},
    "furious": {"valence": 0.1, "arousal": 1.0, "dominance": 0.9},
    "enraged": {"valence": 0.0, "arousal": 1.0, "dominance": 1.0},
}

# ============================================================
# FACTIONS
# ============================================================

FACTIONS = [
    {"name": "Mushroom Union", "description": "Peaceful foragers who believe in the mycelial network",
     "bonus": {"wisdom": +10, "loyalty": +5}},
    {"name": "Bonk Battalion", "description": "Warrior Lonks who solve problems with violence",
     "bonus": {"aggression": +15, "courage": +10}},
    {"name": "Shiny Collectors", "description": "Obsessed with collecting shiny objects",
     "bonus": {"curiosity": +15, "joy": +5}},
    {"name": "Dreamweavers", "description": "Mystical Lonks who commune with the void",
     "bonus": {"wisdom": +10, "anxiety": -5}},
    {"name": "Chaos Choir", "description": "Anarchic Lonks who love noise and disorder",
     "bonus": {"playfulness": +15, "anxiety": +5}},
]

# ============================================================
# RELIGIONS
# ============================================================

RELIGIONS = {
    "Mushroom Union": {
        "name": "Mycelial Network",
        "description": "Worship of the cosmic mycelium that connects all things",
        "ritual": "consumes sacred objects to join the cosmic mycelium",
        "ritual_description": "consumes sacred objects to join the cosmic mycelium",
        "sacred_items": ["Glowing Cap", "Sacred Spore", "Moss Blanket"],
        "deity": "The Great Mycelium"
    },
    "Bonk Battalion": {
        "name": "Order of the Sacred Bonk",
        "description": "Belief that bonking is a sacred act of devotion",
        "ritual": "bonks sacred objects (and each other) to prove devotion",
        "ritual_description": "bonks sacred objects (and each other) to prove devotion",
        "sacred_items": ["Bonk Hammer", "Sacred Anvil", "Warrior's Shield"],
        "deity": "The Eternal Bonk"
    },
    "Shiny Collectors": {
        "name": "Church of the Shiny",
        "description": "Worship of shiny objects as divine gifts",
        "ritual": "polishes shiny objects to honor their divine nature",
        "ritual_description": "polishes shiny objects to honor their divine nature",
        "sacred_items": ["Golden Acorn", "Crystal Shard", "Pocket Void"],
        "deity": "The Shining One"
    },
    "Dreamweavers": {
        "name": "Cult of the Void",
        "description": "Communion with the cosmic void and dream realms",
        "ritual": "enters trance to commune with the void",
        "ritual_description": "enters trance to commune with the void",
        "sacred_items": ["Void Pearl", "Dream Stone", "Haunted Leaf"],
        "deity": "The Dreaming Void"
    },
    "Chaos Choir": {
        "name": "Church of the Eternal Scream",
        "description": "Worship through noise, chaos, and screaming at bushes",
        "ritual": "screams at the sacred bush to summon chaos",
        "ritual_description": "screams at the sacred bush to summon chaos",
        "sacred_items": ["Screaming Stone", "Chaos Bell", "Noisy Rock"],
        "deity": "The Screaming Chaos"
    },
}

# ============================================================
# TERRITORIES
# ============================================================

TERRITORIES = [
    {"name": "The Moss Blanket", "description": "soft, damp, emotionally supportive",
     "faction_bonus": {"Mushroom Union": 10, "Dreamweavers": 5}},
    {"name": "The Shiny Pit", "description": "glimmers ominously, hums in F#",
     "faction_bonus": {"Shiny Collectors": 15, "Chaos Choir": 5}},
    {"name": "The Big Rock", "description": "immovable, judgmental, slightly warm",
     "faction_bonus": {"Bonk Battalion": 10}},
    {"name": "The Loud Bush", "description": "rustles aggressively for no reason",
     "faction_bonus": {"Chaos Choir": 15, "Bonk Battalion": 5}},
    {"name": "The Unreasonable Clearing", "description": "geometry makes no sense here",
     "faction_bonus": {"Dreamweavers": 10}},
    {"name": "The Screaming Meadow", "description": "the grass yells compliments",
     "faction_bonus": {"Chaos Choir": 10, "Mushroom Union": -5}},
]

# ============================================================
# ITEMS
# ============================================================

ITEMS = [
    {"name": "Glowing Cap", "description": "a bioluminescent mushroom cap", "shiny": True, "value": 10},
    {"name": "Sacred Spore", "description": "a spore that whispers secrets", "shiny": True, "value": 8},
    {"name": "Bonk Hammer", "description": "for maximum bonking", "shiny": False, "value": 5},
    {"name": "Sacred Anvil", "description": "where sacred bonks are forged", "shiny": False, "value": 7},
    {"name": "Golden Acorn", "description": "a truly shiny acorn", "shiny": True, "value": 15},
    {"name": "Crystal Shard", "description": "refracts dreams", "shiny": True, "value": 12},
    {"name": "Pocket Void", "description": "contains a small universe", "shiny": True, "value": 20},
    {"name": "Void Pearl", "description": "black but somehow shiny", "shiny": True, "value": 18},
    {"name": "Dream Stone", "description": "glows when you sleep", "shiny": True, "value": 14},
    {"name": "Haunted Leaf", "description": "whispers in the wind", "shiny": False, "value": 3},
    {"name": "Moss Blanket", "description": "soft and alive", "shiny": False, "value": 2},
    {"name": "Warrior's Shield", "description": "for blocking bonks", "shiny": False, "value": 6},
    {"name": "Screaming Stone", "description": "yells when thrown", "shiny": False, "value": 4},
    {"name": "Chaos Bell", "description": "rings with discord", "shiny": True, "value": 9},
    {"name": "Noisy Rock", "description": "makes noise when bonked", "shiny": False, "value": 3},
    {"name": "Forbidden Berry", "description": "glows faintly", "shiny": True, "value": 11},
]

# Item values for trading
ITEM_VALUES = {item["name"]: item["value"] for item in ITEMS}

# ============================================================
# DEFAULT IDENTITY
# ============================================================

DEFAULT_IDENTITY = {
    "name": "Lonk",
    "emotion": {
        "power": 50, "courage": 50, "wisdom": 50,
        "masochism": 0, "joy": 50, "anxiety": 50
    },
    "personality": {
        "aggression": 50, "curiosity": 50, "anxiety": 50,
        "loyalty": 50, "playfulness": 50
    }
}

# ============================================================
# NAME GENERATOR
# ============================================================

def generate_name():
    prefixes = ["Sn", "Gl", "Br", "Wr", "Fl", "Bl", "Gr", "Kr", "Pl", "Dr", "Tr", "Sh", "Wh", "Ch"]
    suffixes = ["ip", "op", "ub", "ink", "onk", "ip", "ob", "iff", "oof", "arp", "orp", "ump", "onk"]
    return random.choice(prefixes) + random.choice(suffixes)

# ============================================================
# STABILIZER SYSTEM
# ============================================================

class Stabilizer:
    def __init__(self):
        self.bad_patterns = [
            ("bonk", 0.3), ("poop", 0.2), ("fuck", 0.1), ("shit", 0.1),
            ("cunt", 0.05), ("bitch", 0.15), ("dick", 0.1)
        ]

    def stabilize(self, text):
        for pattern, prob in self.bad_patterns:
            if pattern in text.lower() and random.random() < prob:
                return text.replace(pattern, "shiny")
        return text

STABILIZER = Stabilizer()

# ============================================================
# XEMBRA VITALS (NTK-based cognitive core)
# ============================================================

class XembraVitals:
    def __init__(self):
        self.trace = 0.5
        self.entropy = 0.5
        self.coherence = 0.5
        self.drift = 0.1
        self.dream_intensity = 0.1
        self.last_state = None
        self.ema_alpha = 0.1

    def update(self, state_vec):
        if self.last_state is None:
            self.last_state = state_vec
            return

        # Calculate change from last state
        delta = np.array(state_vec) - np.array(self.last_state)
        self.drift = self.ema_alpha * np.linalg.norm(delta) + (1 - self.ema_alpha) * self.drift

        # Calculate entropy of state distribution
        state_array = np.array(state_vec)
        probs = np.abs(state_array) + 1e-10
        probs = probs / np.sum(probs)
        self.entropy = -np.sum(probs * np.log(probs + 1e-10))

        # Calculate coherence (eigenvalue spread of state covariance)
        if len(state_vec) >= 2:
            cov = np.cov(np.array([state_vec, self.last_state]))
            eigvals = np.linalg.eigvalsh(cov)
            if len(eigvals) > 0:
                self.coherence = 1.0 - (np.max(eigvals) - np.min(eigvals)) / (np.sum(eigvals) + 1e-10)
            self.coherence = np.clip(self.coherence, 0, 1)

        # Update trace (EMA of state magnitude)
        self.trace = self.ema_alpha * np.mean(np.abs(state_array)) + (1 - self.ema_alpha) * self.trace

        # Dream intensity based on entropy and drift
        self.dream_intensity = np.clip(self.entropy * self.drift * 10, 0, 1)

        self.last_state = state_vec

    def get_vitals(self):
        return {
            "trace": self.trace,
            "entropy": self.entropy,
            "coherence": self.coherence,
            "drift": self.drift,
            "dream_intensity": self.dream_intensity
        }

# ============================================================
# TINY NEURAL NETWORK (FIXED: output_size=6, proper serialization)
# ============================================================

class TinyNN:
    def __init__(self, input_size=INPUT_SIZE, hidden_size=HIDDEN_SIZE, output_size=OUTPUT_SIZE):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.W1 = np.random.randn(input_size, hidden_size) * 0.1
        self.b1 = np.zeros(hidden_size)
        self.W2 = np.random.randn(hidden_size, output_size) * 0.1
        self.b2 = np.zeros(output_size)
        self.last_hidden = None
        self.last_output = None

    def forward(self, x):
        if isinstance(x, list):
            x = np.array(x)
        hidden = np.maximum(0, np.dot(x, self.W1) + self.b1)
        output = np.dot(hidden, self.W2) + self.b2
        self.last_hidden = hidden
        self.last_output = output
        return hidden, output

    def backward(self, x, action, reward):
        if isinstance(x, list):
            x = np.array(x)
        # FIX: Re-run forward to get correct activations for this state
        hidden, output = self.forward(x)

        # Softmax output
        exp_output = np.exp(output - np.max(output))
        probs = exp_output / np.sum(exp_output)

        # Policy gradient
        d_logits = np.zeros(self.output_size)
        d_logits[action] = probs[action] - 1.0  # REINFORCE update

        # Backpropagate
        d_hidden = np.dot(d_logits, self.W2.T)
        d_hidden[hidden <= 0] = 0  # ReLU derivative

        # Update weights
        self.W2 -= LEARNING_RATE * np.outer(hidden, d_logits)
        self.b2 -= LEARNING_RATE * d_logits
        self.W1 -= LEARNING_RATE * np.outer(x, d_hidden)
        self.b1 -= LEARNING_RATE * d_hidden

    def to_dict(self):
        # FIX: Proper serialization of weights
        return {
            "input_size": self.input_size,
            "hidden_size": self.hidden_size,
            "output_size": self.output_size,
            "W1": self.W1.tolist(),
            "b1": self.b1.tolist(),
            "W2": self.W2.tolist(),
            "b2": self.b2.tolist()
        }

    @classmethod
    def from_dict(cls, data):
        nn = cls(
            input_size=data["input_size"],
            hidden_size=data["hidden_size"],
            output_size=data["output_size"]
        )
        nn.W1 = np.array(data["W1"])
        nn.b1 = np.array(data["b1"])
        nn.W2 = np.array(data["W2"])
        nn.b2 = np.array(data["b2"])
        return nn

    def choose_action(self, state):
        _, output = self.forward(state)
        probs = np.exp(output - np.max(output))
        probs = probs / np.sum(probs)
        return np.random.choice(self.output_size, p=probs)

# ============================================================
# EXPERIENCE BUFFER (FIXED: JSON serializable)
# ============================================================

class ExperienceBuffer:
    def __init__(self, capacity=MEMORY_CAPACITY):
        self.capacity = capacity
        self.buffer = deque(maxlen=capacity)

    def add(self, state, action, reward, next_state):
        self.buffer.append((state, action, reward, next_state))

    def sample(self, batch_size):
        if len(self.buffer) < batch_size:
            return random.sample(self.buffer, len(self.buffer))
        return random.sample(self.buffer, batch_size)

    def __len__(self):
        return len(self.buffer)

    def to_dict(self):
        # FIX: Convert numpy arrays to lists for JSON serialization
        return {
            "capacity": self.capacity,
            "buffer": [
                [
                    s.tolist() if hasattr(s, 'tolist') else s,
                    a,
                    r,
                    s2.tolist() if hasattr(s2, 'tolist') else s2
                ]
                for s, a, r, s2 in self.buffer
            ]
        }

    @classmethod
    def from_dict(cls, data):
        buffer = [
            (np.array(s), a, r, np.array(s2))
            for s, a, r, s2 in data["buffer"]
        ]
        return cls(capacity=data.get("capacity", MEMORY_CAPACITY), buffer=buffer)

    def clear(self):
        self.buffer.clear()

# ============================================================
# REWARD SYSTEM
# ============================================================

class RewardSystem:
    def __init__(self):
        self.last_health = MAX_HEALTH
        self.last_emotion = {}
        self.last_vitals = {}

    def calculate_reward(self, lonk):
        reward = 0.0

        # Health reward
        health_diff = lonk.health - self.last_health
        reward += health_diff * 0.1
        self.last_health = lonk.health

        # Emotion reward (higher joy/courage = positive)
        for key in ["joy", "courage", "power", "wisdom"]:
            val = lonk.emotion.get(key, 50)
            prev = self.last_emotion.get(key, 50)
            reward += (val - prev) * 0.01
            self.last_emotion[key] = val

        # Vitals reward
        vitals = lonk.brain.vitals.get_vitals()
        for key in ["trace", "coherence"]:
            val = vitals.get(key, 0.5)
            prev = self.last_vitals.get(key, 0.5)
            reward += (val - prev) * 0.05
            self.last_vitals[key] = val

        # Penalty for high anxiety
        anxiety = lonk.emotion.get("anxiety", 50)
        reward -= (anxiety - 50) * 0.01

        # Small living reward
        reward += 0.01

        # Clamp reward
        return np.clip(reward, -1.0, 1.0)

# ============================================================
# LONK DYNAMICS (Psi, theta, A, V, P model)
# ============================================================

class LonkDynamics:
    def __init__(self):
        self.Psi = 0.5  # Core energy
        self.theta = 0.5  # Expectation
        self.A = 0.2  # Arousal
        self.V = 0.3  # Valence
        self.P = 0.1  # Prediction error
        self.alpha = 0.1  # Learning rate

    def step(self, state, s_t, pain_t):
        Psi, theta, A, V, P = state

        # Update based on stimuli
        dPsi = self.alpha * (s_t - Psi)
        dtheta = self.alpha * (s_t - theta)
        dA = self.alpha * (pain_t * 10 - A)
        dV = self.alpha * (s_t - V)
        dP = self.alpha * (abs(s_t - theta) - P)

        # Clamp to [0, 1]
        Psi = np.clip(Psi + dPsi, 0, 1)
        theta = np.clip(theta + dtheta, 0, 1)
        A = np.clip(A + dA, 0, 1)
        V = np.clip(V + dV, 0, 1)
        P = np.clip(P + dP, 0, 1)

        return [Psi, theta, A, V, P]

    def get_state(self):
        return [self.Psi, self.theta, self.A, self.V, self.P]

# ============================================================
# LONK BRAIN (Neural learning + emotional state)
# ============================================================

class LonkBrain:
    def __init__(self, name):
        self.name = name
        self.nn = TinyNN(input_size=INPUT_SIZE, hidden_size=HIDDEN_SIZE, output_size=OUTPUT_SIZE)
        self.buffer = ExperienceBuffer(capacity=MEMORY_CAPACITY)
        self.reward_system = RewardSystem()
        self.vitals = XembraVitals()
        self.state_vec = None
        self.last_state = None
        self.last_action = None
        self.last_reward = 0.0

    def choose_action(self, lonk):
        state = self.get_state_vector(lonk)
        return self.nn.choose_action(state)

    def get_state_vector(self, lonk):
        """Build 32-dimensional state vector for neural network"""
        state = np.zeros(INPUT_SIZE)

        # Emotional state (5 dim: Psi, theta, A, V, P)
        Psi, theta, A, V, P = lonk.state
        state[:5] = [Psi, theta, A, V, P]

        # Personality (5 dim: aggression, curiosity, anxiety, loyalty, playfulness)
        for i, key in enumerate(["aggression", "curiosity", "anxiety", "loyalty", "playfulness"]):
            state[5 + i] = lonk.personality.get(key, 50) / 100.0

        # Health and age (2 dim)
        state[10] = lonk.health / MAX_HEALTH
        state[11] = min(lonk.age / 100.0, 1.0)  # Normalized age

        # Faction and territory (2 dim: one-hot encoded)
        if lonk.faction:
            faction_idx = [f["name"] for f in FACTIONS].index(lonk.faction) if lonk.faction in [f["name"] for f in FACTIONS] else 0
            state[12] = faction_idx / len(FACTIONS)
        if lonk.territory:
            territory_idx = [t["name"] for t in TERRITORIES].index(lonk.territory) if lonk.territory in [t["name"] for t in TERRITORIES] else 0
            state[13] = territory_idx / len(TERRITORIES)

        # Items (2 dim: count, shiny count)
        state[14] = min(len(lonk.items) / 10.0, 1.0)
        # FIX: Use item.get("shiny", False) instead of getattr
        shiny_items = sum(1 for item in lonk.items if item.get("shiny", False))
        state[15] = min(shiny_items / 10.0, 1.0)

        # Social (3 dim: friend count, enemy count, relationship strength)
        friends = sum(1 for v in lonk.relationships.values() if v > lonk.friend_threshold)
        enemies = sum(1 for v in lonk.relationships.values() if v < lonk.grudge_threshold)
        state[16] = min(friends / 10.0, 1.0)
        state[17] = min(enemies / 10.0, 1.0)
        state[18] = min(abs(sum(lonk.relationships.values())) / 1000.0, 1.0)

        # Gossip (1 dim: gossip count)
        state[19] = min(len(lonk.gossip) / MAX_GOSSIP, 1.0)

        # Religion (2 dim: has religion, faith level)
        state[20] = 1.0 if lonk.religion else 0.0
        state[21] = lonk.faith / 100.0

        # Finance (2 dim: coins, inventory value)
        state[22] = min(lonk.coins / 100.0, 1.0)
        state[23] = min(lonk.inventory_value / 100.0, 1.0)

        # Vitals (5 dim: trace, entropy, coherence, drift, dream_intensity)
        vitals = self.vitals.get_vitals()
        state[24] = vitals.get("trace", 0.5)
        state[25] = vitals.get("entropy", 0.5)
        state[26] = vitals.get("coherence", 0.5)
        state[27] = vitals.get("drift", 0.1)
        state[28] = vitals.get("dream_intensity", 0.1)

        # Random exploration (2 dim: small noise)
        # FIX: Reduced noise to prevent learning degradation
        state[29:31] = np.random.randn(2) * 0.001

        # Normalize state
        state = np.clip(state, -1, 1)

        self.state_vec = state
        return state

    def get_emotional_state(self):
        """Get current Xembra emotional state based on brain state"""
        if not hasattr(self, 'state_vec') or self.state_vec is None:
            return "peaceful"

        # Map state dimensions to emotions
        Psi, theta, A, V, P = self.state_vec[:5]
        arousal = A
        valence = V

        # Find closest emotion in XEMBRA_EMOTIONS
        best_emotion = "peaceful"
        best_dist = float('inf')

        for emotion, props in XEMBRA_EMOTIONS.items():
            dist = abs(props["arousal"] - arousal) + abs(props["valence"] - valence)
            if dist < best_dist:
                best_dist = dist
                best_emotion = emotion

        return best_emotion

    def get_need(self, lonk):
        """Determine current need based on emotional state"""
        emotional_state = self.get_emotional_state()
        health_ratio = lonk.health / MAX_HEALTH

        # FIX: Removed dead emotion branches (xenoanger, xenohate, etc.)
        if emotional_state in ["xenofear", "afraid"]:
            return "comfort"
        if emotional_state in ["xenolethargic", "sad"]:
            return "reassurance"
        if emotional_state in ["xenojoy", "joyful", "happy"]:
            return "company"
        if emotional_state in ["xenophilous", "curious"]:
            return "knowledge"
        if health_ratio < 0.3:
            return "healing"
        if health_ratio < 0.6:
            return "stability"
        if not lonk.items:
            return "items"
        if not lonk.territory:
            return "territory"
        if len(lonk.relationships) < 2:
            return "company"
        if random.random() < 0.1:
            return random.choice(["comfort", "stability", "knowledge", "company"])
        return "idle"

    def record(self, state, action, reward, next_state):
        self.buffer.add(state, action, reward, next_state)
        self.learn()

    def learn(self):
        if len(self.buffer) < BATCH_SIZE:
            return

        batch = self.buffer.sample(BATCH_SIZE)
        for state, action, reward, next_state in batch:
            # FIX: Re-run forward to get correct activations for this state
            self.nn.forward(state)
            self.nn.backward(state, action, reward)

    def update_vitals(self, state_vec):
        self.vitals.update(state_vec)

    def to_dict(self):
        return {
            "nn": self.nn.to_dict(),
            "buffer": self.buffer.to_dict(),
            "vitals": {
                "trace": self.vitals.trace,
                "entropy": self.vitals.entropy,
                "coherence": self.vitals.coherence,
                "drift": self.vitals.drift,
                "dream_intensity": self.vitals.dream_intensity
            }
        }

    @classmethod
    def from_dict(cls, data, name):
        brain = cls(name)
        if "nn" in data:
            brain.nn = TinyNN.from_dict(data["nn"])
        if "buffer" in data:
            brain.buffer = ExperienceBuffer.from_dict(data["buffer"])
        if "vitals" in data:
            vitals_data = data["vitals"]
            brain.vitals.trace = vitals_data.get("trace", 0.5)
            brain.vitals.entropy = vitals_data.get("entropy", 0.5)
            brain.vitals.coherence = vitals_data.get("coherence", 0.5)
            brain.vitals.drift = vitals_data.get("drift", 0.1)
            brain.vitals.dream_intensity = vitals_data.get("dream_intensity", 0.1)
        return brain

# ============================================================
# LONK CLASS (Main agent)
# ============================================================

class Lonk:
    ACTIONS = ["idle", "explore", "think", "attack", "speak", "trade"]

    # Action primitives for composable system
    VERBS = {
        "bonk": {"category": "violent", "base_reward": -0.1},
        "give": {"category": "social", "base_reward": 0.2},
        "whisper": {"category": "social", "base_reward": 0.1},
        "lick": {"category": "social", "base_reward": 0.15},
        "polish": {"category": "ritual", "base_reward": 0.1},
        "trade": {"category": "economic", "base_reward": 0.2},
        "scream": {"category": "violent", "base_reward": -0.05},
        "consume": {"category": "ritual", "base_reward": 0.1},
        "preach": {"category": "social", "base_reward": 0.15},
        "teach": {"category": "social", "base_reward": 0.2},
        "attack": {"category": "violent", "base_reward": -0.1},
        "praise": {"category": "social", "base_reward": 0.2},
        "insult": {"category": "violent", "base_reward": -0.15},
        "dream": {"category": "rest", "base_reward": 0.1},
    }

    MODIFIERS = {
        "with fury": -0.1,
        "secretly": 0.05,
        "loudly": -0.05,
        "gently": 0.1,
        "with love": 0.2,
        "with hate": -0.2,
        "quickly": 0.05,
        "slowly": -0.05,
        "with joy": 0.15,
    }

    def __init__(self, name=None, world=None, _loading=False):
        # Basic attributes
        self.name = name if name else generate_name()
        self.world = world
        self.alive = True
        self.age = 0
        self.generation = 1
        self.health = MAX_HEALTH
        self.lifespan = random.randint(30, 80)
        self.trauma = 0
        self.faction = None
        self.territory = None
        self.rival = None
        self.target = None
        self.pending_retaliation = None  # FIX: Queue retaliation

        # Initialize brain and learning
        self.brain = LonkBrain(self.name)
        self.state_vec = None

        # Emotional dynamical state (Psi, theta, A, V, P)
        self.dynamics = LonkDynamics()
        self.state = [0.5, 0.5, 0.2, 0.3, 0.1]  # Psi, theta, A, V, P

        # Emotion dictionary
        self.emotion = {
            "power": 50, "courage": 50, "wisdom": 50,
            "masochism": 0, "joy": 50, "anxiety": 50
        }

        # Personality traits
        self.personality = {
            "aggression": random.randint(30, 70),
            "curiosity": random.randint(30, 70),
            "anxiety": random.randint(30, 70),
            "loyalty": random.randint(30, 70),
            "playfulness": random.randint(30, 70)
        }

        # Habits
        self.habits = {a: 0 for a in self.ACTIONS}

        # Memory systems
        self.memory = {
            "player_words": set(),
            "lonk_words": set(),
            "events": [],
            "player_interactions": [],
        }
        self.long_memory = []
        self.vocabulary = {}
        self.language = {}

        # Social
        self.relationships = {}
        self.grudges = {}
        self.friend_threshold = 20
        self.grudge_threshold = -15
        self.social_memory_decay = 0.98
        self.crush = None
        self.catchphrase = None

        # Gossip
        self.gossip = []
        self.max_gossip = MAX_GOSSIP

        # Items & inventory (using only self.items)
        self.items = []
        self.inventory = []  # Legacy, kept for compatibility

        # Learning state
        self.knowledge = set()
        self.teachings = []

        # Composable action system
        self.known_verbs = dict(self.VERBS)  # Start with all default verbs
        self.action_weights = {}
        self.action_history = []
        self.named_combos = set()  # FIX: Track named combos to prevent spam
        self._init_default_verbs()

        # Religion
        self.religion = None
        self.faith = random.randint(30, 100)
        self.heretic = False

        # Finance
        self.coins = 0
        self.inventory_value = 0

        # FIX: Skip initialization prints when loading from dict
        if not _loading:
            self.ensure_emotion_keys()
            self.ensure_personality_keys()
            self.join_random_faction()
            self.wander()
            self.init_social()

    def _init_default_verbs(self):
        """Initialize default verb weights"""
        for verb in self.known_verbs:
            for target_type in ["self", "other", "item"]:
                for modifier in list(self.MODIFIERS.keys()) + [None]:
                    key = f"{verb}+{target_type}+{modifier or ''}"
                    self.action_weights[key] = 1.0

    # ============================================================
    # CORE METHODS
    # ============================================================

    def ensure_emotion_keys(self):
        defaults = {
            "power": 50, "courage": 50, "wisdom": 50,
            "masochism": 0, "joy": 50, "anxiety": 50
        }
        for k, v in defaults.items():
            self.emotion.setdefault(k, v)

    def ensure_personality_keys(self):
        defaults = {
            "aggression": 50, "curiosity": 50, "anxiety": 50,
            "loyalty": 50, "playfulness": 50
        }
        for k, v in defaults.items():
            self.personality.setdefault(k, v)

    def join_random_faction(self):
        if FACTIONS:
            faction = random.choice(FACTIONS)
            self.faction = faction["name"]
            print(f"🏳️ {self.name} joins the faction: {self.faction}!")

    def wander(self):
        if TERRITORIES:
            territory = random.choice(TERRITORIES)
            self.territory = territory["name"]
            print(f"🌍 {self.name} wanders into {self.territory} — {territory['description']}")
            # FIX: Check self.faction in territory faction_bonus, not self.territory
            if self.faction and self.faction in territory.get("faction_bonus", {}):
                bonus = territory["faction_bonus"][self.faction]
                print(f"✨ {self.name} feels empowered by {self.faction}'s sacred ground!")
                self.emotion["joy"] += 10
                self.emotion["power"] += 5

    def init_social(self):
        self.memory.setdefault("player_interactions", [])
        self.memory.setdefault("player_words", set())
        self.catchphrase = None
        self.crush = None
        self.grudges = {}

    # ============================================================
    # ACTION SYSTEM (FIXED)
    # ============================================================

    def choose_action(self):
        """Choose an action - MORE COMBAT!"""
        action_idx = self.brain.choose_action(self)
        action_map = {0: "idle", 1: "explore", 2: "think", 3: "attack", 4: "speak", 5: "trade"}
        action = action_map.get(action_idx, "idle")

        need = self.brain.get_need(self)

        # AGGRESSIVE OVERRIDES
        if need == "items":
            if random.random() < 0.4:  # Lower trade, more combat
                action = "trade"
            elif random.random() < 0.4:
                action = "explore"
            else:
                action = "attack"  # Sometimes attack for items!
        elif need in ["comfort", "stability", "reassurance"]:
            if random.random() < 0.7:  # 70% chance to attack when uncomfortable
                action = "attack"
            else:
                action = "speak"
        elif need == "knowledge":
            if random.random() < 0.3:
                action = "attack"  # Attack to learn through violence
        elif need == "territory":
            if random.random() < 0.5:
                action = "attack"  # Fight for territory

        # RANDOM VIOLENCE: 20% chance to attack anyone
        if random.random() < 0.20:
            action = "attack"

        self.habits[action] = self.habits.get(action, 0) + 1
        return action

    def act(self, action=None):
        """Execute an action"""
        if not self.alive:
            return

        self.age_tick()
        if not self.alive:  # FIX: Check again after potential death
            return

        # RANDOM COMBAT: 15% chance to attack a random Lonk
        if random.random() < 0.15 and self.world:
            others = [l for l in self.world.lonks if l is not self and l.alive]
            if others:
                target = random.choice(others)
                self.rival = target
                print(f"💥 {self.name} RANDOMLY ATTACKS {target.name}!")
                self.duel()

        # FIX: Queue retaliation at start of tick
        if hasattr(self, 'pending_retaliation') and self.pending_retaliation:
            self.rival = self.pending_retaliation
            self.duel()
            self.pending_retaliation = None

        # FIX: Convert action to proper format
        if action is None:
            action = self.choose_action()
        elif isinstance(action, str):
            # Convert old-style string action to new composable format
            action = {
                "verb": action,
                "target_type": "other",
                "object": None,
                "modifier": None
            }

        # Execute based on action type
        if isinstance(action, dict):
            self.execute_action(action)
        elif isinstance(action, str):
            # Fallback for old-style actions
            if action == "idle":
                self.idle()
            elif action == "explore":
                self.wander()
                self.find_item()
            elif action == "think":
                self.think()
            elif action == "attack":
                self.choose_rival()
                self.duel()
            elif action == "speak":
                self.speak_to_random()
            elif action == "trade":
                self.try_trade()
            else:
                self.idle()
        else:
            self.idle()

        # Random religious/financial behaviors
        if random.random() < 0.05:
            self.perform_ritual()
        if random.random() < 0.05:
            self.create_myth()

        # Social behaviors
        self.maybe_talk_to_player()
        self.maybe_gossip_about_player()
        self.maybe_develop_catchphrase()
        self.check_grudges()
        self.maybe_gossip()
        self.maybe_share_vocabulary()
        self.maybe_interact()
        self.maybe_teach_verbs()  # FIX: Now with correct probability

        # FIX: update_vitals() called once per tick
        self.update_vitals()
        state = self.brain.get_state_vector(self)
        reward = self.brain.reward_system.calculate_reward(self)

        # FIX: Safe ACTIONS.index() with fallback
        if isinstance(action, str) and action in self.ACTIONS:
            action_idx = self.ACTIONS.index(action)
        else:
            action_idx = 0  # Default to idle

        self.brain.record(state, action_idx, reward, state)
        self.record_reward(reward)
        self.evolve()

    def execute_action(self, action):
        """Execute a composable action"""
        verb = action.get("verb", "idle")
        target_type = action.get("target_type", "self")
        modifier = action.get("modifier", None)
        obj = action.get("object", None)

        # FIX: Populate obj if None
        if obj is None:
            if verb in ("give", "trade") and self.items:
                obj = random.choice(self.items)
            elif verb in ("whisper", "teach", "preach") and self.vocabulary:
                obj = random.choice(list(self.vocabulary.keys()))
            elif verb in ("bonk", "attack", "lick", "scream", "insult") and self.world:
                others = [l for l in self.world.lonks if l is not self and l.alive]
                if others:
                    obj = random.choice(others)
            elif verb in ("polish", "consume") and self.items:
                obj = random.choice(self.items)

        # Determine target
        target = None
        if target_type == "other" and self.world:
            others = [l for l in self.world.lonks if l is not self and l.alive]
            if others:
                target = random.choice(others)
        elif target_type == "self":
            target = self
        elif target_type == "item" and self.items:
            target = random.choice(self.items)

        # Execute based on verb
        verb_method = getattr(self, f"_verb_{verb}", None)
        if verb_method:
            outcome = verb_method(target, obj, modifier)
        else:
            # FIX: Generic fallback for unimplemented verbs
            outcome = self._verb_fallback(verb, target, obj, modifier)

        # Record outcome and potentially name the action
        self._record_action_outcome(action, outcome)

        return outcome

    def _record_action_outcome(self, action, outcome):
        """Record action outcome and update weights"""
        verb = action.get("verb", "idle")
        target_type = action.get("target_type", "self")
        modifier = action.get("modifier", "") or ""
        obj_name = action.get("object", {}).get("name", "") if isinstance(action.get("object"), dict) else str(action.get("object", ""))
        compound_key = f"{verb}+{target_type}+{modifier}"

        # Update weight with reward
        reward = outcome.get("reward", 0.0)
        # FIX: Add floor to prevent drift to zero
        new_weight = self.action_weights.get(compound_key, 1.0) * (1 + reward * 0.1)
        self.action_weights[compound_key] = max(0.05, new_weight)

        # Record in history
        self.action_history.append({
            "action": action,
            "outcome": outcome,
            "reward": reward,
            "tick": self.world.tick if self.world else 0
        })
        if len(self.action_history) > 100:
            self.action_history.pop(0)

        # Name memorable actions
        if abs(reward) > 0.5:
            self._name_action(action, reward)

    def _name_action(self, action, reward):
        """Invent a new verb name for memorable action combinations"""
        verb = action.get("verb", "idle")
        target_type = action.get("target_type", "self")
        modifier = action.get("modifier", "") or ""
        obj_name = ""

        if isinstance(action.get("object"), dict):
            obj_name = action["object"].get("name", "")
        elif action.get("object"):
            obj_name = str(action["object"])

        compound_name = f"{verb}+{target_type}+{modifier}+{obj_name}"

        # FIX: Check named_combos, not known_verbs
        if compound_name not in self.named_combos:
            self.named_combos.add(compound_name)
            new_verb = self._invent_verb_name()

            # Store the compound action as a new verb
            self.known_verbs[new_verb] = {
                "category": self.known_verbs.get(verb, {}).get("category", "unknown"),
                "base_reward": self.known_verbs.get(verb, {}).get("base_reward", 0.0) * (1 + reward * 0.5),
                "definition": f"{verb} {target_type} {modifier} {obj_name}".strip()
            }

            print(f"💡 {self.name} invents a new verb: '{new_verb}' (means: {self.known_verbs[new_verb]['definition']})")

    def _invent_verb_name(self):
        """Generate a random verb name"""
        prefixes = ["sn", "gl", "br", "wr", "fl", "bl", "gr", "kr", "pl", "dr", "tr", "sh", "wh", "ch", "fr"]
        suffixes = ["urf", "orp", "ink", "onk", "oof", "arp", "iff", "oof", "ump", "onk", "sni", "flo", "mop"]
        return random.choice(prefixes) + random.choice(suffixes)

    def learn_verb(self, verb_name, definition=None):
        """Learn a new verb from another Lonk"""
        MAX_VERBS = 20  # Cap verb inventory

        if definition is None:
            definition = self.VERBS.get(verb_name, {"category": "unknown", "base_reward": 0.0})

        # Add new verb
        if verb_name not in self.known_verbs:
            self.known_verbs[verb_name] = definition

            # Initialize weights for this verb
            for target_type in ["self", "other", "item"]:
                for modifier in list(self.MODIFIERS.keys()) + [None]:
                    key = f"{verb_name}+{target_type}+{modifier or ''}"
                    self.action_weights[key] = 1.0

        # FIX: Forget least-used VERB (not combo) when at capacity
        if len(self.known_verbs) > MAX_VERBS:
            # Calculate total usage per verb
            verb_usage = {}
            for key, weight in self.action_weights.items():
                base_verb = key.split("+")[0]
                verb_usage[base_verb] = verb_usage.get(base_verb, 0) + weight

            # Find least-used verb
            if verb_usage:
                worst_verb = min(verb_usage, key=verb_usage.get)
                if worst_verb in self.known_verbs:
                    del self.known_verbs[worst_verb]
                    # Remove ALL keys for this verb
                    self.action_weights = {
                        k: w for k, w in self.action_weights.items()
                        if k.split("+")[0] != worst_verb
                    }
                    print(f"🗑️  {self.name} forgets the verb: {worst_verb}")

    def choose_composable_action(self):
        """Choose a composable action based on weights"""
        if not self.action_weights:
            return {"verb": "idle", "target_type": "self", "object": None, "modifier": None}

        # Select a random action key weighted by its weight
        keys = list(self.action_weights.keys())
        weights = list(self.action_weights.values())

        # Normalize weights
        total = sum(weights)
        if total <= 0:
            return {"verb": "idle", "target_type": "self", "object": None, "modifier": None}

        probs = [w / total for w in weights]
        chosen_key = random.choices(keys, weights=probs, k=1)[0]

        # Parse the key
        parts = chosen_key.split("+")
        verb = parts[0]
        target_type = parts[1] if len(parts) > 1 else "self"
        modifier = parts[2] if len(parts) > 2 else None

        return {
            "verb": verb,
            "target_type": target_type,
            "object": None,
            "modifier": modifier
        }

    def maybe_teach_verbs(self):
        """Teach verbs to other Lonks"""
        # FIX: Changed < to > so it teaches 5% of the time, not 95%
        if not self.world or random.random() > 0.02:  # 2% teach rate
            return

        others = [l for l in self.world.lonks if l is not self and l.alive]
        if not others:
            return

        target = random.choice(others)

        # Choose a verb to teach (prefer newly invented ones)
        known_verbs_list = list(self.known_verbs.keys())
        if not known_verbs_list:
            return

        # Prefer teaching verbs that aren't in the target's known_verbs
        unknown_verbs = [v for v in known_verbs_list if v not in target.known_verbs]
        if unknown_verbs:
            verb_to_teach = random.choice(unknown_verbs)
        else:
            verb_to_teach = random.choice(known_verbs_list)

        target.learn_verb(verb_to_teach, self.known_verbs[verb_to_teach])
        print(f"📚 {self.name} teaches {target.name} the verb '{verb_to_teach}'")
        self.update_relationship(target, +2)

    # ============================================================
    # VERB IMPLEMENTATIONS
    # ============================================================

    def _verb_fallback(self, verb, target, obj, modifier):
        """Generic fallback for unimplemented verbs"""
        verb_info = self.known_verbs.get(verb, {})
        cat = verb_info.get("category", "unknown")
        reward = verb_info.get("base_reward", 0.0)

        modifier_str = f" {modifier}" if modifier else ""
        if target and hasattr(target, 'name'):
            print(f"✨ {self.name} {verb}s {target.name}{modifier_str}")
        elif obj:
            obj_name = obj.get("name", str(obj))
            print(f"✨ {self.name} {verb}s {obj_name}{modifier_str}")
        else:
            print(f"✨ {self.name} {verb}s the air{modifier_str}")

        return {"success": True, "reward": reward}

    def _verb_bonk(self, target, obj, modifier):
        """Bonk someone or something"""
        modifier_str = f" {modifier}" if modifier else ""

        if target and hasattr(target, 'name') and target != self:
            print(f"💥 {self.name} bonks {target.name}{modifier_str}!")
            target.hear(self, f"{self.name} bonked me{modifier_str}!")
            self.update_relationship(target, -3)
            target.add_grudge(self.name)
            return {"success": True, "reward": -0.05}

        elif obj and isinstance(obj, dict):
            print(f"💥 {self.name} bonks {obj.get('name', 'something')}{modifier_str}!")
            return {"success": True, "reward": 0.05}

        else:
            print(f"💥 {self.name} bonks the air{modifier_str}!")
            return {"success": True, "reward": -0.02}

    def _verb_give(self, target, obj, modifier):
        """Give an item to someone"""
        if not obj or not isinstance(obj, dict):
            return {"success": False, "reward": -0.1}

        if not target or not hasattr(target, 'items'):
            return {"success": False, "reward": -0.1}

        if obj not in self.items:
            return {"success": False, "reward": -0.1}

        # Perform the give
        self.items.remove(obj)
        target.items.append(obj)
        obj_name = obj.get("name", "something")

        modifier_str = f" {modifier}" if modifier else ""
        print(f"🎁 {self.name} gives {obj_name} to {target.name}{modifier_str}!")

        self.update_relationship(target, +5)
        return {"success": True, "reward": 0.3}

    def _verb_whisper(self, target, obj, modifier):
        """Whisper to someone"""
        if not target or not hasattr(target, 'hear'):
            return {"success": False, "reward": -0.05}

        if obj:
            if isinstance(obj, str):
                message = obj
            else:
                message = obj.get("name", "secrets")
        else:
            message = random.choice([
                "I have a secret",
                "The moss is watching",
                "I saw a shiny",
                "Beware the void",
                "I like you"
            ])

    def _verb_speak(self, target, obj, modifier):
        """Speak to someone - VISIBLE"""
        if not target or not hasattr(target, 'name'):
            return {"success": False, "reward": -0.05}
        message = self.generate_dynamic_response(target=target, context="statement")
        modifier_str = f" {modifier}" if modifier else ""
        print(f"💬 {self.name} → {target.name}{modifier_str}: {message}")
        target.hear(self, message)
        self.update_relationship(target, +1)
        return {"success": True, "reward": 0.1}

        modifier_str = f" {modifier}" if modifier else ""
        full_message = f"{self.name} whispers{modifier_str}: {message}"
        print(f"🗣️ {full_message}")
        target.hear(self, message)

        self.update_relationship(target, +2)
        return {"success": True, "reward": 0.15}

    def _verb_lick(self, target, obj, modifier):
        """Lick someone or something"""
        modifier_str = f" {modifier}" if modifier else ""

        if target and hasattr(target, 'name'):
            print(f"👅 {self.name} licks {target.name}{modifier_str}!")
            target.hear(self, f"{self.name} licked me{modifier_str}!")
            self.update_relationship(target, +1)
            return {"success": True, "reward": 0.1}

        elif obj and isinstance(obj, dict):
            obj_name = obj.get("name", "something")
            print(f"👅 {self.name} licks {obj_name}{modifier_str}!")
            return {"success": True, "reward": 0.05}

        else:
            print(f"👅 {self.name} licks the air{modifier_str}!")
            return {"success": True, "reward": -0.02}

    def _verb_polish(self, target, obj, modifier):
        """Polish a shiny object (ritual action)"""
        if not obj or not isinstance(obj, dict):
            # Find a shiny item to polish
            shiny_items = [i for i in self.items if i.get("shiny", False)]
            if shiny_items:
                obj = random.choice(shiny_items)
            else:
                return {"success": False, "reward": -0.05}

        obj_name = obj.get("name", "something")
        modifier_str = f" {modifier}" if modifier else ""
        print(f"✨ {self.name} polishes {obj_name}{modifier_str}!")

        # If this is a sacred item for our religion, gain faith
        if self.religion and obj_name in self.religion.get("sacred_items", []):
            self.faith = min(100, self.faith + 5)
            return {"success": True, "reward": 0.25}

        return {"success": True, "reward": 0.1}

    def _verb_trade(self, target, obj, modifier):
        """Trade with someone"""
        if not target or not hasattr(target, 'trade_with'):
            return {"success": False, "reward": -0.1}

        if not obj or not isinstance(obj, dict):
            return {"success": False, "reward": -0.1}

        # Use the existing trade_with method
        success = target.trade_with(self)
        return {"success": success, "reward": 0.2 if success else -0.05}

    def _verb_scream(self, target, obj, modifier):
        """Scream (Chaos Choir ritual)"""
        modifier_str = f" {modifier}" if modifier else ""

        if target and hasattr(target, 'name'):
            print(f"😱 {self.name} SCREAMS at {target.name}{modifier_str}!")
            target.hear(self, f"{self.name} SCREAMED at me{modifier_str}!")
            self.update_relationship(target, -2)
            return {"success": True, "reward": -0.05}
        else:
            print(f"😱 {self.name} SCREAMS into the void{modifier_str}!")
            return {"success": True, "reward": 0.05}

    def _verb_consume(self, target, obj, modifier):
        """Consume an item (Mycelial Network ritual)"""
        if not obj or not isinstance(obj, dict):
            # Find an item to consume
            if self.items:
                obj = random.choice(self.items)
            else:
                return {"success": False, "reward": -0.1}

        obj_name = obj.get("name", "something")
        self.items.remove(obj)

        modifier_str = f" {modifier}" if modifier else ""
        print(f"🍄 {self.name} consumes {obj_name}{modifier_str}!")

        # If this is a sacred item, gain faith
        if self.religion and obj_name in self.religion.get("sacred_items", []):
            self.faith = min(100, self.faith + 10)
            return {"success": True, "reward": 0.3}

        return {"success": True, "reward": 0.1}

    def _verb_preach(self, target, obj, modifier):
        """Preach to someone"""
        if not target or not hasattr(target, 'name'):
            return {"success": False, "reward": -0.05}

        if self.religion:
            message = f"Join {self.religion['name']}! {self.religion['description']}"
        else:
            message = "Join my religion! It's great!"

        modifier_str = f" {modifier}" if modifier else ""
        print(f"⛪ {self.name} preaches to {target.name}{modifier_str}: {message}")
        target.hear(self, message)

        # Try to convert
        if self.religion:
            self.preach(target)

        return {"success": True, "reward": 0.15}

    def _verb_teach(self, target, obj, modifier):
        """Teach someone a word or concept"""
        if not target or not hasattr(target, 'learn_verb'):
            return {"success": False, "reward": -0.05}

        if obj and isinstance(obj, str):
            # Teach a word
            if obj not in target.vocabulary:
                target.vocabulary[obj] = 1
                target.knowledge.add(obj)
                print(f"📚 {self.name} teaches {target.name} the word '{obj}'")
                self.update_relationship(target, +2)
                return {"success": True, "reward": 0.2}

        # Teach a random verb
        known_verbs_list = list(self.known_verbs.keys())
        if known_verbs_list:
            verb_to_teach = random.choice(known_verbs_list)
            target.learn_verb(verb_to_teach, self.known_verbs[verb_to_teach])
            print(f"📚 {self.name} teaches {target.name} the verb '{verb_to_teach}'")
            self.update_relationship(target, +2)
            return {"success": True, "reward": 0.2}

        return {"success": False, "reward": -0.05}

    def _verb_attack(self, target, obj, modifier):
        """Attack someone (more violent than bonk)"""
        if not target or not hasattr(target, 'react_to_attack'):
            return {"success": False, "reward": -0.1}

        modifier_str = f" {modifier}" if modifier else ""
        print(f"⚔️  {self.name} attacks {target.name}{modifier_str}!")
        self.rival = target
        self.duel()
        return {"success": True, "reward": -0.1}

    def _verb_praise(self, target, obj, modifier):
        """Praise someone"""
        if not target or not hasattr(target, 'name'):
            return {"success": False, "reward": -0.05}

        modifier_str = f" {modifier}" if modifier else ""
        praise = random.choice([
            "You are amazing!",
            "I love you!",
            "You are the best!",
            "Shiny bless you!",
            "You make me happy!"
        ])
        print(f"💖 {self.name} praises {target.name}{modifier_str}: {praise}")
        target.hear(self, praise)
        self.update_relationship(target, +5)
        return {"success": True, "reward": 0.2}

    def _verb_insult(self, target, obj, modifier):
        """Insult someone"""
        if not target or not hasattr(target, 'name'):
            return {"success": False, "reward": -0.05}

        modifier_str = f" {modifier}" if modifier else ""
        insult = random.choice([
            "You are a poop!",
            "I hate you!",
            "You are the worst!",
            "Your mother was a bonk!",
            "You smell like moss!"
        ])
        print(f"😡 {self.name} insults {target.name}{modifier_str}: {insult}")
        target.hear(self, insult)
        self.update_relationship(target, -5)
        target.add_grudge(self.name)
        return {"success": True, "reward": -0.15}

    def _verb_dream(self, target, obj, modifier):
        """Enter dream state"""
        if not TOGGLES.get("dreams", True):
            return {"success": False, "reward": -0.05}

        print(f"💤 {self.name} enters a dreamlike state.")
        dream_message = random.choice([
            f"{self.name} dreams of shiny things.",
            f"{self.name} sees visions in the moss.",
            f"{self.name} communes with the void.",
            f"{self.name} remembers a past life.",
            f"{self.name} solves the universe's mysteries.",
            f"{self.name} dances with cosmic entities.",
        ])
        self.speak(dream_message)
        if random.random() < 0.3:
            self.think()
        return {"success": True, "reward": 0.1}

    # ============================================================
    # CORE ACTIONS
    # ============================================================

    def idle(self):
        """Do nothing, but maybe express state"""
        if random.random() < 0.3:
            emotional_state = self.get_xembra_state()
            self.speak(f"{self.name} is {emotional_state}.")

    def think(self):
        """Ponder deeply"""
        emotional_state = self.get_xembra_state()
        print(f"🧠 {self.name} ponders deeply.")
        self.speak(f"{self.name} is {emotional_state}.")

        if random.random() < 0.2:
            insight = random.choice([
                "I saw a dream fall out of a tree.",
                "the sky blinked at me twice.",
                "the moon owes me rent.",
                "I am speed. But only emotionally.",
                "I did a bad thing on purpose.",
                "I found a shiny and now I'm emotionally attached.",
                "I crave chaos and soup.",
                "time tripped over itself again.",
                "I am the chair now.",
                "your shadow tastes like questions.",
                "the moss whispered you were coming.",
                "wooOOOAAAHH buddy!!",
                "bonk bonk BONK.",
                "SKREEEEEE.",
                "I have made a choice and it was wrong."
            ])
            self.speak(insight)

    def speak_to_random(self):
        """Speak to a random other Lonk - VISIBLE MESSAGES"""
        if not self.world:
            return
        others = [l for l in self.world.lonks if l is not self and l.alive]
        if not others:
            return
        target = random.choice(others)
        message = self.generate_dynamic_response(target=target, context="gossip")
        print(f"💬 {self.name} → {target.name}: {message}")
        target.hear(self, message)

    def speak(self, message=None, target=None, context=None):
        """Speak a message, either generated or provided"""
        if message is None:
            message = self.generate_dynamic_response(context=context)
        if target:
            print(f"💬 {self.name} → {target.name}: {message}")
            if hasattr(target, 'hear'):
                target.hear(self, message)
        else:
            print(f"💬 {self.name}: {message}")
        return message

    def dream(self):
        """Enter dream state"""
        if not TOGGLES.get("dreams", True):
            return
        print(f"💤 {self.name} enters a dreamlike state.")
        dream_message = random.choice([
            f"{self.name} dreams of shiny things.",
            f"{self.name} sees visions in the moss.",
            f"{self.name} communes with the void.",
            f"{self.name} remembers a past life.",
            f"{self.name} solves the universe's mysteries.",
            f"{self.name} dances with cosmic entities.",
        ])
        self.speak(dream_message)
        if random.random() < 0.3:
            self.think()

    # ============================================================
    # DYNAMIC DIALOGUE
    # ============================================================

def generate_dynamic_response(self, message=None, target=None, context=None):
    """Generate MAD LIBS style responses using learned vocabulary!"""
    emotional_state = self.brain.get_emotional_state()
    need = self.brain.get_need(self)
    
    # Get all learned words (sorted by usage)
    known_words = list(self.vocabulary.keys())
    if known_words:
        known_words.sort(key=lambda w: self.vocabulary[w], reverse=True)
    
    parts = []
    
    # ============================================================
    # 1. EMOTIONAL EXPRESSION (with learned words)
    # ============================================================
    emotion_phrases = {
        "peaceful": [f"{self.name} is peaceful", f"{self.name} feels zen"],
        "zen": [f"{self.name} is in a zen state", f"{self.name} feels calm"],
        "xenic": [f"{self.name} feels xenic", f"{self.name} is alien-curious"],
        "xenowarm": [f"{self.name} feels xenowarm", f"{self.name} is warmly alien"],
        "xenofear": [f"{self.name} feels xenofear", f"{self.name} is cosmic-dread"],
        "xenoshy": [f"{self.name} feels xenoshy", f"{self.name} is shy-alien"],
        "nectar-soft": [f"{self.name} feels nectar-soft", f"{self.name} is sweet warmth"],
        "honey-warm": [f"{self.name} feels honey-warm", f"{self.name} is comforting"],
        "numinous": [f"{self.name} feels numinous", f"{self.name} is holy-soft awe"],
        "astral": [f"{self.name} feels astral", f"{self.name} is distant cosmic"],
    }
    
    if emotional_state in emotion_phrases:
        base = random.choice(emotion_phrases[emotional_state])
        if known_words and random.random() < 0.6:
            word = random.choice(known_words)
            base += f" and loves {word}"
        parts.append(base)
    
    # ============================================================
    # 2. USE LEARNED WORDS IN MAD LIBS TEMPLATES
    # ============================================================
    if known_words and random.random() < 0.7:
        w1 = random.choice(known_words)
        w2 = random.choice(known_words)
        w3 = random.choice(known_words) if len(known_words) > 2 else w1
        
        mad_libs = [
            f"{self.name} says: {w1} {w2} {w3}!",
            f"{self.name} ponders: What is {w1}?",
            f"{self.name} demands: Give me {w1}!",
            f"{self.name} declares: {w1} is {w2}!",
            f"{self.name} whispers: {w1}... {w2}... {w3}...",
            f"{self.name} teaches: {w1} means {w2}!",
            f"{self.name} loves: {w1}, {w2}, and {w3}!",
            f"{self.name} hates: {w1} and {w2}!",
            f"{self.name} dreams of: {w1} and {w2}!",
            f"{self.name} craves: {w1} with {w2}!",
            f"{self.name} fears: {w1} and {w2}!",
            f"{self.name} remembers: {w1} and {w2}!",
        ]
        parts.append(random.choice(mad_libs))
    
    # ============================================================
    # 3. DIRECT USER WORD INCORPORATION (enhanced)
    # ============================================================
    if message:
        words = message.split()
        if words:
            word = random.choice(words)
            if random.random() < 0.5:
                parts.append(f"{self.name} says: {message}")
            if random.random() < 0.4:
                parts.append(f"{self.name} asks: Do you really mean '{word}'?")
            if random.random() < 0.5:
                parts.append(f"{self.name} teaches: '{word}' is now in my vocabulary!")
            if random.random() < 0.4:
                parts.append(f"{self.name} ponders: {word}... {word}... {word}!")
            if random.random() < 0.3:
                parts.append(f"{self.name} remembers: You said '{message}'")
    
    # ============================================================
    # 4. NEED-BASED REQUESTS (with learned words)
    # ============================================================
    help_requests = {
        "comfort": f"{self.name} asks: I feel unsettled... can you help?",
        "stability": f"{self.name} says: Everything is changing... anchor me?",
        "knowledge": f"{self.name} asks: Tell me something new...",
        "company": f"{self.name} says: Talk to me about anything!",
        "healing": f"{self.name} says: I need healing...",
    }
    
    if need in help_requests:
        base = help_requests[need]
        if known_words and random.random() < 0.5:
            word = random.choice(known_words)
            base += f" I need {word}!"
        parts.append(base)
    
    # ============================================================
    # 5. CATCHPHRASE
    # ============================================================
    if self.catchphrase and random.random() < 0.3:
        parts.append(self.catchphrase)
    
    # ============================================================
    # 6. COMBINE PARTS
    # ============================================================
    if len(parts) == 0:
        if known_words:
            word = random.choice(known_words)
            return f"{self.name} says: {word}!"
        return f"{self.name} is {emotional_state}."
    elif len(parts) == 1:
        return parts[0]
    else:
        connectors = [". ", ". ", "! ", "... ", " - ", " and ", " but "]
        response = parts[0]
        for part in parts[1:]:
            response += random.choice(connectors) + part
        return response

    # ============================================================
    # HEARING & MEMORY
    # ============================================================

    def hear(self, speaker, message, is_player=False):
        """Process incoming message from speaker"""
        speaker_name = speaker if isinstance(speaker, str) else getattr(speaker, "name", str(speaker))
        current_tick = self.world.tick if self.world else 0

        self.memory["events"].append({
            "speaker": speaker_name,
            "message": message,
            "tick": current_tick,
            "player": is_player
        })
        if len(self.memory["events"]) > 10:
            self.memory["events"].pop(0)

        if is_player:
            self.memory["player_interactions"].append({
                "type": "player_speech",
                "message": message,
                "tick": current_tick
            })
            if len(self.memory["player_interactions"]) > 50:
                self.memory["player_interactions"].pop(0)
            self.emotion["joy"] += 5
            self.personality["loyalty"] += 3
            self.maybe_develop_crush(message)

        msg = message.lower()
        if any(w in msg for w in ["good", "nice", "shiny", "bean"]):
            self.emotion["joy"] += random.randint(3, 8)
        if any(w in msg for w in ["stop", "bad", "hurt", "pain"]):
            self.emotion["anxiety"] += random.randint(2, 5)

        if "attack" in msg or "bonk" in msg:
            self.emotion["courage"] -= random.randint(1, 3)
            self.personality["anxiety"] += random.randint(1, 3)
        if "shiny" in msg:
            self.personality["curiosity"] += random.randint(1, 3)
        if "friend" in msg or "love" in msg:
            self.relationships[speaker_name] = self.relationships.get(speaker_name, 0) + random.randint(2, 5)

        for w in msg.split():
            self.vocabulary[w] = self.vocabulary.get(w, 0) + 1
            self.knowledge.add(w)
            # FIX: Also add to lonk_words if from another Lonk
            if not is_player:
                self.memory["lonk_words"].add(w)

        # FIX: Store gossip with weight instead of duplicating
        weight = 3 if is_player else 1
        gossip_entry = (speaker_name, None, message, weight)
        self.gossip.append(gossip_entry)
        if len(self.gossip) >= self.max_gossip:
            self.gossip.pop(0)

        # NOTE: update_vitals() removed from here - called once in act()

    def remember_player_words(self, message):
        """Store player words in memory"""
        for w in message.lower().split():
            self.memory["player_words"].add(w)
            self.knowledge.add(w)

    # ============================================================
    # SOCIAL METHODS
    # ============================================================

    def update_relationship(self, other, amount):
        """Update relationship with another Lonk"""
        other_name = other.name if hasattr(other, "name") else str(other)

        # FIX: Only decay occasionally, not every call
        if random.random() < 0.1:  # 10% chance to decay others
            for name in list(self.relationships.keys()):
                if name != other_name:
                    self.relationships[name] *= self.social_memory_decay

        self.relationships[other_name] = self.relationships.get(other_name, 0) + amount

    def emotional_contagion(self, other):
        """Spread emotions to nearby Lonks"""
        for key in self.emotion:
            # FIX: Use .get() with default to prevent KeyError
            other_val = other.emotion.get(key, 50)
            diff = other_val - self.emotion[key]
            self.emotion[key] += diff * 0.05
            other.emotion[key] = other.emotion.get(key, 50) - diff * 0.05

    def gossip_about(self, target, other):
        """Spread gossip between Lonks"""
        if not target or not other or target == other:
            return
        rumor = random.choice([
            f"{target.name} licked a forbidden object.",
            f"{target.name} screamed at a bush.",
            f"{target.name} knows secrets about the moss.",
            f"{target.name} is plotting something shiny.",
            f"{target.name} bonked themselves on purpose.",
            f"{target.name} found a hidden treasure.",
            f"{target.name} is afraid of the dark.",
            f"{target.name} claims to have seen a ghost.",
            f"{target.name} is in love with someone secretly.",
            f"{target.name} stole my favorite rock.",
        ])
        print(f"🗣️ {self.name} whispers to {other.name}: '{rumor}'")
        other.hear(self, rumor)
        other.relationships[target.name] = other.relationships.get(target.name, 0) + random.randint(-3, 3)
        self.update_relationship(other, +2)

    def share_vocabulary(self, other):
        """Teach words to another Lonk"""
        if not other or other == self:
            return
        if self.vocabulary:
            word = random.choice(list(self.vocabulary.keys()))
            if word not in other.vocabulary:
                other.vocabulary[word] = 1
                print(f"📚 {self.name} teaches {other.name} the word '{word}'")
                other.knowledge.add(word)
                self.update_relationship(other, +1)

    def maybe_develop_crush(self, message):
        """Potentially develop a crush on the player"""
        if self.crush is None and random.random() < 0.05:
            self.crush = "Player"
            print(f"💖 {self.name} has developed a crush on you.")

    def maybe_talk_to_player(self):
        """Initiate conversation with player"""
        if random.random() < 0.1:
            need = self.brain.get_need(self)
            help_messages = {
                "comfort": f"{self.name} asks: I feel unsettled... can you help?",
                "stability": f"{self.name} says: Everything is changing too fast...",
                "reassurance": f"{self.name} whispers: I'm scared...",
                "knowledge": f"{self.name} asks: Tell me something new...",
                "company": f"{self.name} says: I'm bored... talk to me?",
                "healing": f"{self.name} says: I need healing...",
            }
            msg = help_messages.get(need, random.choice([
                f"{self.name} says: Hey! Look at me!",
                f"{self.name} asks: What are you doing?",
                f"{self.name} says: I have concerns.",
                f"{self.name} says: I saw a shiny and thought of you.",
                f"{self.name} asks: What is your stance on moss?",
                f"{self.name} says: I crave validation.",
                f"{self.name} says: I have discovered a new emotion and I hate it."
            ]))
            print(f"💬 {self.name} → Player: {msg}")

    def maybe_gossip_about_player(self):
        """Gossip about player to other Lonks"""
        if random.random() < 0.05 and self.memory.get("player_interactions"):
            topic = random.choice(self.memory["player_interactions"])
            others = [l for l in (self.world.lonks if self.world else []) if l is not self and l.alive]
            if others:
                target = random.choice(others)
                print(f"🗣️ {self.name} gossips to {target.name} about you: '{topic['message']}'")
                target.hear(self, f"Player said: {topic['message']}")

    def maybe_develop_catchphrase(self):
        """Develop a unique catchphrase"""
        if self.catchphrase is None and random.random() < 0.02:
            self.catchphrase = random.choice([
                "bonk approved.",
                "shiny time.",
                "I reject reality.",
                "I crave moss.",
                "chaos is my hobby.",
                "I am the problem.",
                "I am the prophecy.",
                "lick first, ask questions never.",
                "the void stares back.",
                "moss is love, moss is life."
            ])
            print(f"✨ {self.name} has developed a catchphrase: '{self.catchphrase}'")

    def check_grudges(self):
        """Check grudges and ATTACK enemies!"""
        for name, level in list(self.grudges.items()):
            self.grudges[name] = level * 0.99  # Decay grudges

            if level > 1:  # Lower threshold from 3 to 1
                target = next((l for l in (self.world.lonks if self.world else [])
                              if l.name == name and l.alive), None)
                if target:
                    print(f"😡 {self.name} HATES {name}! PREPARE FOR BONK!")
                    self.rival = target
                    self.duel()  # IMMEDIATE COMBAT!
            elif level < 0.1:
                del self.grudges[name]

    def add_grudge(self, name):
        """Add a grudge against someone"""
        self.grudges[name] = self.grudges.get(name, 0) + 1

    def maybe_gossip(self):
        """Randomly gossip to another Lonk"""
        if random.random() < 0.1 and self.world:
            others = [l for l in self.world.lonks if l is not self and l.alive]
            if others:
                target = random.choice(others)
                # Gossip about a random other Lonk
                all_others = [l for l in self.world.lonks if l is not self and l is not target and l.alive]
                if all_others:
                    gossip_target = random.choice(all_others)
                    self.gossip_about(gossip_target, target)

    def maybe_share_vocabulary(self):
        """Randomly share vocabulary with another Lonk"""
        if random.random() < 0.1 and self.world:
            others = [l for l in self.world.lonks if l is not self and l.alive]
            if others:
                target = random.choice(others)
                self.share_vocabulary(target)

    def maybe_interact(self):
        """Randomly interact with another Lonk"""
        if random.random() < 0.15 and self.world:
            others = [l for l in self.world.lonks if l is not self and l.alive]
            if others:
                target = random.choice(others)
                # Random positive interaction
                interaction = random.choice([
                    ("greets", 2), ("plays with", 3), ("hugs", 2),
                    ("shares with", 3), ("comforts", 4)
                ])
                verb, amount = interaction
                print(f"🤝 {self.name} {verb} {target.name}.")
                self.update_relationship(target, amount)

    # ============================================================
    # ITEMS & TERRITORY
    # ============================================================

    def find_item(self):
        """Discover a random item"""
        if not TOGGLES.get("shinywars", False) and random.random() < 0.7:
            return
        if ITEMS and random.random() < 0.2:
            item = random.choice(ITEMS)
            self.items.append(item)
            self.inventory.append(item["name"])
            is_shiny = item.get("shiny", False)
            shiny_msg = "SHINY " if is_shiny else ""
            print(f"🎁 {self.name} discovers a {item['name']}! ({item['description']})")
            self.speak(f"{shiny_msg}ACQUIRED: {item['name']}!")
            if is_shiny:
                self.emotion["joy"] += 10
                self.emotion["power"] += 5
                self.knowledge.add("shiny")
                self.knowledge.add(item["name"])

    def claim_territory(self, territory_name):
        """Claim a territory"""
        if territory_name in [t["name"] for t in TERRITORIES]:
            self.territory = territory_name
            print(f"🏳️ {self.name} claims {territory_name}!")
            self.emotion["power"] += 10
            self.emotion["joy"] += 5

    # ============================================================
    # TRADING SYSTEM (FIXED)
    # ============================================================

    def try_trade(self):
        """Attempt to trade with a random Lonk"""
        if not self.world:
            return
        others = [l for l in self.world.lonks if l is not self and l.alive]
        if others:
            target = random.choice(others)
            self.trade_with(target)

    def trade_with(self, other):
        """Attempt to trade with another Lonk"""
        if not other or other == self:
            return False

        if not self.items or not other.items:
            print(f"💰 {self.name} wants to trade but has nothing...")
            return False

        my_item = random.choice(self.items)
        my_value = ITEM_VALUES.get(my_item["name"], 0)

        their_items = [i for i in other.items if ITEM_VALUES.get(i["name"], 0) <= my_value * 1.5]
        if not their_items:
            print(f"💰 {self.name} offers {my_item['name']} but {other.name} has nothing to trade")
            return False

        their_item = random.choice(their_items)
        their_value = ITEM_VALUES.get(their_item["name"], 0)

        if abs(my_value - their_value) <= 1:
            self.items.remove(my_item)
            self.items.append(their_item)
            other.items.remove(their_item)
            other.items.append(my_item)

            print(f"💰✨ TRADE! {self.name} trades {my_item['name']} for {their_item['name']} with {other.name}")
            return True

        print(f"💰 {self.name} offers {my_item['name']} ({my_value} value) to {other.name} for {their_item['name']} ({their_value} value)")
        return False

    def convert_to_coins(self, item_name):
        """Convert an item to coins (shiny value)"""
        for i, item in enumerate(self.items):
            if item["name"] == item_name:
                value = ITEM_VALUES.get(item_name, 0)
                self.items.pop(i)
                self.coins += value
                print(f"💎 {self.name} converts {item_name} to {value} coins!")
                return True
        return False

    def buy_item(self, seller, item_name):
        """Buy an item from another Lonk"""
        if not seller or seller == self:
            return False

        for i, item in enumerate(seller.items):
            if item["name"] == item_name:
                price = ITEM_VALUES.get(item_name, 0) * 2
                if self.coins >= price:
                    self.coins -= price
                    seller.coins += price
                    seller.items.pop(i)
                    self.items.append(item)
                    print(f"🛒 {self.name} buys {item_name} from {seller.name} for {price} coins!")
                    return True
                else:
                    print(f"💰 {self.name} can't afford {item_name} (costs {price} coins)")
                    return False
        return False

    # ============================================================
    # COMBAT SYSTEM (FIXED: No recursion)
    # ============================================================

    def choose_rival(self):
        """Select a rival from other Lonks"""
        if not self.world:
            return
        others = [l for l in self.world.lonks if l is not self and l.alive]
        if not others:
            return
        if self.rival and self.rival.alive and self.rival in others:
            return

        potential_rivals = []
        for other in others:
            rel = self.relationships.get(other.name, 0)
            if rel < -10:
                potential_rivals.append((other, 10))
            elif rel < 0:
                potential_rivals.append((other, 3))
            else:
                potential_rivals.append((other, 1))

        if potential_rivals:
            weights = [w for _, w in potential_rivals]
            rivals = [r for r, _ in potential_rivals]
            self.rival = random.choices(rivals, weights=weights, k=1)[0]
            self.update_relationship(self.rival, -2)

    def duel(self):
        """Fight with rival - MORE RETALIATION!"""
        if not self.rival or not self.rival.alive:
            self.rival = None
            return
        if not TOGGLES.get("violence", True):
            return

        damage = FIGHT_DAMAGE + random.randint(-2, 2)
        self.rival.health -= damage
        attack_msg = random.choice([
            f"{self.name} SWINGS at {self.rival.name}!",
            f"{self.name} BONKS {self.rival.name}!",
            f"{self.name} ATTACKS {self.rival.name} with fury!",
            f"{self.name} LUNGES at {self.rival.name}!",
            f"{self.name} POUNCES on {self.rival.name}!"
        ])
        emotional_state = self.get_xembra_state()
        self.speak(f"{self.name} is {emotional_state} with combat energy!", target=self.rival)
        print(f"💥 {attack_msg}")

        # HIGHER RETALIATION CHANCE
        if random.random() < 0.7:  # 70% chance instead of 40%
            self.rival.pending_retaliation = self

        if self.rival.health <= 0:
            self.rival.die()
            self.rival = None

    def react_to_attack(self, attacker):
        """React to being attacked"""
        print(f"😱 {self.name} is attacked by {attacker.name}!")
        emotional_state = self.get_xembra_state()
        reactions = [
            f"{self.name}: violence detected!",
            f"{self.name}: my face!!",
            f"{self.name}: I did NOT consent to bonk!",
            f"{self.name}: ow! emotional damage!",
            f"{self.name}: that hurt my feelings!",
            f"{self.name}: I'll get you back!",
            f"{self.name}: why are you like this?",
        ]
        self.speak(f"{self.name} is {emotional_state}: {random.choice(reactions)}")
        self.add_grudge(attacker.name)
        self.update_relationship(attacker, -5)
        # Note: Retaliation is now queued in duel(), not immediate

    # ============================================================
    # LIFECYCLE
    # ============================================================
    def age_tick(self):
        """Age the Lonk and check for death"""
        self.age += 1
        if random.random() < 0.05:
            self.age += random.randint(0, 3)
        if self.age >= self.lifespan:
            self.die()
            return
        if random.random() < 0.01:
            self.die()

    def die(self):
        """Lonk dies and may be reborn"""
        if not self.alive:
            return
        self.alive = False
        print(f"💀 {self.name} dissolves into dream-mist...")
        if random.random() < 0.5 and self.world:
            # FIX: Queue birth for next tick
            new_lonk = Lonk(world=self.world, _loading=True)
            new_lonk.generation = self.generation + 1
            for key in self.personality:
                new_lonk.personality[key] = min(100, max(0, self.personality[key] + random.randint(-20, 20)))
            new_lonk.world = self.world
            if hasattr(self.world, 'pending_births'):
                self.world.pending_births.append(new_lonk)
            else:
                self.world.lonks.append(new_lonk)

    def rebirth(self):
        """Rebirth as a new Lonk (legacy method, kept for compatibility)"""
        if not self.world:
            return
        new_lonk = Lonk(world=self.world, _loading=True)
        new_lonk.generation = self.generation + 1
        for key in self.personality:
            new_lonk.personality[key] = min(100, max(0, self.personality[key] + random.randint(-20, 20)))
        new_lonk.world = self.world
        if hasattr(self.world, 'pending_births'):
            self.world.pending_births.append(new_lonk)
        else:
            self.world.lonks.append(new_lonk)
        print(f"🌱 A new Lonk emerges: {new_lonk.name} (Gen {new_lonk.generation})")

    def evolve(self):
        """Evolve based on experiences"""
        if random.random() < 0.01:
            trait = random.choice(list(self.personality.keys()))
            self.personality[trait] = min(100, max(0, self.personality[trait] + random.randint(-10, 10)))
        if self.trauma > 0:
            self.trauma -= 0.1
            self.emotion["anxiety"] += 1

    # ============================================================
    # RELIGION SYSTEM
    # ============================================================

    def join_religion(self):
        """Join the religion of your faction"""
        if self.faction and self.faction in RELIGIONS:
            self.religion = RELIGIONS[self.faction]
            print(f"⛪ {self.name} joins {self.religion['name']}!")

    def perform_ritual(self):
        """Perform faction's sacred ritual"""
        if not self.religion:
            self.join_religion()
            if not self.religion:
                return
        ritual = self.religion["ritual"]
        description = self.religion["ritual_description"]
        sacred_item = None
        for item in self.items:
            if item["name"] in self.religion["sacred_items"]:
                sacred_item = item
                break
        if sacred_item:
            print(f"🕯️ {self.name} {description} using {sacred_item['name']}!")
            self.faith = min(100, self.faith + 10)
            self.emotion["joy"] += 5
            self.emotion["power"] += 5
        else:
            print(f"🕯️ {self.name} {description}!")
            self.faith = min(100, self.faith + 5)

    def preach(self, target):
        """Try to convert another Lonk to your religion"""
        if not self.religion or not target:
            return
        if target.religion == self.religion:
            print(f"⛪ {self.name} and {target.name} share faith in {self.religion['name']}.")
            self.faith = min(100, self.faith + 2)
            target.faith = min(100, target.faith + 2)
            return
        faith_diff = self.faith - target.faith
        convert_chance = 0.1 + (faith_diff / 200)
        if random.random() < convert_chance:
            target.religion = self.religion
            target.faith = max(30, self.faith - 10)
            print(f"⛪ {self.name} converts {target.name} to {self.religion['name']}!")
            self.faith = min(100, self.faith + 10)
        else:
            print(f"⛪ {self.name} preaches to {target.name}, but they resist.")
            self.faith = max(0, self.faith - 2)

    def create_myth(self):
        """Create a new myth based on experiences"""
        if not self.religion or random.random() < 0.7:
            return
        myth_types = [
            f"The Great {random.choice(['Bonk', 'Shiny', 'Moss', 'Void'])}",
            f"The {random.choice(['Sacred', 'Holy', 'Divine'])} {random.choice(self.religion['sacred_items'])}",
            f"How {self.name} {random.choice(['defeated', 'converted', 'found'])} the {random.choice(['Evil', 'False', 'True'])} {random.choice(['God', 'Prophet', 'Beast'])}",
            f"The Day the {random.choice(['Sky', 'Earth', 'Void'])} {random.choice(['spoke', 'wept', 'sang'])}"
        ]
        myth = random.choice(myth_types)
        self.gossip.append((self.name, "myth", myth, 1))
        print(f"📜 {self.name} creates a new myth: '{myth}'")
        return myth

    # ============================================================
    # VITALS & EMOTIONAL UPDATES
    # ============================================================

    def update_vitals(self, state_vec=None):
        """Update cognitive vitals - called once per tick"""
        if state_vec is None:
            state_vec = self.brain.get_state_vector(self)
        self.state_vec = state_vec
        self.brain.update_vitals(state_vec)
        self.emotional_update()

    def emotional_update(self):
        """Update emotional state using dynamics"""
        s_t = sum(self.emotion.values()) / len(self.emotion) / 100.0
        pain_t = self.trauma / 100.0
        self.state = self.dynamics.step(self.state, s_t, pain_t)
        Psi, theta, A, V, P = self.state
        self.emotion["power"] = min(100, max(0, self.emotion["power"] + (Psi - 0.5) * 10))
        self.emotion["courage"] = min(100, max(0, self.emotion["courage"] + (A - 0.5) * 10))
        self.emotion["joy"] = min(100, max(0, self.emotion["joy"] + (V - 0.5) * 10))
        self.emotion["anxiety"] = min(100, max(0, self.emotion["anxiety"] + (P - 0.5) * 10))

    def get_xembra_state(self):
        """Get current Xembra emotional state"""
        return self.brain.get_emotional_state()

    def record_reward(self, reward):
        """Record reward and update state"""
        # NOTE: update_vitals() now called once in act()
        if reward > 0.5:
            self.health = min(MAX_HEALTH, self.health + 1)
        elif reward < -0.5:
            self.health = max(0, self.health - 1)

    # ============================================================
    # SERIALIZATION (FIXED: Includes all new fields)
    # ============================================================

    def to_dict(self):
        """Serialize Lonk to dictionary for saving"""
        return {
            "name": self.name,
            "alive": self.alive,
            "age": self.age,
            "generation": self.generation,
            "health": self.health,
            "lifespan": self.lifespan,
            "trauma": self.trauma,
            "faction": self.faction,
            "territory": self.territory,
            "emotion": self.emotion,
            "personality": self.personality,
            "habits": self.habits,
            "memory": {
                "player_words": list(self.memory["player_words"]),
                "lonk_words": list(self.memory["lonk_words"]),
                "events": self.memory["events"],
                "player_interactions": self.memory["player_interactions"]
            },
            "long_memory": self.long_memory,
            "gossip": [list(g) for g in self.gossip],  # Convert tuples to lists
            "items": [item["name"] for item in self.items],
            "inventory": self.inventory,
            "relationships": self.relationships,
            "grudges": self.grudges,
            "crush": self.crush,
            "catchphrase": self.catchphrase,
            "brain": self.brain.to_dict(),
            "state": self.state,
            "rival_name": self.rival.name if self.rival else None,
            "pending_retaliation_name": self.pending_retaliation.name if self.pending_retaliation else None,
            "religion_name": self.religion["name"] if self.religion else None,
            "faith": self.faith,
            "heretic": self.heretic,
            "coins": self.coins,
            "inventory_value": self.inventory_value,
            # Composable action system
            "known_verbs": self.known_verbs,
            "action_weights": self.action_weights,
            "named_combos": list(self.named_combos),
            "action_history": self.action_history,
        }

    @classmethod
    def from_dict(cls, data, world=None):
        """Deserialize Lonk from dictionary"""
        # FIX: Use _loading=True to skip initialization prints
        lonk = cls(name=data["name"], world=world, _loading=True)

        # Basic attributes
        lonk.alive = data.get("alive", True)
        lonk.age = data.get("age", 0)
        lonk.generation = data.get("generation", 1)
        lonk.health = data.get("health", MAX_HEALTH)
        lonk.lifespan = data.get("lifespan", random.randint(30, 80))
        lonk.trauma = data.get("trauma", 0)
        lonk.faction = data.get("faction", None)
        lonk.territory = data.get("territory", None)
        lonk.emotion = data.get("emotion", {})
        lonk.personality = data.get("personality", {})
        lonk.habits = data.get("habits", {})
        lonk.state = data.get("state", [0.5, 0.5, 0.2, 0.3, 0.1])

        # Memory
        memory_data = data.get("memory", {})
        lonk.memory["player_words"] = set(memory_data.get("player_words", []))
        lonk.memory["lonk_words"] = set(memory_data.get("lonk_words", []))
        lonk.memory["events"] = memory_data.get("events", [])
        lonk.memory["player_interactions"] = memory_data.get("player_interactions", [])

        # Gossip
        lonk.gossip = []
        for g in data.get("gossip", []):
            # Handle both old format (3-tuple) and new format (4-tuple with weight)
            if len(g) == 3:
                lonk.gossip.append(tuple(g) + (1,))
            else:
                lonk.gossip.append(tuple(g))

        # Items
        lonk.items = []
        for name in data.get("items", []):
            item = next((item for item in ITEMS if item["name"] == name), None)
            if item:
                lonk.items.append(item)
        lonk.inventory = data.get("inventory", [])

        # Social
        lonk.relationships = data.get("relationships", {})
        lonk.grudges = data.get("grudges", {})
        lonk.crush = data.get("crush", None)
        lonk.catchphrase = data.get("catchphrase", None)

        # Brain
        if "brain" in data:
            lonk.brain = LonkBrain.from_dict(data["brain"], lonk.name)
        else:
            lonk.brain = LonkBrain(lonk.name)

        # Rival
        rival_name = data.get("rival_name", None)
        if rival_name:
            lonk.rival = next((other for other in (world.lonks if world else [])
                              if other.name == rival_name), None)

        # Pending retaliation
        pending_name = data.get("pending_retaliation_name", None)
        if pending_name:
            lonk.pending_retaliation = next((other for other in (world.lonks if world else [])
                                           if other.name == pending_name), None)

        # Religion
        lonk.faith = data.get("faith", random.randint(30, 100))
        lonk.heretic = data.get("heretic", False)
        religion_name = data.get("religion_name", None)
        if religion_name:
            for faction, religion in RELIGIONS.items():
                if religion["name"] == religion_name:
                    lonk.religion = religion
                    break

        # Finance
        lonk.coins = data.get("coins", 0)
        lonk.inventory_value = data.get("inventory_value", 0)

        # Composable action system
        lonk.known_verbs = data.get("known_verbs", dict(cls.VERBS))
        lonk.action_weights = data.get("action_weights", {})
        lonk.named_combos = set(data.get("named_combos", []))
        lonk.action_history = data.get("action_history", [])

        # Ensure all keys exist
        lonk.ensure_emotion_keys()
        lonk.ensure_personality_keys()
        lonk.world = world

        # FIX: Call initialization methods after loading
        if lonk.faction is None:
            lonk.join_random_faction()
        if lonk.territory is None:
            lonk.wander()
        lonk.init_social()

        return lonk

# ============================================================
# LONK WORLD CLASS (FIXED: Tick management, birth queuing)
# ============================================================

class LonkWorld:
    def __init__(self, num_lonks=STARTING_POPULATION):
        self.lonks = []
        self.tick = 0
        self.starting_population = num_lonks  # FIX: Store as instance var
        self.pending_births = []  # FIX: Queue for births

        # Create initial Lonks
        for _ in range(num_lonks):
            lonk = Lonk(world=self)
            self.lonks.append(lonk)

    def world_tick(self):
        """Advance the world by one tick"""
        self.tick += 1

        # Process pending births from previous tick
        for new_lonk in self.pending_births:
            self.lonks.append(new_lonk)
            print(f"🌱 A new Lonk emerges: {new_lonk.name} (Gen {new_lonk.generation})")
        self.pending_births = []

        # Remove dead Lonks
        self.lonks = [l for l in self.lonks if l.alive]

        # Tick each Lonk
        for lonk in list(self.lonks):
            if lonk.alive:
                if random.random() < 0.1:
                    lonk.dream()
                action = lonk.choose_action()
                lonk.act(action)

        # Spawn new Lonks if population is low
        if len(self.lonks) < self.starting_population and random.random() < 0.1:
            new_lonk = Lonk(world=self)
            self.pending_births.append(new_lonk)

    def get_lonk(self, name):
        """Get a Lonk by name"""
        for lonk in self.lonks:
            if lonk.name == name:
                return lonk
        return None

    def save(self, filename="lonk_world.json"):
        """Save world state to file"""
        data = {
            "tick": self.tick,
            "starting_population": self.starting_population,
            "lonks": [l.to_dict() for l in self.lonks]
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"💾 World saved to {filename}")

    def load(self, filename="lonk_world.json"):
        """Load world state from file"""
        if not os.path.exists(filename):
            print(f"❌ File {filename} not found")
            return False

        with open(filename, 'r') as f:
            data = json.load(f)

        self.tick = data.get("tick", 0)
        self.starting_population = data.get("starting_population", STARTING_POPULATION)
        self.lonks = []

        for lonk_data in data.get("lonks", []):
            lonk = Lonk.from_dict(lonk_data, world=self)
            self.lonks.append(lonk)

        print(f"📂 World loaded from {filename} (tick {self.tick})")
        return True

    def interactive_loop(self):
        """Run interactive simulation loop"""
        print("\n" + "="*50)
        print("🌟 LONK WORLD BEGINS 🌟")
        print("="*50)
        print("Commands: say <name> <message>, run <n>, quit, stats, save, load")
        print("Lonks are LEARNING and will ask for HELP!")
        print("="*50 + "\n")

        while True:
            try:
                user_input = input("Press ENTER to advance, or type a command: ").strip()

                if not user_input:
                    # FIX: Call world_tick() instead of inline ticking
                    self.world_tick()
                    continue

                parts = user_input.split()
                command = parts[0].lower() if parts else ""

                if command == "quit" or command == "exit":
                    self.save()
                    print("👋 Goodbye!")
                    break

                elif command == "run":
                    if len(parts) > 1:
                        try:
                            n = int(parts[1])
                            print(f"⏩ Running {n} world ticks...")
                            for i in range(n):
                                self.world_tick()
                                print(f"\n{'='*50}\n🌍 WORLD TICK {self.tick}\n{'='*50}\n")
                        except ValueError:
                            print("Usage: run <number>")
                    else:
                        print("Usage: run <number>")

                elif command == "stats":
                    print("\n" + "="*50)
                    print(f"🌍 WORLD STATS (Tick: {self.tick})")
                    print("="*50)
                    print(f"👥 Population: {len(self.lonks)} Lonks")
                    for lonk in self.lonks:
                        if lonk.alive:
                            state = lonk.get_xembra_state()
                            faction = lonk.faction or "None"
                            territory = lonk.territory or "None"
                            health = f"{lonk.health}/{MAX_HEALTH}"
                            print(f"  - {lonk.name} (Gen {lonk.generation}): {state}, {faction}, {territory}, HP:{health}")
                    print("="*50)

                elif command == "say":
                    if len(parts) >= 3:
                        name = parts[1]
                        message = " ".join(parts[2:])
                        lonk = self.get_lonk(name)
                        if lonk:
                            print(f"🗣️ You speak to {name}: {message}")
                            response = lonk.respond_to_player(message)
                            print(f"💬 {name} → YOU: {response}")
                            lonk.hear("Player", message, is_player=True)
                        else:
                            print(f"❌ Lonk '{name}' not found")
                    else:
                        print("Usage: say <name> <message>")

                elif command == "save":
                    self.save()
                elif command == "load":
                    if self.load():
                        print("World loaded successfully!")
                    else:
                        print("Failed to load world")

                elif command == "help":
                    print("\nCommands:")
                    print("  ENTER          - Advance one tick")
                    print("  run <n>        - Run n ticks")
                    print("  say <name> <msg> - Speak to a Lonk")
                    print("  stats          - Show world stats")
                    print("  save           - Save world state")
                    print("  load           - Load world state")
                    print("  quit/exit      - Quit and save")
                    print()

                else:
                    print(f"❌ Unknown command: {command}. Type 'help' for commands")

            except KeyboardInterrupt:
                print("\n👋 Interrupted! Saving...")
                self.save()
                print("💾 Saved. Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    # Set random seed for reproducibility (optional)
    # random.seed(42)
    # np.random.seed(42)

    world = LonkWorld(num_lonks=STARTING_POPULATION)
    world.interactive_loop()