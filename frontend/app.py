"""
Streamlit frontend for the agentic chat backend (FastAPI + a Gemini ReAct
agent with a web-search tool and tiered long-term memory).

Two panels:
  - LEFT (sidebar): theme toggle, new-chat form, chat switcher
  - CENTER:         chat log (chat input docked below it), for the active chat

All backend access goes through ApiClient (frontend/api_client.py) over
HTTP — this file never imports a backend module directly.

Ordering notes (both learned the hard way, via headless testing, not
guesswork — see the sibling project this pattern is taken from):

1. The chat switcher's row buttons (select/delete) are rendered exactly
   ONCE, early. Selecting a chat is just a session_state write inside that
   same render — nothing here calls st.stop() until *after* that write has
   had a chance to happen, so clicking a chat's name takes effect on the
   very click that did it, not the click after.

2. Chat history is rendered into an st.empty() placeholder created *before*
   st.chat_input() is called. The placeholder keeps its screen position
   (above the input) regardless of when it's last written to, so a new
   turn can be appended and the placeholder refilled *after* chat_input
   returns it, and the log still updates immediately, above the input —
   with no extra st.rerun() (which would cause a visible double-render
   flicker).

Row/button styling: an active row and the delete/confirm state are done
via the button's built-in `type="primary"` parameter (see render_chat_rows
below) rather than a wrapping st.container(key=...) — see styles.py for why.

Known limitation (backend, not this file's doing): GET /messages only
returns whatever is still buffered in SQLite (the most recent messages for
that chat). Once older turns get compacted into that chat's Qdrant memory
collection, they're still recallable by the agent's memory tool, but this
history view won't replay them verbatim.

Known quirk (this file, unresolved): in real-browser testing, the theme
toggle button occasionally doesn't respond to the very first click after a
fresh page load, but works normally on the next click and every click after
that. Streamlit's own AppTest framework (which drives the script directly
rather than through the DOM) exercises the exact same code path with no
issue, and every other button in this app was tested the same way in a real
browser without hitting this — so the toggle's own logic isn't the
suspect, but the real cause wasn't pinned down. If it doesn't respond, click
it again.
"""

import os

import streamlit as st

from api_client import ApiClient, ApiError
from styles import inject

APP_TITLE = "Agentic ChatBot"
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title=APP_TITLE, layout="wide")

# ---------------------------------------------------------------- state ---

if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = None
if "chat_histories" not in st.session_state:
    st.session_state.chat_histories = {}  # chat_id -> list[{"role","content"}]
if "confirm_delete_id" not in st.session_state:
    st.session_state.confirm_delete_id = None
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

inject(st.session_state.theme)

api = ApiClient(BACKEND_URL)

# --------------------------------------------------------------- helpers ---


def ensure_chat_history_loaded(chat_id: int):
    """Hydrate a chat's history from the backend the first time it's opened
    this session. After that, local session_state is the source of truth
    (it already includes everything the server has, plus whatever was just
    sent this run)."""
    if chat_id in st.session_state.chat_histories:
        return
    try:
        messages = api.get_messages(chat_id) or []
        st.session_state.chat_histories[chat_id] = [
            {"role": m["role"], "content": m["content"]} for m in messages
        ]
    except ApiError:
        st.session_state.chat_histories[chat_id] = []


def render_chat_rows(chats):
    """Sidebar: the switcher/delete rows. Rendered exactly once per run —
    see module docstring for why."""
    if not chats:
        st.markdown(
            '<div class="empty-state">No chats yet. Create one above to get started.</div>',
            unsafe_allow_html=True,
        )
        return

    for c in chats:
        chat_id = c["id"]
        row_slot = st.empty()

        # draw_normal and draw_confirm both open with a single st.columns(...)
        # call as their very first element inside `with row_slot.container():`.
        # That match matters: when this placeholder gets refilled a second
        # time in the same run (e.g. draw_confirm cancelling back to
        # draw_normal), Streamlit reconciles the new content against the old
        # by position — if the first element's *type* differs between the
        # two fills, the old content doesn't get cleanly replaced, it lingers
        # alongside the new content. Keeping both functions' top-level shape
        # identical avoids that.

        def draw_normal(row_slot=row_slot, c=c, chat_id=chat_id):
            # `is_active` reflects active_chat_id as of the *start* of this
            # run, so on the exact click that changes it, this row's own
            # highlight is one interaction behind (button `type` has to be
            # fixed at creation time, before we know this click's outcome).
            # It self-corrects on the very next interaction — cosmetic only,
            # doesn't affect which chat is actually active.
            is_active = chat_id == st.session_state.active_chat_id
            with row_slot.container():
                col1, col2 = st.columns([4, 1])
                with col1:
                    if st.button(
                        c["name"],
                        key=f"select_{chat_id}",
                        type="primary" if is_active else "secondary",
                        use_container_width=True,
                    ):
                        st.session_state.active_chat_id = chat_id
                        st.session_state.confirm_delete_id = None
                with col2:
                    if st.button(
                        "🗑️", key=f"del_{chat_id}", help="Delete this chat", use_container_width=True
                    ):
                        st.session_state.confirm_delete_id = chat_id
            # Redraw AFTER the `with row_slot.container():` above has fully
            # exited, not from inside its own click handler.
            if st.session_state.confirm_delete_id == chat_id:
                draw_confirm()

        def draw_confirm(row_slot=row_slot, c=c, chat_id=chat_id):
            delete_error = None
            deleted = False
            with row_slot.container():
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(
                        "Confirm delete", key=f"delconfirm_{chat_id}", type="primary", use_container_width=True
                    ):
                        try:
                            api.delete_chat(chat_id)
                            st.session_state.chat_histories.pop(chat_id, None)
                            if st.session_state.active_chat_id == chat_id:
                                st.session_state.active_chat_id = None
                            st.session_state.confirm_delete_id = None
                            deleted = True
                        except ApiError as e:
                            st.session_state.confirm_delete_id = None
                            delete_error = str(e)
                with col2:
                    if st.button("Cancel", key=f"delcancel_{chat_id}", use_container_width=True):
                        st.session_state.confirm_delete_id = None
            if deleted:
                # The chat is gone server-side — clear the row immediately
                # rather than redrawing it as a normal row with stale data
                # that would only disappear on the *next* interaction (once
                # `chats` is refetched at the top of the script).
                row_slot.empty()
            elif st.session_state.confirm_delete_id != chat_id:
                draw_normal()
            if delete_error:
                st.error(f"Couldn't delete chat: {delete_error}")

        if st.session_state.confirm_delete_id == chat_id:
            draw_confirm()
        else:
            draw_normal()


# ------------------------------------------------------------ top-level ---

try:
    chats = api.list_chats()
except ApiError as e:
    st.error(f"⚠️ {e}")
    st.stop()

# Most recently created first.
chats = sorted(chats, key=lambda c: c["id"], reverse=True)

with st.sidebar:
    st.subheader("Orchestrated by Tharun")
    st.markdown(f'<div class="app-title">{APP_TITLE}</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="app-tagline">An agent with acess to Internet and Long-Term Memory.</div>',
        unsafe_allow_html=True,
    )

    with st.form("new_chat_form", clear_on_submit=True, border=True):
        new_name = st.text_input(
            "New chat", placeholder="e.g. Trip planning", label_visibility="collapsed"
        )
        created = st.form_submit_button("+ New chat", use_container_width=True)
        if created:
            if not new_name.strip():
                st.error("Give the chat a name first.")
            else:
                try:
                    result = api.create_chat(new_name.strip())
                    chats = sorted(api.list_chats(), key=lambda c: c["id"], reverse=True)
                    st.session_state.active_chat_id = result["id"]
                except ApiError as e:
                    st.error(f"Couldn't create chat: {e}")

    icon = "☀️" if st.session_state.theme == "dark" else "🌙"
    if st.button(icon, key="theme_toggle_btn", help="Switch light/dark theme", use_container_width=True):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"

    st.divider()
    render_chat_rows(chats)

# `active_chat_id` now reflects: any chat just created above, any row just
# clicked in render_chat_rows, or a delete that just cleared it.
if st.session_state.active_chat_id is not None and not any(
    c["id"] == st.session_state.active_chat_id for c in chats
):
    st.session_state.active_chat_id = None

if st.session_state.active_chat_id is None:
    st.markdown(
        '<div class="empty-state">Select a chat from the sidebar, or create a new one, to get '
        "started.</div>",
        unsafe_allow_html=True,
    )
    st.stop()

active_id = st.session_state.active_chat_id
active_chat = next(c for c in chats if c["id"] == active_id)
ensure_chat_history_loaded(active_id)

st.markdown(f"### {active_chat['name']}")

history = st.session_state.chat_histories.setdefault(active_id, [])

chat_slot = st.empty()


def render_chat_log(chat_slot=chat_slot, history=history):
    with chat_slot.container(height=560, border=True):
        if not history:
            st.markdown(
                '<div class="empty-state">No messages yet. Say hello!</div>',
                unsafe_allow_html=True,
            )
        for turn in history:
            avatar = "🧑" if turn["role"] == "user" else "🤖"
            with st.chat_message(turn["role"], avatar=avatar):
                st.write(turn["content"])


render_chat_log()

prompt = st.chat_input("Message the agent...")
if prompt:
    history.append({"role": "user", "content": prompt})
    with st.spinner("Thinking..."):
        try:
            response = api.send_chat(active_id, prompt)
            history.append({"role": "assistant", "content": response["answer"]})
        except ApiError as e:
            history.append({"role": "assistant", "content": f"⚠️ {e}"})
    render_chat_log()

st.caption(
    "Recent messages are saved and reload with this chat; much older ones move into "
    "long-term memory and aren't replayed here, but the agent can still recall them."
)
