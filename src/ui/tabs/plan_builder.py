"""
Finnie AI — Plan Builder Tab

Interactive financial plan builder with editable goal cards,
year-over-year projections, combined timeline, and scenario comparison.

Works in two modes:
- AI-generated: Pre-populated from chat via st.session_state.active_plan
- Manual: User adds/edits goals directly
"""

import streamlit as st
import math


def render_plan_builder_tab():
    """Render the interactive plan builder tab."""

    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.12) 0%, rgba(167, 139, 250, 0.06) 100%);
        border: 1px solid rgba(167, 139, 250, 0.2);
        border-radius: 16px; padding: 24px 28px; margin-bottom: 20px;
    ">
        <h2 style="margin:0 0 6px 0; color:#c4b5fd;">📋 Plan Builder</h2>
        <p style="margin:0; color:#94a3b8; font-size:0.95rem;">
            Build and refine your financial plan. Add goals, adjust parameters, and see real-time projections.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Initialize plan goals in session state
    if "plan_goals" not in st.session_state:
        st.session_state.plan_goals = []

    # Check if AI generated a plan from chat
    active_plan = st.session_state.get("active_plan")
    if active_plan and active_plan.get("goals") and not st.session_state.plan_goals:
        st.session_state.plan_goals = active_plan["goals"]
        st.toast("✨ Plan loaded from your chat conversation!", icon="📋")

    # Scenario selector
    scenario_col, add_col = st.columns([3, 1])
    with scenario_col:
        scenario = st.radio(
            "Scenario",
            ["📉 Conservative (5%)", "📊 Moderate (7%)", "📈 Aggressive (10%)"],
            index=1,
            horizontal=True,
            key="plan_scenario",
        )
    with add_col:
        if st.button("➕ Add Goal", use_container_width=True, type="primary"):
            st.session_state.plan_goals.append({
                "name": f"New Goal {len(st.session_state.plan_goals) + 1}",
                "icon": "🎯",
                "target": 100_000,
                "timeline_years": 10,
                "current_savings": 0,
                "annual_return": 0.07,
                "vehicle": "Brokerage Account",
                "priority": len(st.session_state.plan_goals),
                "category": "custom",
            })
            st.rerun()

    # Parse scenario return override
    scenario_return = {"Conservative": 0.05, "Moderate": 0.07, "Aggressive": 0.10}
    for key, val in scenario_return.items():
        if key in scenario:
            override_return = val
            break
    else:
        override_return = 0.07

    goals = st.session_state.plan_goals

    if not goals:
        st.markdown("""
        <div style="
            text-align: center; padding: 60px 20px;
            background: rgba(30, 30, 50, 0.4);
            border: 1px dashed rgba(167, 139, 250, 0.3);
            border-radius: 16px; margin: 20px 0;
        ">
            <div style="font-size: 3rem; margin-bottom: 12px;">🎯</div>
            <h3 style="color: #c4b5fd; margin-bottom: 8px;">No Goals Yet</h3>
            <p style="color: #94a3b8;">
                Ask Finnie a question like <em>"Help me plan for retirement, college for my kids, and buying a home"</em>
                in the Chat tab, or click <strong>Add Goal</strong> above to start manually.
            </p>
        </div>
        """, unsafe_allow_html=True)
        # Show quick-start presets
        st.markdown("##### Quick Start Presets")
        preset_cols = st.columns(4)
        presets = [
            {"label": "🏦 Retirement", "goals": [{"name": "Retirement", "icon": "🏦", "target": 2_000_000, "timeline_years": 25, "current_savings": 50_000, "annual_return": 0.07, "vehicle": "401(k) + IRA", "priority": 2, "category": "retirement"}]},
            {"label": "🎓 College (2 Kids)", "goals": [
                {"name": "College — Child 1", "icon": "🎓", "target": 400_000, "timeline_years": 10, "current_savings": 0, "annual_return": 0.07, "vehicle": "529 Plan", "priority": 1, "category": "education"},
                {"name": "College — Child 2", "icon": "🎓", "target": 400_000, "timeline_years": 14, "current_savings": 0, "annual_return": 0.07, "vehicle": "529 Plan", "priority": 1, "category": "education"},
            ]},
            {"label": "🏠 Home Purchase", "goals": [{"name": "Home Down Payment", "icon": "🏠", "target": 400_000, "timeline_years": 3, "current_savings": 50_000, "annual_return": 0.04, "vehicle": "HYSA / Treasury", "priority": 0, "category": "home"}]},
            {"label": "🛡️ Emergency Fund", "goals": [{"name": "Emergency Fund", "icon": "🛡️", "target": 50_000, "timeline_years": 1, "current_savings": 10_000, "annual_return": 0.045, "vehicle": "HYSA", "priority": 0, "category": "emergency"}]},
        ]
        for col, preset in zip(preset_cols, presets):
            with col:
                if st.button(preset["label"], use_container_width=True):
                    st.session_state.plan_goals.extend(preset["goals"])
                    st.rerun()
        return

    # =========================================================================
    # Render Goal Cards
    # =========================================================================
    st.markdown("---")
    total_monthly_all = 0
    all_goal_projections = []

    for idx, goal in enumerate(goals):
        effective_return = override_return if goal.get("category") not in ("home", "emergency") else goal["annual_return"]

        with st.expander(f"{goal.get('icon', '🎯')} {goal['name']}", expanded=(idx < 3)):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                goal["name"] = st.text_input(
                    "Goal Name", goal["name"], key=f"goal_name_{idx}"
                )
                goal["target"] = st.number_input(
                    "Target Amount ($)", min_value=1_000, max_value=50_000_000,
                    value=int(goal["target"]), step=10_000, key=f"goal_target_{idx}",
                )
                goal["current_savings"] = st.number_input(
                    "Already Saved ($)", min_value=0, max_value=10_000_000,
                    value=int(goal.get("current_savings", 0)), step=5_000, key=f"goal_saved_{idx}",
                )
            with col2:
                goal["timeline_years"] = st.slider(
                    "Timeline (years)", 1, 40, int(goal["timeline_years"]), key=f"goal_years_{idx}",
                )
                effective_return = st.slider(
                    "Expected Return (%)", 1.0, 15.0,
                    float(effective_return * 100), step=0.5, key=f"goal_return_{idx}",
                ) / 100
                goal["annual_return"] = effective_return
                goal["vehicle"] = st.text_input(
                    "Investment Vehicle", goal.get("vehicle", "Brokerage"), key=f"goal_vehicle_{idx}",
                )
            with col3:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🗑️ Remove", key=f"goal_del_{idx}", use_container_width=True):
                    st.session_state.plan_goals.pop(idx)
                    st.rerun()

            # ── Calculate projection ────────────────────────────
            target = goal["target"]
            years = goal["timeline_years"]
            current = goal.get("current_savings", 0)
            rate = effective_return
            monthly_rate = rate / 12
            months = years * 12

            # Future value of current savings
            fv_current = current * ((1 + monthly_rate) ** months)
            remaining = max(0, target - fv_current)

            if monthly_rate > 0 and months > 0:
                monthly_needed = remaining * monthly_rate / (((1 + monthly_rate) ** months) - 1)
            else:
                monthly_needed = remaining / max(months, 1)

            total_monthly_all += monthly_needed

            # Year-over-year projection data
            balance = current
            yearly = []
            for y in range(1, years + 1):
                for _ in range(12):
                    balance = balance * (1 + monthly_rate) + monthly_needed
                yearly.append({"year": y, "balance": balance, "contributed": current + monthly_needed * 12 * y})
            all_goal_projections.append({"goal": goal, "monthly": monthly_needed, "yearly": yearly})

            # ── Metrics row ─────────────────────────────────────
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("🎯 Target", f"${target:,.0f}")
            with m2:
                st.metric("💵 Monthly Needed", f"${monthly_needed:,.0f}")
            with m3:
                total_contrib = current + monthly_needed * months
                growth = target - total_contrib
                st.metric("📈 Projected Growth", f"${max(0, growth):,.0f}")
            with m4:
                st.metric("📅 Timeline", f"{years} years")

            # ── Year-over-year chart ────────────────────────────
            try:
                import plotly.graph_objects as go

                fig = go.Figure()

                y_vals = [d["balance"] for d in yearly]
                c_vals = [d["contributed"] for d in yearly]
                x_vals = [d["year"] for d in yearly]

                # Contributions area
                fig.add_trace(go.Scatter(
                    x=x_vals, y=c_vals,
                    fill="tozeroy",
                    fillcolor="rgba(99, 102, 241, 0.15)",
                    line=dict(color="rgba(99, 102, 241, 0.4)", width=1),
                    name="Contributions",
                    hovertemplate="Year %{x}<br>Contributed: $%{y:,.0f}<extra></extra>",
                ))

                # Balance line
                fig.add_trace(go.Scatter(
                    x=x_vals, y=y_vals,
                    fill="tonexty",
                    fillcolor="rgba(34, 197, 94, 0.12)",
                    line=dict(color="#22c55e", width=2.5),
                    name="Total Balance",
                    hovertemplate="Year %{x}<br>Balance: $%{y:,.0f}<extra></extra>",
                ))

                # Target line
                fig.add_hline(
                    y=target, line_dash="dash", line_color="#f59e0b",
                    annotation_text=f"Goal: ${target:,.0f}",
                    annotation_position="top left",
                    annotation_font_color="#f59e0b",
                )

                fig.update_layout(
                    title=f"Year-over-Year Projection — {goal['name']}",
                    xaxis_title="Year",
                    yaxis_title="Value ($)",
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    height=320,
                    yaxis=dict(tickformat="$,.0f"),
                    margin=dict(t=40, b=30, l=60, r=20),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02),
                    showlegend=True,
                )
                st.plotly_chart(fig, use_container_width=True)
            except ImportError:
                st.info("Install plotly for interactive charts: `pip install plotly`")

    # =========================================================================
    # Combined Summary Section
    # =========================================================================
    if len(all_goal_projections) >= 1:
        st.markdown("---")
        st.markdown("""
        <h3 style="color: #c4b5fd; margin-bottom: 4px;">📊 Combined Financial Plan Summary</h3>
        """, unsafe_allow_html=True)

        # ── Total metrics ───────────────────────────────────────
        total_target = sum(g["goal"]["target"] for g in all_goal_projections)
        total_current = sum(g["goal"].get("current_savings", 0) for g in all_goal_projections)

        s1, s2, s3, s4 = st.columns(4)
        with s1:
            st.metric("🎯 Total Goals Value", f"${total_target:,.0f}")
        with s2:
            st.metric("💵 Total Monthly Savings", f"${total_monthly_all:,.0f}")
        with s3:
            st.metric("📅 Annual Savings Needed", f"${total_monthly_all * 12:,.0f}")
        with s4:
            st.metric("💰 Already Saved", f"${total_current:,.0f}")

        # ── Priority Table ──────────────────────────────────────
        st.markdown("#### 📋 Goal Breakdown")
        table_md = "| Priority | Goal | Target | Monthly | Vehicle | Timeline |\n"
        table_md += "|----------|------|--------|---------|---------|----------|\n"
        for i, gp in enumerate(sorted(all_goal_projections, key=lambda x: x["goal"].get("priority", 99))):
            g = gp["goal"]
            prio_labels = {0: "🔴 Critical", 1: "🟠 High", 2: "🟡 Medium", 3: "🟢 Normal"}
            prio = prio_labels.get(g.get("priority", 3), "🟢 Normal")
            table_md += f"| {prio} | {g.get('icon', '🎯')} {g['name']} | ${g['target']:,.0f} | ${gp['monthly']:,.0f} | {g.get('vehicle', '-')} | {g['timeline_years']}y |\n"
        table_md += f"| | **Total** | **${total_target:,.0f}** | **${total_monthly_all:,.0f}** | | |\n"
        st.markdown(table_md)

        # ── Combined Timeline Chart ─────────────────────────────
        st.markdown("#### 📈 Combined Growth Timeline")
        try:
            import plotly.graph_objects as go

            fig = go.Figure()

            # Colors for each goal
            colors = [
                ("#6366f1", "rgba(99, 102, 241, 0.15)"),
                ("#22c55e", "rgba(34, 197, 94, 0.12)"),
                ("#f59e0b", "rgba(245, 158, 11, 0.12)"),
                ("#ec4899", "rgba(236, 72, 153, 0.12)"),
                ("#06b6d4", "rgba(6, 182, 212, 0.12)"),
                ("#8b5cf6", "rgba(139, 92, 246, 0.12)"),
            ]

            max_years = max(gp["goal"]["timeline_years"] for gp in all_goal_projections)

            for i, gp in enumerate(all_goal_projections):
                color_line, color_fill = colors[i % len(colors)]
                yearly = gp["yearly"]
                x_vals = [d["year"] for d in yearly]
                y_vals = [d["balance"] for d in yearly]

                fig.add_trace(go.Scatter(
                    x=x_vals, y=y_vals,
                    mode="lines",
                    line=dict(color=color_line, width=2.5),
                    fill="tozeroy",
                    fillcolor=color_fill,
                    name=f"{gp['goal'].get('icon', '')} {gp['goal']['name']}",
                    hovertemplate=f"{gp['goal']['name']}<br>Year %{{x}}<br>${{y:,.0f}}<extra></extra>",
                ))

                # Add target marker
                fig.add_trace(go.Scatter(
                    x=[gp["goal"]["timeline_years"]],
                    y=[gp["goal"]["target"]],
                    mode="markers+text",
                    marker=dict(size=10, color=color_line, symbol="star"),
                    text=[f"${gp['goal']['target']:,.0f}"],
                    textposition="top center",
                    textfont=dict(size=10, color=color_line),
                    showlegend=False,
                    hoverinfo="skip",
                ))

            fig.update_layout(
                xaxis_title="Year",
                yaxis_title="Portfolio Value ($)",
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=420,
                yaxis=dict(tickformat="$,.0f"),
                margin=dict(t=20, b=40, l=60, r=20),
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02,
                    xanchor="center", x=0.5,
                ),
            )
            st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            pass

        # ── Quarter-by-Quarter Breakdown (First 3 Years) ────────
        st.markdown("#### 📅 Quarter-by-Quarter Savings Breakdown")

        qtr_years = min(3, max(gp["goal"]["timeline_years"] for gp in all_goal_projections))
        qtr_table = "| Quarter |"
        for gp in all_goal_projections:
            qtr_table += f" {gp['goal'].get('icon', '')} {gp['goal']['name'][:15]} |"
        qtr_table += " **Total** |\n"
        qtr_table += "|---------|" + "---------|" * len(all_goal_projections) + "---------|\n"

        for y in range(1, qtr_years + 1):
            for q in range(1, 5):
                quarter_label = f"Y{y} Q{q}"
                row = f"| {quarter_label} |"
                total_qtr = 0
                for gp in all_goal_projections:
                    monthly = gp["monthly"]
                    quarterly_savings = monthly * 3
                    total_qtr += quarterly_savings
                    row += f" ${quarterly_savings:,.0f} |"
                row += f" **${total_qtr:,.0f}** |"
                qtr_table += row + "\n"

        st.markdown(qtr_table)

        # ── Scenario Comparison ─────────────────────────────────
        st.markdown("#### 🔄 Scenario Comparison")

        scenarios = {"Conservative (5%)": 0.05, "Moderate (7%)": 0.07, "Aggressive (10%)": 0.10}
        comp_table = "| Goal |"
        for s_name in scenarios:
            comp_table += f" {s_name} |"
        comp_table += "\n|------|" + "------|" * len(scenarios) + "\n"

        for gp in all_goal_projections:
            g = gp["goal"]
            row = f"| {g.get('icon', '🎯')} {g['name'][:20]} |"
            for s_name, s_rate in scenarios.items():
                # Use scenario rate for non-short-term goals
                rate = s_rate if g.get("category") not in ("home", "emergency") else g["annual_return"]
                mr = rate / 12
                months = g["timeline_years"] * 12
                fv = g.get("current_savings", 0) * ((1 + mr) ** months)
                rem = max(0, g["target"] - fv)
                if mr > 0 and months > 0:
                    monthly = rem * mr / (((1 + mr) ** months) - 1)
                else:
                    monthly = rem / max(months, 1)
                row += f" ${monthly:,.0f}/mo |"
            comp_table += row + "\n"

        # Totals row
        total_row = "| **Total** |"
        for s_name, s_rate in scenarios.items():
            total = 0
            for gp in all_goal_projections:
                g = gp["goal"]
                rate = s_rate if g.get("category") not in ("home", "emergency") else g["annual_return"]
                mr = rate / 12
                months = g["timeline_years"] * 12
                fv = g.get("current_savings", 0) * ((1 + mr) ** months)
                rem = max(0, g["target"] - fv)
                if mr > 0 and months > 0:
                    monthly = rem * mr / (((1 + mr) ** months) - 1)
                else:
                    monthly = rem / max(months, 1)
                total += monthly
            total_row += f" **${total:,.0f}/mo** |"
        comp_table += total_row + "\n"
        st.markdown(comp_table)

        # ── Actionable Insights ─────────────────────────────────
        st.markdown("---")
        annual_salary_estimate = total_monthly_all * 12 / 0.25  # assume saving 25%

        if total_monthly_all > 0:
            st.markdown(f"""
> **💡 To fund all goals, you need to save ~${total_monthly_all:,.0f}/month (${total_monthly_all * 12:,.0f}/year).**
>
> This represents roughly 25% of a ${annual_salary_estimate:,.0f}/year income.
> Prioritize tax-advantaged accounts (401k match → HSA → Roth IRA → 529) before taxable brokerage.
            """)

        st.markdown("---")
        st.caption("⚠️ All projections assume consistent contributions and steady returns. Actual returns will vary. This is educational guidance, not professional financial advice.")

    # ── Clear plan button ─────────────────────────────────────
    st.markdown("")
    col_clear1, col_clear2 = st.columns([4, 1])
    with col_clear2:
        if st.button("🗑️ Clear All Goals", use_container_width=True):
            st.session_state.plan_goals = []
            if "active_plan" in st.session_state:
                del st.session_state["active_plan"]
            st.rerun()
