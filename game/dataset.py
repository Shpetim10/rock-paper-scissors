"""Dataset loading helpers shared by the Dataset Gallery page.

Kept in a regular importable module (rather than the page script) so that
`st.cache_data` can pickle `DatasetImage` — Streamlit runs page scripts as
`__main__`, and pickle cannot resolve classes defined there.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from PIL import Image


@dataclass
class DatasetImage:
    path: Path
    label: str
    filename: str
    source: str
    width: int
    height: int


def classify_source(label: str, filename: str) -> str:
    """Augmented images are generated as `{label}_{n}.png`; anything else is original."""
    pattern = re.compile(rf"^{re.escape(label)}_\d+\.png$", re.IGNORECASE)
    return "Augmented" if pattern.match(filename) else "Original"


def load_dataset(root: str, class_names: list[str]) -> list[DatasetImage]:
    images: list[DatasetImage] = []
    for label in class_names:
        class_dir = Path(root) / label
        if not class_dir.is_dir():
            continue
        for entry in sorted(os.listdir(class_dir)):
            path = class_dir / entry
            if not path.is_file():
                continue
            try:
                with Image.open(path) as im:
                    width, height = im.size
            except Exception:
                continue
            images.append(
                DatasetImage(
                    path=path,
                    label=label,
                    filename=entry,
                    source=classify_source(label, entry),
                    width=width,
                    height=height,
                )
            )
    return images
