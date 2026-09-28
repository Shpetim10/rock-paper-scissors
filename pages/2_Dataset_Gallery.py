"""Dataset Gallery screen — explore the images used to train and test the RPS gesture classifier."""

from __future__ import annotations

import base64
import io
import sys
from pathlib import Path

if (_root := str(Path(__file__).resolve().parent.parent)) not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st
from PIL import Image

from game.classifier import CLASS_NAMES
from game.dataset import DatasetImage, load_all_sources
from game.theme import CLASS_COLORS, inject_theme, render_hero

SOURCE_TABS = [
    ("Original", "\U0001F4F7 Original"),
    ("Augmented", "\U0001FA84 Augmented"),
    ("Test", "\U0001F9EA Test Data"),
]

PAGE_CSS = """
.kpi-card { text-align: center; margin-bottom: 0.5rem; }
.kpi-value { font-size: 2.1rem; font-weight: 800; }
.kpi-label { font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.06em; margin-top: 0.2rem; }

.gallery-card { padding: 0; overflow: hidden; margin-bottom: 1.1rem; }
.gallery-card img { width: 100%; display: block; border-radius: 20px 20px 0 0; }
.gallery-card-body { padding: 0.8rem 0.9rem 0.5rem 0.9rem; }
.gallery-filename {
    font-size: 0.78rem;
    color: var(--text-muted);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin-top: 0.4rem;
}

.chart-row { display: flex; align-items: center; gap: 0.6rem; margin-top: 0.5rem; font-size: 0.85rem; }
.chart-label { width: 90px; text-transform: capitalize; color: var(--text-muted); }
.chart-track { flex: 1; height: 14px; border-radius: 7px; background: var(--card-bg-strong); overflow: hidden; display: flex; }
.chart-fill { height: 100%; }
.chart-count { width: 90px; text-align: right; color: var(--text-primary); font-weight: 600; }

.legend { display: flex; gap: 1.2rem; margin-top: 0.8rem; flex-wrap: wrap; }
.legend-item { display: flex; align-items: center; gap: 0.4rem; font-size: 0.8rem; color: var(--text-muted); }
.legend-dot { width: 10px; height: 10px; border-radius: 3px; }
"""

# Page config (title/icon/layout) is set once by the app.py entrypoint via
# st.navigation; this page only needs to inject its own CSS and content.


@st.cache_data(show_spinner=False)
def load_sources() -> dict[str, list[DatasetImage]]:
    return load_all_sources(CLASS_NAMES)


@st.cache_data(show_spinner=False)
def thumbnail_data_uri(path_str: str, max_size: int = 320) -> str:
    path = Path(path_str)
    with Image.open(path) as im:
        im = im.convert("RGB")
        im.thumbnail((max_size, max_size))
        buffer = io.BytesIO()
        im.save(buffer, format="JPEG", quality=80)
        encoded = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/jpeg;base64,{encoded}"


def render_kpis(all_images: list[DatasetImage], test_images: list[DatasetImage]) -> None:
    total = len(all_images)
    counts = {label: sum(1 for img in all_images if img.label == label) for label in CLASS_NAMES}

    cards = [
        ("Training Images", total, "#f1f1f6"),
        ("Rock", counts.get("rock", 0), CLASS_COLORS["rock"]),
        ("Paper", counts.get("paper", 0), CLASS_COLORS["paper"]),
        ("Scissors", counts.get("scissors", 0), CLASS_COLORS["scissors"]),
        ("Held-out Test Images", len(test_images), "#38bdf8"),
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


def source_badge_html(source: str) -> str:
    return f'<span class="badge badge-source-{source.lower()}">{source}</span>'


@st.dialog("Image Details")
def show_detail_dialog(img: DatasetImage) -> None:
    st.image(str(img.path), use_container_width=True)
    st.markdown(
        f"{badge_html(img.label)} &nbsp; {source_badge_html(img.source)}",
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
        | Source | {img.source} |
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
                            {badge_html(img.label)} {source_badge_html(img.source)}
                            <div class="gallery-filename" title="{img.filename}">{img.filename}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.markdown("</div>", unsafe_allow_html=True)
                    if st.button("View", key=f"view_{img.source}_{img.path.as_posix()}", use_container_width=True):
                        show_detail_dialog(img)


def render_distribution_chart(images: list[DatasetImage], title: str) -> None:
    total = len(images)
    counts = {label: sum(1 for img in images if img.label == label) for label in CLASS_NAMES}
    max_count = max(counts.values(), default=0) or 1

    st.markdown(f"**{title}**")
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


def render_split_chart(sources: dict[str, list[DatasetImage]]) -> None:
    st.markdown("**Dataset Split — Original vs. Augmented vs. Test**")
    split_colors = {"Original": "#4ade80", "Augmented": "#facc15", "Test": "#38bdf8"}
    for label in CLASS_NAMES:
        per_source = {name: sum(1 for img in imgs if img.label == label) for name, imgs in sources.items()}
        total = sum(per_source.values()) or 1
        st.markdown(f'<div class="chart-row"><div class="chart-label">{label.capitalize()}</div>'
                    f'<div class="chart-track">'
                    + "".join(
                        f'<div class="chart-fill" style="width:{(count / total) * 100}%; background:{split_colors[name]};"></div>'
                        for name, count in per_source.items()
                    )
                    + f'</div><div class="chart-count">{"/".join(str(c) for c in per_source.values())}</div></div>',
                    unsafe_allow_html=True)
    st.markdown(
        """
        <div class="legend">
            <div class="legend-item"><span class="legend-dot" style="background:#4ade80;"></span> Original</div>
            <div class="legend-item"><span class="legend-dot" style="background:#facc15;"></span> Augmented</div>
            <div class="legend-item"><span class="legend-dot" style="background:#38bdf8;"></span> Test</div>
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


def render_insights(sources: dict[str, list[DatasetImage]]) -> None:
    st.subheader("Dataset Insights")
    left, right = st.columns(2)
    with left:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        render_distribution_chart(sources["Original"], "Training Class Distribution")
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        render_split_chart(sources)
        st.markdown("</div>", unsafe_allow_html=True)
    st.write("")
    all_images = [img for imgs in sources.values() for img in imgs]
    render_sample_stats(all_images)


def main() -> None:
    inject_theme(PAGE_CSS)
    sources = load_sources()
    all_by_source = {name: imgs for name, imgs in sources.items()}

    render_hero("Dataset Gallery", "Explore the hand-gesture images used to train and test the Rock-Paper-Scissors model.")
    render_kpis(sources["Original"], sources["Test"])
    st.caption("Original and Augmented images are used for training; Test images are a held-out set never seen during training.")
    st.write("")

    st.subheader("Image Gallery")
    filter_col, search_col = st.columns([1, 2])
    with filter_col:
        category = st.selectbox("Category", ["All"] + [name.capitalize() for name in CLASS_NAMES])
    with search_col:
        search = st.text_input("Search by filename", placeholder="e.g. rock_01.jpg")

    def apply_filters(images: list[DatasetImage]) -> list[DatasetImage]:
        filtered = images
        if category != "All":
            filtered = [img for img in filtered if img.label == category.lower()]
        if search:
            needle = search.strip().lower()
            filtered = [img for img in filtered if needle in img.filename.lower()]
        return filtered

    tabs = st.tabs([label for _, label in SOURCE_TABS])
    for (source_key, _), tab in zip(SOURCE_TABS, tabs):
        with tab:
            filtered = apply_filters(all_by_source[source_key])
            st.caption(f"Showing {len(filtered)} of {len(all_by_source[source_key])} {source_key.lower()} images")
            render_gallery(filtered)

    st.write("")
    render_insights(sources)


if __name__ == "__main__":
    main()
