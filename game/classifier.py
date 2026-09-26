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

MODEL_PATH = os.environ.get("RPS_MODEL_PATH", "model/rps_model.h5")
IMAGE_SIZE = (150, 150)
CLASS_NAMES = ["paper", "rock", "scissors"]

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

    def predict(self, image: Image.Image) -> Prediction:
        if self._model is None:
            label = random.choice(CLASS_NAMES)
            confidence = random.uniform(0.6, 0.99)
            return Prediction(label=label, confidence=confidence, is_mock=True)

        img = image.convert("RGB").resize(IMAGE_SIZE)
        array = np.asarray(img, dtype="float32") / 255.0
        batch = np.expand_dims(array, axis=0)
        probabilities = self._model.predict(batch, verbose=0)[0]
        index = int(np.argmax(probabilities))
        return Prediction(
            label=CLASS_NAMES[index],
            confidence=float(probabilities[index]),
            is_mock=False,
        )


def computer_move() -> str:
    return random.choice(CLASS_NAMES)


def judge(human: str, computer: str) -> str:
    """Return 'win', 'lose', or 'draw' from the human's perspective."""
    if human == computer:
        return "draw"
    beats = {"rock": "scissors", "paper": "rock", "scissors": "paper"}
    return "win" if beats[human] == computer else "lose"
