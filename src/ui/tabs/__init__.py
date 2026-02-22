"""
Finnie AI — Modular UI Tabs

Each tab is a separate module for maintainability.
"""

from src.ui.tabs.chat import render_chat_tab
from src.ui.tabs.portfolio import render_portfolio_tab
from src.ui.tabs.market import render_market_tab
from src.ui.tabs.projections import render_projections_tab
from src.ui.tabs.planner import render_planner_tab
from src.ui.tabs.crypto import render_crypto_tab
from src.ui.tabs.settings import render_settings_tab

__all__ = [
    "render_chat_tab",
    "render_portfolio_tab",
    "render_market_tab",
    "render_projections_tab",
    "render_planner_tab",
    "render_crypto_tab",
    "render_settings_tab",
]
