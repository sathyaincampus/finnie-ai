"""
Finnie AI — Portfolio Tab

Visual portfolio overview with allocation breakdown and performance.
"""

import streamlit as st


def render_portfolio_tab():
    """Render the portfolio management tab."""
    
    st.header("💼 Portfolio Overview")
    
    portfolio = st.session_state.get("portfolio_data", None)
    
    if not portfolio:
        _render_empty_portfolio()
        return
    
    # Portfolio metrics row
    _render_portfolio_metrics(portfolio)
    
    # Holdings table
    _render_holdings_table(portfolio)
    
    # Allocation chart
    _render_allocation_chart(portfolio)


def _render_empty_portfolio():
    """Show placeholder when no portfolio is configured."""
    st.info("📋 **No portfolio configured yet.**")
    
    st.markdown("""
    To get started, add your holdings in the Settings tab or tell Finnie:
    
    > *"I have 10 shares of AAPL, 5 shares of GOOGL, and $5000 in VOO"*
    
    Finnie will track your portfolio and provide:
    - **Real-time valuation** with live market prices
    - **Allocation breakdown** by sector and asset class
    - **Performance tracking** vs benchmarks
    - **Rebalancing suggestions** based on your goals
    """)
    
    # Quick add form
    with st.expander("📝 Quick Add Holdings"):
        col1, col2 = st.columns(2)
        with col1:
            ticker = st.text_input("Ticker Symbol", placeholder="AAPL")
        with col2:
            shares = st.number_input("Shares", min_value=0.0, step=1.0)
        
        if st.button("Add to Portfolio", type="primary"):
            if ticker and shares > 0:
                holdings = st.session_state.get("portfolio_data", {"holdings": []})
                if not isinstance(holdings, dict):
                    holdings = {"holdings": []}
                holdings.setdefault("holdings", []).append({
                    "ticker": ticker.upper(),
                    "shares": shares,
                })
                st.session_state["portfolio_data"] = holdings
                st.success(f"Added {shares} shares of {ticker.upper()}")
                st.rerun()


def _render_portfolio_metrics(portfolio: dict):
    """Render top-level portfolio metrics."""
    holdings = portfolio.get("holdings", [])
    total_value = portfolio.get("total_value", 0)
    daily_change = portfolio.get("daily_change", 0)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Value", f"${total_value:,.2f}")
    with col2:
        st.metric("Daily Change", f"${daily_change:,.2f}", 
                  f"{(daily_change/total_value*100):.2f}%" if total_value else "0%")
    with col3:
        st.metric("Holdings", len(holdings))
    with col4:
        st.metric("Cash", f"${portfolio.get('cash', 0):,.2f}")


def _render_holdings_table(portfolio: dict):
    """Render the holdings table."""
    holdings = portfolio.get("holdings", [])
    
    if not holdings:
        return
    
    st.subheader("📊 Holdings")
    
    # Build data for table
    import pandas as pd
    
    df = pd.DataFrame(holdings)
    if not df.empty:
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
        )


def _render_allocation_chart(portfolio: dict):
    """Render allocation breakdown."""
    holdings = portfolio.get("holdings", [])
    
    if not holdings:
        return
    
    st.subheader("🎯 Allocation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**By Ticker:**")
        for h in holdings[:10]:
            ticker = h.get("ticker", "???")
            pct = h.get("weight", 0)
            st.progress(pct / 100 if pct else 0.1, text=f"{ticker}: {pct:.1f}%")
    
    with col2:
        st.markdown("**Diversification Tips:**")
        st.markdown("""
        - 📈 **US Stocks:** 40-60%
        - 🌍 **International:** 15-25%
        - 📉 **Bonds:** 15-30%
        - 🏠 **REITs:** 5-10%
        - 💰 **Cash:** 5-10%
        """)
