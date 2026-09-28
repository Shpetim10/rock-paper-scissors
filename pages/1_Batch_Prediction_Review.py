"""Batch Prediction & Human Review screen for the RPS gesture classifier."""

from __future__ import annotations

import csv
import hashlib
import io
import sys
from dataclasses import dataclass, field
from pathlib import Path

if (_root := str(Path(__file__).resolve().parent.parent)) not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st
from PIL import Image

from game.classifier import CLASS_NAMES, GestureClassifier
from game.theme import inject_theme, render_hero

# Page config (title/icon/layout) is set once by the app.py entrypoint via
# st.navigation; this page only needs to inject its own CSS and content.


@st.cache_resource
def get_classifier() -> GestureClassifier:
    return GestureClassifier()


@dataclass
class ReviewItem:
    item_id: str
    name: str
    image_bytes: bytes
    predicted_label: str
    confidence: float
    probabilities: dict
    is_mock: bool
    feedback_status: str | None = None  # "correct" | "incorrect" | None
    true_label: str | None = None

    @property
    def reviewed(self) -> bool:
        return self.feedback_status == "correct" or (
            self.feedback_status == "incorrect" and self.true_label is not None
        )


def init_state() -> None:
    if "batch_items" not in st.session_state:
        st.session_state.batch_items = []  # list[ReviewItem]
    if "batch_report" not in st.session_state:
        st.session_state.batch_report = None


PAGE_CSS = """
.prob-row { display: flex; align-items: center; gap: 0.5rem; margin-top: 0.3rem; font-size: 0.78rem; }
.prob-label { width: 60px; text-transform: capitalize; color: var(--text-muted); }
.prob-track { flex: 1; height: 8px; border-radius: 6px; background: var(--card-bg-strong); overflow: hidden; }
.prob-fill { height: 100%; border-radius: 6px; background: linear-gradient(90deg, var(--accent-2), var(--accent-3)); }
.prob-pct { width: 40px; text-align: right; color: var(--text-primary); }

.badge-correct { background: rgba(74, 222, 128, 0.16); color: #22a35a; border: 1px solid #4ade80; }
.badge-incorrect { background: rgba(248, 113, 113, 0.16); color: #d64545; border: 1px solid #f87171; }

.progress-wrap { margin: 1rem 0; }
.progress-track { width: 100%; height: 14px; border-radius: 8px; background: var(--card-bg-strong); overflow: hidden; }
.progress-fill { height: 100%; border-radius: 8px; background: linear-gradient(90deg, var(--accent-3), var(--accent-2)); transition: width 0.4s ease; }
.progress-text { text-align: center; margin-top: 0.4rem; color: var(--text-muted); font-size: 0.9rem; }

.gauge-wrap { display: flex; flex-direction: column; align-items: center; gap: 0.6rem; }
.gauge {
    width: 180px; height: 180px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    background: conic-gradient(var(--accent-3) calc(var(--pct) * 1%), var(--card-bg-strong) 0);
}
.gauge-inner {
    width: 140px; height: 140px; border-radius: 50%;
    background: var(--surface);
    display: flex; flex-direction: column; align-items: center; justify-content: center;
}
.gauge-value { font-size: 2rem; font-weight: 800; color: var(--accent-3); }
.gauge-label { font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }

.stat-value { font-size: 2rem; font-weight: 800; }
.stat-label { font-size: 0.85rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.06em; }

.cm-table { width: 100%; border-collapse: collapse; text-align: center; }
.cm-table th, .cm-table td { padding: 0.6rem; border: 1px solid var(--card-border); }
.cm-table th { color: var(--text-muted); font-weight: 700; text-transform: capitalize; }
"""


def badge_html(label: str) -> str:
    return f'<span class="badge badge-{label}">{label.capitalize()}</span>'


def prob_bars_html(probabilities: dict) -> str:
    rows = []
    for name in CLASS_NAMES:
        pct = round(probabilities.get(name, 0.0) * 100, 1)
        rows.append(
            f"""
            <div class="prob-row">
                <div class="prob-label">{name}</div>
                <div class="prob-track"><div class="prob-fill" style="width:{pct}%;"></div></div>
                <div class="prob-pct">{pct}%</div>
            </div>
            """
        )
    return "".join(rows)


def make_item_id(name: str, data: bytes) -> str:
    return hashlib.md5(name.encode() + data).hexdigest()


def ingest_uploads(uploaded_files, classifier: GestureClassifier) -> None:
    existing_ids = {item.item_id for item in st.session_state.batch_items}
    for uploaded in uploaded_files or []:
        data = uploaded.getvalue()
        item_id = make_item_id(uploaded.name, data)
        if item_id in existing_ids:
            continue
        image = Image.open(io.BytesIO(data))
        probabilities, is_mock = classifier.predict_proba(image)
        predicted_label = max(probabilities, key=probabilities.get)
        st.session_state.batch_items.append(
            ReviewItem(
                item_id=item_id,
                name=uploaded.name,
                image_bytes=data,
                predicted_label=predicted_label,
                confidence=probabilities[predicted_label],
                probabilities=probabilities,
                is_mock=is_mock,
            )
        )


def render_capture_tab(classifier: GestureClassifier) -> None:
    if "batch_camera_key" not in st.session_state:
        st.session_state.batch_camera_key = 0

    photo = st.camera_input(
        "Take a photo of your hand gesture",
        key=f"batch_camera_{st.session_state.batch_camera_key}",
    )
    if photo is not None:
        ingest_uploads([photo], classifier)
        st.session_state.batch_camera_key += 1
        st.rerun()


def render_progress() -> None:
    items = st.session_state.batch_items
    total = len(items)
    reviewed = sum(1 for item in items if item.reviewed)
    pct = int((reviewed / total) * 100) if total else 0
    st.markdown(
        f"""
        <div class="progress-wrap">
            <div class="progress-track"><div class="progress-fill" style="width:{pct}%;"></div></div>
            <div class="progress-text">{reviewed} / {total} images reviewed</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    return reviewed, total


def render_card(item: ReviewItem) -> None:
    with st.container():
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.image(item.image_bytes, use_container_width=True)
        st.markdown(
            f"{badge_html(item.predicted_label)} &nbsp; "
            f"<span style='color:var(--text-muted); font-size:0.85rem;'>{round(item.confidence * 100, 1)}% confidence</span>",
            unsafe_allow_html=True,
        )
        if item.is_mock:
            st.caption("Mock prediction — no trained model found.")
        st.markdown(prob_bars_html(item.probabilities), unsafe_allow_html=True)

        st.write("")
        col_correct, col_incorrect = st.columns(2)
        with col_correct:
            if st.button("Correct", key=f"correct_{item.item_id}", use_container_width=True):
                item.feedback_status = "correct"
                item.true_label = item.predicted_label
                st.rerun()
        with col_incorrect:
            if st.button("Incorrect", key=f"incorrect_{item.item_id}", use_container_width=True):
                item.feedback_status = "incorrect"
                item.true_label = None
                st.rerun()

        if item.feedback_status == "correct":
            st.markdown('<span class="badge badge-correct">Correct</span>', unsafe_allow_html=True)
        elif item.feedback_status == "incorrect":
            choice = st.radio(
                "What was the actual gesture?",
                CLASS_NAMES,
                index=None,
                key=f"true_label_{item.item_id}",
                horizontal=True,
            )
            if choice is not None:
                item.true_label = choice
            st.markdown('<span class="badge badge-incorrect">Incorrect</span>', unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)


def render_grid() -> None:
    items = st.session_state.batch_items
    columns_per_row = 4
    for row_start in range(0, len(items), columns_per_row):
        row_items = items[row_start : row_start + columns_per_row]
        columns = st.columns(columns_per_row)
        for column, item in zip(columns, row_items):
            with column:
                render_card(item)


def build_confusion_matrix(items: list[ReviewItem]) -> dict:
    matrix = {true: {pred: 0 for pred in CLASS_NAMES} for true in CLASS_NAMES}
    for item in items:
        matrix[item.true_label][item.predicted_label] += 1
    return matrix


def render_confusion_matrix(matrix: dict) -> None:
    max_value = max((v for row in matrix.values() for v in row.values()), default=0) or 1
    header = "".join(f"<th>{name}</th>" for name in CLASS_NAMES)
    rows_html = ""
    for true_label in CLASS_NAMES:
        cells = ""
        for pred_label in CLASS_NAMES:
            value = matrix[true_label][pred_label]
            intensity = value / max_value
            color = f"rgba(74, 222, 128, {0.15 + 0.65 * intensity})" if true_label == pred_label else f"rgba(248, 113, 113, {0.1 + 0.5 * intensity})"
            cells += f'<td style="background:{color};">{value}</td>'
        rows_html += f"<tr><th>{true_label}</th>{cells}</tr>"
    st.markdown(
        f"""
        <table class="cm-table">
            <tr><th>True \\ Predicted</th>{header}</tr>
            {rows_html}
        </table>
        """,
        unsafe_allow_html=True,
    )


def render_gauge(accuracy_pct: float) -> None:
    st.markdown(
        f"""
        <div class="gauge-wrap">
            <div class="gauge" style="--pct:{accuracy_pct};">
                <div class="gauge-inner">
                    <div class="gauge-value">{accuracy_pct:.1f}%</div>
                    <div class="gauge-label">Accuracy</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def build_report_csv(items: list[ReviewItem]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["file_name", "predicted_label", "confidence", "true_label", "correct"])
    for item in items:
        writer.writerow(
            [
                item.name,
                item.predicted_label,
                f"{item.confidence:.4f}",
                item.true_label,
                item.predicted_label == item.true_label,
            ]
        )
    return buffer.getvalue().encode("utf-8")


def render_accuracy_section() -> None:
    items = st.session_state.batch_items
    if st.button("Calculate Prediction Accuracy", type="primary", use_container_width=True):
        correct = sum(1 for item in items if item.predicted_label == item.true_label)
        total = len(items)
        st.session_state.batch_report = {
            "total": total,
            "correct": correct,
            "incorrect": total - correct,
            "accuracy": (correct / total * 100) if total else 0.0,
            "matrix": build_confusion_matrix(items),
        }

    report = st.session_state.batch_report
    if not report:
        return

    st.write("")
    st.subheader("Accuracy Report")
    stat_cols = st.columns(4)
    stats = [
        ("Total Images", report["total"]),
        ("Correct Predictions", report["correct"]),
        ("Incorrect Predictions", report["incorrect"]),
        ("Accuracy %", f"{report['accuracy']:.1f}%"),
    ]
    for column, (label, value) in zip(stat_cols, stats):
        with column:
            st.markdown(
                f"""
                <div class="glass-card" style="text-align:center;">
                    <div class="stat-label">{label}</div>
                    <div class="stat-value">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.write("")
    matrix_col, gauge_col = st.columns([2, 1])
    with matrix_col:
        st.markdown("**Confusion Matrix** (rows = true label, columns = predicted)")
        render_confusion_matrix(report["matrix"])
    with gauge_col:
        render_gauge(report["accuracy"])

    st.write("")
    st.download_button(
        "Download Review Report",
        data=build_report_csv(st.session_state.batch_items),
        file_name="batch_review_report.csv",
        mime="text/csv",
        use_container_width=True,
    )


def main() -> None:
    init_state()
    inject_theme(PAGE_CSS)
    classifier = get_classifier()

    render_hero("Batch Gesture Classification", "Upload multiple hand gesture images and review AI predictions.")

    upload_tab, camera_tab = st.tabs(["Upload Files", "Take Photo"])
    with upload_tab:
        uploaded_files = st.file_uploader(
            "Drag and drop hand gesture images here, or click to browse",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=True,
        )
        ingest_uploads(uploaded_files, classifier)
    with camera_tab:
        render_capture_tab(classifier)

    if not st.session_state.batch_items:
        st.info("Upload one or more images to get started.")
        return

    top_left, top_right = st.columns([3, 1])
    with top_right:
        if st.button("Clear All", use_container_width=True):
            st.session_state.batch_items = []
            st.session_state.batch_report = None
            st.rerun()

    reviewed, total = render_progress()
    st.write("")
    render_grid()

    st.write("")
    if reviewed == total and total > 0:
        render_accuracy_section()
    else:
        st.info(f"Provide feedback for all images to unlock accuracy evaluation ({reviewed}/{total} done).")


if __name__ == "__main__":
    main()
