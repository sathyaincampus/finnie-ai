"""
Finnie AI — Projections Tab

Interactive investment projection calculator with forward and goal-based modes.
"""

import streamlit as st
import math
import random


def render_projections_tab():
    """Render the projections tab with interactive calculators."""
    
    st.header("🔮 Investment Projections")
    
    mode = st.radio(
        "Projection Mode",
        ["📊 Forward Projection", "🎯 Goal-Based"],
        horizontal=True,
        key="projection_mode",
    )
    
    if "Forward" in mode:
        _render_forward_projection()
    else:
        _render_goal_projection()


def _render_forward_projection():
    """Interactive forward projection calculator."""
    st.subheader("📊 What will my investment grow to?")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        initial = st.number_input(
            "Initial Investment ($)",
            min_value=0, max_value=10_000_000,
            value=10000, step=1000,
            key="proj_initial",
        )
    
    with col2:
        monthly = st.number_input(
            "Monthly Contribution ($)",
            min_value=0, max_value=100_000,
            value=500, step=100,
            key="proj_monthly",
        )
    
    with col3:
        years = st.slider(
            "Time Horizon (years)",
            min_value=1, max_value=40,
            value=10,
            key="proj_years",
        )
    
    # Advanced options
    with st.expander("⚙️ Advanced Settings"):
        annual_return = st.slider(
            "Expected Annual Return (%)",
            min_value=1.0, max_value=20.0,
            value=8.0, step=0.5,
            key="proj_return",
        ) / 100
        
        annual_std = st.slider(
            "Market Volatility / Std Dev (%)",
            min_value=5.0, max_value=30.0,
            value=18.0, step=1.0,
            key="proj_std",
        ) / 100
    
    if st.button("Run Projection", type="primary", key="run_forward"):
        results = _run_monte_carlo(initial, monthly, years, annual_return, annual_std)
        _display_forward_results(results, initial, monthly, years)


def _render_goal_projection():
    """Interactive goal-based projection calculator."""
    st.subheader("🎯 How much do I need to invest?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        target = st.number_input(
            "Target Amount ($)",
            min_value=1000, max_value=100_000_000,
            value=1_000_000, step=50_000,
            key="goal_target",
        )
        
        current_savings = st.number_input(
            "Current Savings ($)",
            min_value=0, max_value=10_000_000,
            value=50000, step=5000,
            key="goal_current",
        )
    
    with col2:
        years_to_goal = st.slider(
            "Years to Goal",
            min_value=1, max_value=40,
            value=20,
            key="goal_years",
        )
        
        risk_profile = st.selectbox(
            "Risk Profile",
            ["Conservative (6%)", "Moderate (8%)", "Aggressive (10%)"],
            index=1,
            key="goal_risk",
        )
    
    if st.button("Calculate", type="primary", key="run_goal"):
        risk_key = risk_profile.split("(")[0].strip().lower()
        results = _run_goal_calculation(target, years_to_goal, current_savings, risk_key)
        _display_goal_results(results, target, years_to_goal, current_savings)


def _run_monte_carlo(
    initial: float,
    monthly: float,
    years: int,
    annual_return: float = 0.08,
    annual_std: float = 0.18,
    num_sims: int = 1000,
) -> dict:
    """Run Monte Carlo simulation."""
    monthly_return = annual_return / 12
    monthly_std = annual_std / math.sqrt(12)
    months = years * 12
    total_contributions = initial + (monthly * months)
    
    final_values = []
    for _ in range(num_sims):
        value = initial
        for _ in range(months):
            ret = random.gauss(monthly_return, monthly_std)
            value = value * (1 + ret) + monthly
        final_values.append(value)
    
    final_values.sort()
    
    return {
        "conservative": final_values[int(num_sims * 0.10)],
        "expected": final_values[int(num_sims * 0.50)],
        "optimistic": final_values[int(num_sims * 0.90)],
        "total_contributions": total_contributions,
    }


def _run_goal_calculation(
    target: float,
    years: int,
    current_savings: float,
    risk: str,
) -> dict:
    """Calculate required monthly investment for a goal."""
    profiles = {
        "conservative": 0.06,
        "moderate": 0.08,
        "aggressive": 0.10,
    }
    
    results = {}
    for name, rate in profiles.items():
        months = years * 12
        monthly_rate = rate / 12
        fv_current = current_savings * ((1 + monthly_rate) ** months)
        remaining = max(0, target - fv_current)
        
        if monthly_rate > 0:
            monthly_needed = remaining * monthly_rate / (((1 + monthly_rate) ** months) - 1)
        else:
            monthly_needed = remaining / max(months, 1)
        
        total_contrib = current_savings + (monthly_needed * months)
        
        results[name] = {
            "monthly": monthly_needed,
            "total_contributions": total_contrib,
            "growth": target - total_contrib,
            "rate": rate * 100,
        }
    
    return results


def _display_forward_results(results: dict, initial: float, monthly: float, years: int):
    """Display forward projection results."""
    st.divider()
    st.subheader("📊 Results")
    
    total = results["total_contributions"]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        val = results["conservative"]
        growth = (val / total - 1) * 100
        st.metric("📉 Conservative", f"${val:,.0f}", f"+{growth:.1f}%")
    
    with col2:
        val = results["expected"]
        growth = (val / total - 1) * 100
        st.metric("📊 Expected", f"${val:,.0f}", f"+{growth:.1f}%")
    
    with col3:
        val = results["optimistic"]
        growth = (val / total - 1) * 100
        st.metric("📈 Optimistic", f"${val:,.0f}", f"+{growth:.1f}%")
    
    st.caption(f"Total contributions: ${total:,.0f} over {years} years")
    
    st.info("💡 These projections use Monte Carlo simulation with 1,000 scenarios. "
            "Past performance does not guarantee future results.")


def _display_goal_results(results: dict, target: float, years: int, current: float):
    """Display goal-based projection results."""
    st.divider()
    st.subheader(f"🎯 Path to ${target:,.0f}")
    
    col1, col2, col3 = st.columns(3)
    
    for col, (name, data) in zip([col1, col2, col3], results.items()):
        emoji = {"conservative": "📉", "moderate": "📊", "aggressive": "📈"}[name]
        with col:
            st.metric(
                f"{emoji} {name.title()} ({data['rate']:.0f}%)",
                f"${data['monthly']:,.0f}/mo",
                f"${data['growth']:,.0f} growth",
            )
    
    st.caption(f"Starting with ${current:,.0f} • {years}-year horizon")
    
    # Action plan
    moderate = results.get("moderate", {})
    st.success(f"💡 **Recommended:** Invest **${moderate.get('monthly', 0):,.0f}/month** "
               f"in a diversified index fund to reach your goal.")
