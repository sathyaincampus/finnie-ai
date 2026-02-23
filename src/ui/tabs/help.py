"""
Finnie AI — Help & Features Tab

Interactive guide showing all features, example queries, and tips.
"""

import streamlit as st


def render_help_tab():
    """Render the Help & Features tab."""

    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(124, 92, 252, 0.15) 0%, rgba(96, 165, 250, 0.08) 100%);
        border: 1px solid rgba(124, 92, 252, 0.25);
        border-radius: 18px;
        padding: 28px 32px;
        margin-bottom: 24px;
        backdrop-filter: blur(12px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
    ">
        <h2 style="
            background: linear-gradient(135deg, #c4b5fd, #60a5fa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0 0 8px 0;
            font-size: 1.8rem;
        ">Welcome to Finnie AI</h2>
        <p style="color: #94a3b8; font-size: 1rem; margin: 0;">
            Your autonomous financial intelligence assistant — powered by 11 specialized AI agents,
            real-time market data, and a 105-concept knowledge graph.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ─── Feature Cards ───────────────────────────────────────────────
    features = [
        {
            "icon": "💬",
            "title": "AI Chat",
            "tab": "Chat",
            "description": "Ask any financial question. 11 agents collaborate behind the scenes — market data, education, portfolio analysis, crypto, and planning.",
            "examples": [
                "What's AAPL trading at?",
                "Compare TSLA and F stock",
                "Explain dollar cost averaging",
                "I'm on H1B with $200K savings, plan my finances",
                "What's Bitcoin price?",
            ],
        },
        {
            "icon": "📊",
            "title": "Portfolio Tracker",
            "tab": "Portfolio",
            "description": "Add your holdings and get real-time portfolio valuation, allocation breakdown, gain/loss tracking, and risk metrics.",
            "examples": [
                "Add: AAPL 100 shares @ $150",
                "Add: NVDA 50 shares @ $110",
                "View allocation pie chart",
                "Track total gain/loss",
            ],
        },
        {
            "icon": "📈",
            "title": "Market Dashboard",
            "tab": "Market",
            "description": "Live market indices (S&P 500, NASDAQ, Dow), Market Movers (top gainers & losers), and deep stock lookup with interactive charts.",
            "examples": [
                "Quick access buttons: AAPL, GOOGL, MSFT",
                "View 6M candlestick chart",
                "See today's top gainers",
                "Check P/E ratio and 52W high",
            ],
        },
        {
            "icon": "🔮",
            "title": "Projections",
            "tab": "Projections",
            "description": "Monte Carlo simulations for investment growth. See conservative, expected, and optimistic outcomes with interactive charts.",
            "examples": [
                "Project $50K invested, $1000/month for 20 years",
                "Goal: $1M in 15 years, how much monthly?",
                "Compare aggressive vs conservative returns",
            ],
        },
        {
            "icon": "📋",
            "title": "Plan Builder",
            "tab": "Plan Builder",
            "description": "Interactive financial goal cards. Set retirement, education, home, and emergency fund targets with visual progress tracking.",
            "examples": [
                "Set retirement goal: $2M by age 60",
                "College fund: $200K in 10 years",
                "Emergency fund: 12 months expenses",
            ],
        },
        {
            "icon": "🪙",
            "title": "Crypto Dashboard",
            "tab": "Crypto",
            "description": "Real-time crypto prices via CoinGecko. Track BTC, ETH, SOL, and 20+ coins with 24h change, market cap, and volume.",
            "examples": [
                "What's BTC trading at?",
                "Compare ETH and SOL",
                "Crypto market overview",
            ],
        },
    ]

    for i, feat in enumerate(features):
        _render_feature_card(feat, i)

    # ─── Knowledge Explorer ──────────────────────────────────────────
    st.markdown("---")
    _render_knowledge_explorer()

    # ─── Agent Architecture ──────────────────────────────────────────
    st.markdown("---")
    st.subheader("🤖 AI Agent Architecture")

    st.markdown("""
    Finnie AI uses **11 specialized agents** that collaborate on every query:

    | Agent | Role | Emoji |
    |-------|------|-------|
    | **Enhancer** | Optimizes your query before processing | ✨ |
    | **Quant** | Real-time stock data & market metrics | 📊 |
    | **Professor** | Financial education & concept explanations | 📚 |
    | **Analyst** | Deep company & sector analysis | 🔬 |
    | **Advisor** | Portfolio strategy & asset allocation | 💼 |
    | **Oracle** | Projections & Monte Carlo simulations | 🔮 |
    | **Scout** | News, trends & market intelligence | 🔍 |
    | **Planner** | Comprehensive financial life planning | 📋 |
    | **Crypto** | Cryptocurrency market data & analysis | 🪙 |
    | **Guardian** | Compliance checks & safety disclaimers | 🛡️ |
    | **Scribe** | Formats & synthesizes final responses | ✍️ |
    """)

    # ─── Technology Stack ────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🛠️ Technology Stack")

    cols = st.columns(3)
    with cols[0]:
        st.markdown("""
        **AI / LLM**
        - Google Gemini 2.0 Flash
        - LangChain + LangGraph
        - GraphRAG (Neo4j/AuraDB)
        - 105 financial concepts
        """)
    with cols[1]:
        st.markdown("""
        **Data & APIs**
        - yfinance (stocks)
        - CoinGecko (crypto)
        - MCP Tools protocol
        - Real-time market feeds
        """)
    with cols[2]:
        st.markdown("""
        **Infrastructure**
        - Streamlit UI
        - Docker / Cloud Run
        - Phoenix observability
        - FastAPI endpoints
        """)

    # ─── Tips ────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("💡 Tips for Best Results")

    st.markdown("""
    1. **Be specific** — "Compare AAPL and MSFT P/E ratios" works better than "tell me about stocks"
    2. **Mention your situation** — "I'm 35, on H1B, $150K income, $200K saved" unlocks personalized plans
    3. **Ask follow-ups** — The chat remembers context within your session
    4. **Use ticker symbols** — AAPL, TSLA, BTC for fastest responses
    5. **Try voice** — Click the 🎤 mic button for hands-free interaction
    """)

    # ─── Disclaimer ──────────────────────────────────────────────────
    st.markdown("""
    <div class="disclaimer">
        ⚠️ <strong>Disclaimer:</strong> Finnie AI provides educational financial information only.
        It is not a registered investment advisor. Always consult a qualified financial professional
        before making investment decisions.
    </div>
    """, unsafe_allow_html=True)


def _render_feature_card(feat: dict, index: int):
    """Render a single feature card with glassmorphism styling."""
    examples_html = "".join(
        f'<li style="color: #94a3b8; padding: 3px 0; font-size: 0.88rem;">'
        f'<code style="background: rgba(124, 92, 252, 0.12); padding: 2px 8px; border-radius: 4px; '
        f'color: #c4b5fd; font-size: 0.82rem;">{ex}</code></li>'
        for ex in feat["examples"]
    )

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, rgba(20, 20, 50, 0.7) 0%, rgba(25, 25, 60, 0.5) 100%);
        border: 1px solid rgba(124, 92, 252, 0.15);
        border-radius: 16px;
        padding: 24px 28px;
        margin-bottom: 14px;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
        transition: all 0.3s ease;
    ">
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 10px;">
            <span style="font-size: 1.8rem;">{feat['icon']}</span>
            <div>
                <h3 style="color: #e0d4ff; margin: 0; font-size: 1.15rem; font-weight: 600;">
                    {feat['title']}
                </h3>
                <span style="color: #64748b; font-size: 0.8rem;">Tab: {feat['tab']}</span>
            </div>
        </div>
        <p style="color: #94a3b8; font-size: 0.92rem; line-height: 1.5; margin-bottom: 12px;">
            {feat['description']}
        </p>
        <div style="
            background: rgba(0, 0, 0, 0.2);
            border-radius: 10px;
            padding: 12px 16px;
            border: 1px solid rgba(255, 255, 255, 0.04);
        ">
            <span style="color: #7c5cfc; font-weight: 600; font-size: 0.82rem; text-transform: uppercase;
                letter-spacing: 0.05em;">Try saying:</span>
            <ul style="list-style: none; padding: 4px 0 0 0; margin: 0;">
                {examples_html}
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)


@st.cache_data(ttl=3600)
def _load_concepts():
    """Load concepts JSON from disk (cached for 1 hour)."""
    import json
    from pathlib import Path
    concepts_path = Path(__file__).parent.parent.parent / "graphrag" / "data" / "concepts.json"
    with open(concepts_path) as f:
        return json.load(f)


@st.fragment
def _render_knowledge_explorer():
    """Render the interactive Knowledge Explorer (runs as a fragment — partial rerun only)."""

    # Category emoji mapping
    CAT_EMOJI = {
        "valuation": "📐", "fundamentals": "📊", "income": "💰",
        "instruments": "🏦", "international": "🌍", "market": "📈",
        "personal_finance": "🏠", "retirement": "🏖️", "risk": "⚠️",
        "strategy": "♟️", "tax": "📋", "technical": "📉", "education": "🎓",
    }
    DIFF_COLOR = {
        "beginner": "#22c55e",
        "intermediate": "#f59e0b",
        "advanced": "#ef4444",
    }
    DIFF_EMOJI = {
        "beginner": "🟢",
        "intermediate": "🟡",
        "advanced": "🔴",
    }

    # ── Header
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(124, 92, 252, 0.12) 0%, rgba(96, 165, 250, 0.06) 100%);
        border: 1px solid rgba(124, 92, 252, 0.2);
        border-radius: 16px;
        padding: 22px 28px;
        margin-bottom: 20px;
        backdrop-filter: blur(10px);
    ">
        <h3 style="
            background: linear-gradient(135deg, #c4b5fd, #60a5fa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0 0 6px 0;
            font-size: 1.4rem;
        ">🧠 Knowledge Explorer</h3>
        <p style="color: #94a3b8; font-size: 0.9rem; margin: 0;">
            Browse 105 financial concepts powered by our Knowledge Graph.
            Search, filter, and click <strong style="color: #c4b5fd;">Ask Finnie</strong>
            to get a RAG-enhanced AI explanation.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Load concepts (cached)
    try:
        concepts = _load_concepts()
    except Exception:
        st.warning("Could not load concepts data.")
        return

    all_categories = sorted(set(c["category"] for c in concepts))
    all_difficulties = ["beginner", "intermediate", "advanced"]

    # ── Filters row
    filter_col1, filter_col2, filter_col3 = st.columns([2, 1.5, 1.5])

    with filter_col1:
        search_query = st.text_input(
            "🔍 Search concepts",
            placeholder="e.g., P/E ratio, diversification, 529...",
            key="kb_search",
            label_visibility="collapsed",
        )

    with filter_col2:
        selected_cats = st.multiselect(
            "Category",
            options=all_categories,
            default=[],
            format_func=lambda c: f"{CAT_EMOJI.get(c, '📌')} {c.replace('_', ' ').title()}",
            key="kb_category",
            placeholder="All categories",
        )

    with filter_col3:
        selected_diffs = st.multiselect(
            "Difficulty",
            options=all_difficulties,
            default=[],
            format_func=lambda d: f"{DIFF_EMOJI.get(d, '')} {d.title()}",
            key="kb_difficulty",
            placeholder="All levels",
        )

    # ── Filter concepts
    filtered = concepts
    if search_query:
        q = search_query.lower()
        filtered = [
            c for c in filtered
            if q in c["name"].lower()
            or q in c.get("aliases", "").lower()
            or q in c.get("definition", "").lower()
        ]
    if selected_cats:
        filtered = [c for c in filtered if c["category"] in selected_cats]
    if selected_diffs:
        filtered = [c for c in filtered if c["difficulty"] in selected_diffs]

    # ── Results count
    st.caption(f"Showing **{len(filtered)}** of {len(concepts)} concepts")

    # ── Concept cards — 3 per row
    if not filtered:
        st.info("No concepts match your filters. Try broadening your search.")
        return

    # ── Pagination — 12 per page to keep it fast
    PAGE_SIZE = 12
    total_pages = max(1, (len(filtered) + PAGE_SIZE - 1) // PAGE_SIZE)

    if "kb_page" not in st.session_state:
        st.session_state.kb_page = 0
    # Reset page when filters change
    filter_key = f"{search_query}|{selected_cats}|{selected_diffs}"
    if st.session_state.get("_kb_last_filter") != filter_key:
        st.session_state.kb_page = 0
        st.session_state._kb_last_filter = filter_key

    page = st.session_state.kb_page
    page_start = page * PAGE_SIZE
    page_concepts = filtered[page_start : page_start + PAGE_SIZE]

    for row_start in range(0, len(page_concepts), 3):
        row_concepts = page_concepts[row_start : row_start + 3]
        cols = st.columns(3)
        for col_idx, concept in enumerate(row_concepts):
            with cols[col_idx]:
                cat_emoji = CAT_EMOJI.get(concept["category"], "📌")
                diff_color = DIFF_COLOR.get(concept["difficulty"], "#94a3b8")
                diff_label = concept["difficulty"].title()
                cat_label = concept["category"].replace("_", " ").title()
                takeaway = concept.get("keyTakeaway", "")

                # Card HTML — includes key takeaway inline (no expander = faster)
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, rgba(20, 20, 50, 0.7) 0%, rgba(25, 25, 60, 0.5) 100%);
                    border: 1px solid rgba(124, 92, 252, 0.12);
                    border-radius: 14px;
                    padding: 18px 20px;
                    min-height: 200px;
                    backdrop-filter: blur(8px);
                    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
                    margin-bottom: 4px;
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-size: 1rem; font-weight: 600; color: #e0d4ff;">
                            {cat_emoji} {concept['name']}
                        </span>
                    </div>
                    <div style="display: flex; gap: 8px; margin-bottom: 10px;">
                        <span style="
                            font-size: 0.7rem; padding: 2px 8px; border-radius: 10px;
                            background: {diff_color}22; color: {diff_color}; font-weight: 600;
                            border: 1px solid {diff_color}44;
                        ">{diff_label}</span>
                        <span style="
                            font-size: 0.7rem; padding: 2px 8px; border-radius: 10px;
                            background: rgba(124, 92, 252, 0.1); color: #a78bfa;
                            border: 1px solid rgba(124, 92, 252, 0.2);
                        ">{cat_label}</span>
                    </div>
                    <p style="color: #94a3b8; font-size: 0.82rem; line-height: 1.5; margin: 0 0 10px 0;">
                        {concept['definition'][:150]}{'...' if len(concept['definition']) > 150 else ''}
                    </p>
                    <div style="
                        background: rgba(34, 197, 94, 0.06);
                        border-left: 3px solid rgba(34, 197, 94, 0.4);
                        border-radius: 0 8px 8px 0;
                        padding: 8px 12px;
                    ">
                        <span style="color: #6ee7b7; font-size: 0.72rem; font-weight: 600;">💡 KEY TAKEAWAY</span>
                        <p style="color: #94a3b8; font-size: 0.78rem; margin: 4px 0 0 0; line-height: 1.4;">
                            {takeaway[:140]}{'...' if len(takeaway) > 140 else ''}
                        </p>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Ask Finnie button
                if st.button(
                    "🧠 Ask Finnie",
                    key=f"ask_{concept['name'].replace(' ', '_').lower()}",
                    use_container_width=True,
                ):
                    st.session_state.pending_chat_question = f"What is {concept['name']}?"
                    st.toast(f"💬 Asking about **{concept['name']}**")
                    st.rerun(scope="app")  # full rerun to reach Chat tab

    # ── Pagination controls
    if total_pages > 1:
        st.markdown("")  # spacer
        nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])
        with nav_col1:
            if st.button("⬅️ Previous", disabled=(page == 0), key="kb_prev", use_container_width=True):
                st.session_state.kb_page = max(0, page - 1)
                st.rerun()
        with nav_col2:
            st.markdown(
                f"<p style='text-align: center; color: #94a3b8; padding-top: 8px;'>"
                f"Page <strong>{page + 1}</strong> of <strong>{total_pages}</strong>"
                f"</p>",
                unsafe_allow_html=True,
            )
        with nav_col3:
            if st.button("Next ➡️", disabled=(page >= total_pages - 1), key="kb_next", use_container_width=True):
                st.session_state.kb_page = min(total_pages - 1, page + 1)
                st.rerun()
