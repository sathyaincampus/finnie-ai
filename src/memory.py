"""
Finnie AI — Persistent Memory Layer

SQLite-backed chat persistence for user conversations.
Stores messages, conversations, and user profiles.
"""

import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional


# Database file lives in project root
DB_PATH = Path(__file__).parent.parent / "finnie_data.db"


def _get_connection() -> sqlite3.Connection:
    """Get a SQLite connection with row factory."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = _get_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE,
                name TEXT,
                avatar_url TEXT,
                provider TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                last_login TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT DEFAULT 'New Chat',
                summary TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                agent TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_conv_user ON conversations(user_id);
            CREATE INDEX IF NOT EXISTS idx_msg_conv ON messages(conversation_id);
            CREATE INDEX IF NOT EXISTS idx_msg_created ON messages(created_at);
        """)
        conn.commit()
    finally:
        conn.close()


# =============================================================================
# User Management
# =============================================================================

def upsert_user(
    user_id: str,
    email: str,
    name: str,
    avatar_url: str = "",
    provider: str = "local",
) -> dict:
    """Create or update a user. Returns user dict."""
    conn = _get_connection()
    try:
        conn.execute("""
            INSERT INTO users (id, email, name, avatar_url, provider)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                avatar_url = excluded.avatar_url,
                last_login = datetime('now')
        """, (user_id, email, name, avatar_url, provider))
        conn.commit()

        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else {}
    finally:
        conn.close()


def get_user(user_id: str) -> Optional[dict]:
    """Get user by ID."""
    conn = _get_connection()
    try:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_user_by_email(email: str) -> Optional[dict]:
    """Get user by email."""
    conn = _get_connection()
    try:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# =============================================================================
# Conversation Management
# =============================================================================

def create_conversation(user_id: str, title: str = "New Chat") -> str:
    """Create a new conversation. Returns conversation ID."""
    conv_id = str(uuid.uuid4())
    conn = _get_connection()
    try:
        conn.execute(
            "INSERT INTO conversations (id, user_id, title) VALUES (?, ?, ?)",
            (conv_id, user_id, title),
        )
        conn.commit()
        return conv_id
    finally:
        conn.close()


def get_conversations(user_id: str, limit: int = 20) -> list[dict]:
    """Get recent conversations for a user, newest first."""
    conn = _get_connection()
    try:
        rows = conn.execute("""
            SELECT c.*, COUNT(m.id) as message_count
            FROM conversations c
            LEFT JOIN messages m ON m.conversation_id = c.id
            WHERE c.user_id = ?
            GROUP BY c.id
            ORDER BY c.updated_at DESC
            LIMIT ?
        """, (user_id, limit)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def update_conversation_title(conv_id: str, title: str):
    """Update a conversation's title."""
    conn = _get_connection()
    try:
        conn.execute(
            "UPDATE conversations SET title = ?, updated_at = datetime('now') WHERE id = ?",
            (title, conv_id),
        )
        conn.commit()
    finally:
        conn.close()


def update_conversation_summary(conv_id: str, summary: str):
    """Update a conversation's summary."""
    conn = _get_connection()
    try:
        conn.execute(
            "UPDATE conversations SET summary = ?, updated_at = datetime('now') WHERE id = ?",
            (summary, conv_id),
        )
        conn.commit()
    finally:
        conn.close()


def delete_conversation(conv_id: str):
    """Delete a conversation and its messages."""
    conn = _get_connection()
    try:
        conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
        conn.commit()
    finally:
        conn.close()


# =============================================================================
# Message Management
# =============================================================================

def save_message(
    conversation_id: str,
    role: str,
    content: str,
    agent: str = None,
) -> str:
    """Save a message to a conversation. Returns message ID."""
    msg_id = str(uuid.uuid4())
    conn = _get_connection()
    try:
        conn.execute(
            "INSERT INTO messages (id, conversation_id, role, content, agent) VALUES (?, ?, ?, ?, ?)",
            (msg_id, conversation_id, role, content, agent),
        )
        # Update conversation timestamp
        conn.execute(
            "UPDATE conversations SET updated_at = datetime('now') WHERE id = ?",
            (conversation_id,),
        )
        conn.commit()
        return msg_id
    finally:
        conn.close()


def get_messages(conversation_id: str, limit: int = 100) -> list[dict]:
    """Get messages for a conversation, oldest first."""
    conn = _get_connection()
    try:
        rows = conn.execute("""
            SELECT * FROM messages
            WHERE conversation_id = ?
            ORDER BY created_at ASC
            LIMIT ?
        """, (conversation_id, limit)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_recent_messages(user_id: str, limit: int = 50) -> list[dict]:
    """Get most recent messages across all conversations for a user."""
    conn = _get_connection()
    try:
        rows = conn.execute("""
            SELECT m.*, c.title as conversation_title
            FROM messages m
            JOIN conversations c ON c.id = m.conversation_id
            WHERE c.user_id = ?
            ORDER BY m.created_at DESC
            LIMIT ?
        """, (user_id, limit)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# =============================================================================
# Memory & Context
# =============================================================================

def get_conversation_summary(user_id: str) -> str:
    """
    Build a summary of recent conversations for memory context.
    
    Returns a concise text summary that can be injected into agent prompts.
    """
    conn = _get_connection()
    try:
        # Get last 5 conversations with their messages
        convs = conn.execute("""
            SELECT c.id, c.title, c.summary, c.updated_at
            FROM conversations c
            WHERE c.user_id = ?
            ORDER BY c.updated_at DESC
            LIMIT 5
        """, (user_id,)).fetchall()

        if not convs:
            return ""

        lines = ["Recent conversation history:"]
        for conv in convs:
            conv = dict(conv)
            title = conv.get("title", "Chat")
            summary = conv.get("summary", "")
            date = conv.get("updated_at", "")[:10]

            if summary:
                lines.append(f"- [{date}] {title}: {summary}")
            else:
                # Get last few messages as summary
                msgs = conn.execute("""
                    SELECT role, content FROM messages
                    WHERE conversation_id = ?
                    ORDER BY created_at DESC
                    LIMIT 4
                """, (conv["id"],)).fetchall()

                if msgs:
                    topics = []
                    for msg in reversed(list(msgs)):
                        msg = dict(msg)
                        if msg["role"] == "user":
                            # Truncate long messages
                            text = msg["content"][:80]
                            topics.append(text)
                    if topics:
                        lines.append(f"- [{date}] {title}: Asked about {'; '.join(topics)}")

        return "\n".join(lines) if len(lines) > 1 else ""
    finally:
        conn.close()


def auto_title_conversation(conv_id: str, first_message: str):
    """Auto-generate a conversation title from the first user message."""
    # Truncate to a reasonable title length
    title = first_message[:50].strip()
    if len(first_message) > 50:
        title += "…"
    # Clean up
    title = title.replace("\n", " ").strip()
    if title:
        update_conversation_title(conv_id, title)


def clear_user_history(user_id: str):
    """Delete all conversations and messages for a user."""
    conn = _get_connection()
    try:
        # Get all conversation IDs for user
        conv_ids = conn.execute(
            "SELECT id FROM conversations WHERE user_id = ?", (user_id,)
        ).fetchall()

        for conv in conv_ids:
            conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conv["id"],))

        conn.execute("DELETE FROM conversations WHERE user_id = ?", (user_id,))
        conn.commit()
    finally:
        conn.close()


# Initialize DB on import
init_db()
