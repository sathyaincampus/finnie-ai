"""
Finnie AI — Voice Interface

Text-to-Speech (TTS) via edge-tts and browser-based Speech-to-Text.
Provides voice input/output for the chat interface.
"""

from __future__ import annotations

import asyncio
import base64
import io
import os
import tempfile
from pathlib import Path
from typing import Optional

import streamlit.components.v1 as _components

# Register the STT custom component once at module level
_STT_COMPONENT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stt_component")
_stt_func = _components.declare_component("stt_input", path=_STT_COMPONENT_DIR)


# =============================================================================
# TTS — Text-to-Speech (via edge-tts)
# =============================================================================


async def text_to_speech(
    text: str,
    voice: str = "en-US-AriaNeural",
    rate: str = "+0%",
) -> bytes:
    """
    Convert text to speech audio using edge-tts.

    Args:
        text: Text to convert to speech.
        voice: Voice name (Microsoft Edge TTS voices).
        rate: Speed adjustment (e.g., "+10%", "-10%").

    Returns:
        Audio bytes in MP3 format.
    """
    import edge_tts

    communicate = edge_tts.Communicate(text, voice, rate=rate)

    # Collect audio chunks
    audio_chunks = []
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_chunks.append(chunk["data"])

    return b"".join(audio_chunks)


def text_to_speech_sync(
    text: str,
    voice: str = "en-US-AriaNeural",
    rate: str = "+0%",
) -> bytes:
    """Synchronous wrapper for text_to_speech."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(text_to_speech(text, voice, rate))
    finally:
        loop.close()


def audio_to_base64(audio_bytes: bytes) -> str:
    """Convert audio bytes to base64 for embedding in HTML audio elements."""
    return base64.b64encode(audio_bytes).decode("utf-8")


# =============================================================================
# Available Voices
# =============================================================================

AVAILABLE_VOICES = {
    "Aria (US Female)": "en-US-AriaNeural",
    "Guy (US Male)": "en-US-GuyNeural",
    "Jenny (US Female)": "en-US-JennyNeural",
    "Ryan (UK Male)": "en-GB-RyanNeural",
    "Sonia (UK Female)": "en-GB-SoniaNeural",
    "Natasha (AU Female)": "en-AU-NatashaNeural",
}


# =============================================================================
# Streamlit Voice Component
# =============================================================================


def render_voice_controls():
    """Render voice input/output controls in Streamlit."""
    import streamlit as st

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        voice_enabled = st.toggle("🎤 Voice Mode", key="voice_mode", value=False)

    with col2:
        if voice_enabled:
            voice_name = st.selectbox(
                "Voice",
                options=list(AVAILABLE_VOICES.keys()),
                key="voice_select",
                label_visibility="collapsed",
            )
        else:
            voice_name = "Aria (US Female)"

    with col3:
        if voice_enabled:
            auto_speak = st.toggle("Auto-speak", key="auto_speak", value=True)
        else:
            auto_speak = False

    return {
        "enabled": voice_enabled,
        "voice": AVAILABLE_VOICES.get(voice_name, "en-US-AriaNeural"),
        "auto_speak": auto_speak,
    }


def speak_response(text: str, voice: str = "en-US-AriaNeural"):
    """Generate and play TTS audio in Streamlit."""
    import streamlit as st

    # Strip markdown formatting for cleaner speech
    clean_text = _strip_markdown(text)

    # Limit length for TTS
    if len(clean_text) > 1000:
        clean_text = clean_text[:1000] + "... That's the summary."

    try:
        audio_bytes = text_to_speech_sync(clean_text, voice=voice)
        b64_audio = audio_to_base64(audio_bytes)

        # Auto-playing audio element
        st.markdown(
            f"""
            <audio autoplay>
                <source src="data:audio/mp3;base64,{b64_audio}" type="audio/mp3">
            </audio>
            """,
            unsafe_allow_html=True,
        )
    except Exception as e:
        st.warning(f"Voice output unavailable: {e}")


def render_stt_component() -> str | None:
    """
    Render browser-based Speech-to-Text input.

    Uses a proper Streamlit custom component (declare_component) for
    bi-directional communication. The Web Speech API captures voice in the
    browser and sends the transcript back to Python.

    Returns:
        Transcribed text string, or None if nothing new captured.
    """
    import streamlit as st

    # Render the component — returns the value set by JS via setComponentValue
    result = _stt_func(key="stt_input", default=None)

    # De-duplicate: only return transcript if it's new (timestamp differs)
    if result and isinstance(result, dict):
        transcript = result.get("transcript", "")
        timestamp = result.get("timestamp", 0)

        if transcript and timestamp != st.session_state.get("_last_stt_ts"):
            st.session_state._last_stt_ts = timestamp
            return transcript

    return None


# =============================================================================
# Helpers
# =============================================================================


def _strip_markdown(text: str) -> str:
    """Remove common markdown formatting for cleaner TTS output."""
    import re

    # Remove headers
    text = re.sub(r"#{1,6}\s*", "", text)
    # Remove bold/italic
    text = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", text)
    # Remove links
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # Remove code blocks
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    # Remove table pipes
    text = re.sub(r"\|", " ", text)
    # Remove horizontal rules
    text = re.sub(r"---+", "", text)
    # Remove emojis (keep it cleaner for TTS)
    text = re.sub(
        r"[\U0001f300-\U0001f9ff\U00002600-\U000027bf\U0000fe00-\U0000feff]",
        "",
        text,
    )
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text
