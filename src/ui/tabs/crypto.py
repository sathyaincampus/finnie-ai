"""
Finnie AI — Crypto Tab

Live cryptocurrency dashboard with prices, charts, portfolio allocation, and market data.
Uses CoinGecko API for real-time and historical data.
"""

import streamlit as st
from datetime import datetime, timedelta


def render_crypto_tab():
    """Render the cryptocurrency tab."""
    
    st.header("🪙 Cryptocurrency Dashboard")
    
    # Live prices
    _render_crypto_prices()
    
    st.divider()
    
    # Price chart for selected coin
    _render_price_chart()
    
    st.divider()
    
    # Portfolio allocation calculator
    _render_allocation_calculator()
    
    # Tax information
    _render_crypto_tax_info()


def _render_crypto_prices():
    """Render live crypto prices with metrics."""
    st.subheader("📊 Live Market Prices")
    
    top_coins = ["bitcoin", "ethereum", "solana", "binancecoin", "ripple", "cardano"]
    
    names = {
        "bitcoin": ("BTC", "₿"),
        "ethereum": ("ETH", "Ξ"),
        "solana": ("SOL", "◎"),
        "binancecoin": ("BNB", "▣"),
        "ripple": ("XRP", "✕"),
        "cardano": ("ADA", "₳"),
    }
    
    try:
        from pycoingecko import CoinGeckoAPI
        cg = CoinGeckoAPI()
        
        ids = ",".join(top_coins)
        data = cg.get_price(
            ids=ids,
            vs_currencies="usd",
            include_market_cap=True,
            include_24hr_change=True,
            include_24hr_vol=True,
        )
        
        # Store data in session state for other components
        st.session_state["crypto_live_data"] = data
        
        cols = st.columns(3)
        
        for i, coin_id in enumerate(top_coins):
            info = data.get(coin_id, {})
            with cols[i % 3]:
                price = info.get("usd", 0)
                change = info.get("usd_24h_change", 0)
                cap = info.get("usd_market_cap", 0)
                vol = info.get("usd_24h_vol", 0)
                
                symbol, icon = names.get(coin_id, (coin_id.upper()[:4], ""))
                price_str = f"${price:,.2f}" if price >= 1 else f"${price:.6f}"
                
                st.metric(
                    f"{icon} {symbol}",
                    price_str,
                    f"{change:+.2f}%",
                )
                cap_str = f"MCap: ${cap/1e9:.1f}B" if cap > 1e9 else f"MCap: ${cap/1e6:.0f}M"
                vol_str = f"Vol: ${vol/1e9:.1f}B" if vol > 1e9 else f"Vol: ${vol/1e6:.0f}M"
                st.caption(f"{cap_str} · {vol_str}")
    
    except ImportError:
        st.warning("📦 Install `pycoingecko` for live crypto prices: `pip install pycoingecko`")
        _render_placeholder_prices()
    except Exception as e:
        st.error(f"Error fetching crypto data: {e}")
        _render_placeholder_prices()


def _render_placeholder_prices():
    """Show placeholder when live data is unavailable."""
    cols = st.columns(3)
    placeholder_data = [
        ("BTC", "$97,234", "+1.8%"),
        ("ETH", "$3,412", "+2.1%"),
        ("SOL", "$198.50", "-0.5%"),
        ("BNB", "$612.30", "+0.9%"),
        ("XRP", "$2.34", "+3.2%"),
        ("ADA", "$0.98", "-1.1%"),
    ]
    for i, (sym, price, change) in enumerate(placeholder_data):
        with cols[i % 3]:
            st.metric(sym, price, change)
    st.caption("⚠️ Showing cached data. Install `pycoingecko` for live prices.")


def _render_price_chart():
    """Render interactive price chart for a selected coin."""
    st.subheader("📈 Price History")
    
    # Quick-select buttons for popular coins
    popular = {
        "Bitcoin": "bitcoin", "Ethereum": "ethereum", "Solana": "solana",
        "XRP": "ripple", "BNB": "binancecoin", "Cardano": "cardano",
        "Dogecoin": "dogecoin", "Polkadot": "polkadot",
    }
    
    cols = st.columns(len(popular))
    for i, (name, cid) in enumerate(popular.items()):
        with cols[i]:
            if st.button(name, key=f"quick_{cid}", use_container_width=True):
                st.session_state["crypto_search_coin_id"] = cid
                st.session_state["crypto_search_coin_name"] = name
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_query = st.text_input(
            "🔍 Search any cryptocurrency (name or symbol)",
            placeholder="e.g. shiba inu, pepe, avax, matic...",
            key="crypto_search_input",
        )
        
        # Search CoinGecko for matching coins
        coin_id = st.session_state.get("crypto_search_coin_id", "bitcoin")
        selected_name = st.session_state.get("crypto_search_coin_name", "Bitcoin")
        
        if search_query:
            try:
                from pycoingecko import CoinGeckoAPI
                cg = CoinGeckoAPI()
                results = cg.search(search_query)
                coins = results.get("coins", [])[:8]
                
                if coins:
                    options = {f"{c['name']} ({c['symbol'].upper()})": c['id'] for c in coins}
                    selected = st.selectbox(
                        "Select from results:",
                        list(options.keys()),
                        key="crypto_search_result",
                    )
                    coin_id = options[selected]
                    selected_name = selected
                    st.session_state["crypto_search_coin_id"] = coin_id
                    st.session_state["crypto_search_coin_name"] = selected_name
                else:
                    st.warning(f"No results for '{search_query}'")
            except ImportError:
                st.warning("Install `pycoingecko` for search: `pip install pycoingecko`")
            except Exception as e:
                st.error(f"Search error: {e}")
    
    with col2:
        time_range = st.selectbox(
            "Time Range",
            ["7 Days", "30 Days", "90 Days", "1 Year", "Max"],
            index=1,
            key="crypto_chart_range",
        )
    
    days_map = {"7 Days": 7, "30 Days": 30, "90 Days": 90, "1 Year": 365, "Max": "max"}
    days = days_map[time_range]
    
    try:
        from pycoingecko import CoinGeckoAPI
        cg = CoinGeckoAPI()
        
        with st.spinner(f"Fetching {selected_name} price history..."):
            chart_data = cg.get_coin_market_chart_by_id(
                id=coin_id,
                vs_currency="usd",
                days=days,
            )
        
        prices = chart_data.get("prices", [])
        volumes = chart_data.get("total_volumes", [])
        
        if prices:
            timestamps = [datetime.fromtimestamp(p[0] / 1000) for p in prices]
            price_values = [p[1] for p in prices]
            volume_values = [v[1] for v in volumes] if volumes else []
            
            # Price stats
            current_price = price_values[-1]
            start_price = price_values[0]
            high_price = max(price_values)
            low_price = min(price_values)
            price_change = ((current_price - start_price) / start_price) * 100
            
            # Display stats
            stat_cols = st.columns(4)
            with stat_cols[0]:
                st.metric("Current", f"${current_price:,.2f}", f"{price_change:+.2f}%")
            with stat_cols[1]:
                st.metric("High", f"${high_price:,.2f}")
            with stat_cols[2]:
                st.metric("Low", f"${low_price:,.2f}")
            with stat_cols[3]:
                st.metric("Range", f"${high_price - low_price:,.2f}")
            
            # Build chart
            try:
                import plotly.graph_objects as go
                from plotly.subplots import make_subplots
                
                fig = make_subplots(
                    rows=2, cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.03,
                    row_heights=[0.75, 0.25],
                    subplot_titles=[f"{selected_name} Price", "Volume"],
                )
                
                # Price line
                color = "#22c55e" if price_change >= 0 else "#ef4444"
                fig.add_trace(go.Scatter(
                    x=timestamps, y=price_values,
                    fill="tozeroy",
                    fillcolor=f"rgba({'34,197,94' if price_change >= 0 else '239,68,68'}, 0.1)",
                    line=dict(color=color, width=2),
                    name="Price",
                    hovertemplate="%{x}<br>$%{y:,.2f}<extra></extra>",
                ), row=1, col=1)
                
                # Volume bars
                if volume_values and len(volume_values) == len(timestamps):
                    fig.add_trace(go.Bar(
                        x=timestamps, y=volume_values,
                        name="Volume",
                        marker_color="rgba(99, 102, 241, 0.4)",
                        hovertemplate="%{x}<br>Vol: $%{y:,.0f}<extra></extra>",
                    ), row=2, col=1)
                
                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    height=500,
                    showlegend=False,
                    yaxis=dict(tickformat="$,.2f" if current_price >= 1 else "$,.6f"),
                    yaxis2=dict(tickformat=",.0f"),
                    margin=dict(t=30, b=10),
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
            except ImportError:
                st.line_chart(
                    dict(zip(
                        [t.strftime("%m/%d") for t in timestamps],
                        price_values,
                    ))
                )
        else:
            st.warning("No price data returned for this period.")
    
    except ImportError:
        st.info(
            "📦 Install `pycoingecko` to see price charts:\n\n"
            "```\npip install pycoingecko\n```"
        )
    except Exception as e:
        st.error(f"Error fetching chart data: {e}")


def _render_allocation_calculator():
    """Interactive crypto portfolio allocation calculator."""
    st.subheader("💼 Crypto Allocation Calculator")
    
    col1, col2 = st.columns(2)
    
    with col1:
        total_portfolio = st.number_input(
            "Total Investment Portfolio ($)",
            min_value=1000, max_value=50_000_000,
            value=100000, step=5000,
            key="crypto_portfolio",
        )
    
    with col2:
        risk_profile = st.selectbox(
            "Risk Profile",
            ["Conservative (1-3%)", "Moderate (3-7%)", "Aggressive (7-15%)"],
            index=1,
            key="crypto_risk",
        )
    
    # Determine allocation
    if "Conservative" in risk_profile:
        pct = 0.02
        breakdown = {"Bitcoin": 70, "Ethereum": 30}
    elif "Moderate" in risk_profile:
        pct = 0.05
        breakdown = {"Bitcoin": 50, "Ethereum": 30, "Top Alts": 20}
    else:
        pct = 0.10
        breakdown = {"Bitcoin": 40, "Ethereum": 25, "Layer 1s": 20, "DeFi/Alts": 15}
    
    crypto_allocation = total_portfolio * pct
    
    # Display
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Recommended Crypto Allocation", f"${crypto_allocation:,.0f}",
                  f"{pct*100:.0f}% of portfolio")
        
        st.markdown("**Suggested Breakdown:**")
        for asset, share in breakdown.items():
            amount = crypto_allocation * share / 100
            st.markdown(f"- **{asset}** ({share}%): ${amount:,.0f}")
    
    with col2:
        try:
            import plotly.graph_objects as go
            
            labels = list(breakdown.keys())
            values = [crypto_allocation * s / 100 for s in breakdown.values()]
            colors = ["#f7931a", "#627eea", "#14f195", "#ec4899"][:len(labels)]
            
            fig = go.Figure(data=[go.Pie(
                labels=labels, values=values,
                hole=0.5,
                marker_colors=colors,
                textinfo="label+percent",
                hovertemplate="%{label}: $%{value:,.0f}<extra></extra>",
            )])
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                height=300,
                margin=dict(t=10, b=10),
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            pass
    
    st.warning("⚠️ Crypto is highly volatile. Never invest more than you can afford to lose.")


def _render_crypto_tax_info():
    """Render crypto tax information."""
    st.subheader("💰 Crypto Tax Guide (US)")
    
    with st.expander("📋 Tax Rules"):
        st.markdown("""
        **Crypto is treated as PROPERTY by the IRS.**
        
        | Event | Tax Treatment |
        |-------|---------------|
        | Buy and hold | No tax event |
        | Sell for profit | Capital gains tax |
        | Swap one crypto for another | Taxable event |
        | Receive as payment | Ordinary income |
        | Mining/staking rewards | Ordinary income |
        | Gifts (< $18K) | No tax for giver |
        | Gifts (> $18K) | Gift tax reporting |
        
        **Capital Gains Rates (2025):**
        | Holding Period | Rate |
        |---------------|------|
        | < 1 year | 10% - 37% (ordinary income) |
        | > 1 year | 0%, 15%, or 20% |
        
        **Pro Tips:**
        - Use **tax-loss harvesting** — sell losers to offset gains
        - Hold for **>1 year** for lower long-term rates
        - Track cost basis for **every transaction**
        - Use crypto tax software (CoinTracker, Koinly, TaxBit)
        """)
    
    st.info("💡 Ask Finnie: *\"What are the tax implications of selling my Bitcoin?\"*")
