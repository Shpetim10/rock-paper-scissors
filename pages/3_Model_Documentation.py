"""Model Documentation screen — renders README.md as an interactive docs portal.

Every piece of content on this page comes directly from README.md, parsed
section by section. Nothing here is invented or simulated — if it's not in
the README, it doesn't appear here.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

if (_root := str(Path(__file__).resolve().parent.parent)) not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st

README_PATH = Path("README.md")

# Page config (title/icon/layout) is set once by the app.py entrypoint via
# st.navigation; this page only needs to inject its own CSS and content.


# ---------------------------------------------------------------------------
# README parsing — the single source of truth for this page's content
# ---------------------------------------------------------------------------


@st.cache_data(show_spinner=False)
def load_readme(_path: str) -> str:
    path = Path(_path)
    return path.read_text() if path.exists() else "# README not found"


SECTION_PATTERN = re.compile(r"^##\s+(.*)$", re.MULTILINE)
IMAGE_PATTERN = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
H1_LINE_PATTERN = re.compile(r"^#\s+.*\n+")


def slugify(heading: str) -> str:
    heading = re.sub(r"^\d+\.\s*", "", heading)
    return re.sub(r"[^a-z0-9]+", "-", heading.lower()).strip("-")


@st.cache_data(show_spinner=False)
def parse_readme_sections(readme_text: str) -> list[tuple[str, str]]:
    """Split README.md into (heading, body) pairs at '## ' headings.

    The intro before the first '## ' heading (title + description) is
    returned first with an empty heading.
    """
    matches = list(SECTION_PATTERN.finditer(readme_text))
    sections: list[tuple[str, str]] = []

    intro_end = matches[0].start() if matches else len(readme_text)
    intro = H1_LINE_PATTERN.sub("", readme_text[:intro_end], count=1).strip()
    if intro:
        sections.append(("", intro))

    for i, match in enumerate(matches):
        heading = match.group(1).strip()
        if heading.lower() == "table of contents":
            continue
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(readme_text)
        body = readme_text[start:end].strip()
        sections.append((heading, body))
    return sections


def matches_query(text: str, query: str) -> bool:
    return not query or query.lower() in text.lower()


def render_section_body(body: str) -> None:
    """Render a section's markdown, swapping local image references for st.image."""
    pos = 0
    for match in IMAGE_PATTERN.finditer(body):
        before = body[pos : match.start()].strip()
        if before:
            st.markdown(before)
        alt, src = match.group(1), match.group(2)
        if Path(src).exists():
            st.image(src, caption=alt or None, use_container_width=True)
        else:
            st.caption(f"(image not found: {src})")
        pos = match.end()
    remainder = body[pos:].strip()
    if remainder:
        st.markdown(remainder)


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

        .glass-card {{
            background: {card_bg};
            border: 1px solid {card_border};
            border-radius: 18px;
            padding: 1.3rem 1.5rem;
            margin-bottom: 1rem;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        .glass-card:hover {{ transform: translateY(-2px); }}

        code {{ background: {code_bg} !important; }}

        h2, h3 {{ scroll-margin-top: 1.5rem; }}

        div[data-testid="stDataFrame"] {{ border-radius: 14px; overflow: hidden; }}

        @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(-8px); }} to {{ opacity: 1; transform: translateY(0); }} }}
        @keyframes shimmer {{ to {{ background-position: 200% center; }} }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def section_anchor(anchor_id: str) -> None:
    st.markdown(f'<div id="{anchor_id}"></div>', unsafe_allow_html=True)


def render_hero() -> None:
    st.markdown(
        """
        <div class="doc-hero">
            <h1>\U0001F4DA Model Documentation</h1>
            <p>A direct rendering of this project's README.md.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(search_query: str, nav_sections: list[tuple[str, str]]) -> str:
    with st.sidebar:
        st.markdown("### \U0001F4D6 Documentation")
        query = st.text_input("Search docs", value=search_query, placeholder="Search sections, code, terms...")
        st.markdown("---")
        for anchor_id, label in nav_sections:
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


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    if "doc_theme" not in st.session_state:
        st.session_state["doc_theme"] = "dark"

    readme_text = load_readme(str(README_PATH))
    sections = parse_readme_sections(readme_text)
    nav_sections = [(slugify(heading), heading) for heading, _ in sections if heading]

    query = st.session_state.get("doc_search", "")
    query = render_sidebar(query, nav_sections)
    st.session_state["doc_search"] = query

    inject_css(st.session_state["doc_theme"])
    render_hero()

    for heading, body in sections:
        if query and not matches_query(heading + "\n" + body, query):
            continue
        anchor = slugify(heading) if heading else "overview"
        section_anchor(anchor)
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        if heading:
            st.markdown(f"## {heading}")
        render_section_body(body)
        st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
