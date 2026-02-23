"""
Finnie AI — LLM Gateway

Smart routing and cost optimization for LLM calls.
Routes simple queries to cheap models and complex queries to powerful ones.
Tracks token usage and budget.

Routing:
  - Greetings, lookups → gemini-2.0-flash (free)
  - Definitions, explanations → gpt-4o-mini ($0.15/M)
  - Analysis, planning → gpt-4o / user's configured model
"""

from __future__ import annotations

import os
import re
import logging
import streamlit as st
from datetime import datetime, date

logger = logging.getLogger(__name__)


# ── Complexity tiers ────────────────────────────────────────────
TIER_FREE = "free"        # Gemini Flash — simple queries
TIER_CHEAP = "cheap"      # GPT-4o-mini — moderate queries
TIER_FULL = "full"        # User's configured model — complex queries

# Model mapping per tier
TIER_MODELS = {
    TIER_FREE: {
        "provider": "google",
        "model": "gemini-2.0-flash",
    },
    TIER_CHEAP: {
        "provider": "openai",
        "model": "gpt-4o-mini",
    },
    # TIER_FULL uses whatever the user has configured in settings
}

# Cost per million tokens (input + output averaged)
TIER_COSTS = {
    TIER_FREE: 0.0,
    TIER_CHEAP: 0.30,      # gpt-4o-mini avg
    TIER_FULL: 5.00,       # gpt-4o avg
}


def classify_query_complexity(user_input: str) -> str:
    """
    Classify a query into a complexity tier for smart routing.
    
    Returns: TIER_FREE, TIER_CHEAP, or TIER_FULL
    """
    text = user_input.lower().strip()
    word_count = len(text.split())
    
    # ── TIER_FREE: greetings, simple lookups ──
    simple_patterns = [
        "hello", "hi", "hey", "thanks", "thank you", "bye",
        "good morning", "good evening", "sup", "yo", "howdy",
        "what time", "date today",
    ]
    if text in simple_patterns or word_count <= 3:
        return TIER_FREE
    
    # ── TIER_FULL: complex multi-goal, planning, analysis ──
    complex_indicators = [
        # Multi-goal planning
        "retirement", "college savings", "529", "down payment",
        "financial plan", "what should i do",
        # Deep analysis
        "analyze", "analysis", "projection", "monte carlo",
        "compare", "scenario", "strategy", "rebalancing",
        # Long queries are usually complex
        "h1b", "visa", "relocation",
        # Index/market strategy
        "nasdaq", "spy", "dow", "russell",
        "entering", "leaving", "reconstitution",
    ]
    
    complex_count = sum(1 for p in complex_indicators if p in text)
    
    if complex_count >= 2 or word_count >= 50:
        return TIER_FULL
    
    # ── TIER_CHEAP: moderate queries ──
    moderate_patterns = [
        "what is", "explain", "how does", "tell me about",
        "price", "stock", "ticker", "market",
        "crypto", "bitcoin", "ethereum",
    ]
    if any(p in text for p in moderate_patterns):
        return TIER_CHEAP
    
    # Default: use the full model for anything not clearly simple
    return TIER_FULL


def get_routed_model(user_input: str) -> dict:
    """
    Get the optimal model for a query based on complexity.
    
    Returns dict with: provider, model, api_key, tier
    """
    tier = classify_query_complexity(user_input)
    
    # User's configured settings
    user_provider = st.session_state.get("llm_provider", "google")
    user_model = st.session_state.get("llm_model", "gemini-2.0-flash")
    user_key = st.session_state.get("llm_api_key", "")
    
    if tier == TIER_FULL:
        # Use user's configured model
        return {
            "provider": user_provider,
            "model": user_model,
            "api_key": user_key,
            "tier": tier,
        }
    
    if tier == TIER_FREE:
        # Try Gemini Flash (free)
        google_key = os.getenv("GOOGLE_API_KEY", "")
        if google_key:
            return {
                "provider": "google",
                "model": "gemini-2.0-flash",
                "api_key": google_key,
                "tier": tier,
            }
        # Fall back to user's model
        return {
            "provider": user_provider,
            "model": user_model,
            "api_key": user_key,
            "tier": TIER_FULL,
        }
    
    if tier == TIER_CHEAP:
        # Try GPT-4o-mini
        openai_key = os.getenv("OPENAI_API_KEY", "")
        if openai_key:
            return {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "api_key": openai_key,
                "tier": tier,
            }
        # Try Gemini Flash as fallback
        google_key = os.getenv("GOOGLE_API_KEY", "")
        if google_key:
            return {
                "provider": "google",
                "model": "gemini-2.0-flash",
                "api_key": google_key,
                "tier": TIER_FREE,
            }
        # Fall back to user's model
        return {
            "provider": user_provider,
            "model": user_model,
            "api_key": user_key,
            "tier": TIER_FULL,
        }
    
    return {
        "provider": user_provider,
        "model": user_model,
        "api_key": user_key,
        "tier": TIER_FULL,
    }


# ── Token Budget Tracking ──────────────────────────────────────

def track_usage(tier: str, input_tokens: int = 0, output_tokens: int = 0):
    """Track token usage for budget monitoring."""
    if "llm_usage" not in st.session_state:
        st.session_state.llm_usage = {
            "total_tokens": 0,
            "total_cost": 0.0,
            "by_tier": {},
            "today": str(date.today()),
            "daily_tokens": 0,
            "daily_cost": 0.0,
        }
    
    usage = st.session_state.llm_usage
    
    # Reset daily counters if new day
    if usage.get("today") != str(date.today()):
        usage["today"] = str(date.today())
        usage["daily_tokens"] = 0
        usage["daily_cost"] = 0.0
    
    total = input_tokens + output_tokens
    cost_per_m = TIER_COSTS.get(tier, 5.0)
    cost = (total / 1_000_000) * cost_per_m
    
    usage["total_tokens"] += total
    usage["total_cost"] += cost
    usage["daily_tokens"] += total
    usage["daily_cost"] += cost
    
    # Track by tier
    if tier not in usage["by_tier"]:
        usage["by_tier"][tier] = {"tokens": 0, "cost": 0.0, "calls": 0}
    usage["by_tier"][tier]["tokens"] += total
    usage["by_tier"][tier]["cost"] += cost
    usage["by_tier"][tier]["calls"] += 1
    
    logger.debug(
        f"LLM usage: tier={tier}, tokens={total}, cost=${cost:.4f}, "
        f"daily_total=${usage['daily_cost']:.4f}"
    )


def get_usage_summary() -> dict:
    """Get current token usage summary."""
    return st.session_state.get("llm_usage", {
        "total_tokens": 0,
        "total_cost": 0.0,
        "daily_tokens": 0,
        "daily_cost": 0.0,
        "by_tier": {},
    })
