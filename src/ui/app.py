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
    """Load custom CSS for premium dark mode styling."""
    st.markdown("""
    <style>
    /* ================================================================
       Import Google Fonts
       ================================================================ */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* ================================================================
       Global styling
       ================================================================ */
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* ================================================================
       Header
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
    }

    .finnie-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #a78bfa;
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
       Tabs — clean, readable labels
       ================================================================ */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: rgba(30, 30, 50, 0.6);
        padding: 6px;
        border-radius: 14px;
        border: 1px solid rgba(255, 255, 255, 0.06);
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 10px 22px;
        font-weight: 500;
        font-size: 0.9rem;
        color: #94a3b8 !important;
        background: transparent;
        border: none;
        transition: all 0.2s ease;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(167, 139, 250, 0.1);
        color: #c4b5fd !important;
    }

    .stTabs [aria-selected="true"] {
        background: rgba(167, 139, 250, 0.18) !important;
        color: #c4b5fd !important;
        font-weight: 600;
        border-bottom: none !important;
    }

    /* tab bottom border override */
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: transparent !important;
    }

    .stTabs [data-baseweb="tab-border"] {
        display: none;
    }

    /* ================================================================
       Chat messages — use Streamlit native, but improve theme
       ================================================================ */
    [data-testid="stChatMessage"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 14px;
        padding: 16px 20px;
        margin-bottom: 10px;
    }

    /* User messages */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        background: rgba(167, 139, 250, 0.08);
        border: 1px solid rgba(167, 139, 250, 0.15);
    }

    /* ================================================================
       Inputs
       ================================================================ */
    .stTextInput > div > div > input,
    [data-testid="stChatInputTextArea"] {
        background: rgba(30, 30, 50, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        color: #e2e8f0 !important;
        font-size: 0.95rem;
    }

    .stTextInput > div > div > input:focus,
    [data-testid="stChatInputTextArea"]:focus {
        border-color: #7c5cfc !important;
        box-shadow: 0 0 0 2px rgba(124, 92, 252, 0.2) !important;
    }

    .stTextInput > div > div > input::placeholder {
        color: #64748b !important;
    }

    /* ================================================================
       Buttons
       ================================================================ */
    .stButton > button {
        background: linear-gradient(135deg, #7c5cfc 0%, #a78bfa 100%);
        border: none;
        border-radius: 10px;
        padding: 8px 20px;
        font-weight: 500;
        color: white;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        opacity: 0.9;
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(124, 92, 252, 0.3);
    }

    .stButton > button:active {
        transform: translateY(0);
    }

    /* ================================================================
       Metrics
       ================================================================ */
    [data-testid="stMetric"] {
        background: rgba(30, 30, 50, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 16px;
    }

    [data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
        font-size: 0.85rem;
    }

    [data-testid="stMetricValue"] {
        color: #e2e8f0 !important;
        font-weight: 600;
    }

    /* Positive delta */
    [data-testid="stMetricDelta"] svg {
        display: inline;
    }

    /* ================================================================
       Select boxes / Dropdowns
       ================================================================ */
    .stSelectbox > div > div {
        background: rgba(30, 30, 50, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }

    /* ================================================================
       Info / Warning / Success boxes
       ================================================================ */
    .stAlert {
        border-radius: 10px;
    }

    /* ================================================================
       Disclaimer
       ================================================================ */
    .disclaimer {
        font-size: 0.8rem;
        color: #94a3b8;
        padding: 10px 14px;
        background: rgba(250, 204, 21, 0.08);
        border-radius: 10px;
        border-left: 3px solid #facc15;
        margin-top: 12px;
    }

    /* ================================================================
       Welcome card
       ================================================================ */
    .welcome-card {
        background: linear-gradient(135deg, rgba(124, 92, 252, 0.1) 0%, rgba(167, 139, 250, 0.05) 100%);
        border: 1px solid rgba(167, 139, 250, 0.15);
        border-radius: 16px;
        padding: 28px 32px;
        margin: 12px 0 20px 0;
    }

    .welcome-card h3 {
        color: #c4b5fd;
        margin-bottom: 12px;
        font-weight: 600;
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
        padding: 6px 0;
    }

    .welcome-card .feature-item .icon {
        font-size: 1.1rem;
    }

    /* ================================================================
       Dividers
       ================================================================ */
    hr {
        border: none;
        border-top: 1px solid rgba(255, 255, 255, 0.06);
        margin: 1rem 0;
    }

    /* ================================================================
       Hide Streamlit branding
       ================================================================ */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] {
        background: transparent;
    }

    /* ================================================================
       Responsive
       ================================================================ */
    @media (max-width: 768px) {
        .finnie-title {
            font-size: 1.6rem;
        }
        .welcome-card .feature-grid {
            grid-template-columns: 1fr;
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
    """Render the Market tab."""
    st.markdown("#### 📈 Market Lookup")
    st.caption("Supports tickers like AAPL, BRK-B, BRK.B, GOOGL")

    # Common typo corrections
    TICKER_CORRECTIONS = {
        "APPL": "AAPL", "APLE": "AAPL", "APPLE": "AAPL",
        "GOGLE": "GOOGL", "GOOG": "GOOGL", "GOOGLE": "GOOGL",
        "MSFT": "MSFT", "MICROSOFT": "MSFT",
        "AMAZN": "AMZN", "AMAZON": "AMZN",
        "TSLA": "TSLA", "TESLA": "TSLA",
        "FB": "META", "FACEBOOK": "META",
        "NVDA": "NVDA", "NVIDIA": "NVDA",
        "BRKB": "BRK-B", "BRKA": "BRK-A",
        "BERKSHIRE": "BRK-B",
    }

    # Input row with search button
    input_col, btn_col = st.columns([5, 1])
    with input_col:
        raw_ticker = st.text_input("Enter stock ticker", placeholder="e.g., AAPL, BRK-B, NVDA",
                                   label_visibility="collapsed", key="market_input")
    with btn_col:
        search_clicked = st.button("🔍 Search", use_container_width=True)

    # Quick access buttons — 2 rows of 4
    st.caption("Quick access:")
    quick_tickers = ["AAPL", "GOOGL", "MSFT", "AMZN", "NVDA", "TSLA", "META", "BRK-B"]
    row1 = st.columns(4)
    row2 = st.columns(4)
    for i, qt in enumerate(quick_tickers):
        col = row1[i] if i < 4 else row2[i - 4]
        with col:
            if st.button(qt, key=f"quick_{qt}", use_container_width=True):
                st.session_state.active_market_ticker = qt
                st.rerun()

    # Determine which ticker to look up — persist in session state
    if search_clicked and raw_ticker:
        st.session_state.active_market_ticker = raw_ticker
    elif raw_ticker and not st.session_state.get("active_market_ticker"):
        st.session_state.active_market_ticker = raw_ticker

    ticker_to_lookup = st.session_state.get("active_market_ticker")

    if ticker_to_lookup:
        ticker = _normalize_ticker(ticker_to_lookup)

        # Check for typo corrections
        corrected = TICKER_CORRECTIONS.get(ticker, None)
        if corrected and corrected != ticker:
            st.info(f"🔄 Corrected **{ticker}** → **{corrected}**")
            ticker = corrected

        with st.spinner(f"Fetching data for {ticker}..."):
            try:
                import yfinance as yf
                stock = yf.Ticker(ticker)
                info = stock.info

                if info and info.get("shortName"):
                    st.markdown(f"### {info.get('shortName', ticker)} ({ticker})")

                    col1, col2, col3, col4 = st.columns(4)

                    price = info.get('regularMarketPrice', info.get('previousClose', 0))
                    prev_close = info.get('previousClose', price)
                    change = price - prev_close if price and prev_close else 0
                    change_pct = (change / prev_close * 100) if prev_close else 0

                    with col1:
                        st.metric("Price", f"${price:.2f}", f"{change_pct:+.2f}%")
                    with col2:
                        mc = info.get('marketCap', 0)
                        if mc >= 1e12:
                            mc_str = f"${mc/1e12:.2f}T"
                        elif mc >= 1e9:
                            mc_str = f"${mc/1e9:.1f}B"
                        else:
                            mc_str = f"${mc/1e6:.0f}M"
                        st.metric("Market Cap", mc_str)
                    with col3:
                        pe = info.get('trailingPE')
                        st.metric("P/E Ratio", f"{pe:.1f}" if pe else "N/A")
                    with col4:
                        st.metric("52W High", f"${info.get('fiftyTwoWeekHigh', 0):.2f}")

                    # Price chart with time range selector
                    st.markdown("---")

                    # Time range selector — radio keeps state across reruns
                    range_map = {"1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y", "2Y": "2y", "5Y": "5y"}
                    selected_label = st.radio(
                        "Chart range", list(range_map.keys()),
                        index=2,  # default to 6M
                        horizontal=True,
                        key="chart_range",
                        label_visibility="collapsed",
                    )
                    period = range_map[selected_label]
                    hist = stock.history(period=period)
                    if not hist.empty:
                        import plotly.graph_objects as go
                        fig = go.Figure()

                        # Calculate Y range from data with 5% padding
                        y_min = hist['Close'].min()
                        y_max = hist['Close'].max()
                        y_pad = (y_max - y_min) * 0.05
                        fig.add_trace(go.Scatter(
                            x=hist.index, y=hist['Close'],
                            mode='lines',
                            line=dict(color='#7c5cfc', width=2),
                            fill='tozeroy',
                            fillcolor='rgba(124, 92, 252, 0.1)',
                            name='Close'
                        ))
                        fig.update_layout(
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)',
                            font_color='#94a3b8',
                            xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
                            yaxis=dict(
                                gridcolor='rgba(255,255,255,0.05)',
                                range=[y_min - y_pad, y_max + y_pad],
                                fixedrange=True,  # lock Y — zoom only on time axis
                            ),
                            dragmode='zoom',  # default to horizontal zoom
                            margin=dict(t=10, b=30, l=50, r=20),
                            height=300,
                            showlegend=False,
                        )
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning(f"No data found for **{ticker}**. Check the ticker symbol — for Apple use `AAPL`, not `APPL`.")
            except Exception as e:
                st.error(f"Couldn't fetch data: {str(e)}")


def render_projections_tab():
    """Render the Projections tab."""
    st.markdown("#### 🔮 Investment Projection Calculator")

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
        st.markdown("⬜ GraphRAG")


# =============================================================================
# Message Processing
# =============================================================================

def generate_response(user_input: str) -> str:
    """Generate a response to user input.
    
    Routing priority:
    1. Greetings / general queries → default help response
    2. Educational queries → Professor agent
    3. Trending queries → Scout agent
    4. Projection queries → Oracle agent
    5. Ticker-based queries → Quant agent (last, to avoid false positives)
    """
    user_lower = user_input.lower().strip()

    # ── 1. Greetings & simple messages ──────────────────────────
    greeting_patterns = ["hello", "hi", "hey", "help", "what can you do",
                         "who are you", "good morning", "good evening", "thanks",
                         "thank you", "sup", "yo", "howdy"]
    if user_lower in greeting_patterns or any(user_lower == p for p in greeting_patterns):
        return _default_response()

    # ── 2. Educational queries ──────────────────────────────────
    educational_patterns = [
        "what is", "what's a ", "what are", "explain", "how does",
        "how do", "tell me about", "define", "meaning of",
        "difference between", "why is", "why do", "what does",
    ]
    if any(user_lower.startswith(p) or f" {p}" in f" {user_lower}" for p in educational_patterns):
        # Check if this is really a stock query like "what is AAPL trading at"
        stock_qualifiers = ["trading", "price", "stock price", "worth", "cost"]
        # Check if this is really an investment / market question
        market_qualifiers = [
            "invest", "investment", "buy", "sell", "market trend",
            "best stock", "best sector", "portfolio", "right now",
            "should i", "recommend", "opportunity", "current market",
        ]
        if any(q in user_lower for q in stock_qualifiers):
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

    # ── Fallback ────────────────────────────────────────────────
    return _default_response()


def _default_response() -> str:
    """Return the default help response."""
    return """I'm **Finnie AI**, your financial intelligence assistant! 🦈

Here's what I can do:

| Command | Example |
|---------|---------|
| 📊 **Stock Prices** | "What's AAPL trading at?" |
| 📚 **Education** | "What is P/E ratio?" |
| 🌍 **Trending** | "What's trending today?" |
| 🔮 **Projections** | "If I invest $10k for 10 years" |
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

    # Tabs
    tabs = st.tabs(["💬 Chat", "📊 Portfolio", "📈 Market", "🔮 Projections", "⚙️ Settings"])

    with tabs[0]:
        render_chat_tab()

    with tabs[1]:
        render_portfolio_tab()

    with tabs[2]:
        render_market_tab()

    with tabs[3]:
        render_projections_tab()

    with tabs[4]:
        render_settings_tab()


if __name__ == "__main__":
    main()
