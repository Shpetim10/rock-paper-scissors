"""Shared visual theme for every screen of the Rock-Paper-Scissors app.

Centralizes the "glass, neon, futuristic" look so every page (game, batch
review, dataset gallery, docs) stays visually consistent and adapts to the
viewer's OS light/dark preference automatically via `prefers-color-scheme`.
"""

from __future__ import annotations

import streamlit as st

CLASS_COLORS = {"rock": "#7aa2ff", "paper": "#facc15", "scissors": "#ff6ec4"}

BASE_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;600&display=swap');

:root {
    --bg-grad-1: #241454;
    --bg-grad-2: #120f2b;
    --bg-grad-3: #060512;
    --text-primary: #f3f3fb;
    --text-muted: #a9a9c8;
    --surface: #16142f;
    --card-bg: rgba(255, 255, 255, 0.055);
    --card-bg-strong: rgba(255, 255, 255, 0.09);
    --card-border: rgba(255, 255, 255, 0.12);
    --sidebar-bg: rgba(10, 8, 28, 0.55);
    --code-bg: rgba(255, 255, 255, 0.08);
    --accent-1: #ff6ec4;
    --accent-2: #7873f5;
    --accent-3: #4ade80;
    --accent-4: #38bdf8;
    --shadow-color: rgba(0, 0, 0, 0.4);
}

@media (prefers-color-scheme: light) {
    :root {
        --bg-grad-1: #eef1ff;
        --bg-grad-2: #f6f7fc;
        --bg-grad-3: #ffffff;
        --text-primary: #16162a;
        --text-muted: #5b5b78;
        --surface: #ffffff;
        --card-bg: rgba(22, 20, 50, 0.045);
        --card-bg-strong: rgba(22, 20, 50, 0.08);
        --card-border: rgba(22, 20, 50, 0.1);
        --sidebar-bg: rgba(238, 241, 255, 0.6);
        --code-bg: rgba(22, 20, 50, 0.06);
        --shadow-color: rgba(30, 20, 80, 0.12);
    }
}

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp {
    background: radial-gradient(circle at 15% -10%, var(--bg-grad-1) 0%, var(--bg-grad-2) 45%, var(--bg-grad-3) 100%);
    color: var(--text-primary);
}

section[data-testid="stSidebar"] {
    background: var(--sidebar-bg);
    border-right: 1px solid var(--card-border);
    backdrop-filter: blur(18px);
}
section[data-testid="stSidebar"] * { color: var(--text-primary); }

[data-testid="stSidebarNav"] li a {
    border-radius: 10px !important;
    font-weight: 600;
    transition: background 0.2s ease, transform 0.15s ease;
}
[data-testid="stSidebarNav"] li a:hover { transform: translateX(2px); }
[data-testid="stSidebarNav"] li a[aria-current="page"] {
    background: var(--card-bg-strong);
    box-shadow: inset 2px 0 0 var(--accent-2);
}

.hero { text-align: center; padding: 2.4rem 1rem 1.4rem 1rem; animation: rps-fade-in 0.8s ease; }
.hero h1 {
    font-size: 2.7rem;
    font-weight: 900;
    margin: 0;
    letter-spacing: -0.02em;
    background: linear-gradient(90deg, var(--accent-1), var(--accent-2), var(--accent-3), var(--accent-4));
    background-size: 300% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: rps-shimmer 8s linear infinite;
}
.hero p { font-size: 1.05rem; color: var(--text-muted); margin-top: 0.55rem; }

.glass-card {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 20px;
    padding: 1.3rem 1.4rem;
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    box-shadow: 0 8px 32px var(--shadow-color);
    transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease;
}
.glass-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 14px 40px var(--shadow-color);
    border-color: var(--accent-2);
}

.badge {
    display: inline-block;
    padding: 0.24rem 0.72rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
.badge-rock { background: rgba(122, 162, 255, 0.16); color: #7aa2ff; border: 1px solid #7aa2ff; }
.badge-paper { background: rgba(250, 204, 21, 0.16); color: #d69f00; border: 1px solid #facc15; }
.badge-scissors { background: rgba(255, 110, 196, 0.16); color: #ff6ec4; border: 1px solid #ff6ec4; }
@media (prefers-color-scheme: light) {
    .badge-paper { color: #92700a; }
}
.badge-source-original { background: var(--card-bg-strong); color: var(--text-primary); border: 1px solid var(--text-muted); }
.badge-source-augmented { background: rgba(250, 204, 21, 0.15); color: #d69f00; border: 1px solid #facc15; }
.badge-source-test { background: rgba(56, 189, 248, 0.16); color: #38bdf8; border: 1px solid #38bdf8; }

code { background: var(--code-bg) !important; }
div[data-testid="stDataFrame"] { border-radius: 14px; overflow: hidden; }
h2, h3 { scroll-margin-top: 1.5rem; }

@keyframes rps-fade-in { from { opacity: 0; transform: translateY(-8px); } to { opacity: 1; transform: translateY(0); } }
@keyframes rps-pop-in { from { opacity: 0; transform: scale(0.92); } to { opacity: 1; transform: scale(1); } }
@keyframes rps-shimmer { to { background-position: 300% center; } }
@keyframes rps-bounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-14px); } }
"""


def inject_theme(extra_css: str = "") -> None:
    """Inject the shared base theme, plus any page-specific CSS on top."""
    st.markdown(f"<style>{BASE_CSS}\n{extra_css}</style>", unsafe_allow_html=True)


def render_hero(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="hero">
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
