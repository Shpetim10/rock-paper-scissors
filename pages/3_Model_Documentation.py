"""Model Documentation screen — renders README.md as an interactive docs portal."""

from __future__ import annotations

import hashlib
import random
import re
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st
from PIL import Image

from game.classifier import CLASS_NAMES, GestureClassifier, IMAGE_SIZE, MODEL_PATH

README_PATH = Path("README.md")
DATASET_ROOT = Path("datasets")
CLASS_COLORS = {"rock": "#7aa2ff", "paper": "#facc15", "scissors": "#ff6ec4"}

st.set_page_config(
    page_title="Model Documentation",
    page_icon="\U0001F4DA",
    layout="wide",
)

NAV_SECTIONS = [
    ("overview", "Overview"),
    ("dataset", "Dataset"),
    ("architecture", "Model Architecture"),
    ("training", "Training Process"),
    ("evaluation", "Evaluation Results"),
    ("usage", "Usage Instructions"),
    ("future", "Future Improvements"),
]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


@st.cache_data(show_spinner=False)
def load_readme(_path: str) -> str:
    path = Path(_path)
    return path.read_text() if path.exists() else "# README not found"


@st.cache_data(show_spinner=False)
def dataset_counts(_root: str) -> dict[str, int]:
    counts = {}
    for label in CLASS_NAMES:
        class_dir = Path(_root) / label
        counts[label] = len(list(class_dir.glob("*"))) if class_dir.is_dir() else 0
    return counts


@st.cache_data(show_spinner=False)
def sample_images(_root: str, per_class: int = 1) -> list[tuple[str, Path]]:
    samples = []
    for label in CLASS_NAMES:
        class_dir = Path(_root) / label
        if not class_dir.is_dir():
            continue
        files = sorted(p for p in class_dir.iterdir() if p.is_file())
        samples.extend((label, p) for p in files[:per_class])
    return samples


@st.cache_data(show_spinner=False)
def mock_training_history(seed: int = 42, epochs: int = 30) -> pd.DataFrame:
    """Deterministic, illustrative training curves used until a real model is trained."""
    rng = random.Random(seed)
    rows = []
    train_acc, val_acc, train_loss, val_loss = 0.42, 0.38, 1.05, 1.15
    for epoch in range(1, epochs + 1):
        train_acc = min(0.995, train_acc + rng.uniform(0.01, 0.035))
        val_acc = min(0.97, val_acc + rng.uniform(0.008, 0.03))
        train_loss = max(0.02, train_loss * rng.uniform(0.85, 0.95))
        val_loss = max(0.05, val_loss * rng.uniform(0.87, 0.97))
        rows.append(
            {
                "Epoch": epoch,
                "Training Accuracy": round(train_acc, 4),
                "Validation Accuracy": round(val_acc, 4),
                "Training Loss": round(train_loss, 4),
                "Validation Loss": round(val_loss, 4),
            }
        )
    return pd.DataFrame(rows)


@st.cache_data(show_spinner=False)
def mock_confusion_matrix(seed: int = 42) -> pd.DataFrame:
    rng = random.Random(seed)
    rows = []
    for true_label in CLASS_NAMES:
        total = dataset_counts(str(DATASET_ROOT)).get(true_label, 80)
        correct_share = rng.uniform(0.86, 0.96)
        correct = int(total * correct_share)
        remainder = total - correct
        others = [c for c in CLASS_NAMES if c != true_label]
        split = remainder // 2
        errors = {others[0]: split, others[1]: remainder - split}
        for pred_label in CLASS_NAMES:
            count = correct if pred_label == true_label else errors[pred_label]
            rows.append({"Actual": true_label, "Predicted": pred_label, "Count": count})
    return pd.DataFrame(rows)


def mock_precision_recall_f1(cm: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for label in CLASS_NAMES:
        tp = cm[(cm.Actual == label) & (cm.Predicted == label)]["Count"].sum()
        fp = cm[(cm.Actual != label) & (cm.Predicted == label)]["Count"].sum()
        fn = cm[(cm.Actual == label) & (cm.Predicted != label)]["Count"].sum()
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        rows.append(
            {
                "Class": label.capitalize(),
                "Precision": round(precision, 3),
                "Recall": round(recall, 3),
                "F1 Score": round(f1, 3),
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------


def inject_css(theme: str) -> None:
    if theme == "light":
        bg = "radial-gradient(circle at 20% -10%, #eef1ff 0%, #f7f8fc 45%, #ffffff 100%)"
        text = "#1a1a2e"
        muted = "#5c5c74"
        card_bg = "rgba(20, 20, 40, 0.04)"
        card_border = "rgba(20, 20, 40, 0.10)"
        sidebar_bg = "rgba(20, 20, 40, 0.03)"
        code_bg = "rgba(20, 20, 40, 0.06)"
    else:
        bg = "radial-gradient(circle at 20% -10%, #2b1055 0%, #0f0c29 45%, #0a0a16 100%)"
        text = "#f1f1f6"
        muted = "#b9b9d0"
        card_bg = "rgba(255, 255, 255, 0.06)"
        card_border = "rgba(255, 255, 255, 0.12)"
        sidebar_bg = "rgba(255, 255, 255, 0.03)"
        code_bg = "rgba(255, 255, 255, 0.07)"

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

        html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}

        .stApp {{ background: {bg}; color: {text}; }}

        section[data-testid="stSidebar"] {{ background: {sidebar_bg}; }}
        section[data-testid="stSidebar"] a {{
            display: block;
            padding: 0.45rem 0.7rem;
            margin-bottom: 0.15rem;
            border-radius: 10px;
            color: {text};
            text-decoration: none;
            font-weight: 600;
            font-size: 0.92rem;
            transition: background 0.2s ease;
        }}
        section[data-testid="stSidebar"] a:hover {{
            background: {card_border};
        }}

        .doc-hero {{
            text-align: center;
            padding: 2.2rem 1rem 1.4rem 1rem;
            animation: fadeIn 0.8s ease;
        }}
        .doc-hero h1 {{
            font-size: 2.6rem;
            font-weight: 800;
            margin: 0;
            background: linear-gradient(90deg, #ff6ec4, #7873f5, #4ade80);
            background-size: 200% auto;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: shimmer 6s linear infinite;
        }}
        .doc-hero p {{ font-size: 1.05rem; color: {muted}; margin-top: 0.5rem; }}

        .badge-row {{ display: flex; gap: 0.6rem; justify-content: center; flex-wrap: wrap; margin-top: 1rem; }}
        .doc-badge {{
            padding: 0.35rem 0.9rem;
            border-radius: 999px;
            font-size: 0.82rem;
            font-weight: 700;
            border: 1px solid {card_border};
            background: {card_bg};
        }}
        .badge-status {{ color: #4ade80; border-color: rgba(74, 222, 128, 0.5); }}
        .badge-version {{ color: #7873f5; border-color: rgba(120, 115, 245, 0.5); }}
        .badge-date {{ color: #facc15; border-color: rgba(250, 204, 21, 0.5); }}

        .glass-card {{
            background: {card_bg};
            border: 1px solid {card_border};
            border-radius: 18px;
            padding: 1.3rem 1.5rem;
            margin-bottom: 1rem;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        .glass-card:hover {{ transform: translateY(-2px); }}

        .callout {{
            border-radius: 14px;
            padding: 0.9rem 1.1rem;
            margin: 0.8rem 0;
            border-left: 4px solid;
            font-size: 0.95rem;
        }}
        .callout-info {{ background: rgba(120, 115, 245, 0.10); border-color: #7873f5; }}
        .callout-warning {{ background: rgba(250, 204, 21, 0.10); border-color: #facc15; }}
        .callout-success {{ background: rgba(74, 222, 128, 0.10); border-color: #4ade80; }}
        .callout-tip {{ background: rgba(255, 110, 196, 0.10); border-color: #ff6ec4; }}

        .metric-tile {{
            text-align: center;
            padding: 1rem 0.6rem;
            border-radius: 16px;
            background: {card_bg};
            border: 1px solid {card_border};
        }}
        .metric-tile .value {{ font-size: 1.7rem; font-weight: 800; }}
        .metric-tile .label {{
            font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.06em; color: {muted};
        }}

        .flow-diagram {{ display: flex; align-items: center; gap: 0.4rem; flex-wrap: wrap; justify-content: center; padding: 1rem 0; }}
        .flow-box {{
            padding: 0.8rem 1.1rem;
            border-radius: 14px;
            background: {card_bg};
            border: 1px solid {card_border};
            font-weight: 700;
            font-size: 0.85rem;
            text-align: center;
            min-width: 110px;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        .flow-box:hover {{ transform: scale(1.06); box-shadow: 0 6px 22px rgba(120, 115, 245, 0.35); }}
        .flow-arrow {{ font-size: 1.3rem; color: {muted}; }}

        code {{ background: {code_bg} !important; }}

        h2, h3 {{ scroll-margin-top: 1.5rem; }}

        div[data-testid="stDataFrame"] {{ border-radius: 14px; overflow: hidden; }}

        @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(-8px); }} to {{ opacity: 1; transform: translateY(0); }} }}
        @keyframes shimmer {{ to {{ background-position: 200% center; }} }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def callout(kind: str, icon: str, text: str) -> None:
    st.markdown(
        f'<div class="callout callout-{kind}">{icon} {text}</div>',
        unsafe_allow_html=True,
    )


def section_anchor(anchor_id: str) -> None:
    st.markdown(f'<div id="{anchor_id}"></div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Section renderers
# ---------------------------------------------------------------------------


def render_hero(is_mock: bool) -> None:
    status = "Awaiting Training" if is_mock else "Trained & Deployed"
    st.markdown(
        f"""
        <div class="doc-hero">
            <h1>\U0001F4DA Model Documentation</h1>
            <p>Rock-Paper-Scissors Gesture Classifier &mdash; an interactive guide to the dataset,
            architecture, training process, and evaluation results behind the game.</p>
            <div class="badge-row">
                <span class="doc-badge badge-version">Version 1.0.0</span>
                <span class="doc-badge badge-status">{status}</span>
                <span class="doc-badge badge-date">Docs updated 2026-09-26</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(search_query: str) -> str:
    with st.sidebar:
        st.markdown("### \U0001F4D6 Documentation")
        query = st.text_input("Search docs", value=search_query, placeholder="Search sections, code, terms...")
        st.markdown("---")
        for anchor_id, label in NAV_SECTIONS:
            st.markdown(f'<a href="#{anchor_id}">{label}</a>', unsafe_allow_html=True)
        st.markdown("---")
        theme = st.radio("Theme", ["Dark", "Light"], horizontal=True, key="doc_theme_radio")
        st.session_state["doc_theme"] = theme.lower()
        st.download_button(
            "\U0001F4E5 Download README",
            data=load_readme(str(README_PATH)),
            file_name="README.md",
            mime="text/markdown",
            use_container_width=True,
        )
    return query


def matches_query(text: str, query: str) -> bool:
    return not query or query.lower() in text.lower()


def render_overview(readme_text: str, query: str) -> None:
    section_anchor("overview")
    st.markdown("## Overview")
    match = re.search(r"# Rock-Paper-Scissors Dataset\n(.*?)(?=\n## )", readme_text, re.DOTALL)
    intro = match.group(1).strip() if match else "This project trains a gesture classifier for Rock, Paper, Scissors."
    if matches_query(intro, query):
        st.markdown(intro)
    with st.expander("\U0001F4A1 What is this project?", expanded=False):
        st.write(
            "A hand-gesture image classifier that recognizes Rock, Paper, or Scissors from a "
            "photo, powering a real-time browser game (`app.py`) and a batch review tool "
            "(`pages/1_Batch_Prediction_Review.py`)."
        )
    callout("info", "ℹ️", "This page renders the project's `README.md` as a searchable, navigable documentation portal.")


def render_dataset_section(readme_text: str, query: str) -> None:
    section_anchor("dataset")
    st.markdown("## Dataset")
    counts = dataset_counts(str(DATASET_ROOT))
    total = sum(counts.values())

    cols = st.columns(len(CLASS_NAMES) + 1)
    for col, label in zip(cols[:-1], CLASS_NAMES):
        with col:
            st.markdown(
                f"""
                <div class="metric-tile">
                    <div class="value" style="color:{CLASS_COLORS[label]}">{counts.get(label, 0)}</div>
                    <div class="label">{label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    with cols[-1]:
        st.markdown(
            f"""
            <div class="metric-tile">
                <div class="value">{total}</div>
                <div class="label">Total Images</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")
    df = pd.DataFrame(
        [{"Class": label.capitalize(), "Images": count} for label, count in counts.items()]
        + [{"Class": "Total", "Images": total}]
    )
    st.caption("Click a column header to sort.")
    st.dataframe(df, use_container_width=True, hide_index=True)

    with st.expander("\U0001F3A8 Dataset diversity & augmentation", expanded=False):
        section = re.search(r"## Dataset Diversity(.*?)## Data Augmentation(.*?)(?=\n## |\Z)", readme_text, re.DOTALL)
        if section and matches_query(section.group(0), query):
            st.markdown("### Diversity")
            st.markdown(section.group(1).strip())
            st.markdown("### Augmentation")
            st.markdown(section.group(2).strip())

    samples = sample_images(str(DATASET_ROOT), per_class=1)
    if samples:
        st.markdown("**Sample images per class**")
        img_cols = st.columns(len(samples))
        for col, (label, path) in zip(img_cols, samples):
            with col:
                st.image(str(path), caption=label.capitalize(), use_container_width=True)


def render_architecture_section(is_mock: bool) -> None:
    section_anchor("architecture")
    st.markdown("## Model Architecture")
    callout(
        "info",
        "\U0001F3D7️",
        f"Built with **TensorFlow / Keras** on top of a **MobileNetV2** (alpha=0.35) feature "
        f"extractor, trained with Google's Teachable Machine. Input images are resized to "
        f"**{IMAGE_SIZE[0]}×{IMAGE_SIZE[1]}** pixels across **{len(CLASS_NAMES)} classes**: "
        f"{', '.join(c.capitalize() for c in CLASS_NAMES)}.",
    )
    st.markdown(
        """
        <div class="flow-diagram">
            <div class="flow-box">Input Image<br>224&times;224&times;3</div>
            <div class="flow-arrow">&rarr;</div>
            <div class="flow-box">MobileNetV2<br>(alpha=0.35)<br>feature extractor</div>
            <div class="flow-arrow">&rarr;</div>
            <div class="flow-box">Global Average<br>Pooling</div>
            <div class="flow-arrow">&rarr;</div>
            <div class="flow-box">Dense(100)<br>+ ReLU</div>
            <div class="flow-arrow">&rarr;</div>
            <div class="flow-box">Softmax<br>3 classes</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.expander("\U0001F4C4 Classifier interface (game/classifier.py)", expanded=False):
        st.code(
            '''MODEL_PATH = os.environ.get("RPS_MODEL_PATH", "model/rps_model.keras")
LABELS_PATH = os.environ.get("RPS_LABELS_PATH", "model/labels.txt")
IMAGE_SIZE = (224, 224)
CLASS_NAMES = ["rock", "paper", "scissors"]  # loaded from labels.txt

class GestureClassifier:
    def predict(self, image: Image.Image) -> Prediction:
        probabilities, is_mock = self.predict_proba(image)
        label = max(probabilities, key=probabilities.get)
        return Prediction(label=label, confidence=probabilities[label], is_mock=is_mock)''',
            language="python",
        )
    if is_mock:
        callout(
            "warning",
            "⚠️",
            f"No trained weights were found at `{MODEL_PATH}`. The architecture above is "
            "illustrative until a trained model is committed.",
        )
    else:
        callout(
            "success",
            "✅",
            f"Trained weights loaded from `{MODEL_PATH}`. The architecture above reflects the "
            "actual model in use.",
        )


def render_training_section(is_mock: bool) -> None:
    section_anchor("training")
    st.markdown("## Training Process")
    st.markdown(
        "Images are loaded from `datasets/` (247 originals) and `augmented_dataset/` "
        "(494 images including augmentations), resized to 224×224, and normalized to `[-1, 1]` "
        "before being split into training and validation sets. The model was trained with "
        "[Google Teachable Machine](https://teachablemachine.withgoogle.com/), which fine-tunes "
        "a MobileNetV2 classification head on the uploaded dataset and exports a Keras `.h5` "
        "checkpoint (converted here to the native Keras 3 format for compatibility)."
    )
    with st.expander("⚙️ Augmentation pipeline (Pillow)", expanded=False):
        st.code(
            """# Randomly applied per image, generating one augmented version per original:
# - Horizontal flip: 50% probability
# - Rotation: -15deg to +15deg
# - Brightness: 85% - 115%
# - Contrast: 85% - 115%
# - Random crop/zoom: 90% - 100% of original area, then resized back""",
            language="python",
        )
    st.markdown("### Training Curves")
    if is_mock:
        callout("warning", "\U0001F9EA", "No trained model was found. The curves below are **simulated** to illustrate the documentation layout.")
    else:
        callout("info", "\U00002139\U0000FE0F", "Teachable Machine does not export per-epoch training history, so the curves below are **simulated** to illustrate the documentation layout.")
    history = mock_training_history()
    acc_df = history.set_index("Epoch")[["Training Accuracy", "Validation Accuracy"]]
    loss_df = history.set_index("Epoch")[["Training Loss", "Validation Loss"]]
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Accuracy**")
        st.line_chart(acc_df)
    with col_b:
        st.markdown("**Loss**")
        st.line_chart(loss_df)


def render_evaluation_section(query: str, is_mock: bool) -> None:
    section_anchor("evaluation")
    st.markdown("## Evaluation Results")
    cm = mock_confusion_matrix()
    metrics_df = mock_precision_recall_f1(cm)
    overall_accuracy = (cm[cm.Actual == cm.Predicted]["Count"].sum()) / cm["Count"].sum()

    tiles = [
        ("Framework", "TensorFlow / Keras"),
        ("Classes", str(len(CLASS_NAMES))),
        ("Dataset Size", "494 (augmented)"),
        ("Accuracy", f"{overall_accuracy * 100:.1f}%"),
        ("Precision", f"{metrics_df['Precision'].mean() * 100:.1f}%"),
        ("Recall", f"{metrics_df['Recall'].mean() * 100:.1f}%"),
        ("F1 Score", f"{metrics_df['F1 Score'].mean() * 100:.1f}%"),
    ]
    cols = st.columns(len(tiles))
    for col, (label, value) in zip(cols, tiles):
        with col:
            st.markdown(
                f"""
                <div class="metric-tile">
                    <div class="value">{value}</div>
                    <div class="label">{label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.write("")
    st.markdown("### Confusion Matrix")
    heatmap = (
        alt.Chart(cm)
        .mark_rect()
        .encode(
            x=alt.X("Predicted:N", title="Predicted"),
            y=alt.Y("Actual:N", title="Actual"),
            color=alt.Color("Count:Q", scale=alt.Scale(scheme="purples")),
            tooltip=["Actual", "Predicted", "Count"],
        )
        .properties(height=280)
    )
    text = (
        alt.Chart(cm)
        .mark_text(baseline="middle")
        .encode(x="Predicted:N", y="Actual:N", text="Count:Q", color=alt.value("white"))
    )
    st.altair_chart(heatmap + text, use_container_width=True)

    st.markdown("### Precision / Recall / F1 by Class")
    st.caption("Click a column header to sort.")
    st.dataframe(metrics_df, use_container_width=True, hide_index=True)

    with st.expander("\U0001F9EE Formula reference", expanded=False):
        st.latex(r"\text{Precision} = \frac{TP}{TP + FP}")
        st.latex(r"\text{Recall} = \frac{TP}{TP + FN}")
        st.latex(r"F_1 = 2 \cdot \frac{\text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}")

    if is_mock:
        callout("warning", "\U0001F9EA", "Metrics and confusion matrix above are simulated placeholders until a real evaluation run is recorded.")
    else:
        callout("info", "\U00002139\U0000FE0F", "Teachable Machine does not export a held-out evaluation report, so the metrics and confusion matrix above are simulated placeholders until a real evaluation run is recorded.")

    header = "| " + " | ".join(metrics_df.columns) + " |"
    separator = "| " + " | ".join("---" for _ in metrics_df.columns) + " |"
    body = "\n".join(
        "| " + " | ".join(str(v) for v in row) + " |" for row in metrics_df.itertuples(index=False)
    )
    report_lines = [
        "# Model Report",
        "",
        f"Overall accuracy: {overall_accuracy * 100:.1f}% (simulated)",
        "",
        header,
        separator,
        body,
    ]
    st.download_button(
        "\U0001F4E5 Download Model Report",
        data="\n".join(report_lines),
        file_name="model_report.md",
        mime="text/markdown",
    )


def render_usage_section() -> None:
    section_anchor("usage")
    st.markdown("## Usage Instructions")
    with st.expander("▶️ Run the game locally", expanded=True):
        st.code("pip install -r requirements.txt\nstreamlit run app.py", language="bash")
    with st.expander("\U0001F5C2️ Batch prediction review", expanded=False):
        st.code("streamlit run app.py\n# then open 'Batch Prediction Review' in the sidebar", language="bash")
    with st.expander("\U0001F9E9 Loading the classifier in code", expanded=False):
        st.code(
            """from game.classifier import GestureClassifier
from PIL import Image

classifier = GestureClassifier()
image = Image.open("path/to/hand.jpg")
prediction = classifier.predict(image)
print(prediction.label, prediction.confidence)""",
            language="python",
        )
    callout(
        "tip",
        "\U0001F4A1",
        f"Set the `RPS_MODEL_PATH` environment variable to point at a trained model "
        f"(default: `{MODEL_PATH}`). Without it, predictions fall back to a random mock classifier.",
    )


def render_future_section() -> None:
    section_anchor("future")
    st.markdown("## Future Improvements")
    items = [
        "Track real training history and evaluation metrics instead of simulated ones.",
        "Expand the dataset with more hands, lighting conditions, and backgrounds.",
        "Add model versioning and a changelog for retrained checkpoints.",
        "Export a confusion matrix and metrics report automatically after each training run.",
        "Retrain without the Teachable Machine export step to get native Keras 3 checkpoints directly.",
    ]
    for item in items:
        st.markdown(f"- {item}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


@st.cache_resource
def get_classifier() -> GestureClassifier:
    return GestureClassifier()


def main() -> None:
    if "doc_theme" not in st.session_state:
        st.session_state["doc_theme"] = "dark"

    classifier = get_classifier()
    readme_text = load_readme(str(README_PATH))

    query = st.session_state.get("doc_search", "")
    query = render_sidebar(query)
    st.session_state["doc_search"] = query

    inject_css(st.session_state["doc_theme"])
    render_hero(classifier.is_mock)

    if classifier.is_mock:
        callout(
            "warning",
            "⚠️",
            f"No trained model found at `{MODEL_PATH}`. This documentation page shows the real "
            "dataset statistics alongside simulated training/evaluation visuals so the layout "
            "can be reviewed end-to-end before a model is trained.",
        )

    render_overview(readme_text, query)
    st.divider()
    render_dataset_section(readme_text, query)
    st.divider()
    render_architecture_section(classifier.is_mock)
    st.divider()
    render_training_section(classifier.is_mock)
    st.divider()
    render_evaluation_section(query, classifier.is_mock)
    st.divider()
    render_usage_section()
    st.divider()
    render_future_section()


if __name__ == "__main__":
    main()
