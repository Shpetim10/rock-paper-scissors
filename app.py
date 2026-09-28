"""Rock Paper Scissors AI Challenge - Streamlit entrypoint & game screen.

This file is both the app's launch script (`streamlit run app.py`) and the
"Play Game" page. It sets the page config once and uses `st.navigation` to
define clean, custom-labeled sidebar entries for every screen, instead of
relying on Streamlit's filename-derived page names.
"""

import time

import streamlit as st
from PIL import Image

from game.classifier import GESTURE_EMOJI, GestureClassifier, computer_move, judge
from game.theme import inject_theme, render_hero

WINS_NEEDED = 3

st.set_page_config(
    page_title="Rock Paper Scissors AI Challenge",
    page_icon="\U0001FAA8",
    layout="wide",
)


@st.cache_resource
def get_classifier() -> GestureClassifier:
    return GestureClassifier()


def init_state() -> None:
    defaults = {
        "human_score": 0,
        "computer_score": 0,
        "round": 1,
        "history": [],
        "last_result": None,
        "game_over": False,
        "winner": None,
        "pending_move": None,
        "pending_confidence": None,
        "pending_is_mock": None,
        "camera_key": 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_game() -> None:
    st.session_state.human_score = 0
    st.session_state.computer_score = 0
    st.session_state.round = 1
    st.session_state.history = []
    st.session_state.last_result = None
    st.session_state.game_over = False
    st.session_state.winner = None
    st.session_state.pending_move = None
    st.session_state.pending_confidence = None
    st.session_state.pending_is_mock = None
    st.session_state.camera_key += 1


PAGE_CSS = """
.scoreboard { display: flex; gap: 1rem; justify-content: center; margin-bottom: 1.5rem; }
.score-item { text-align: center; flex: 1; }
.score-label { font-size: 0.85rem; letter-spacing: 0.08em; text-transform: uppercase; color: var(--text-muted); }
.score-value { font-size: 2.4rem; font-weight: 800; margin-top: 0.2rem; }
.score-human { color: var(--accent-3); }
.score-computer { color: var(--accent-1); }
.score-round { color: var(--accent-2); }
.score-remaining { color: #facc15; }

.move-card {
    text-align: center;
    padding: 1.6rem 1rem;
    border-radius: 20px;
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    animation: rps-pop-in 0.4s ease;
}
.move-emoji { font-size: 4.5rem; line-height: 1; }
.move-label { margin-top: 0.6rem; font-size: 1.1rem; font-weight: 700; text-transform: capitalize; }

.result-banner {
    text-align: center;
    padding: 1rem;
    border-radius: 16px;
    font-size: 1.6rem;
    font-weight: 800;
    margin: 1rem 0;
    animation: rps-pop-in 0.5s ease;
}
.result-win { background: rgba(74, 222, 128, 0.15); color: #22a35a; border: 1px solid #4ade80; }
.result-lose { background: rgba(255, 110, 196, 0.15); color: #d63384; border: 1px solid #ff6ec4; }
.result-draw { background: rgba(250, 204, 21, 0.15); color: #b8860b; border: 1px solid #facc15; }

.confidence-track {
    width: 100%;
    height: 10px;
    border-radius: 6px;
    background: var(--card-bg-strong);
    overflow: hidden;
    margin-top: 0.4rem;
}
.confidence-fill {
    height: 100%;
    border-radius: 6px;
    background: linear-gradient(90deg, var(--accent-3), var(--accent-2));
    transition: width 0.6s ease;
}

.mock-banner {
    text-align: center;
    padding: 0.5rem 1rem;
    border-radius: 10px;
    background: rgba(250, 204, 21, 0.12);
    border: 1px solid rgba(250, 204, 21, 0.4);
    color: #b8860b;
    font-size: 0.85rem;
    margin-bottom: 1rem;
}

.victory-card {
    text-align: center;
    padding: 3rem 1.5rem;
    border-radius: 24px;
    background: linear-gradient(160deg, rgba(255, 215, 0, 0.14), rgba(120, 115, 245, 0.14));
    border: 1px solid rgba(255, 215, 0, 0.4);
    animation: rps-pop-in 0.6s ease;
}
.trophy { font-size: 6rem; animation: rps-bounce 1.4s ease infinite; }
"""


def render_scoreboard() -> None:
    remaining = max(
        WINS_NEEDED - max(st.session_state.human_score, st.session_state.computer_score), 0
    )
    st.markdown(
        f"""
        <div class="glass-card scoreboard">
            <div class="score-item">
                <div class="score-label">Human</div>
                <div class="score-value score-human">{st.session_state.human_score}</div>
            </div>
            <div class="score-item">
                <div class="score-label">Computer</div>
                <div class="score-value score-computer">{st.session_state.computer_score}</div>
            </div>
            <div class="score-item">
                <div class="score-label">Round</div>
                <div class="score-value score-round">{st.session_state.round}</div>
            </div>
            <div class="score-item">
                <div class="score-label">Wins Needed</div>
                <div class="score-value score-remaining">{remaining}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_move_card(column, title: str, gesture: str | None, footer: str = "") -> None:
    emoji = GESTURE_EMOJI.get(gesture, "❓") if gesture else "\U0001F937"
    label = gesture if gesture else "Waiting..."
    with column:
        st.markdown(
            f"""
            <div class="move-card">
                <div class="score-label">{title}</div>
                <div class="move-emoji">{emoji}</div>
                <div class="move-label">{label}</div>
                {f'<div class="score-label">{footer}</div>' if footer else ""}
            </div>
            """,
            unsafe_allow_html=True,
        )


def play_round_with_move(human_move: str, confidence: float, is_mock: bool) -> None:
    comp_move = computer_move()
    outcome = judge(human_move, comp_move)

    if outcome == "win":
        st.session_state.human_score += 1
    elif outcome == "lose":
        st.session_state.computer_score += 1

    st.session_state.history.append(
        {
            "Round": st.session_state.round,
            "Human": human_move.capitalize(),
            "Computer": comp_move.capitalize(),
            "Result": {"win": "Win", "lose": "Lose", "draw": "Draw"}[outcome],
        }
    )
    st.session_state.last_result = {
        "human_move": human_move,
        "computer_move": comp_move,
        "outcome": outcome,
        "confidence": confidence,
        "is_mock": is_mock,
    }
    st.session_state.round += 1

    if st.session_state.human_score >= WINS_NEEDED:
        st.session_state.game_over = True
        st.session_state.winner = "human"
    elif st.session_state.computer_score >= WINS_NEEDED:
        st.session_state.game_over = True
        st.session_state.winner = "computer"


def play_round(image: Image.Image, classifier: GestureClassifier) -> None:
    prediction = classifier.predict(image)
    play_round_with_move(prediction.label, prediction.confidence, prediction.is_mock)


def render_victory_screen() -> None:
    champion = "You" if st.session_state.winner == "human" else "The Computer"
    st.markdown(
        f"""
        <div class="victory-card">
            <div class="trophy">\U0001F3C6</div>
            <h1>{champion} won the match!</h1>
            <p>Final Score &mdash; Human {st.session_state.human_score} : {st.session_state.computer_score} Computer</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    st.subheader("Match Summary")
    st.dataframe(st.session_state.history, use_container_width=True, hide_index=True)
    st.write("")
    _, center, _ = st.columns([1, 1, 1])
    with center:
        if st.button("Restart Game", use_container_width=True, type="primary"):
            reset_game()
            st.rerun()


def render_capture_and_round(classifier: GestureClassifier) -> None:
    st.subheader("Take Your Shot")
    left, right = st.columns([1, 1])

    awaiting_reveal = st.session_state.pending_move is not None

    with left:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        if not awaiting_reveal:
            photo = st.camera_input(
                "Take Picture",
                label_visibility="visible",
                key=f"camera_{st.session_state.camera_key}",
            )
            if photo is not None:
                image = Image.open(photo)
                with st.spinner("Analyzing your gesture..."):
                    time.sleep(0.4)
                    prediction = classifier.predict(image)
                st.session_state.pending_move = prediction.label
                st.session_state.pending_confidence = prediction.confidence
                st.session_state.pending_is_mock = prediction.is_mock
                st.rerun()
        else:
            st.markdown(f"**You played:** {GESTURE_EMOJI.get(st.session_state.pending_move, '')} "
                        f"{st.session_state.pending_move.capitalize()}")
            if st.button("Reveal Computer's Move", type="primary", use_container_width=True):
                play_round_with_move(
                    st.session_state.pending_move,
                    st.session_state.pending_confidence,
                    st.session_state.pending_is_mock,
                )
                st.session_state.pending_move = None
                st.session_state.pending_confidence = None
                st.session_state.pending_is_mock = None
                st.session_state.camera_key += 1
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    result = st.session_state.last_result
    if result is None:
        with right:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.info("Take a picture to play your first round.")
            st.markdown("</div>", unsafe_allow_html=True)
        return

    with right:
        if result["is_mock"]:
            st.markdown(
                '<div class="mock-banner">No trained model found at '
                '<code>model/rps_model.keras</code> &mdash; showing a mock prediction.</div>',
                unsafe_allow_html=True,
            )
        confidence_pct = round(result["confidence"] * 100, 1)
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown(f"**Predicted Gesture:** {result['human_move'].capitalize()}")
        st.markdown(f"**Confidence:** {confidence_pct}%")
        st.markdown(
            f"""
            <div class="confidence-track">
                <div class="confidence-fill" style="width: {confidence_pct}%;"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    col_human, col_vs, col_computer = st.columns([2, 1, 2])
    render_move_card(col_human, "You Played", result["human_move"])
    with col_vs:
        st.markdown(
            "<div style='text-align:center; font-size:2rem; padding-top:2.5rem;'>VS</div>",
            unsafe_allow_html=True,
        )
    render_move_card(col_computer, "Computer Played", result["computer_move"])

    outcome = result["outcome"]
    banner_text = {"win": "You Win This Round!", "lose": "Computer Wins This Round!", "draw": "It's a Draw!"}
    st.markdown(
        f'<div class="result-banner result-{outcome}">{banner_text[outcome]}</div>',
        unsafe_allow_html=True,
    )


def render_history() -> None:
    if not st.session_state.history:
        return
    st.subheader("Game History")
    st.dataframe(st.session_state.history, use_container_width=True, hide_index=True)


def render_game() -> None:
    init_state()
    inject_theme(PAGE_CSS)
    classifier = get_classifier()

    render_hero("Rock Paper Scissors AI Challenge", "First player to reach 3 wins becomes the champion.")
    render_scoreboard()
    st.write("")

    if st.session_state.game_over:
        render_victory_screen()
    else:
        render_capture_and_round(classifier)
        st.write("")
        render_history()


# ---------------------------------------------------------------------------
# Navigation — custom sidebar labels/icons instead of Streamlit's
# filename-derived page names.
# ---------------------------------------------------------------------------

pages = st.navigation(
    [
        st.Page(render_game, title="Play Game", icon="\U0001F3AE", default=True, url_path="play"),
        st.Page("pages/1_Batch_Prediction_Review.py", title="Batch Review", icon="\U0001F4F8", url_path="batch-review"),
        st.Page("pages/2_Dataset_Gallery.py", title="Dataset Gallery", icon="\U0001F5BC", url_path="dataset-gallery"),
        st.Page("pages/3_Model_Documentation.py", title="Model Docs", icon="\U0001F4DA", url_path="model-docs"),
    ]
)

if __name__ == "__main__":
    pages.run()
