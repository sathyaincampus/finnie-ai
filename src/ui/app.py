"""
Finnie AI — Streamlit UI Application

Main entry point for the Streamlit frontend.
"""

import streamlit as st

# Force reload imported modules during development
import importlib
import src.agents.oracle
importlib.reload(src.agents.oracle)

from src.ui.auth import require_auth, render_user_header, logout
from src.ui.voice import render_voice_controls, speak_response, render_stt_component
from src.memory import (
    save_message, get_messages, get_conversations,
    create_conversation, auto_title_conversation,
    delete_conversation, get_conversation_summary,
    clear_user_history, upsert_user,
)

# Page configuration must be first Streamlit command
st.set_page_config(
    page_title="Finnie AI",
    page_icon="🦈",
    layout="wide",
    initial_sidebar_state="auto",
)

import asyncio
from src.config import get_settings, get_available_providers, get_models_for_provider


# =============================================================================
# Phoenix / OpenTelemetry Auto-Instrumentation
# =============================================================================

def _init_phoenix_tracing():
    """Initialize OpenTelemetry tracing to send LangChain spans to Phoenix.
    
    This auto-instruments all LangChain LLM calls (ChatOpenAI, ChatAnthropic, etc.)
    so every call shows up in the Phoenix dashboard at http://localhost:6006.
    """
    import os
    if os.getenv("PHOENIX_ENABLED", "true").lower() != "true":
        return

    try:
        from opentelemetry import trace as otel_trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SimpleSpanProcessor
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from openinference.instrumentation.langchain import LangChainInstrumentor

        # Only instrument once
        if otel_trace.get_tracer_provider().__class__.__name__ != "TracerProvider":
            # Set up OTLP exporter pointing to Phoenix
            phoenix_endpoint = os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006/v1/traces")
            exporter = OTLPSpanExporter(endpoint=phoenix_endpoint)
            
            provider = TracerProvider()
            provider.add_span_processor(SimpleSpanProcessor(exporter))
            otel_trace.set_tracer_provider(provider)
            
            # Auto-instrument LangChain — captures all ChatOpenAI/Anthropic/Google calls
            LangChainInstrumentor().instrument()

    except ImportError:
        pass  # Phoenix/OTEL not installed, skip silently
    except Exception:
        pass  # Don't crash the app if tracing fails


# Initialize tracing on app load (Streamlit re-runs this file on every interaction)
if "phoenix_initialized" not in st.session_state:
    _init_phoenix_tracing()
    st.session_state.phoenix_initialized = True


# =============================================================================
# Session State Initialization
# =============================================================================

def init_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "llm_provider" not in st.session_state:
        settings = get_settings()
        st.session_state.llm_provider = settings.default_llm_provider

    if "llm_model" not in st.session_state:
        settings = get_settings()
        st.session_state.llm_model = settings.default_llm_model

    if "llm_api_key" not in st.session_state:
        # Load API key from .env (via config) so users don't have to re-enter it
        try:
            settings = get_settings()
            st.session_state.llm_api_key = settings.get_llm_api_key()
        except (ValueError, Exception):
            st.session_state.llm_api_key = ""

    if "portfolio" not in st.session_state:
        st.session_state.portfolio = {"holdings": []}

    if "current_tab" not in st.session_state:
        st.session_state.current_tab = "Chat"

    if "current_conversation_id" not in st.session_state:
        st.session_state.current_conversation_id = None

    # Voice state
    if "voice_settings" not in st.session_state:
        st.session_state.voice_settings = {
            "enabled": False,
            "voice": "en-US-AriaNeural",
            "auto_speak": True,
        }
    if "stt_input" not in st.session_state:
        st.session_state.stt_input = None


# =============================================================================
# CSS Styling
# =============================================================================

def load_custom_css():
    """Load custom CSS for premium dark mode styling with glassmorphism."""
    st.markdown("""
    <style>
    /* ================================================================
       Import Google Fonts
       ================================================================ */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* ================================================================
       Keyframe Animations
       ================================================================ */
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    @keyframes subtleGlow {
        0%, 100% { box-shadow: 0 0 15px rgba(124, 92, 252, 0.15); }
        50% { box-shadow: 0 0 25px rgba(124, 92, 252, 0.25); }
    }

    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* ================================================================
       Global Styling
       ================================================================ */
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: rgba(15, 15, 30, 0.5);
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(124, 92, 252, 0.3);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(124, 92, 252, 0.5);
    }

    /* ================================================================
       Header — Animated Gradient Title
       ================================================================ */
    .finnie-header {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 0.5rem 0 0.3rem 0;
    }

    .finnie-logo {
        font-size: 2.4rem;
        line-height: 1;
        filter: drop-shadow(0 0 8px rgba(124, 92, 252, 0.4));
    }

    .finnie-title {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #a78bfa 0%, #7c5cfc 30%, #60a5fa 60%, #a78bfa 100%);
        background-size: 200% 200%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: gradientShift 4s ease infinite;
        letter-spacing: -0.5px;
    }

    .finnie-subtitle {
        color: #64748b;
        font-size: 0.95rem;
        font-weight: 400;
        margin-bottom: 1.5rem;
        padding-left: 2px;
    }

    /* ================================================================
       Tabs — Glassmorphism with Glow on Active
       ================================================================ */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: rgba(15, 15, 35, 0.7);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        padding: 6px;
        border-radius: 14px;
        border: 1px solid rgba(124, 92, 252, 0.12);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 10px 22px;
        font-weight: 500;
        font-size: 0.9rem;
        color: #94a3b8 !important;
        background: transparent;
        border: none;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(124, 92, 252, 0.1);
        color: #c4b5fd !important;
        transform: translateY(-1px);
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(124, 92, 252, 0.25) 0%, rgba(167, 139, 250, 0.15) 100%) !important;
        color: #e0d4ff !important;
        font-weight: 600;
        border-bottom: none !important;
        box-shadow: 0 0 20px rgba(124, 92, 252, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(124, 92, 252, 0.25);
    }

    .stTabs [data-baseweb="tab-highlight"] {
        background-color: transparent !important;
    }

    .stTabs [data-baseweb="tab-border"] {
        display: none;
    }

    /* ================================================================
       Chat Messages — Glass Bubbles with Depth
       ================================================================ */
    [data-testid="stChatMessage"] {
        background: rgba(20, 20, 45, 0.6);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 18px 22px;
        margin-bottom: 12px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
        animation: fadeInUp 0.3s ease;
        transition: border-color 0.3s ease;
    }

    [data-testid="stChatMessage"]:hover {
        border-color: rgba(124, 92, 252, 0.15);
    }

    /* User messages — purple glass tint */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        background: linear-gradient(135deg, rgba(124, 92, 252, 0.12) 0%, rgba(96, 165, 250, 0.06) 100%);
        border: 1px solid rgba(124, 92, 252, 0.2);
        box-shadow: 0 4px 16px rgba(124, 92, 252, 0.1);
    }

    /* Tables inside chat — premium styling */
    [data-testid="stChatMessage"] table {
        border-collapse: separate;
        border-spacing: 0;
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid rgba(124, 92, 252, 0.15);
        width: 100%;
        margin: 8px 0;
    }

    [data-testid="stChatMessage"] th {
        background: linear-gradient(135deg, rgba(124, 92, 252, 0.2) 0%, rgba(96, 165, 250, 0.1) 100%);
        color: #c4b5fd;
        font-weight: 600;
        padding: 10px 14px;
        text-align: left;
        font-size: 0.85rem;
        letter-spacing: 0.03em;
        border-bottom: 1px solid rgba(124, 92, 252, 0.2);
    }

    [data-testid="stChatMessage"] td {
        padding: 8px 14px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.04);
        color: #cbd5e1;
        font-size: 0.9rem;
    }

    [data-testid="stChatMessage"] tr:last-child td {
        border-bottom: none;
    }

    [data-testid="stChatMessage"] tr:hover td {
        background: rgba(124, 92, 252, 0.05);
    }

    /* ================================================================
       Inputs — Glass with Focus Glow
       ================================================================ */
    .stTextInput > div > div > input,
    [data-testid="stChatInputTextArea"] {
        background: rgba(15, 15, 35, 0.7) !important;
        backdrop-filter: blur(8px);
        border: 1px solid rgba(124, 92, 252, 0.15) !important;
        border-radius: 12px !important;
        color: #e2e8f0 !important;
        font-size: 0.95rem;
        transition: all 0.3s ease;
    }

    .stTextInput > div > div > input:focus,
    [data-testid="stChatInputTextArea"]:focus {
        border-color: #7c5cfc !important;
        box-shadow: 0 0 0 3px rgba(124, 92, 252, 0.15), 0 0 20px rgba(124, 92, 252, 0.1) !important;
    }

    .stTextInput > div > div > input::placeholder {
        color: #64748b !important;
    }

    /* ================================================================
       Buttons — Gradient with Glow Hover
       ================================================================ */
    .stButton > button {
        background: linear-gradient(135deg, #7c5cfc 0%, #6d45e8 50%, #a78bfa 100%);
        background-size: 200% 200%;
        border: none;
        border-radius: 10px;
        padding: 8px 20px;
        font-weight: 500;
        color: white;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 2px 10px rgba(124, 92, 252, 0.2);
    }

    .stButton > button:hover {
        background-position: 100% 50%;
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(124, 92, 252, 0.35);
    }

    .stButton > button:active {
        transform: translateY(0);
        box-shadow: 0 2px 8px rgba(124, 92, 252, 0.2);
    }

    /* ================================================================
       Metric Cards — Glassmorphism with Gradient Border
       ================================================================ */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(20, 20, 50, 0.8) 0%, rgba(25, 25, 55, 0.6) 100%);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(124, 92, 252, 0.15);
        border-radius: 14px;
        padding: 18px 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.05);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    [data-testid="stMetric"]:hover {
        border-color: rgba(124, 92, 252, 0.3);
        box-shadow: 0 8px 30px rgba(124, 92, 252, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.08);
        transform: translateY(-2px);
    }

    [data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 500;
    }

    [data-testid="stMetricValue"] {
        color: #f1f5f9 !important;
        font-weight: 700;
        font-size: 1.6rem;
    }

    /* Positive delta — green glow */
    [data-testid="stMetricDelta"][data-testid="stMetricDelta"] > div:first-child {
        font-weight: 600;
    }

    [data-testid="stMetricDelta"] svg {
        display: inline;
    }

    /* ================================================================
       Select Boxes / Dropdowns — Glass
       ================================================================ */
    .stSelectbox > div > div {
        background: rgba(15, 15, 35, 0.7);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(124, 92, 252, 0.12);
        border-radius: 10px;
        transition: border-color 0.3s ease;
    }

    .stSelectbox > div > div:hover {
        border-color: rgba(124, 92, 252, 0.3);
    }

    /* ================================================================
       Radio Buttons — Pill Style
       ================================================================ */
    .stRadio > div {
        gap: 6px !important;
    }

    .stRadio > div > label {
        background: rgba(20, 20, 50, 0.6);
        border: 1px solid rgba(124, 92, 252, 0.1);
        border-radius: 20px;
        padding: 6px 16px;
        transition: all 0.2s ease;
    }

    .stRadio > div > label:hover {
        border-color: rgba(124, 92, 252, 0.3);
        background: rgba(124, 92, 252, 0.08);
    }

    /* ================================================================
       Info / Warning / Success Boxes — Themed Glass
       ================================================================ */
    .stAlert {
        border-radius: 12px;
        backdrop-filter: blur(8px);
    }

    /* ================================================================
       Disclaimer
       ================================================================ */
    .disclaimer {
        font-size: 0.8rem;
        color: #94a3b8;
        padding: 10px 14px;
        background: rgba(250, 204, 21, 0.06);
        backdrop-filter: blur(8px);
        border-radius: 10px;
        border-left: 3px solid #facc15;
        margin-top: 12px;
    }

    /* ================================================================
       Welcome Card — Premium Glass
       ================================================================ */
    .welcome-card {
        background: linear-gradient(135deg, rgba(124, 92, 252, 0.12) 0%, rgba(96, 165, 250, 0.06) 50%, rgba(167, 139, 250, 0.08) 100%);
        backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);
        border: 1px solid rgba(124, 92, 252, 0.2);
        border-radius: 18px;
        padding: 28px 32px;
        margin: 12px 0 20px 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.08);
        animation: subtleGlow 3s ease-in-out infinite;
    }

    .welcome-card h3 {
        background: linear-gradient(135deg, #c4b5fd, #60a5fa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 12px;
        font-weight: 700;
    }

    .welcome-card p {
        color: #94a3b8;
        line-height: 1.6;
    }

    .welcome-card .feature-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        margin-top: 16px;
    }

    .welcome-card .feature-item {
        display: flex;
        align-items: center;
        gap: 8px;
        color: #cbd5e1;
        font-size: 0.9rem;
        padding: 8px 12px;
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.04);
        transition: all 0.2s ease;
    }

    .welcome-card .feature-item:hover {
        background: rgba(124, 92, 252, 0.08);
        border-color: rgba(124, 92, 252, 0.15);
    }

    .welcome-card .feature-item .icon {
        font-size: 1.1rem;
    }

    /* ================================================================
       Subheaders — Gradient Left Bar
       ================================================================ */
    [data-testid="stSubheader"] {
        padding-left: 14px !important;
        border-left: 3px solid;
        border-image: linear-gradient(to bottom, #7c5cfc, #60a5fa) 1;
    }

    /* ================================================================
       Expanders — Glass
       ================================================================ */
    .stExpander {
        background: rgba(20, 20, 50, 0.4);
        border: 1px solid rgba(124, 92, 252, 0.1);
        border-radius: 12px;
        overflow: hidden;
    }

    .stExpander:hover {
        border-color: rgba(124, 92, 252, 0.2);
    }

    /* ================================================================
       Dividers
       ================================================================ */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(to right, transparent, rgba(124, 92, 252, 0.2), transparent);
        margin: 1.2rem 0;
    }

    /* ================================================================
       Data Tables (st.dataframe)
       ================================================================ */
    [data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid rgba(124, 92, 252, 0.12);
    }

    /* ================================================================
       Plotly Charts — Remove White Background
       ================================================================ */
    .stPlotlyChart {
        border-radius: 14px;
        overflow: hidden;
        border: 1px solid rgba(124, 92, 252, 0.1);
        background: rgba(15, 15, 35, 0.4);
    }

    /* ================================================================
       Hide Streamlit Branding
       ================================================================ */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] {
        background: transparent;
    }

    /* ================================================================
       Markdown Tables (outside chat) — Premium Style
       ================================================================ */
    [data-testid="stMarkdownContainer"] table {
        border-collapse: separate;
        border-spacing: 0;
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid rgba(124, 92, 252, 0.12);
        width: 100%;
    }

    [data-testid="stMarkdownContainer"] th {
        background: linear-gradient(135deg, rgba(124, 92, 252, 0.15), rgba(96, 165, 250, 0.08));
        color: #c4b5fd;
        font-weight: 600;
        padding: 10px 14px;
        text-align: left;
        font-size: 0.85rem;
        border-bottom: 1px solid rgba(124, 92, 252, 0.15);
    }

    [data-testid="stMarkdownContainer"] td {
        padding: 8px 14px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.04);
        color: #cbd5e1;
    }

    [data-testid="stMarkdownContainer"] tr:last-child td {
        border-bottom: none;
    }

    /* ================================================================
       Spinner — Themed
       ================================================================ */
    .stSpinner > div > div {
        border-color: #7c5cfc transparent transparent transparent !important;
    }

    /* ================================================================
       Columns gap fix
       ================================================================ */
    [data-testid="stHorizontalBlock"] {
        gap: 12px;
    }

    /* ================================================================
       Responsive — Mobile
       ================================================================ */
    @media (max-width: 768px) {
        .finnie-title {
            font-size: 1.6rem;
        }
        .welcome-card .feature-grid {
            grid-template-columns: 1fr;
        }

        /* Chat message text — prevent overflow */
        [data-testid="stChatMessage"] {
            padding: 12px 14px;
            overflow-x: hidden;
        }
        [data-testid="stChatMessage"] p,
        [data-testid="stChatMessage"] li,
        [data-testid="stChatMessage"] td,
        [data-testid="stChatMessage"] th {
            word-wrap: break-word;
            overflow-wrap: break-word;
            word-break: break-word;
        }

        /* Tables inside chat — horizontal scroll */
        [data-testid="stChatMessage"] table {
            display: block;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            font-size: 0.8rem;
            white-space: nowrap;
        }

        /* Tighter metric cards */
        [data-testid="stMetric"] {
            padding: 12px 10px;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.2rem !important;
        }

        /* Column padding */
        div[data-testid="column"] {
            padding: 0 4px !important;
        }

        /* Expanders */
        .stExpander {
            padding: 0 !important;
        }

        /* Markdown content — horizontal scroll for tables */
        [data-testid="stMarkdownContainer"] {
            overflow-x: auto;
        }
        [data-testid="stMarkdownContainer"] table {
            display: block;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
        }

        /* Tabs — smaller on mobile */
        .stTabs [data-baseweb="tab"] {
            padding: 8px 12px;
            font-size: 0.8rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)


# =============================================================================
# Tab Components
# =============================================================================

def _process_chat_input(user_input: str, is_guest: bool, user_id: str):
    """Process a chat input (from text or voice) and generate a response."""
    # Ensure we have a conversation ID
    if not st.session_state.current_conversation_id and not is_guest:
        conv_id = create_conversation(user_id)
        st.session_state.current_conversation_id = conv_id

    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
    })

    # Save user message to DB (non-guest only)
    conv_id = st.session_state.current_conversation_id
    if conv_id:
        save_message(conv_id, "user", user_input)
        # Auto-title on first message
        if len(st.session_state.messages) == 1:
            auto_title_conversation(conv_id, user_input)

    with st.spinner("🦈 Thinking..."):
        response = generate_response(user_input)

    st.session_state.messages.append({
        "role": "assistant",
        "content": response,
    })

    # Save assistant response to DB
    if conv_id:
        save_message(conv_id, "assistant", response)

    # Run Phoenix evaluations in background (non-blocking)
    import threading
    def _bg_eval():
        try:
            from src.evals import run_evals_on_response
            results = run_evals_on_response(user_input=user_input, response=response)
            if results:
                import logging
                logging.getLogger("finnie.evals").info(f"Evals logged: {list(results.keys())}")
        except Exception as e:
            import logging, traceback
            logging.getLogger("finnie.evals").error(f"Eval failed: {e}\n{traceback.format_exc()}")
    threading.Thread(target=_bg_eval, daemon=True).start()

    # Flag for TTS — defer to render phase (audio would be destroyed by rerun)
    voice = st.session_state.voice_settings
    if voice.get("enabled") and voice.get("auto_speak"):
        st.session_state._speak_next = response

    st.rerun()


def render_chat_tab():
    """Render the Chat tab using Streamlit's native chat components."""
    user = st.session_state.get("user", {})
    user_id = user.get("user_id", "guest")
    is_guest = user.get("provider") == "guest"

    # ── Voice controls bar ──────────────────────────────────────
    voice = render_voice_controls()
    st.session_state.voice_settings = voice

    if voice["enabled"]:
        st.markdown("---")

    # Welcome card if no messages
    if not st.session_state.messages:
        name = user.get("name", "")
        greeting = f"Welcome back, {name}!" if name and not is_guest else "Welcome to Finnie AI"
        st.markdown(f"""
        <div class="welcome-card">
            <h3>👋 {greeting}</h3>
            <p>Your autonomous financial intelligence assistant. Ask me anything about the markets!</p>
            <div class="feature-grid">
                <div class="feature-item"><span class="icon">📊</span> Real-time stock prices</div>
                <div class="feature-item"><span class="icon">📚</span> Financial education</div>
                <div class="feature-item"><span class="icon">🔮</span> Investment projections</div>
                <div class="feature-item"><span class="icon">💼</span> Portfolio analysis</div>
                <div class="feature-item"><span class="icon">🌍</span> Market trends</div>
                <div class="feature-item"><span class="icon">🛡️</span> Risk awareness</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Display message history using native Streamlit chat
    for message in st.session_state.messages:
        avatar = "🦈" if message["role"] == "assistant" else "👤"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

    # ── TTS playback (deferred from _process_chat_input) ─────────
    if st.session_state.get("_speak_next"):
        text_to_speak = st.session_state._speak_next
        st.session_state._speak_next = None
        speak_response(text_to_speak, voice=voice.get("voice", "en-US-AriaNeural"))

    # ── Voice input (STT) ───────────────────────────────────────
    if voice["enabled"]:
        stt_result = render_stt_component()
        if stt_result and isinstance(stt_result, str) and stt_result.strip():
            _process_chat_input(stt_result.strip(), is_guest, user_id)

    # Chat input — use rerun pattern so messages always appear above input
    # Handle "Ask Finnie" from Knowledge Explorer
    if pending := st.session_state.pop("pending_chat_question", None):
        _process_chat_input(pending, is_guest, user_id)

    if user_input := st.chat_input("Ask anything about finance..."):
        _process_chat_input(user_input, is_guest, user_id)


def _normalize_ticker(raw: str) -> str:
    """Normalize ticker input: handle BRK.B → BRK-B, lowercase, whitespace."""
    t = raw.strip().upper()
    t = t.replace(".", "-")  # Yahoo uses BRK-B format
    return t


def _fetch_live_price(ticker: str) -> dict | None:
    """Fetch live price data for a ticker via yfinance."""
    import yfinance as yf
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        if info and info.get("shortName"):
            price = info.get('regularMarketPrice', info.get('previousClose', 0))
            return {
                "name": info.get("shortName", ticker),
                "price": price or 0,
                "prev_close": info.get("previousClose", price),
            }
    except Exception:
        pass
    return None


def render_portfolio_tab():
    """Render the Portfolio tab with live pricing."""
    holdings = st.session_state.portfolio.get("holdings", [])

    # ── Add holding form (top for easy access) ──────────────────
    st.markdown("#### ➕ Add Position")
    st.caption("Enter your **current** shares and cost basis per share (as shown in your brokerage).")

    add_col1, add_col2, add_col3 = st.columns(3)
    with add_col1:
        ticker = st.text_input("Ticker", placeholder="AAPL, BRK-B, MSFT")
    with add_col2:
        shares = st.number_input("Current Shares", min_value=0.0, step=1.0,
                                 help="Your current share count (post any splits)")
    with add_col3:
        cost_basis = st.number_input("Avg Cost / Share ($)", min_value=0.0, step=0.01,
                                     help="Your average cost basis per share")

    if st.button("Add Position", use_container_width=True):
        if ticker and shares > 0:
            normalized = _normalize_ticker(ticker)
            st.session_state.portfolio["holdings"].append({
                "ticker": normalized,
                "shares": shares,
                "cost_basis": cost_basis,
            })
            st.success(f"Added {shares:.0f} shares of {normalized}")
            st.rerun()

    if not holdings:
        st.info("No holdings yet. Add your first position above!")
        return

    # ── Fetch live prices for all holdings ──────────────────────
    st.markdown("---")
    st.markdown("#### 📊 Your Portfolio")

    with st.spinner("Fetching live prices..."):
        enriched = []
        for h in holdings:
            live = _fetch_live_price(h["ticker"])
            if live and live["price"]:
                current_price = live["price"]
                current_value = current_price * h["shares"]
                cost_total = h["cost_basis"] * h["shares"]
                gain_loss = current_value - cost_total
                gain_pct = (gain_loss / cost_total * 100) if cost_total > 0 else 0
                enriched.append({
                    **h,
                    "name": live["name"],
                    "current_price": current_price,
                    "current_value": current_value,
                    "cost_total": cost_total,
                    "gain_loss": gain_loss,
                    "gain_pct": gain_pct,
                })
            else:
                cost_total = h["cost_basis"] * h["shares"]
                enriched.append({
                    **h,
                    "name": h["ticker"],
                    "current_price": 0,
                    "current_value": 0,
                    "cost_total": cost_total,
                    "gain_loss": 0,
                    "gain_pct": 0,
                })

    # ── Summary metrics ─────────────────────────────────────────
    total_value = sum(e["current_value"] for e in enriched)
    total_cost = sum(e["cost_total"] for e in enriched)
    total_gain = total_value - total_cost
    total_gain_pct = (total_gain / total_cost * 100) if total_cost > 0 else 0

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("💰 Total Value", f"${total_value:,.2f}")
    with m2:
        st.metric("💵 Total Cost", f"${total_cost:,.2f}")
    with m3:
        arrow = "📈" if total_gain >= 0 else "📉"
        st.metric(f"{arrow} Total Gain/Loss", f"${total_gain:,.2f}",
                 f"{total_gain_pct:+.1f}%")
    with m4:
        st.metric("📋 Positions", f"{len(enriched)}")

    # ── Holdings table ──────────────────────────────────────────
    st.markdown("---")

    for idx, e in enumerate(enriched):
        with st.container():
            c1, c2, c3, c4, c5, c6 = st.columns([2, 1.2, 1.2, 1.5, 1.5, 0.6])
            with c1:
                st.markdown(f"**{e['ticker']}**")
                st.caption(e["name"])
            with c2:
                st.markdown(f"{e['shares']:.0f} shares")
            with c3:
                st.markdown(f"${e['current_price']:.2f}")
                st.caption(f"Cost: ${e['cost_basis']:.2f}")
            with c4:
                st.markdown(f"${e['current_value']:,.2f}")
                st.caption(f"Cost: ${e['cost_total']:,.2f}")
            with c5:
                color = "🟢" if e["gain_loss"] >= 0 else "🔴"
                st.markdown(f"{color} ${e['gain_loss']:,.2f} ({e['gain_pct']:+.1f}%)")
            with c6:
                if st.button("❌", key=f"del_{idx}", help=f"Remove {e['ticker']}"):
                    st.session_state.portfolio["holdings"].pop(idx)
                    st.rerun()
            st.markdown("", unsafe_allow_html=True)  # spacer

    # ── Allocation chart ────────────────────────────────────────
    if total_value > 0:
        st.markdown("---")
        st.markdown("#### 📊 Allocation")

        import plotly.express as px
        import pandas as pd

        chart_data = [{"ticker": e["ticker"], "value": e["current_value"]} for e in enriched if e["current_value"] > 0]
        if chart_data:
            df = pd.DataFrame(chart_data)
            fig = px.pie(
                df, values='value', names='ticker', hole=0.45,
                color_discrete_sequence=['#7c5cfc', '#a78bfa', '#c4b5fd', '#38bdf8', '#34d399', '#f472b6']
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#94a3b8',
                showlegend=True,
                legend=dict(font=dict(size=12)),
                margin=dict(t=20, b=20, l=20, r=20),
                height=350,
            )
            fig.update_traces(textfont_color='white', textinfo='label+percent')
            st.plotly_chart(fig, use_container_width=True)

    # ── Clear portfolio button ──────────────────────────────────
    st.markdown("---")
    if st.button("🗑️ Clear All Holdings"):
        st.session_state.portfolio = {"holdings": []}
        st.rerun()


def render_market_tab():
    """Render the Market tab (delegates to modular implementation)."""
    from src.ui.tabs.market import render_market_tab as _render_market_modular
    _render_market_modular()


def render_projections_tab():
    """Render the Projections tab with forward and goal-based modes."""
    st.markdown("#### 🔮 Investment Projection Calculator")

    # Mode selector
    proj_mode = st.radio(
        "Projection Mode",
        ["📊 Forward Projection", "🎯 Goal-Based (Reverse)"],
        horizontal=True,
        key="proj_mode_select",
    )

    if "Forward" in proj_mode:
        _render_forward_projection()
    else:
        _render_goal_projection()


def _render_forward_projection():
    """Forward projection: How will my investment grow?"""
    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("**Configure your scenario**")
        initial = st.number_input("Initial Investment ($)", value=10000, step=1000)
        monthly = st.number_input("Monthly Contribution ($)", value=500, step=100)
        years = st.slider("Time Horizon (Years)", 1, 30, 10)

        # Risk profile selector
        risk_profile = st.radio(
            "Risk Profile",
            ["🛡️ Conservative", "⚖️ Moderate", "🚀 Aggressive"],
            index=1,
            horizontal=True,
            key="risk_profile",
        )

        # Map risk profile to return/volatility params
        risk_params = {
            "🛡️ Conservative": {"return": 0.05, "volatility": 0.10, "label": "Conservative (Bonds/Stable)"},
            "⚖️ Moderate":     {"return": 0.08, "volatility": 0.18, "label": "Moderate (S&P 500 blend)"},
            "🚀 Aggressive":   {"return": 0.12, "volatility": 0.25, "label": "Aggressive (Growth/Tech)"},
        }
        params = risk_params[risk_profile]

        if st.button("🔮 Calculate Projection", use_container_width=True):
            from src.agents.oracle import OracleAgent

            agent = OracleAgent()
            simulation = agent._monte_carlo_simulation(
                initial, monthly, years,
                annual_return=params["return"],
                annual_std=params["volatility"],
            )
            st.session_state.projection = simulation
            st.session_state.projection_params = {
                "initial": initial, "monthly": monthly, "years": years,
                "risk_label": params["label"],
                "annual_return": params["return"],
                "annual_std": params["volatility"],
            }

    with col2:
        if "projection" in st.session_state:
            sim = st.session_state.projection
            params = st.session_state.get("projection_params", {})

            st.markdown(f"**Projected outcomes for ${params.get('initial', 0):,} + ${params.get('monthly', 0):,}/mo over {params.get('years', 0)} years**")

            r1, r2, r3 = st.columns(3)
            with r1:
                st.metric("📉 Conservative", f"${sim['conservative']:,.0f}",
                         f"{sim['growth_conservative']:.1f}%")
            with r2:
                st.metric("📊 Expected", f"${sim['expected']:,.0f}",
                         f"{sim['growth_expected']:.1f}%")
            with r3:
                st.metric("📈 Optimistic", f"${sim['optimistic']:,.0f}",
                         f"{sim['growth_optimistic']:.1f}%")

            st.info(f"💰 Total Contributions: ${sim['total_contributions']:,.0f}")

            risk_label = params.get('risk_label', 'Moderate (S&P 500 blend)')
            avg_return = params.get('annual_return', 0.08)
            vol = params.get('annual_std', 0.18)
            st.markdown(f"""
            <div class="disclaimer">
                ⚠️ Based on 1,000 Monte Carlo simulations · Risk: <b>{risk_label}</b> ·
                {avg_return*100:.0f}% avg return · {vol*100:.0f}% volatility.
                Past performance does not guarantee future results.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="welcome-card">
                <h3>📐 How it works</h3>
                <p>We run 1,000 Monte Carlo simulations based on historical S&P 500 returns
                to project three scenarios for your investment growth.</p>
                <div class="feature-grid">
                    <div class="feature-item"><span class="icon">📉</span> Conservative (10th percentile)</div>
                    <div class="feature-item"><span class="icon">📊</span> Expected (50th percentile)</div>
                    <div class="feature-item"><span class="icon">📈</span> Optimistic (90th percentile)</div>
                    <div class="feature-item"><span class="icon">🎲</span> Based on real volatility data</div>
                </div>
            </div>
            """, unsafe_allow_html=True)


def _render_goal_projection():
    """Goal-based reverse projection: How much do I need to invest?"""
    import math

    st.markdown("**🎯 I need a specific amount by a target date**")

    col1, col2 = st.columns(2)

    with col1:
        target_amount = st.number_input(
            "Target Amount ($)", min_value=1000, max_value=100_000_000,
            value=1_000_000, step=50000, key="goal_target",
        )
        current_age = st.number_input(
            "Your Current Age", min_value=18, max_value=80,
            value=30, key="goal_current_age",
        )
        target_age = st.number_input(
            "Target Age", min_value=25, max_value=90,
            value=55, key="goal_target_age",
        )

    with col2:
        current_savings = st.number_input(
            "Current Savings ($)", min_value=0, max_value=50_000_000,
            value=50000, step=5000, key="goal_savings",
        )
        risk_profile = st.selectbox(
            "Risk Profile",
            ["Conservative (6%)", "Moderate (8%)", "Aggressive (10%)"],
            index=1, key="goal_risk_profile",
        )

    years_to_goal = max(1, target_age - current_age)

    if st.button("🎯 Calculate Required Investment", use_container_width=True, key="calc_goal"):
        profiles = {
            "Conservative (6%)": 0.06,
            "Moderate (8%)": 0.08,
            "Aggressive (10%)": 0.10,
        }

        st.divider()
        st.subheader(f"🎯 Path to ${target_amount:,.0f} by Age {target_age}")

        results_cols = st.columns(3)
        all_results = {}

        for i, (name, rate) in enumerate(profiles.items()):
            months = years_to_goal * 12
            monthly_rate = rate / 12

            # Future value of current savings
            fv_current = current_savings * ((1 + monthly_rate) ** months)
            remaining = max(0, target_amount - fv_current)

            # Required monthly contribution
            if monthly_rate > 0 and months > 0:
                monthly_needed = remaining * monthly_rate / (((1 + monthly_rate) ** months) - 1)
            else:
                monthly_needed = remaining / max(months, 1)

            total_contrib = current_savings + (monthly_needed * months)
            growth = target_amount - total_contrib

            emoji = ["📉", "📊", "📈"][i]
            label = name.split("(")[0].strip()

            with results_cols[i]:
                st.metric(
                    f"{emoji} {label} ({rate*100:.0f}%)",
                    f"${monthly_needed:,.0f}/mo",
                    f"${growth:,.0f} growth",
                )

            all_results[label] = {
                "monthly": monthly_needed,
                "total": total_contrib,
                "growth": growth,
                "rate": rate,
            }

        # Summary
        st.caption(f"Starting with ${current_savings:,.0f} · {years_to_goal} years · Age {current_age} → {target_age}")

        selected_rate = profiles.get(risk_profile, 0.08)
        selected_label = risk_profile.split("(")[0].strip()
        selected = all_results.get(selected_label, {})

        if selected:
            st.success(
                f"💡 **Recommended ({selected_label}):** Invest **${selected['monthly']:,.0f}/month** "
                f"to reach **${target_amount:,.0f}** by age **{target_age}**."
            )

        # Growth chart
        try:
            import plotly.graph_objects as go

            fig = go.Figure()

            for label, data in all_results.items():
                monthly_r = data["rate"] / 12
                balance = current_savings
                chart_x = [current_age]
                chart_y = [current_savings]

                for yr in range(1, years_to_goal + 1):
                    for _ in range(12):
                        balance = balance * (1 + monthly_r) + data["monthly"]
                    chart_x.append(current_age + yr)
                    chart_y.append(balance)

                colors = {"Conservative": "#06b6d4", "Moderate": "#6366f1", "Aggressive": "#22c55e"}
                fig.add_trace(go.Scatter(
                    x=chart_x, y=chart_y,
                    name=f"{label} ({data['rate']*100:.0f}%)",
                    line=dict(color=colors.get(label, "#6366f1"), width=2),
                    hovertemplate="Age %{x}<br>$%{y:,.0f}<extra></extra>",
                ))

            fig.add_hline(
                y=target_amount, line_dash="dash", line_color="#f59e0b",
                annotation_text=f"Goal: ${target_amount:,.0f}",
            )

            fig.update_layout(
                title=f"Growth Projection: Age {current_age} → {target_age}",
                xaxis_title="Age",
                yaxis_title="Portfolio Value ($)",
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=400,
                yaxis=dict(tickformat="$,.0f"),
            )

            st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            pass

        st.markdown("""
        <div class="disclaimer">
            ⚠️ Projections assume consistent monthly contributions and fixed annual returns.
            Actual results will vary based on market conditions.
        </div>
        """, unsafe_allow_html=True)


def render_settings_tab():
    """Render the Settings tab."""
    st.markdown("#### ⚙️ LLM Provider Configuration")

    # Provider selection
    available_providers = get_available_providers()
    if not available_providers:
        available_providers = ["openai", "anthropic", "google"]

    provider = st.selectbox(
        "LLM Provider",
        available_providers,
        index=available_providers.index(st.session_state.llm_provider)
              if st.session_state.llm_provider in available_providers else 0,
    )

    # Model selection
    models = get_models_for_provider(provider)
    model_ids = [m[0] for m in models]
    model_names = [f"{m[1]} ({m[0]})" for m in models]

    current_model_idx = 0
    if st.session_state.llm_model in model_ids:
        current_model_idx = model_ids.index(st.session_state.llm_model)

    model_selection = st.selectbox(
        "Model",
        model_names,
        index=current_model_idx,
    )

    selected_model = model_ids[model_names.index(model_selection)]

    # API Key
    api_key = st.text_input(
        f"{provider.title()} API Key",
        value=st.session_state.llm_api_key,
        type="password",
        placeholder=f"Enter your {provider} API key",
    )

    if st.button("💾 Save Settings", use_container_width=True):
        st.session_state.llm_provider = provider
        st.session_state.llm_model = selected_model
        st.session_state.llm_api_key = api_key
        st.success("Settings saved!")

    # Connection status
    st.markdown("---")
    st.markdown("#### Connection Status")

    if st.session_state.llm_api_key:
        st.success(f"✅ Connected — {provider.title()} / {selected_model}")
    else:
        st.warning(f"⚠️ No API key — market data & projections still work without one")

    # Feature status
    st.markdown("---")
    st.markdown("#### Feature Status")

    status_col1, status_col2 = st.columns(2)
    with status_col1:
        st.markdown("✅ Market Data (yFinance)")
        st.markdown("✅ Projections (Monte Carlo)")
        st.markdown("✅ Portfolio Tracking")
    with status_col2:
        st.markdown(f"{'✅' if st.session_state.llm_api_key else '⬜'} LLM Chat")
        st.markdown("✅ Voice Interface (TTS + STT)")
        # Cache graph check in session_state to avoid blocking every rerun
        if "_graphrag_available" not in st.session_state:
            try:
                from src.graphrag.graph_client import is_graph_available
                st.session_state._graphrag_available = is_graph_available()
            except Exception:
                st.session_state._graphrag_available = False
        graph_ok = st.session_state._graphrag_available
        st.markdown(f"{'✅' if graph_ok else '⬜'} GraphRAG")
        if not graph_ok:
            if st.button("🔄 Re-check GraphRAG", key="recheck_graphrag"):
                try:
                    from src.graphrag.graph_client import is_graph_available
                    st.session_state._graphrag_available = is_graph_available()
                    st.rerun()
                except Exception:
                    pass


# =============================================================================
# Message Processing
# =============================================================================

def generate_response(user_input: str) -> str:
    """Generate a response to user input.
    
    Routing priority:
    1. Greetings (only when no conversation history) → default help
    2. Educational queries → Professor agent
    3. Trending queries → Scout agent
    3b. Financial planning → Planner agent
    4. Projection queries → Oracle agent
    5. Ticker-based queries → Quant agent (last, to avoid false positives)
    6. Contextual fallback (with history) → LLM with conversation context
    7. No history fallback → default help response
    """
    user_lower = user_input.lower().strip()
    has_history = len(st.session_state.get("messages", [])) > 0

    # ── 1. Greetings & simple messages (ONLY when no conversation history) ──
    greeting_patterns = ["hello", "hi", "hey", "help", "what can you do",
                         "who are you", "good morning", "good evening", "thanks",
                         "thank you", "sup", "yo", "howdy"]
    if not has_history and (user_lower in greeting_patterns or any(user_lower == p for p in greeting_patterns)):
        return _default_response()

    # ── 2. Educational queries ──────────────────────────────────
    educational_patterns = [
        "what is", "what's a ", "what are", "explain", "how does",
        "how do", "tell me about", "define", "meaning of",
        "difference between", "why is", "why do", "what does",
    ]
    if any(user_lower.startswith(p) or f" {p}" in f" {user_lower}" for p in educational_patterns):
        # Check if this is really a stock query like "what is AAPL trading at"
        stock_qualifiers = ["trading at", "price of", "stock price", "worth right now",
                            "share price", "trading for", "cost basis"]
        has_stock_qualifier = any(q in user_lower for q in stock_qualifiers)
        has_ticker = bool(extract_tickers(user_input))

        # Check if this is really an investment / market question
        market_qualifiers = [
            "invest", "investment", "buy", "sell", "market trend",
            "best stock", "best sector", "portfolio", "right now",
            "should i", "recommend", "opportunity", "current market",
        ]

        if has_stock_qualifier and has_ticker:
            pass  # fall through to ticker-based routing below
        elif any(q in user_lower for q in market_qualifiers):
            # Route to Scout for market/investment strategy questions
            from src.agents.scout import ScoutAgent
            agent = ScoutAgent()
            state = {
                "user_input": user_input,
                "llm_provider": st.session_state.llm_provider,
                "llm_model": st.session_state.llm_model,
                "llm_api_key": st.session_state.llm_api_key,
            }
            result = asyncio.run(agent.process(state))
            response = result.get("content", "Let me check the market for you.")
            response += "\n\n---\n*⚠️ Educational purposes only, not financial advice.*"
            return response
        else:
            # Route to Professor for pure educational queries
            from src.agents.professor import ProfessorAgent
            agent = ProfessorAgent()

            state = {
                "user_input": user_input,
                "llm_provider": st.session_state.llm_provider,
                "llm_model": st.session_state.llm_model,
                "llm_api_key": st.session_state.llm_api_key,
            }

            result = asyncio.run(agent.process(state))
            return result.get("content", "Let me find that information for you.")

    # ── 3. Trending queries ─────────────────────────────────────
    trending_patterns = ["trending", "movers", "hot stocks", "what's moving",
                         "market today", "top gainers", "top losers",
                         "best invest", "market trend", "current market",
                         "should i buy", "best stock", "opportunity",
                         "market move", "how did the market", "market do",
                         "last week", "last month", "this week",
                         "will move", "on monday", "on tuesday", "on wednesday",
                         "on thursday", "on friday", "next week", "tomorrow",
                         "what will", "predict", "forecast", "outlook",
                         "momentum", "recent momentum"]
    if any(p in user_lower for p in trending_patterns):
        from src.agents.scout import ScoutAgent
        agent = ScoutAgent()
        state = {
            "user_input": user_input,
            "llm_provider": st.session_state.llm_provider,
            "llm_model": st.session_state.llm_model,
            "llm_api_key": st.session_state.llm_api_key,
        }
        result = asyncio.run(agent.process(state))
        response = result.get("content", "Let me check the market movers.")
        response += "\n\n---\n*⚠️ Educational purposes only, not financial advice.*"
        return response

    # ── 3b. Financial planning queries ──────────────────────────
    planning_patterns = [
        "save for", "saving for", "savings for", "plan for",
        "retirement goal", "retire", "retirement", "college savings",
        "college fund", "education fund", "529", "down payment",
        "buy a home", "buy a house", "home purchase",
        "financial plan", "financial goal", "money goal",
        "how should i", "what should i do", "help me plan",
        "save for my", "need to save", "want to save",
        "2 sons", "2 kids", "two kids", "two sons", "children",
        "emergency fund", "million dollar",
    ]
    # Multi-goal indicator: mentions 2+ distinct financial goals
    goal_keywords = ["college", "retirement", "home", "house", "down payment",
                     "emergency", "car", "wedding", "vacation", "debt"]
    goal_count = sum(1 for kw in goal_keywords if kw in user_lower)

    if goal_count >= 2 or any(p in user_lower for p in planning_patterns):
        from src.agents.planner import PlannerAgent
        agent = PlannerAgent()
        state = {
            "user_input": user_input,
            "enhanced_input": user_input,
            "llm_provider": st.session_state.llm_provider,
            "llm_model": st.session_state.llm_model,
            "llm_api_key": st.session_state.llm_api_key,
            "portfolio_data": st.session_state.portfolio.get("holdings", []),
        }
        result = asyncio.run(agent.process(state))
        response = result.get("content", "Let me help you create a financial plan.")

        # Store parsed plan data for the Plan Builder tab
        plan_data = result.get("data", {})
        if plan_data:
            st.session_state.active_plan = plan_data

        response += "\n\n---\n📋 **Open the Plan Builder tab** to adjust assumptions and see detailed year-over-year projections with interactive controls."
        response += "\n\n*⚠️ This is educational guidance, not professional financial advice.*"
        return response

    # ── 4. Projection queries ───────────────────────────────────
    projection_patterns = ["if i invest", "project", "how much will",
                           "growth", "invest $", "compound", "returns on"]
    if any(p in user_lower for p in projection_patterns):
        from src.agents.oracle import OracleAgent
        agent = OracleAgent()
        state = {"user_input": user_input}
        result = asyncio.run(agent.process(state))
        return result.get("content", "Check the Projections tab for detailed calculations!")

    # ── 5. Analysis / stock-specific queries ─────────────────────
    # Catch "analyze", "should I buy [company]", "compare" etc.
    analysis_patterns = ["analyze", "analysis", "compare", "versus",
                         "should i buy", "should i sell", "worth buying",
                         "good investment", "undervalued", "overvalued"]
    if any(p in user_lower for p in analysis_patterns):
        # Try to find a company name → ticker mapping
        COMPANY_TO_TICKER = {
            "google": "GOOGL", "apple": "AAPL", "microsoft": "MSFT",
            "amazon": "AMZN", "tesla": "TSLA", "nvidia": "NVDA",
            "meta": "META", "facebook": "META", "netflix": "NFLX",
            "disney": "DIS", "berkshire": "BRK-B", "coinbase": "COIN",
            "paypal": "PYPL", "shopify": "SHOP", "uber": "UBER",
            "palantir": "PLTR", "amd": "AMD", "intel": "INTC",
            "starbucks": "SBUX", "nike": "NKE", "walmart": "WMT",
            "costco": "COST", "boeing": "BA",
        }
        found_tickers = []
        for company, ticker in COMPANY_TO_TICKER.items():
            if company in user_lower:
                found_tickers.append(ticker)
        # Also check for actual tickers in the text
        found_tickers.extend(extract_tickers(user_input))
        found_tickers = list(dict.fromkeys(found_tickers))  # dedupe, preserve order

        if found_tickers:
            from src.agents.quant import QuantAgent
            agent = QuantAgent()
            state = {
                "user_input": user_input,
                "tickers": found_tickers,
                "llm_provider": st.session_state.llm_provider,
                "llm_model": st.session_state.llm_model,
                "llm_api_key": st.session_state.llm_api_key,
            }
            result = asyncio.run(agent.process(state))
            response = result.get("content", "I couldn't fetch that data.")
            response += "\n\n---\n*⚠️ Educational purposes only, not financial advice.*"
            return response

    # ── 6. Ticker-based queries (last priority) ─────────────────
    tickers = extract_tickers(user_input)

    # Also check company names if no tickers found
    if not tickers:
        COMPANY_TO_TICKER = {
            "google": "GOOGL", "apple": "AAPL", "microsoft": "MSFT",
            "amazon": "AMZN", "tesla": "TSLA", "nvidia": "NVDA",
            "meta": "META", "facebook": "META", "netflix": "NFLX",
        }
        for company, ticker in COMPANY_TO_TICKER.items():
            if company in user_lower:
                tickers.append(ticker)

    if tickers:
        # Apply common typo corrections
        TICKER_CORRECTIONS = {
            "APPL": "AAPL", "APLE": "AAPL", "APPLE": "AAPL",
            "GOGLE": "GOOGL", "GOOG": "GOOGL", "GOOGLE": "GOOGL",
            "AMAZN": "AMZN", "AMAZON": "AMZN",
            "FB": "META", "FACEBOOK": "META",
            "BRKB": "BRK-B", "BRKA": "BRK-A",
            "BERKSHIRE": "BRK-B", "NVIDIA": "NVDA",
            "TESLA": "TSLA", "MICROSOFT": "MSFT",
        }
        tickers = [TICKER_CORRECTIONS.get(t, t) for t in tickers]

        from src.agents.quant import QuantAgent
        agent = QuantAgent()

        state = {
            "user_input": user_input,
            "tickers": tickers,  # pass corrected tickers
            "llm_provider": st.session_state.llm_provider,
            "llm_model": st.session_state.llm_model,
            "llm_api_key": st.session_state.llm_api_key,
        }

        result = asyncio.run(agent.process(state))
        response = result.get("content", "I couldn't fetch that data.")
        response += "\n\n---\n*⚠️ Educational purposes only, not financial advice.*"
        return response

    # ── Fallback — contextual LLM response with conversation history ──
    if has_history:
        return _contextual_llm_response(user_input)

    return _default_response()


def _contextual_llm_response(user_input: str) -> str:
    """Generate a contextual response using conversation history.
    
    Uses smart context management:
    - Keep first 2 messages (original intent/context)
    - Summarize middle messages (compressed essence)
    - Keep last 5 messages (recent conversation)
    
    Also uses LLM gateway for cost-optimized model routing.
    """
    from src.llm import get_llm_adapter

    messages = st.session_state.get("messages", [])
    
    # ── Context Window Management ──
    # Keep original + recent, compress the middle
    if len(messages) <= 8:
        # Short conversation — use all messages
        history = messages
    else:
        # Long conversation — compress middle
        first_msgs = messages[:2]    # original intent
        last_msgs = messages[-5:]    # recent context
        middle_msgs = messages[2:-5] # to be summarized
        
        # Create a compressed summary of middle messages
        middle_summary = _summarize_middle_context(middle_msgs)
        
        history = first_msgs + [
            {"role": "assistant", "content": f"[Earlier conversation summary: {middle_summary}]"}
        ] + last_msgs
    
    llm_messages = []
    for msg in history:
        llm_messages.append({
            "role": msg["role"],
            "content": msg["content"],
        })

    # Add the current user message
    llm_messages.append({"role": "user", "content": user_input})

    system_prompt = """You are Finnie AI 🦈, an autonomous financial intelligence assistant.

You are having a conversation with a user about their finances. Use the conversation
history to understand context and provide relevant, helpful follow-up answers.

Your capabilities:
- Stock prices and market data (real-time via yfinance)
- Financial education (explain concepts clearly)
- Investment projections and Monte Carlo simulations
- Financial planning (retirement, 529 college savings, home buying, tax optimization)
- Portfolio analysis and allocation advice
- Crypto market data
- Market trends and news
- Index rebalancing strategies (NASDAQ-100, S&P 500, Dow Jones, Russell 2000)

Rules:
- Be specific with numbers, dollar amounts, and percentages
- Reference the user's earlier goals/context from the conversation
- Use markdown formatting for readability
- If the user asks about stocks to invest in, provide specific tickers with rationale
- If the user asks a follow-up to a financial plan, reference their specific goals
- Always add: "⚠️ This is educational guidance, not professional financial advice."
- Be concise but comprehensive"""

    try:
        # ── Smart routing — pick model based on query complexity ──
        try:
            from src.llm_gateway import get_routed_model, track_usage
            routed = get_routed_model(user_input)
            provider = routed["provider"]
            model = routed["model"]
            api_key = routed["api_key"]
        except ImportError:
            provider = st.session_state.llm_provider
            model = st.session_state.llm_model
            api_key = st.session_state.llm_api_key
        
        adapter = get_llm_adapter(
            provider=provider,
            model=model,
            api_key=api_key,
        )

        response = asyncio.run(adapter.chat(
            messages=llm_messages,
            system_prompt=system_prompt,
        ))

        # Track usage
        try:
            from src.llm_gateway import track_usage
            tier = routed.get("tier", "full")
            # Estimate tokens (rough: 4 chars per token)
            input_tokens = sum(len(m["content"]) // 4 for m in llm_messages)
            output_tokens = len(response.content) // 4
            track_usage(tier, input_tokens, output_tokens)
        except Exception:
            pass

        return response.content
    except Exception as e:
        return (
            "I'd love to help with that! Based on our conversation, could you "
            "provide a bit more detail? For example:\n\n"
            "- **Stock recommendations:** \"What are good index funds for long-term growth?\"\n"
            "- **Plan adjustments:** \"What if I increase my monthly savings to $3,000?\"\n"
            "- **Market data:** \"What's AAPL trading at?\"\n\n"
            "*⚠️ This is educational guidance, not professional financial advice.*"
        )


def _summarize_middle_context(middle_msgs: list[dict]) -> str:
    """Compress middle conversation messages into a brief summary.
    
    Uses a lightweight approach: extract key topics and numbers
    without an LLM call (to save cost and latency).
    """
    if not middle_msgs:
        return "No additional context."
    
    # Extract key content snippets
    topics = []
    for msg in middle_msgs:
        content = msg.get("content", "")
        # Keep first 100 chars of each message as a hint
        snippet = content[:100].replace("\n", " ").strip()
        if snippet:
            role = "User" if msg["role"] == "user" else "Finnie"
            topics.append(f"{role}: {snippet}...")
    
    return " | ".join(topics[:6])  # max 6 snippets


def _default_response() -> str:
    """Return the default help response. Only shown for first interaction."""
    return """I'm **Finnie AI**, your financial intelligence assistant! 🦈

Here's what I can do:

| Command | Example |
|---------|---------|
| 📊 **Stock Prices** | "What's AAPL trading at?" |
| 📚 **Education** | "What is P/E ratio?" |
| 🌍 **Trending** | "What's trending today?" |
| 🔮 **Projections** | "If I invest $10k for 10 years" |
| 📋 **Financial Planning** | "Help me plan for retirement and college" |
| 💼 **Portfolio** | Use the Portfolio tab |

Try one of these to get started!"""


def extract_tickers(text: str) -> list[str]:
    """Extract stock tickers from text.
    
    Uses a whitelist approach to avoid false positives:
    - $AAPL — always treated as a ticker (explicit signal)
    - BRK-A / BRK.B — hyphenated/dotted always treated as tickers
    - AAPL — bare uppercase words only match KNOWN popular tickers
    
    This avoids the endless whack-a-mole of excluding common words.
    """
    import re
    upper_text = text.upper()

    tickers = []

    # Known popular tickers — bare words only match these
    KNOWN_TICKERS = {
        # Major indices & ETFs
        "SPY", "QQQ", "DIA", "IWM", "VTI", "VOO", "ARKK", "XLF", "XLE", "XLK",
        # Mega-cap tech
        "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "META", "NVDA", "TSLA",
        # Major companies
        "JPM", "JNJ", "UNH", "PG", "HD", "BAC", "WMT", "KO", "PEP", "MCD",
        "DIS", "NFLX", "PYPL", "SQ", "SHOP", "UBER", "LYFT", "SNAP", "PINS",
        "AMD", "INTC", "CRM", "ORCL", "IBM", "CSCO", "QCOM", "AVGO", "TXN",
        "BA", "GE", "CAT", "MMM", "GS", "MS", "C", "WFC", "V", "MA", "AXP",
        "PFE", "MRNA", "ABBV", "BMY", "LLY", "MRK", "AMGN", "GILD",
        "XOM", "CVX", "COP", "SLB", "OXY",
        "COST", "TGT", "LOW", "SBUX", "NKE", "LULU",
        "COIN", "HOOD", "PLTR", "SOFI", "RIVN", "LCID", "NIO",
        "F", "GM", "TM", "ABNB", "BKNG", "MAR",
        # Crypto-related
        "MSTR", "MARA", "RIOT",
    }

    # Pattern 1: $-prefixed (always a ticker) — e.g. $AAPL, $BRK-A
    for m in re.finditer(r'\$([A-Z]{1,5})(?:[\-\.]([A-Z]{1,2}))?\b', upper_text):
        if m.group(2):
            ticker = f"{m.group(1)}-{m.group(2)}"
        else:
            ticker = m.group(1)
        if ticker not in tickers:
            tickers.append(ticker)

    # Pattern 2: Hyphenated/dotted (always a ticker) — e.g. BRK-A, BRK.B
    for m in re.finditer(r'\b([A-Z]{1,5})[\-\.]([A-Z]{1,2})\b', upper_text):
        ticker = f"{m.group(1)}-{m.group(2)}"
        if ticker not in tickers:
            tickers.append(ticker)

    # Pattern 3: Bare uppercase words — ONLY match if in KNOWN_TICKERS
    hyph_parts = set()
    for t in tickers:
        hyph_parts.update(t.split('-'))

    for m in re.finditer(r'\b([A-Z]{1,5})\b', upper_text):
        word = m.group(1)
        if (word in KNOWN_TICKERS
            and word not in tickers
            and word not in hyph_parts):
            tickers.append(word)

    return tickers


# =============================================================================
# Main App
# =============================================================================

def render_sidebar():
    """Render conversation sidebar with history and new chat button."""
    user = st.session_state.get("user", {})
    user_id = user.get("user_id", "guest")
    is_guest = user.get("provider") == "guest"

    with st.sidebar:
        # User info at top
        name = user.get("name", "Guest")
        avatar = user.get("avatar_url", "")
        provider = user.get("provider", "guest")

        if avatar:
            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:10px; padding:0.5rem 0; margin-bottom:0.5rem;">
                <img src="{avatar}" style="width:36px; height:36px; border-radius:50%;">
                <div>
                    <div style="font-weight:600; font-size:0.95rem;">{name}</div>
                    <div style="font-size:0.75rem; color:#888;">{provider.title()}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            emoji = "👤" if is_guest else "🔵"
            st.markdown(f"**{emoji} {name}**")
            if is_guest:
                st.caption("Guest mode — chats not saved")

        st.markdown("---")

        # New Chat button
        if st.button("➕ New Chat", use_container_width=True, type="primary"):
            st.session_state.messages = []
            st.session_state.current_conversation_id = None
            st.rerun()

        # Conversation history (authenticated users only)
        if not is_guest:
            st.markdown("##### 💬 Recent Chats")
            conversations = get_conversations(user_id, limit=15)

            if conversations:
                for conv in conversations:
                    conv_id = conv["id"]
                    title = conv.get("title", "New Chat")[:35]
                    msg_count = conv.get("message_count", 0)
                    date = conv.get("updated_at", "")[:10]
                    is_active = conv_id == st.session_state.current_conversation_id

                    col1, col2 = st.columns([5, 1])
                    with col1:
                        label = f"{'▸ ' if is_active else ''}{title}"
                        if st.button(
                            label,
                            key=f"conv_{conv_id}",
                            use_container_width=True,
                            type="primary" if is_active else "secondary",
                        ):
                            # Load this conversation
                            st.session_state.current_conversation_id = conv_id
                            msgs = get_messages(conv_id)
                            st.session_state.messages = [
                                {"role": m["role"], "content": m["content"]} for m in msgs
                            ]
                            st.rerun()
                    with col2:
                        if st.button("🗑", key=f"del_conv_{conv_id}", help="Delete"):
                            delete_conversation(conv_id)
                            if conv_id == st.session_state.current_conversation_id:
                                st.session_state.messages = []
                                st.session_state.current_conversation_id = None
                            st.rerun()
            else:
                st.caption("No conversations yet")

            st.markdown("---")
            if st.button("🗑️ Clear All History", use_container_width=True):
                clear_user_history(user_id)
                st.session_state.messages = []
                st.session_state.current_conversation_id = None
                st.rerun()

        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            logout()


def main():
    """Main application entry point."""
    init_session_state()
    load_custom_css()

    # ── Auth gate ──────────────────────────────────────────────
    user = require_auth()

    # Register user in DB if authenticated (non-guest)
    if user.get("provider") != "guest":
        upsert_user(
            user_id=user["user_id"],
            email=user["email"],
            name=user["name"],
            avatar_url=user.get("avatar_url", ""),
            provider=user["provider"],
        )

    # ── Sidebar ───────────────────────────────────────────────
    render_sidebar()

    # ── Header ────────────────────────────────────────────────
    st.markdown("""
    <div class="finnie-header">
        <span class="finnie-logo">🦈</span>
        <span class="finnie-title">Finnie AI</span>
    </div>
    <p class="finnie-subtitle">Autonomous Financial Intelligence</p>
    """, unsafe_allow_html=True)

    # Tabs — expanded with Plan Builder and Crypto
    tabs = st.tabs([
        "💬 Chat",
        "📊 Portfolio",
        "📈 Market",
        "🔮 Projections",
        "📋 Plan Builder",
        "🪙 Crypto",
        "⚙️ Settings",
        "❓ Help",
    ])

    with tabs[0]:
        render_chat_tab()

    with tabs[1]:
        render_portfolio_tab()

    with tabs[2]:
        render_market_tab()

    with tabs[3]:
        render_projections_tab()

    with tabs[4]:
        # Interactive Plan Builder — imported from modular tab
        from src.ui.tabs.plan_builder import render_plan_builder_tab as _render_plan_builder
        _render_plan_builder()

    with tabs[5]:
        # Crypto Dashboard — imported from modular tab
        from src.ui.tabs.crypto import render_crypto_tab as _render_crypto
        _render_crypto()

    with tabs[6]:
        render_settings_tab()

    with tabs[7]:
        from src.ui.tabs.help import render_help_tab as _render_help
        _render_help()


if __name__ == "__main__":
    main()

