from __future__ import annotations

import streamlit as st


APP_CSS = """
<style>
    :root {
        --bg: #0b1118;
        --bg2: #101924;
        --panel: rgba(15, 24, 34, 0.94);
        --panel-soft: rgba(21, 33, 46, 0.86);
        --line: rgba(117, 139, 163, 0.16);
        --line-strong: rgba(117, 139, 163, 0.26);
        --text: #edf3f8;
        --muted: #93a6b8;
        --accent: #63b3ed;
        --accent2: #2dd4bf;
        --warn: #f59e0b;
    }
    .stApp {
        color: var(--text);
        background:
            radial-gradient(circle at top left, rgba(99, 179, 237, 0.08), transparent 22%),
            linear-gradient(180deg, var(--bg) 0%, var(--bg2) 100%);
    }
    #MainMenu, header[data-testid="stHeader"], [data-testid="stSidebarNav"] { display: none; }
    [data-testid="stAppViewContainer"] { background: transparent; }
    .block-container {
        max-width: 1460px;
        padding-top: 0.75rem;
        padding-bottom: 2rem;
    }
    .hero {
        border: 1px solid var(--line-strong);
        border-radius: 18px;
        background: linear-gradient(180deg, rgba(17, 27, 38, 0.98), rgba(11, 17, 24, 0.98));
        padding: 1.05rem 1.15rem;
        box-shadow: 0 16px 34px rgba(0, 0, 0, 0.24);
        margin-bottom: 0.85rem;
    }
    .hero-kicker {
        color: #89c9ff;
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.28rem;
    }
    .hero-title {
        color: var(--text);
        font-size: 2.05rem;
        font-weight: 820;
        line-height: 1.0;
        margin-bottom: 0.35rem;
    }
    .hero-copy {
        color: var(--muted);
        font-size: 0.9rem;
        line-height: 1.58;
        max-width: 64rem;
    }
    .hero-pills { margin-top: 0.7rem; display: flex; gap: 0.42rem; flex-wrap: wrap; }
    .pill {
        display: inline-block;
        border-radius: 999px;
        padding: 0.24rem 0.54rem;
        border: 1px solid var(--line);
        background: rgba(255, 255, 255, 0.03);
        color: #d7e3ef;
        font-size: 0.73rem;
        font-weight: 750;
    }
    .surface {
        border: 1px solid var(--line);
        border-radius: 14px;
        background: linear-gradient(180deg, rgba(16, 25, 36, 0.98), rgba(11, 17, 24, 0.98));
        padding: 0.82rem 0.86rem 0.88rem;
        box-shadow: 0 10px 24px rgba(0, 0, 0, 0.2);
        margin-bottom: 0.8rem;
    }
    .surface-label {
        display: inline-block;
        border-radius: 999px;
        background: rgba(99, 179, 237, 0.10);
        color: #90d1ff;
        padding: 0.18rem 0.45rem;
        font-size: 0.68rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.34rem;
    }
    .panel-title {
        color: var(--text);
        font-size: 1rem;
        font-weight: 760;
        margin-bottom: 0.16rem;
    }
    .panel-copy {
        color: var(--muted);
        font-size: 0.84rem;
        line-height: 1.55;
        margin-bottom: 0.55rem;
    }
    .detail-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.5rem;
        margin-bottom: 0.6rem;
    }
    .detail-card {
        border: 1px solid var(--line);
        border-radius: 10px;
        padding: 0.55rem 0.6rem;
        background: rgba(255, 255, 255, 0.024);
    }
    .detail-label {
        color: var(--muted);
        font-size: 0.68rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.12rem;
    }
    .detail-value {
        color: var(--text);
        font-weight: 760;
        font-size: 0.92rem;
    }
    .note {
        border: 1px dashed var(--line);
        border-radius: 10px;
        padding: 0.55rem 0.62rem;
        background: rgba(255,255,255,0.02);
        color: var(--muted);
        font-size: 0.8rem;
        line-height: 1.5;
    }
    div[data-testid="stMetric"] {
        border: 1px solid var(--line);
        border-radius: 10px;
        background: linear-gradient(180deg, rgba(16, 25, 36, 0.98), rgba(11, 17, 24, 0.98));
        padding: 0.58rem 0.68rem;
    }
    div[data-testid="stMetricLabel"] * { color: var(--muted); }
    div[data-testid="stMetricValue"] * { color: var(--text); }
    div[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; border: 1px solid var(--line); }
    div[data-baseweb="select"] > div, .stNumberInput > div > div {
        background: rgba(255,255,255,0.03);
        border-color: var(--line);
        color: var(--text);
    }
    @media (max-width: 980px) {
        .detail-grid { grid-template-columns: 1fr; }
        .hero-title { font-size: 1.7rem; }
    }
</style>
"""


def apply_theme() -> None:
    st.markdown(APP_CSS, unsafe_allow_html=True)


def render_surface_header(title: str, copy: str, label: str | None = None) -> None:
    st.markdown("<div class='surface'>", unsafe_allow_html=True)
    if label:
        st.markdown(f"<div class='surface-label'>{label}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='panel-title'>{title}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='panel-copy'>{copy}</div>", unsafe_allow_html=True)


def close_surface() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def fmt_money(value: float) -> str:
    return f"${value:,.0f}"


def fmt_pct(value: float) -> str:
    return f"{value:.2f}%"


def fmt_bps(value: float) -> str:
    return f"{value:.2f} bps"
