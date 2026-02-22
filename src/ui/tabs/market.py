"""
Finnie AI — Market Tab

Live market overview with movers, sector performance, and search.
"""

import streamlit as st


def render_market_tab():
    """Render the market overview tab."""
    
    st.header("📈 Market Overview")
    
    # Market indices
    _render_market_indices()
    
    # Stock search
    _render_stock_search()
    
    # Market movers
    _render_market_movers()


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
    st.subheader("🔍 Stock Lookup")
    
    ticker_input = st.text_input(
        "Enter ticker symbol",
        placeholder="AAPL, GOOGL, MSFT...",
        key="market_ticker_search",
    )
    
    if ticker_input:
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


def _render_market_movers():
    """Render market movers section."""
    st.subheader("🔥 Market Movers")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📈 Top Gainers**")
        st.caption("Refresh to see latest movers")
    
    with col2:
        st.markdown("**📉 Top Losers**")
        st.caption("Refresh to see latest movers")
    
    st.info("💡 Ask Finnie in the Chat tab: *\"What's trending in the market today?\"*")


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
