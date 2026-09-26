"""Gesture classification wrapper around the Keras Rock-Paper-Scissors model.

Looks for a trained model at MODEL_PATH. Until one is trained and dropped in,
predictions fall back to a random mock classifier so the game UI can be
built and tested end-to-end. `is_mock` on the result tells the UI which mode
is active.
"""

import os
import random
from dataclasses import dataclass

import numpy as np
from PIL import Image

MODEL_PATH = os.environ.get("RPS_MODEL_PATH", "model/rps_model.keras")
LABELS_PATH = os.environ.get("RPS_LABELS_PATH", "model/labels.txt")
IMAGE_SIZE = (224, 224)


def _load_class_names() -> list[str]:
    if not os.path.exists(LABELS_PATH):
        return ["paper", "rock", "scissors"]
    names = []
    with open(LABELS_PATH) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            _, name = line.split(maxsplit=1)
            names.append(name)
    return names


CLASS_NAMES = _load_class_names()

GESTURE_EMOJI = {"rock": "\U0001FAA8", "paper": "\U0001F4C4", "scissors": "✂️"}


@dataclass
class Prediction:
    label: str
    confidence: float
    is_mock: bool


class GestureClassifier:
    def __init__(self, model_path: str = MODEL_PATH):
        self.model_path = model_path
        self._model = None
        self._is_mock = True
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.model_path):
            self._is_mock = True
            return
        try:
            from tensorflow import keras

            self._model = keras.models.load_model(self.model_path)
            self._is_mock = False
        except Exception:
            self._model = None
            self._is_mock = True

    @property
    def is_mock(self) -> bool:
        return self._is_mock

    def predict_proba(self, image: Image.Image) -> tuple[dict[str, float], bool]:
        """Return a {class_name: probability} distribution and the mock flag."""
        if self._model is None:
            top = random.choice(CLASS_NAMES)
            confidence = random.uniform(0.6, 0.99)
            leftover = 1.0 - confidence
            others = [c for c in CLASS_NAMES if c != top]
            probabilities = {top: confidence}
            for i, name in enumerate(others):
                probabilities[name] = leftover / 2 if i == 0 else leftover - probabilities[others[0]]
            return probabilities, True

        img = image.convert("RGB").resize(IMAGE_SIZE)
        array = (np.asarray(img, dtype="float32") / 127.5) - 1.0
        batch = np.expand_dims(array, axis=0)
        probabilities = self._model.predict(batch, verbose=0)[0]
        return {name: float(p) for name, p in zip(CLASS_NAMES, probabilities)}, False

    def predict(self, image: Image.Image) -> Prediction:
        probabilities, is_mock = self.predict_proba(image)
        label = max(probabilities, key=probabilities.get)
        return Prediction(label=label, confidence=probabilities[label], is_mock=is_mock)


def computer_move() -> str:
    return random.choice(CLASS_NAMES)


def judge(human: str, computer: str) -> str:
    """Return 'win', 'lose', or 'draw' from the human's perspective."""
    if human == computer:
        return "draw"
    beats = {"rock": "scissors", "paper": "rock", "scissors": "paper"}
    return "win" if beats[human] == computer else "lose"
