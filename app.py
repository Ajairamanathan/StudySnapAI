import streamlit as st
import time

from google import genai
from google.genai.errors import APIError
from google.genai import types

from prompts import (
    SYSTEM_PROMPT,
    WELCOME_MESSAGE_TEMPLATE,
    SUMMARY_REQUEST_PROMPT
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="StudySnap AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CONFIGURATION
# ============================================================

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

MODEL_NAME = "gemini-3.1-flash-lite"


# ============================================================
# GEMINI CLIENT
# ============================================================

@st.cache_resource
def get_gemini_client():

    return genai.Client(
        api_key=GEMINI_API_KEY
    )


gemini_client = get_gemini_client()


def create_gemini_chat():

    return gemini_client.chats.create(
        model=MODEL_NAME,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT
        )
    )


# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []


if "onboarded" not in st.session_state:
    st.session_state.onboarded = False


if (
    st.session_state.onboarded
    and st.session_state.get("chat_model") != MODEL_NAME
):
    st.session_state.chat = create_gemini_chat()
    st.session_state.chat_model = MODEL_NAME


# ============================================================
# MESSAGE RENDERING
# ============================================================

def render_message(message):

    with st.chat_message(message["role"]):

        if message["kind"] == "text":

            st.markdown(message["content"])

        elif message["kind"] == "image":

            st.image(
                message["content"],
                use_container_width=True
            )


def add_message(role, kind, content):

    st.session_state.messages.append(
        {
            "role": role,
            "kind": kind,
            "content": content
        }
    )

    render_message(
        st.session_state.messages[-1]
    )


# ============================================================
# GEMINI REQUEST
# ============================================================

def ask_gemini(parts):

    for attempt in range(3):

        try:

            response = st.session_state.chat.send_message(
                parts
            )

            if response.text:
                return response.text

            return "I couldn't generate an answer."

        except APIError as error:

            if error.code == 503 and attempt < 2:
                time.sleep(attempt + 1)
                continue

            return (
                "⚠️ Something went wrong while contacting Gemini.\n\n"
                f"`{error}`"
            )

        except Exception as error:

            return (
                "⚠️ Something went wrong while contacting Gemini.\n\n"
                f"`{error}`"
            )


# ============================================================
# ONBOARDING
# ============================================================

if not st.session_state.onboarded:

    st.title("📚 StudySnap AI")

    st.subheader(
        "Your AI-powered exam study assistant"
    )

    st.write(
        "Upload questions, notes, diagrams or textbook pages "
        "and let AI explain them."
    )

    st.divider()

    with st.form("onboarding_form"):

        name = st.text_input(
            "Your name",
            placeholder="Enter your name"
        )

        email = st.text_input(
            "Your email",
            placeholder="yourname@gmail.com"
        )

        submitted = st.form_submit_button(
            "🚀 Start Studying",
            use_container_width=True
        )

    if submitted:

        if not name.strip():

            st.warning(
                "Please enter your name."
            )

        elif not email.strip():

            st.warning(
                "Please enter your email."
            )

        else:

            st.session_state.name = name.strip()

            st.session_state.email = email.strip()

            st.session_state.chat = create_gemini_chat()
            st.session_state.chat_model = MODEL_NAME

            st.session_state.messages = []

            st.session_state.onboarded = True

            st.rerun()

    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("📚 StudySnap")

    st.caption(
        "AI Exam Study Assistant"
    )

    st.divider()

    st.write(
        f"👤 **Student**\n\n"
        f"{st.session_state.name}"
    )

    st.write(
        f"📧 **Email**\n\n"
        f"{st.session_state.email}"
    )

    st.divider()

    st.subheader("🎯 Quick Prompts")

    if st.button(
        "📝 2 Mark Answer",
        use_container_width=True
    ):

        st.session_state.quick_prompt = (
            "Give me a concise 2-mark exam answer."
        )

    if st.button(
        "📖 5 Mark Answer",
        use_container_width=True
    ):

        st.session_state.quick_prompt = (
            "Give me a clear 5-mark exam answer."
        )

    if st.button(
        "📚 8 Mark Answer",
        use_container_width=True
    ):

        st.session_state.quick_prompt = (
            "Give me a detailed 8-mark exam answer "
            "with important points and diagram explanation."
        )

    if st.button(
        "📕 10 Mark Answer",
        use_container_width=True
    ):

        st.session_state.quick_prompt = (
            "Give me a detailed 10-mark exam answer."
        )

    if st.button(
        "📘 16 Mark Answer",
        use_container_width=True
    ):

        st.session_state.quick_prompt = (
            "Give me a complete 16-mark exam answer "
            "with definition, explanation, diagram, "
            "working, example, advantages and applications."
        )

    if st.button(
        "🗣️ Explain in Thunglish",
        use_container_width=True
    ):

        st.session_state.quick_prompt = (
            "Explain this in simple Thunglish."
        )

    st.divider()

    st.caption(
        "StudySnap AI • Gemini Vision"
    )


# ============================================================
# MAIN HEADER
# ============================================================

header_col, action_col = st.columns(
    [6, 2],
    vertical_alignment="center"
)


with header_col:

    st.title("📚 StudySnap AI")

    st.caption(
        "Upload. Understand. Prepare. Score."
    )


with action_col:

    if st.button(
        "📩 Study Notes",
        use_container_width=True
    ):

        if len(st.session_state.messages) <= 1:

            st.warning(
                "Ask at least one question first."
            )

        else:

            with st.spinner(
                "Preparing your study notes..."
            ):

                summary = ask_gemini(
                    [SUMMARY_REQUEST_PROMPT]
                )

            st.session_state.generated_summary = summary

            st.success(
                "Study notes generated!"
            )


st.divider()


# ============================================================
# WELCOME MESSAGE
# ============================================================

if not st.session_state.messages:

    add_message(
        "assistant",
        "text",
        WELCOME_MESSAGE_TEMPLATE.format(
            name=st.session_state.name
        )
    )

else:

    for message in st.session_state.messages:

        render_message(message)


# ============================================================
# QUICK PROMPT HANDLER
# ============================================================

if "quick_prompt" in st.session_state:

    prompt = st.session_state.quick_prompt

    del st.session_state.quick_prompt

    add_message(
        "user",
        "text",
        prompt
    )

    with st.spinner(
        "StudySnap is thinking..."
    ):

        answer = ask_gemini(
            [prompt]
        )

    add_message(
        "assistant",
        "text",
        answer
    )


# ============================================================
# CHAT INPUT
# ============================================================

user_input = st.chat_input(
    "Ask a question or attach an image...",
    accept_file=True,
    file_type=[
        "jpg",
        "jpeg",
        "png",
        "webp"
    ]
)


if user_input:

    photo = (
        user_input.files[0]
        if user_input.files
        else None
    )

    text = user_input.text

    parts = []


    # --------------------------------------------------------
    # IMAGE
    # --------------------------------------------------------

    if photo is not None:

        photo_bytes = photo.getvalue()

        add_message(
            "user",
            "image",
            photo_bytes
        )

        parts.append(
            types.Part.from_bytes(
                data=photo_bytes,
                mime_type=photo.type
            )
        )


    # --------------------------------------------------------
    # TEXT
    # --------------------------------------------------------

    if text:

        add_message(
            "user",
            "text",
            text
        )

        parts.append(text)


    # --------------------------------------------------------
    # IMAGE WITHOUT TEXT
    # --------------------------------------------------------

    elif photo is not None:

        parts.append(
            """
            Analyze this uploaded academic image.

            Identify the question or topic.

            Explain the content clearly.

            Provide an exam-ready answer.

            Include important formulas, algorithms,
            steps and diagram explanations when applicable.
            """
        )


    # --------------------------------------------------------
    # GEMINI
    # --------------------------------------------------------

    if parts:

        with st.spinner(
            "🔍 StudySnap is analyzing..."
        ):

            answer = ask_gemini(
                parts
            )

        add_message(
            "assistant",
            "text",
            answer
        )


# ============================================================
# GENERATED STUDY NOTES
# ============================================================

if "generated_summary" in st.session_state:

    st.divider()

    st.subheader(
        "📖 Your Study Notes"
    )

    st.markdown(
        st.session_state.generated_summary
    )

    st.download_button(
        label="⬇️ Download Study Notes",
        data=st.session_state.generated_summary,
        file_name="studysnap_notes.txt",
        mime="text/plain",
        use_container_width=True
    )