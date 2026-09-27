"""
Central CSS for the app — the only source of visual styling (not dependent
on .streamlit/config.toml, which only loads from the current working
directory and silently fails to apply if the app is launched from anywhere
else).

Palette: "graphite & signal" — a deep graphite dark mode and a warm-paper
light mode, both built around a single muted cyan-teal accent (evokes
scanning/searching rather than a generic chat-bot blue), instead of the
near-black+neon-accent or flat-blue combinations most AI-generated UIs
default to. Fits the subject matter (an agent that goes out to the web and
comes back with something worth remembering).

Row/button styling note: the sidebar's chat rows (select / delete / confirm)
are styled entirely through Streamlit's own `type="primary"` button
parameter, not through a wrapping st.container(key=...) — see app.py's
render_chat_rows for why: that function's normal and confirm states must
keep an identical top-level shape (both open with a bare st.columns(...))
so Streamlit can cleanly swap one for the other inside the same st.empty()
placeholder; a keyed wrapper around only one of the two states would itself
break that shape match. The theme toggle button is styled the same
class-based way, via its own key (`st-key-theme_toggle_btn`) rather than a
wrapping container — see app.py's module docstring for an unresolved click
quirk on that specific button found during headless browser testing.
"""

PALETTES = {
    "dark": {
        "bg": "#14171A",
        "bg-panel": "#191D21",
        "bg-card": "#1F2429",
        "bg-card-hi": "#272D33",
        "border": "#2E3540",
        "text": "#E4E7EA",
        "text-dim": "#8B939C",
        "accent": "#4FB8AC",
        "accent-hi": "#63CBBF",
        "accent-text": "#0B1E1B",
        "danger": "#C9645F",
        "danger-hi": "#DA7B76",
        "danger-text": "#2A1210",
        "success": "#6FA97E",
        "shadow": "0 2px 10px rgba(0,0,0,0.35)",
    },
    "light": {
        "bg": "#F6F4EF",
        "bg-panel": "#EFECE3",
        "bg-card": "#FFFFFF",
        "bg-card-hi": "#F7F5EE",
        "border": "#DEDACC",
        "text": "#22262A",
        "text-dim": "#6E7278",
        "accent": "#1E8B7D",
        "accent-hi": "#177367",
        "accent-text": "#FFFFFF",
        "danger": "#A23D3A",
        "danger-hi": "#8A312F",
        "danger-text": "#FFFFFF",
        "success": "#3E7A4C",
        "shadow": "0 2px 10px rgba(40,35,20,0.10)",
    },
}

CSS_TEMPLATE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {{
    --bg:          {bg};
    --bg-panel:    {bg-panel};
    --bg-card:     {bg-card};
    --bg-card-hi:  {bg-card-hi};
    --border:      {border};
    --text:        {text};
    --text-dim:    {text-dim};
    --accent:      {accent};
    --accent-hi:   {accent-hi};
    --accent-text: {accent-text};
    --danger:      {danger};
    --danger-hi:   {danger-hi};
    --danger-text: {danger-text};
    --success:     {success};
    --shadow:      {shadow};
}}

/* ---- base ---- */
[data-testid="stApp"], [data-testid="stAppViewContainer"], [data-testid="stHeader"], .main {{
    background-color: var(--bg) !important;
}}
[data-testid="stBottom"], [data-testid="stBottomBlockContainer"] {{
    background-color: var(--bg) !important;
}}
[data-testid="stBottom"] > div {{
    background-color: transparent !important;
}}
[data-testid="stSidebar"] {{
    background-color: var(--bg-panel) !important;
    border-right: 1px solid var(--border) !important;
}}
html, body, [class*="css"] {{
    color: var(--text) !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
}}
h1, h2, h3, h4 {{
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    color: var(--text) !important;
    letter-spacing: 0.01em;
}}
p, span, label, div {{ color: var(--text); }}
a {{ color: var(--accent) !important; }}

/* ---- app title block ---- */
.app-title {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.3rem;
    font-weight: 700;
    line-height: 1.25;
    color: var(--text);
    margin-bottom: 0.2rem;
    padding-top: 0.3rem;
}}
.app-tagline {{
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 0.8rem;
    color: var(--text-dim);
    margin-bottom: 0.9rem;
}}

/* ---- theme toggle ----
   Targeted via the button's own `key`-derived class on its
   stElementContainer ancestor (st-key-theme_toggle_btn), not a wrapping
   st.container(key=...) — same reasoning as the chat rows above: styling
   through the widget's own key avoids an extra layout wrapper. Separately
   (and unrelated to this styling choice — removing the wrapper was tried
   and didn't change it), this specific button occasionally ignores the
   first real click after a fresh page load; see app.py's module docstring. */
div[class*="st-key-theme_toggle_btn"] button {{
    background-color: transparent !important;
    border: 1px solid var(--border) !important;
    border-radius: 999px !important;
    padding: 0.15rem 0.6rem !important;
    font-size: 0.85rem !important;
}}
div[class*="st-key-theme_toggle_btn"] button:hover {{
    border-color: var(--accent) !important;
    color: var(--accent) !important;
}}

/* ---- generic buttons: quiet by default, signal-teal when primary ----
   Targeted by data-testid rather than DOM nesting (.stButton > button):
   the actual <button> sits inside tooltip-wrapper spans, several levels
   below .stButton, so a direct-child selector silently never matches and
   Streamlit's own default (light-theme) button styling shows through. */
[data-testid="stBaseButton-secondary"],
[data-testid="stBaseButton-secondaryFormSubmit"] {{
    background-color: var(--bg-card) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-weight: 500 !important;
}}
[data-testid="stBaseButton-secondary"] p,
[data-testid="stBaseButton-secondaryFormSubmit"] p,
[data-testid="stBaseButton-primary"] p {{
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    white-space: nowrap !important;
}}
[data-testid="stBaseButton-secondary"]:hover,
[data-testid="stBaseButton-secondaryFormSubmit"]:hover {{
    background-color: var(--bg-card-hi) !important;
    border-color: var(--accent) !important;
    color: var(--accent-hi) !important;
}}
[data-testid="stBaseButton-secondary"]:focus-visible,
[data-testid="stBaseButton-secondaryFormSubmit"]:focus-visible,
[data-testid="stBaseButton-primary"]:focus-visible {{
    outline: 2px solid var(--accent) !important;
    outline-offset: 1px;
}}
[data-testid="stBaseButton-primary"] {{
    background-color: var(--accent) !important;
    color: var(--accent-text) !important;
    border: 1px solid var(--accent) !important;
}}
[data-testid="stBaseButton-primary"]:hover {{
    background-color: var(--accent-hi) !important;
    color: var(--accent-text) !important;
}}

/* ---- inputs ---- */
.stTextInput input, .stTextArea textarea {{
    background-color: var(--bg-card) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.9rem !important;
}}
.stTextInput input:focus, .stTextArea textarea:focus {{
    border-color: var(--accent) !important;
    box-shadow: none !important;
}}
[data-testid="stForm"] {{
    background-color: var(--bg-panel) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}}

/* ---- chat log + bubbles ---- */
[data-testid="stChatMessage"] {{
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    box-shadow: var(--shadow);
}}
/* The chat input's own inner wrapper divs carry a hardcoded light-grey
   background (Streamlit's default "pill" look) that doesn't respond to
   theme — force it transparent and color the outer box ourselves. */
[data-testid="stChatInput"] {{
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
}}
[data-testid="stChatInput"] div {{
    background-color: transparent !important;
}}
[data-testid="stChatInputTextArea"] {{
    color: var(--text) !important;
}}
[data-testid="stChatInputSubmitButton"] {{
    color: var(--accent) !important;
}}

/* ---- empty states ---- */
.empty-state {{
    color: var(--text-dim);
    font-size: 0.9rem;
    border: 1px dashed var(--border);
    border-radius: 8px;
    padding: 1rem;
    text-align: left;
}}

/* ---- misc ---- */
hr {{ border-color: var(--border) !important; }}
[data-testid="stAlert"] {{ border-radius: 8px !important; }}
</style>
"""


def inject(theme: str = "dark"):
    import streamlit as st
    palette = PALETTES.get(theme, PALETTES["dark"])
    st.markdown(CSS_TEMPLATE.format(**palette), unsafe_allow_html=True)
