"""Dataset loading helpers shared by the Dataset Gallery page.

Kept in a regular importable module (rather than the page script) so that
`st.cache_data` can pickle `DatasetImage` — Streamlit runs page scripts as
`__main__`, and pickle cannot resolve classes defined there.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

# Source directories, each labeled explicitly rather than guessed from
# filenames (the old heuristic misclassified plenty of originals whose
# filenames happened to look like `label_123.png`).
DATASET_SOURCES = {
    "Original": "datasets",
    "Augmented": "augmented_dataset",
    "Test": "test_dataset",
}


@dataclass
class DatasetImage:
    path: Path
    label: str
    filename: str
    source: str
    width: int
    height: int


def load_dataset(root: str, class_names: list[str], source: str = "Original") -> list[DatasetImage]:
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
                    source=source,
                    width=width,
                    height=height,
                )
            )
    return images


def load_all_sources(class_names: list[str]) -> dict[str, list[DatasetImage]]:
    """Load every known dataset split, keyed by its source label."""
    return {
        source: load_dataset(root, class_names, source=source)
        for source, root in DATASET_SOURCES.items()
    }
