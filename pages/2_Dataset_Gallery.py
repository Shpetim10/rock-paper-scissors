"""Dataset Gallery screen — explore the images used to train the RPS gesture classifier."""

from __future__ import annotations

import base64
import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

import streamlit as st
from PIL import Image

from game.classifier import CLASS_NAMES

DATASET_ROOT = Path("datasets")
CLASS_COLORS = {"rock": "#7aa2ff", "paper": "#facc15", "scissors": "#ff6ec4"}
VAL_HOLDOUT = 0.2  # deterministic 80/20 split, no train/val folders exist on disk

st.set_page_config(
    page_title="Dataset Gallery",
    page_icon="\U0001F5BC️",
    layout="wide",
)


@dataclass
class DatasetImage:
    path: Path
    label: str
    filename: str
    split: str
    width: int
    height: int


def assign_split(filename: str) -> str:
    digest = hashlib.md5(filename.encode()).hexdigest()
    bucket = int(digest, 16) % 100
    return "Validation" if bucket < int(VAL_HOLDOUT * 100) else "Training"


@st.cache_data(show_spinner=False)
def load_dataset(_root: str) -> list[DatasetImage]:
    images: list[DatasetImage] = []
    for label in CLASS_NAMES:
        class_dir = Path(_root) / label
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
                    split=assign_split(entry),
                    width=width,
                    height=height,
                )
            )
    return images


@st.cache_data(show_spinner=False)
def thumbnail_data_uri(path_str: str, max_size: int = 320) -> str:
    path = Path(path_str)
    with Image.open(path) as im:
        im = im.convert("RGB")
        im.thumbnail((max_size, max_size))
        import io

        buffer = io.BytesIO()
        im.save(buffer, format="JPEG", quality=80)
        encoded = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/jpeg;base64,{encoded}"


def inject_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

        :root {
            --bg-grad-1: #2b1055;
            --bg-grad-2: #0f0c29;
            --bg-grad-3: #0a0a16;
            --text-primary: #f1f1f6;
            --text-muted: #b9b9d0;
            --card-bg: rgba(255, 255, 255, 0.06);
            --card-border: rgba(255, 255, 255, 0.12);
            --surface: #14122b;
        }
        @media (prefers-color-scheme: light) {
            :root {
                --bg-grad-1: #f5f3ff;
                --bg-grad-2: #eef2ff;
                --bg-grad-3: #ffffff;
                --text-primary: #1e1b2e;
                --text-muted: #5b5773;
                --card-bg: rgba(20, 18, 43, 0.04);
                --card-border: rgba(20, 18, 43, 0.1);
                --surface: #ffffff;
            }
        }

        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

        .stApp {
            background: radial-gradient(circle at 20% -10%, var(--bg-grad-1) 0%, var(--bg-grad-2) 45%, var(--bg-grad-3) 100%);
            color: var(--text-primary);
        }

        .hero { text-align: center; padding: 2.5rem 1rem 1rem 1rem; animation: fadeIn 0.8s ease; }
        .hero h1 {
            font-size: 2.6rem;
            font-weight: 800;
            margin: 0;
            background: linear-gradient(90deg, #ff6ec4, #7873f5, #4ade80);
            background-size: 200% auto;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: shimmer 6s linear infinite;
        }
        .hero p { font-size: 1.05rem; color: var(--text-muted); margin-top: 0.5rem; }

        .glass-card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 18px;
            padding: 1.1rem;
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .glass-card:hover { transform: translateY(-3px); box-shadow: 0 12px 40px rgba(0, 0, 0, 0.35); }

        .kpi-card { text-align: center; margin-bottom: 0.5rem; }
        .kpi-value { font-size: 2.1rem; font-weight: 800; }
        .kpi-label { font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.06em; margin-top: 0.2rem; }

        .gallery-card { padding: 0; overflow: hidden; margin-bottom: 1.1rem; }
        .gallery-card img { width: 100%; display: block; border-radius: 18px 18px 0 0; }
        .gallery-card-body { padding: 0.8rem 0.9rem 0.5rem 0.9rem; }
        .gallery-filename {
            font-size: 0.78rem;
            color: var(--text-muted);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            margin-top: 0.4rem;
        }

        .badge {
            display: inline-block;
            padding: 0.22rem 0.65rem;
            border-radius: 999px;
            font-size: 0.72rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        .badge-rock { background: rgba(122, 162, 255, 0.18); color: #7aa2ff; border: 1px solid #7aa2ff; }
        .badge-paper { background: rgba(250, 204, 21, 0.18); color: #facc15; border: 1px solid #facc15; }
        .badge-scissors { background: rgba(255, 110, 196, 0.18); color: #ff6ec4; border: 1px solid #ff6ec4; }
        .badge-split-training { background: rgba(74, 222, 128, 0.15); color: #4ade80; border: 1px solid #4ade80; }
        .badge-split-validation { background: rgba(122, 162, 255, 0.15); color: #7aa2ff; border: 1px solid #7aa2ff; }

        .chart-row { display: flex; align-items: center; gap: 0.6rem; margin-top: 0.5rem; font-size: 0.85rem; }
        .chart-label { width: 90px; text-transform: capitalize; color: var(--text-muted); }
        .chart-track { flex: 1; height: 14px; border-radius: 7px; background: var(--card-bg); overflow: hidden; display: flex; }
        .chart-fill { height: 100%; }
        .chart-count { width: 90px; text-align: right; color: var(--text-primary); font-weight: 600; }

        .legend { display: flex; gap: 1.2rem; margin-top: 0.8rem; flex-wrap: wrap; }
        .legend-item { display: flex; align-items: center; gap: 0.4rem; font-size: 0.8rem; color: var(--text-muted); }
        .legend-dot { width: 10px; height: 10px; border-radius: 3px; }

        @keyframes fadeIn { from { opacity: 0; transform: translateY(-8px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes shimmer { to { background-position: 200% center; } }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    st.markdown(
        """
        <div class="hero">
            <h1>Dataset Gallery</h1>
            <p>Explore the hand-gesture images used to train the Rock-Paper-Scissors model.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpis(images: list[DatasetImage]) -> None:
    total = len(images)
    counts = {label: sum(1 for img in images if img.label == label) for label in CLASS_NAMES}
    val_count = sum(1 for img in images if img.split == "Validation")
    train_count = total - val_count
    split_ratio = f"{train_count}/{val_count}" if total else "0/0"

    cards = [
        ("Total Images", total, "#f1f1f6"),
        ("Rock Images", counts.get("rock", 0), CLASS_COLORS["rock"]),
        ("Paper Images", counts.get("paper", 0), CLASS_COLORS["paper"]),
        ("Scissors Images", counts.get("scissors", 0), CLASS_COLORS["scissors"]),
        ("Train / Val Split", split_ratio, "#4ade80"),
    ]
    columns = st.columns(len(cards))
    for column, (label, value, color) in zip(columns, cards):
        with column:
            st.markdown(
                f"""
                <div class="glass-card kpi-card">
                    <div class="kpi-value" style="color:{color};">{value}</div>
                    <div class="kpi-label">{label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def badge_html(label: str) -> str:
    return f'<span class="badge badge-{label}">{label.capitalize()}</span>'


def split_badge_html(split: str) -> str:
    return f'<span class="badge badge-split-{split.lower()}">{split}</span>'


@st.dialog("Image Details")
def show_detail_dialog(img: DatasetImage) -> None:
    st.image(str(img.path), use_container_width=True)
    st.markdown(
        f"{badge_html(img.label)} &nbsp; {split_badge_html(img.split)}",
        unsafe_allow_html=True,
    )
    st.write("")
    st.markdown(
        f"""
        | Field | Value |
        |---|---|
        | Filename | `{img.filename}` |
        | Label | {img.label.capitalize()} |
        | Resolution | {img.width} × {img.height} px |
        | Dataset split | {img.split} |
        | Dataset location | `{img.path.as_posix()}` |
        """
    )


def render_gallery(images: list[DatasetImage]) -> None:
    if not images:
        st.info("No images match the current filters.")
        return

    columns_per_row = 4
    for row_start in range(0, len(images), columns_per_row):
        row_items = images[row_start : row_start + columns_per_row]
        columns = st.columns(columns_per_row)
        for column, img in zip(columns, row_items):
            with column:
                with st.container():
                    st.markdown('<div class="glass-card gallery-card">', unsafe_allow_html=True)
                    st.markdown(
                        f'<img src="{thumbnail_data_uri(str(img.path))}" alt="{img.filename}"/>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f"""
                        <div class="gallery-card-body">
                            {badge_html(img.label)} {split_badge_html(img.split)}
                            <div class="gallery-filename" title="{img.filename}">{img.filename}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.markdown("</div>", unsafe_allow_html=True)
                    if st.button("View", key=f"view_{img.path.as_posix()}", use_container_width=True):
                        show_detail_dialog(img)


def render_distribution_chart(images: list[DatasetImage]) -> None:
    total = len(images)
    counts = {label: sum(1 for img in images if img.label == label) for label in CLASS_NAMES}
    max_count = max(counts.values(), default=0) or 1

    st.markdown("**Class Distribution**")
    for label in CLASS_NAMES:
        count = counts.get(label, 0)
        pct = (count / max_count) * 100
        color = CLASS_COLORS[label]
        st.markdown(
            f"""
            <div class="chart-row">
                <div class="chart-label">{label.capitalize()}</div>
                <div class="chart-track"><div class="chart-fill" style="width:{pct}%; background:{color};"></div></div>
                <div class="chart-count">{count} ({(count / total * 100) if total else 0:.0f}%)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_balance_chart(images: list[DatasetImage]) -> None:
    st.markdown("**Dataset Balance — Training vs. Validation**")
    for label in CLASS_NAMES:
        class_images = [img for img in images if img.label == label]
        total = len(class_images)
        train = sum(1 for img in class_images if img.split == "Training")
        val = total - train
        train_pct = (train / total * 100) if total else 0
        val_pct = 100 - train_pct if total else 0
        st.markdown(
            f"""
            <div class="chart-row">
                <div class="chart-label">{label.capitalize()}</div>
                <div class="chart-track">
                    <div class="chart-fill" style="width:{train_pct}%; background:#4ade80;"></div>
                    <div class="chart-fill" style="width:{val_pct}%; background:#7aa2ff;"></div>
                </div>
                <div class="chart-count">{train} / {val}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown(
        """
        <div class="legend">
            <div class="legend-item"><span class="legend-dot" style="background:#4ade80;"></span> Training</div>
            <div class="legend-item"><span class="legend-dot" style="background:#7aa2ff;"></span> Validation</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sample_stats(images: list[DatasetImage]) -> None:
    st.markdown("**Sample Statistics**")
    if not images:
        st.caption("No images loaded.")
        return
    widths = [img.width for img in images]
    heights = [img.height for img in images]
    avg_w = sum(widths) / len(widths)
    avg_h = sum(heights) / len(heights)
    unique_res = {(img.width, img.height) for img in images}

    stat_cols = st.columns(3)
    stats = [
        ("Avg. Resolution", f"{avg_w:.0f} × {avg_h:.0f}"),
        ("Unique Resolutions", len(unique_res)),
        ("Total Images", len(images)),
    ]
    for column, (label, value) in zip(stat_cols, stats):
        with column:
            st.markdown(
                f"""
                <div class="glass-card kpi-card">
                    <div class="kpi-value" style="font-size:1.5rem;">{value}</div>
                    <div class="kpi-label">{label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_insights(images: list[DatasetImage]) -> None:
    st.subheader("Dataset Insights")
    left, right = st.columns(2)
    with left:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        render_distribution_chart(images)
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        render_balance_chart(images)
        st.markdown("</div>", unsafe_allow_html=True)
    st.write("")
    render_sample_stats(images)


def main() -> None:
    inject_css()
    all_images = load_dataset(str(DATASET_ROOT))

    render_header()
    render_kpis(all_images)
    st.write("")

    st.subheader("Image Gallery")
    filter_col, search_col = st.columns([1, 2])
    with filter_col:
        category = st.selectbox("Category", ["All"] + [name.capitalize() for name in CLASS_NAMES])
    with search_col:
        search = st.text_input("Search by filename", placeholder="e.g. rock_01.jpg")

    filtered = all_images
    if category != "All":
        filtered = [img for img in filtered if img.label == category.lower()]
    if search:
        needle = search.strip().lower()
        filtered = [img for img in filtered if needle in img.filename.lower()]

    st.caption(f"Showing {len(filtered)} of {len(all_images)} images")
    render_gallery(filtered)

    st.write("")
    render_insights(all_images)


if __name__ == "__main__":
    main()
