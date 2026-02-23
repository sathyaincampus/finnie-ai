"""
Finnie AI — Authentication Module

Handles OAuth login (Google/GitHub) and user session management.
Falls back to guest mode if OAuth is not configured.
"""

import streamlit as st
import hashlib
from typing import Optional


def _oauth_configured() -> bool:
    """Check if OAuth credentials are configured in secrets."""
    try:
        auth = st.secrets.get("auth", {})
        # Streamlit expects [auth.google] / [auth.github], not [auth.providers.*]
        return any(
            key in auth for key in ("google", "github", "providers")
        )
    except Exception:
        return False


def _get_user_info() -> Optional[dict]:
    """
    Get the authenticated user's info from Streamlit's native auth.
    Returns dict with: email, name, avatar_url, provider, user_id
    """
    try:
        # Streamlit 1.54+ uses st.user; older versions use st.experimental_user
        user = getattr(st, 'user', None) or getattr(st, 'experimental_user', None)
        if user and hasattr(user, 'email') and user.email:
            email = user.email
            name = getattr(user, 'name', None) or email.split('@')[0]
            avatar = getattr(user, 'picture', None) or getattr(user, 'avatar_url', '') or ''

            # Generate a stable user_id from email
            user_id = hashlib.sha256(email.encode()).hexdigest()[:16]

            return {
                "user_id": user_id,
                "email": email,
                "name": name,
                "avatar_url": avatar,
                "provider": "oauth",
            }
    except Exception:
        pass
    return None


def _create_guest_user() -> dict:
    """Create a guest user session."""
    return {
        "user_id": "guest",
        "email": "guest@finnie.ai",
        "name": "Guest",
        "avatar_url": "",
        "provider": "guest",
    }


def _oauth_has_real_credentials() -> bool:
    """Check if OAuth credentials are real (not placeholders)."""
    if not _oauth_configured():
        return False
    try:
        auth = st.secrets.get("auth", {})
        # Check direct provider keys (auth.google, auth.github)
        for key in ("google", "github"):
            provider = auth.get(key, {})
            if isinstance(provider, dict):
                client_id = provider.get("client_id", "")
                if client_id and "YOUR_" not in client_id:
                    return True
        # Fallback: check old providers format
        providers = auth.get("providers", {})
        for provider in providers.values():
            client_id = provider.get("client_id", "")
            if client_id and "YOUR_" not in client_id:
                return True
    except Exception:
        pass
    return False


def render_login_page():
    """Render a beautiful login page."""
    st.markdown("""
    <style>
    .login-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 70vh;
        text-align: center;
    }
    .login-card {
        background: linear-gradient(145deg, #1a1d2e 0%, #0e1117 100%);
        border: 1px solid rgba(124, 92, 252, 0.3);
        border-radius: 20px;
        padding: 3rem;
        max-width: 480px;
        width: 100%;
        box-shadow: 0 20px 60px rgba(124, 92, 252, 0.15);
    }
    .login-logo {
        font-size: 4rem;
        margin-bottom: 0.5rem;
    }
    .login-title {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #7c5cfc, #00d4ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .login-subtitle {
        color: #8888aa;
        font-size: 0.95rem;
        margin-bottom: 2rem;
    }
    .login-divider {
        display: flex;
        align-items: center;
        margin: 1.5rem 0;
        color: #555;
        font-size: 0.85rem;
    }
    .login-divider::before,
    .login-divider::after {
        content: '';
        flex: 1;
        border-bottom: 1px solid #333;
    }
    .login-divider::before { margin-right: 1rem; }
    .login-divider::after { margin-left: 1rem; }
    .feature-list {
        text-align: left;
        margin-top: 1.5rem;
        padding: 1rem;
        background: rgba(124, 92, 252, 0.05);
        border-radius: 12px;
    }
    .feature-list-item {
        color: #aaa;
        font-size: 0.85rem;
        padding: 0.3rem 0;
    }
    </style>
    
    <div class="login-container">
        <div class="login-card">
            <div class="login-logo">🦈</div>
            <div class="login-title">Finnie AI</div>
            <div class="login-subtitle">Autonomous Financial Intelligence</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Center the login buttons
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if _oauth_configured():
            st.markdown("##### Sign in to save your chats")

            if st.button("🔵 Continue with Google", use_container_width=True, key="login_google"):
                try:
                    st.login("google")
                except Exception as e:
                    st.error(f"Google login error: {e}")




            st.markdown('<div class="login-divider">or</div>', unsafe_allow_html=True)

        if st.button("👤 Continue as Guest", use_container_width=True, key="login_guest"):
            st.session_state.user = _create_guest_user()
            st.session_state.auth_complete = True
            st.session_state.logged_out = False
            st.rerun()

        st.markdown("""
        <div class="feature-list">
            <div class="feature-list-item">📊 Real-time market data & analysis</div>
            <div class="feature-list-item">🔮 Monte Carlo investment projections</div>
            <div class="feature-list-item">💼 Portfolio tracking & management</div>
            <div class="feature-list-item">💬 Chat history saved across sessions</div>
        </div>
        """, unsafe_allow_html=True)


def require_auth() -> dict:
    """
    Gate the app behind authentication.
    
    Returns user info dict if authenticated, otherwise shows login page and stops.
    Auto-enters guest mode if OAuth is not configured (local dev).
    """
    # Check for existing session (within this browser session)
    if st.session_state.get("auth_complete") and st.session_state.get("user"):
        return st.session_state.user

    # Only auto-detect OAuth when returning from the OAuth redirect flow,
    # NOT on a general page refresh. This ensures logout truly logs out.
    query_params = st.query_params.to_dict()
    is_oauth_callback = "code" in query_params or "oauth2callback" in query_params.get("", "")

    if is_oauth_callback:
        oauth_user = _get_user_info()
        if oauth_user:
            st.session_state.user = oauth_user
            st.session_state.auth_complete = True

            # Register user in database
            from src.memory import upsert_user
            upsert_user(
                user_id=oauth_user["user_id"],
                email=oauth_user["email"],
                name=oauth_user["name"],
                avatar_url=oauth_user.get("avatar_url", ""),
                provider=oauth_user["provider"],
            )
            return oauth_user

    # Auto-enter guest mode if OAuth isn't properly configured
    # (avoids requiring a click every refresh during local dev)
    # BUT skip if user explicitly logged out
    if not _oauth_has_real_credentials() and not st.session_state.get("logged_out"):
        guest = _create_guest_user()
        st.session_state.user = guest
        st.session_state.auth_complete = True
        return guest

    # Not authenticated — show login page
    render_login_page()
    st.stop()


def render_user_header(user: dict):
    """Render user avatar + name in the header with logout."""
    name = user.get("name", "Guest")
    avatar = user.get("avatar_url", "")
    is_guest = user.get("provider") == "guest"

    # User info in the top-right area
    cols = st.columns([6, 1])
    with cols[1]:
        if avatar:
            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:8px; justify-content:flex-end;">
                <img src="{avatar}" style="width:32px; height:32px; border-radius:50%;">
                <span style="font-size:0.85rem; color:#aaa;">{name}</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            emoji = "👤" if is_guest else "🔵"
            st.markdown(f"""
            <div style="text-align:right; font-size:0.85rem; color:#aaa;">
                {emoji} {name}
            </div>
            """, unsafe_allow_html=True)

        if st.button("Logout", key="logout_btn", type="secondary"):
            logout()


def logout():
    """Clear ALL session state and return to login page."""
    is_oauth = st.session_state.get("user", {}).get("provider") != "guest"

    # If OAuth, call Streamlit's built-in logout first
    if is_oauth:
        try:
            st.logout()
        except Exception:
            pass

    # Nuclear option — clear everything
    keys_to_keep = set()  # nothing to keep
    for key in list(st.session_state.keys()):
        if key not in keys_to_keep:
            del st.session_state[key]

    # Set logged_out flag AFTER clearing (prevents auto-guest re-entry)
    st.session_state.logged_out = True

    st.rerun()
