"""
Finnie AI — Chat Tab

Main conversational interface for interacting with Finnie.
"""

import streamlit as st
from datetime import datetime


def render_chat_tab():
    """Render the main chat interface tab."""
    
    # Chat history display
    _render_chat_messages()
    
    # Chat input
    _render_chat_input()


def _render_chat_messages():
    """Display the conversation history."""
    messages = st.session_state.get("messages", [])
    
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        
        if role == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown(content)
        elif role == "assistant":
            with st.chat_message("assistant", avatar="🐟"):
                st.markdown(content)
                
                # Render visualizations if present
                viz = msg.get("visualizations", [])
                for v in viz:
                    _render_visualization(v)


def _render_chat_input():
    """Render the chat input box and handle submission."""
    if prompt := st.chat_input("Ask Finnie anything about finance..."):
        # Add user message
        st.session_state.setdefault("messages", []).append({
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now().isoformat(),
        })
        
        # Process with Finnie
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
        
        with st.chat_message("assistant", avatar="🐟"):
            with st.spinner("Finnie is thinking..."):
                response = _process_query(prompt)
                st.markdown(response.get("content", ""))
                
                # Render any visualizations
                for viz in response.get("visualizations", []):
                    _render_visualization(viz)
        
        # Add assistant message
        st.session_state["messages"].append({
            "role": "assistant",
            "content": response.get("content", ""),
            "visualizations": response.get("visualizations", []),
            "timestamp": datetime.now().isoformat(),
        })


def _process_query(prompt: str) -> dict:
    """Process a user query through the Finnie AI pipeline."""
    import asyncio
    
    try:
        from src.orchestration.graph import run_finnie
        
        llm_provider = st.session_state.get("llm_provider", "openai")
        llm_model = st.session_state.get("llm_model", "gpt-4o")
        llm_api_key = st.session_state.get("llm_api_key", "")
        session_id = st.session_state.get("session_id", "default")
        portfolio = st.session_state.get("portfolio_data", None)
        
        result = asyncio.run(run_finnie(
            user_input=prompt,
            session_id=session_id,
            llm_provider=llm_provider,
            llm_model=llm_model,
            llm_api_key=llm_api_key,
            portfolio_data=portfolio,
        ))
        
        return {
            "content": result.get("final_response", "I couldn't process that request."),
            "visualizations": result.get("visualizations", []),
        }
    except Exception as e:
        return {
            "content": f"⚠️ Error processing your request: {str(e)}",
            "visualizations": [],
        }


def _render_visualization(viz: dict):
    """Render a visualization based on its type."""
    viz_type = viz.get("type", "")
    data = viz.get("data", {})
    
    if viz_type in ("projection_chart", "goal_projection_chart"):
        _render_projection_chart(data, viz.get("title", "Projection"))
    elif viz_type == "crypto_overview":
        _render_crypto_chart(data)


def _render_projection_chart(data: dict, title: str):
    """Render a projection chart using Streamlit columns."""
    if not data:
        return
    
    st.subheader(title)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        value = data.get("conservative", data.get("monthly_conservative", 0))
        st.metric("📉 Conservative", f"${value:,.0f}")
    
    with col2:
        value = data.get("expected", data.get("required_monthly", 0))
        st.metric("📊 Expected", f"${value:,.0f}")
    
    with col3:
        value = data.get("optimistic", data.get("monthly_aggressive", 0))
        st.metric("📈 Optimistic", f"${value:,.0f}")


def _render_crypto_chart(data: dict):
    """Render a crypto overview with price metrics."""
    if not data:
        return
    
    st.subheader("🪙 Live Crypto Prices")
    
    cols = st.columns(min(len(data), 4))
    for i, (coin, info) in enumerate(data.items()):
        with cols[i % len(cols)]:
            price = info.get("usd", 0)
            change = info.get("usd_24h_change", 0)
            delta = f"{change:+.2f}%"
            st.metric(coin.title(), f"${price:,.2f}", delta)
