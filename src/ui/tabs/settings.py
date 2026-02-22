"""
Finnie AI — Settings Tab

Configuration for LLM providers, API keys, and application preferences.
"""

import streamlit as st


def render_settings_tab():
    """Render the settings and configuration tab."""
    
    st.header("⚙️ Settings")
    
    # LLM Configuration
    _render_llm_settings()
    
    # Observability
    _render_observability_settings()
    
    # System info
    _render_system_info()


def _render_llm_settings():
    """Render LLM provider configuration."""
    st.subheader("🤖 LLM Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        provider = st.selectbox(
            "LLM Provider",
            ["openai", "anthropic", "google"],
            index=["openai", "anthropic", "google"].index(
                st.session_state.get("llm_provider", "openai")
            ),
            key="settings_provider",
        )
        
        if provider != st.session_state.get("llm_provider"):
            st.session_state["llm_provider"] = provider
    
    with col2:
        models = {
            "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
            "anthropic": ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"],
            "google": ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
        }
        
        available_models = models.get(provider, ["gpt-4o"])
        current = st.session_state.get("llm_model", available_models[0])
        idx = available_models.index(current) if current in available_models else 0
        
        model = st.selectbox(
            "Model",
            available_models,
            index=idx,
            key="settings_model",
        )
        
        if model != st.session_state.get("llm_model"):
            st.session_state["llm_model"] = model
    
    # API Key
    api_key = st.text_input(
        f"{provider.title()} API Key",
        value=st.session_state.get("llm_api_key", ""),
        type="password",
        key="settings_api_key",
    )
    
    if api_key != st.session_state.get("llm_api_key"):
        st.session_state["llm_api_key"] = api_key
    
    if api_key:
        st.success(f"✅ {provider.title()} API key configured")
    else:
        st.warning(f"⚠️ No API key set — configure your {provider.title()} key to use Finnie")


def _render_observability_settings():
    """Render observability/Phoenix settings."""
    st.subheader("📊 Observability (Arize Phoenix)")
    
    # Phoenix dashboard link — always show if PHOENIX_ENABLED
    import os
    phoenix_enabled = os.getenv("PHOENIX_ENABLED", "true").lower() == "true"
    
    if phoenix_enabled:
        phoenix_url = os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006").replace("/v1/traces", "")
        st.success(f"✅ Phoenix tracing active — [Open Dashboard]({phoenix_url})")
        
        st.markdown("""
        **What's being tracked:**
        - 🔗 Every LLM call (prompt, response, tokens, latency)
        - 📊 Evaluation metrics (relevance, QA quality, toxicity, hallucination)
        - 📈 Cost and token usage per request
        """)
        
        # Batch evaluation trigger
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Run Batch Evals on All Traces", use_container_width=True, type="primary"):
                with st.spinner("Running evaluations on all traces..."):
                    try:
                        from src.evals import run_evals_on_traces
                        run_evals_on_traces()
                        st.success("✅ Batch evaluations complete — check Phoenix dashboard")
                    except Exception as e:
                        st.error(f"Eval error: {e}")
        with col2:
            st.caption(
                "Runs relevance, QA quality, toxicity, and hallucination "
                "evaluators on all existing Phoenix traces."
            )
    else:
        st.info("Set `PHOENIX_ENABLED=true` in `.env` to enable tracing.")
    
    try:
        from src.observability import get_observer
        observer = get_observer()
        
        if observer.is_enabled:
            metrics = observer.get_metrics()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Requests", metrics.get("total_requests", 0))
            with col2:
                st.metric("Avg Latency", f"{metrics.get('avg_latency_ms', 0)}ms")
            with col3:
                st.metric("Errors", metrics.get("error_count", 0))
            with col4:
                st.metric("Total Tokens", f"{metrics.get('total_tokens', 0):,}")
            
            traces = observer.get_recent_traces(5)
            if traces:
                with st.expander("📋 Recent Traces"):
                    for t in traces:
                        st.markdown(
                            f"**{t['timestamp'][:19]}** | "
                            f"`{t['session_id'][:8]}` | "
                            f"{t['latency_ms']}ms | "
                            f"{t['spans']} spans | "
                            f"*{t['input'][:60]}...*"
                        )
    except Exception:
        pass


def _render_system_info():
    """Render system information."""
    st.subheader("ℹ️ System Info")
    
    with st.expander("System Details"):
        import sys
        
        st.markdown(f"""
        | Setting | Value |
        |---------|-------|
        | Python | {sys.version.split()[0]} |
        | Finnie Version | 2.0.0 |
        | Session ID | `{st.session_state.get('session_id', 'N/A')}` |
        | Provider | {st.session_state.get('llm_provider', 'openai')} |
        | Model | {st.session_state.get('llm_model', 'gpt-4o')} |
        """)
        
        st.markdown("**Available Agents:**")
        agents = [
            "✨ Enhancer", "📊 Quant", "📚 Professor", "📰 Analyst",
            "💼 Advisor", "🔮 Oracle", "🔍 Scout", "📋 Planner",
            "🪙 Crypto", "🛡️ Guardian", "📝 Scribe",
        ]
        st.markdown(" • ".join(agents))
