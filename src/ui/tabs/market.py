"""
Finnie AI — Market Tab

Live market overview with movers, sector performance, and search.
"""

import streamlit as st


def render_market_tab():
    """Render the market overview tab."""
    
    st.header("📈 Market Overview")
    
    # Market indices (fast — 4 API calls)
    _render_market_indices()
    
    # Market movers FIRST (most impactful, cached)
    _render_market_movers()
    
    # Stock search (on-demand)
    _render_stock_search()


def _render_market_indices():
    """Render major market indices."""
    st.subheader("🏛️ Indices")
    
    try:
        import yfinance as yf
        
        indices = {
            "^GSPC": "S&P 500",
            "^DJI": "Dow Jones",
            "^IXIC": "NASDAQ",
            "^RUT": "Russell 2000",
        }
        
        cols = st.columns(len(indices))
        
        for i, (symbol, name) in enumerate(indices.items()):
            with cols[i]:
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.fast_info
                    price = info.get("lastPrice", 0)
                    prev = info.get("previousClose", price)
                    change = price - prev
                    pct = (change / prev * 100) if prev else 0
                    st.metric(name, f"{price:,.0f}", f"{pct:+.2f}%")
                except Exception:
                    st.metric(name, "—", "Loading...")
    
    except ImportError:
        st.warning("yfinance not installed — market data unavailable")


def _render_stock_search():
    """Render the stock search/lookup section."""
    st.subheader("🔍 Market Lookup")
    st.caption("Supports tickers like AAPL, BRK-B, BRK.B, GOOGL")
    
    col_input, col_btn = st.columns([4, 1])
    with col_input:
        ticker_input = st.text_input(
            "Enter ticker",
            placeholder="e.g., AAPL, BRK-B, NVDA",
            key="market_ticker_search",
            label_visibility="collapsed",
        )
    with col_btn:
        search_clicked = st.button("🔍 Search", use_container_width=True, type="primary")
    
    # Quick access buttons
    st.caption("Quick access:")
    quick_cols = st.columns(4)
    quick_tickers = [
        ["AAPL", "GOOGL", "MSFT", "AMZN"],
        ["NVDA", "TSLA", "META", "BRK-B"],
    ]
    for row in quick_tickers:
        cols = st.columns(len(row))
        for i, t in enumerate(row):
            with cols[i]:
                if st.button(t, key=f"quick_{t}", use_container_width=True):
                    ticker_input = t
                    search_clicked = True
    
    if ticker_input and search_clicked:
        _show_stock_details(ticker_input.upper().strip())
    elif ticker_input:
        _show_stock_details(ticker_input.upper().strip())


def _show_stock_details(symbol: str):
    """Show detailed stock information."""
    try:
        import yfinance as yf
        
        with st.spinner(f"Fetching {symbol}..."):
            ticker = yf.Ticker(symbol)
            info = ticker.info
        
        if not info or "shortName" not in info:
            st.error(f"Could not find data for {symbol}")
            return
        
        # Header
        name = info.get("shortName", symbol)
        price = info.get("currentPrice", info.get("regularMarketPrice", 0))
        prev = info.get("previousClose", price)
        change = price - prev
        pct = (change / prev * 100) if prev else 0
        
        st.markdown(f"### {name} ({symbol})")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Price", f"${price:,.2f}", f"{pct:+.2f}%")
        with col2:
            st.metric("Market Cap", _format_large_number(info.get("marketCap", 0)))
        with col3:
            st.metric("P/E Ratio", f"{info.get('trailingPE', 'N/A'):.1f}" if isinstance(info.get('trailingPE'), (int, float)) else "N/A")
        with col4:
            st.metric("52W Range", f"${info.get('fiftyTwoWeekLow', 0):,.0f} - ${info.get('fiftyTwoWeekHigh', 0):,.0f}")
        
        # Price chart
        hist = ticker.history(period="6mo")
        if not hist.empty:
            st.line_chart(hist["Close"], use_container_width=True)
    
    except ImportError:
        st.warning("yfinance not installed")
    except Exception as e:
        st.error(f"Error fetching {symbol}: {e}")


@st.cache_data(ttl=300, show_spinner=False)
def _fetch_movers(period: str) -> list[dict]:
    """Fetch market movers data (cached 5 min)."""
    import yfinance as yf
    
    # Top 20 tickers for fast initial load
    tracked_tickers = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B",
        "JPM", "V", "JNJ", "UNH", "XOM", "LLY", "NFLX", "AMD",
        "CRM", "COIN", "PLTR", "SOFI",
    ]
    
    movers = []
    for ticker_symbol in tracked_tickers:
        try:
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period=period)
            if hist.empty or len(hist) < 1:
                continue
            
            start_price = hist["Close"].iloc[0]
            end_price = hist["Close"].iloc[-1]
            pct_change = ((end_price - start_price) / start_price) * 100
            
            movers.append({
                "Symbol": ticker_symbol,
                "Price": f"${end_price:,.2f}",
                "Change": f"{pct_change:+.2f}%",
                "pct": pct_change,
            })
        except Exception:
            continue
    
    movers.sort(key=lambda x: x["pct"], reverse=True)
    return movers


def _render_market_movers():
    """Render market movers section with real data."""
    st.subheader("🔥 Market Movers")
    
    period_tab = st.radio(
        "Time Period",
        ["Today", "This Week", "This Month"],
        horizontal=True,
        key="movers_period",
    )
    
    period_map = {"Today": "1d", "This Week": "5d", "This Month": "1mo"}
    period = period_map[period_tab]
    
    try:
        with st.spinner("Fetching market movers..."):
            movers = _fetch_movers(period)
        
        if movers:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📈 Top Gainers**")
                gainers = [m for m in movers if m["pct"] > 0][:10]
                for g in gainers:
                    color = "#22c55e"
                    st.markdown(
                        f"<div style='display:flex; justify-content:space-between; padding:6px 10px; "
                        f"border-left:3px solid {color}; margin:3px 0; background:rgba(34,197,94,0.08); "
                        f"border-radius:0 6px 6px 0;'>"
                        f"<span style='font-weight:600;'>{g['Symbol']}</span>"
                        f"<span>{g['Price']}</span>"
                        f"<span style='color:{color}; font-weight:600;'>{g['Change']}</span>"
                        f"</div>", unsafe_allow_html=True
                    )
            
            with col2:
                st.markdown("**📉 Top Losers**")
                losers = [m for m in movers if m["pct"] < 0]
                losers.sort(key=lambda x: x["pct"])  # most negative first
                for l in losers[:10]:
                    color = "#ef4444"
                    st.markdown(
                        f"<div style='display:flex; justify-content:space-between; padding:6px 10px; "
                        f"border-left:3px solid {color}; margin:3px 0; background:rgba(239,68,68,0.08); "
                        f"border-radius:0 6px 6px 0;'>"
                        f"<span style='font-weight:600;'>{l['Symbol']}</span>"
                        f"<span>{l['Price']}</span>"
                        f"<span style='color:{color}; font-weight:600;'>{l['Change']}</span>"
                        f"</div>", unsafe_allow_html=True
                    )
        else:
            st.warning("Could not fetch market data. Try again later.")
    
    except ImportError:
        st.warning("Install `yfinance` for market movers: `pip install yfinance`")
    except Exception as e:
        st.error(f"Error fetching movers: {e}")
    
    st.info("💡 Also try asking Finnie: *\"Show me top stock gainers today\"* or *\"What stocks are moving this week?\"*")


def _format_large_number(num: float) -> str:
    """Format large numbers (1.5T, 250B, 3.2M)."""
    if num >= 1e12:
        return f"${num/1e12:.1f}T"
    elif num >= 1e9:
        return f"${num/1e9:.1f}B"
    elif num >= 1e6:
        return f"${num/1e6:.1f}M"
    elif num >= 1e3:
        return f"${num/1e3:.0f}K"
    else:
        return f"${num:,.0f}"
