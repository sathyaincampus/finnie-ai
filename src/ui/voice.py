"""
Finnie AI — Voice Interface

Text-to-Speech (TTS) via edge-tts and browser-based Speech-to-Text.
Provides voice input/output for the chat interface.
"""

from __future__ import annotations

import asyncio
import base64
import io
import tempfile
from pathlib import Path
from typing import Optional


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


def render_stt_component():
    """
    Render browser-based Speech-to-Text input.

    Uses the Web Speech API (webkitSpeechRecognition) via a Streamlit HTML component.
    Returns transcribed text through a hidden Streamlit text input.
    """
    import streamlit as st
    import streamlit.components.v1 as components

    stt_html = """
    <div id="stt-container" style="text-align: center;">
        <button id="stt-btn" onclick="startListening()" 
                style="
                    width: 60px; height: 60px; border-radius: 50%;
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    border: none; cursor: pointer; font-size: 24px;
                    color: white; transition: all 0.3s ease;
                    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
                ">
            🎤
        </button>
        <p id="stt-status" style="color: #888; font-size: 0.85rem; margin-top: 8px;">
            Click to speak
        </p>
    </div>

    <script>
    function startListening() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            document.getElementById('stt-status').textContent = 'Speech recognition not supported';
            return;
        }

        const recognition = new SpeechRecognition();
        recognition.lang = 'en-US';
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;

        const btn = document.getElementById('stt-btn');
        const status = document.getElementById('stt-status');

        btn.style.background = 'linear-gradient(135deg, #e74c3c, #c0392b)';
        btn.textContent = '⏺';
        status.textContent = 'Listening...';

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            status.textContent = transcript;
            btn.style.background = 'linear-gradient(135deg, #667eea, #764ba2)';
            btn.textContent = '🎤';

            // Send transcript to Streamlit
            window.parent.postMessage({
                type: 'streamlit:setComponentValue',
                value: transcript
            }, '*');
        };

        recognition.onerror = (event) => {
            status.textContent = 'Error: ' + event.error;
            btn.style.background = 'linear-gradient(135deg, #667eea, #764ba2)';
            btn.textContent = '🎤';
        };

        recognition.onend = () => {
            btn.style.background = 'linear-gradient(135deg, #667eea, #764ba2)';
            btn.textContent = '🎤';
        };

        recognition.start();
    }
    </script>
    """

    components.html(stt_html, height=120)


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
