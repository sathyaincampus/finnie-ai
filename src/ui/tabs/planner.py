"""
Finnie AI — Financial Planner Tab

Comprehensive financial life planning interface with interactive calculators.
"""

import streamlit as st
import math


def render_planner_tab():
    """Render the financial planning tab."""
    
    st.header("📋 Financial Life Planner")
    
    # Planning categories
    category = st.selectbox(
        "Planning Category",
        [
            "🏦 Retirement Planning",
            "🎓 Education Savings (529)",
            "💰 Tax Optimization",
            "🌍 Visa & Immigration Planning",
            "📊 Budget & Expenses",
            "💼 Side Hustles",
            "🎯 Goal-Based Savings",
        ],
        key="planner_category",
    )
    
    # Route to appropriate section
    if "Retirement" in category:
        _render_retirement_section()
    elif "Education" in category:
        _render_education_section()
    elif "Tax" in category:
        _render_tax_section()
    elif "Visa" in category:
        _render_visa_section()
    elif "Budget" in category:
        _render_budget_section()
    elif "Side Hustles" in category:
        _render_side_hustle_section()
    elif "Goal" in category:
        _render_goal_section()


def _render_retirement_section():
    """Interactive retirement planning calculator."""
    st.subheader("🏦 Retirement Planner")
    st.markdown("Enter your details to see a personalized retirement projection.")
    
    # --- User Inputs ---
    col1, col2, col3 = st.columns(3)
    
    with col1:
        current_age = st.number_input("Current Age", 18, 70, 30, key="ret_age")
        annual_salary = st.number_input(
            "Annual Salary ($)", 0, 1_000_000, 120000, step=5000, key="ret_salary"
        )
    
    with col2:
        retirement_age = st.number_input("Target Retirement Age", 40, 80, 60, key="ret_target_age")
        current_savings = st.number_input(
            "Current Retirement Savings ($)", 0, 10_000_000, 50000, step=5000, key="ret_savings"
        )
    
    with col3:
        monthly_401k = st.number_input(
            "Monthly 401(k) Contribution ($)", 0, 5000, 1500, step=100, key="ret_401k"
        )
        employer_match_pct = st.slider(
            "Employer Match (%)", 0, 10, 4, key="ret_match"
        )
    
    # Additional inputs
    with st.expander("⚙️ Additional Settings"):
        col_a, col_b = st.columns(2)
        with col_a:
            monthly_ira = st.number_input(
                "Monthly IRA Contribution ($)", 0, 1000, 300, step=50, key="ret_ira"
            )
            expected_return = st.slider(
                "Expected Annual Return (%)", 4.0, 12.0, 7.0, step=0.5, key="ret_return"
            ) / 100
        with col_b:
            annual_raise = st.slider(
                "Expected Annual Raise (%)", 0.0, 10.0, 3.0, step=0.5, key="ret_raise"
            ) / 100
            inflation_rate = st.slider(
                "Inflation Rate (%)", 1.0, 6.0, 3.0, step=0.5, key="ret_inflation"
            ) / 100
    
    # --- Calculate Projections ---
    years_to_retire = max(1, retirement_age - current_age)
    monthly_rate = expected_return / 12
    
    # Employer match (capped at salary percentage)
    annual_match = (annual_salary * employer_match_pct / 100)
    monthly_match = annual_match / 12
    
    # Total monthly contributions
    total_monthly = monthly_401k + monthly_ira + monthly_match
    
    # Year-by-year projection
    balance = current_savings
    yearly_data = []
    salary = annual_salary
    
    for year in range(1, years_to_retire + 1):
        for month in range(12):
            balance = balance * (1 + monthly_rate) + total_monthly
        
        yearly_data.append({
            "Year": year,
            "Age": current_age + year,
            "Balance": balance,
            "Salary": salary,
        })
        
        # Apply annual raise to salary and match
        salary *= (1 + annual_raise)
        monthly_match_adjusted = salary * employer_match_pct / 100 / 12
        total_monthly = monthly_401k + monthly_ira + monthly_match_adjusted
    
    # Final numbers
    projected_balance = balance
    total_contributions = current_savings + (monthly_401k + monthly_ira) * 12 * years_to_retire
    total_growth = projected_balance - total_contributions
    
    # Inflation-adjusted
    real_balance = projected_balance / ((1 + inflation_rate) ** years_to_retire)
    
    # Safe withdrawal (4% rule)
    annual_income = projected_balance * 0.04
    monthly_income = annual_income / 12
    
    # --- Display Results ---
    st.divider()
    st.subheader("📊 Your Retirement Projection")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🎯 Projected Balance", f"${projected_balance:,.0f}")
    with col2:
        st.metric("📉 Inflation-Adjusted", f"${real_balance:,.0f}")
    with col3:
        st.metric("💰 Monthly Income (4% rule)", f"${monthly_income:,.0f}/mo")
    with col4:
        st.metric("📈 Investment Growth", f"${total_growth:,.0f}")
    
    # Chart — balance growth over time
    try:
        import plotly.graph_objects as go
        
        ages = [d["Age"] for d in yearly_data]
        balances = [d["Balance"] for d in yearly_data]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=ages, y=balances,
            fill="tozeroy",
            fillcolor="rgba(99, 102, 241, 0.15)",
            line=dict(color="#6366f1", width=2),
            name="Portfolio Value",
            hovertemplate="Age %{x}<br>Balance: $%{y:,.0f}<extra></extra>",
        ))
        
        fig.update_layout(
            title=f"Projected Growth: Age {current_age} → {retirement_age}",
            xaxis_title="Age",
            yaxis_title="Portfolio Value ($)",
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=400,
            yaxis=dict(tickformat="$,.0f"),
        )
        
        st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        pass
    
    # Summary breakdown
    with st.expander("📋 Contribution Breakdown"):
        st.markdown(f"""
        | Category | Monthly | Annual |
        |----------|---------|--------|
        | Your 401(k) | ${monthly_401k:,.0f} | ${monthly_401k * 12:,.0f} |
        | Employer Match ({employer_match_pct}%) | ${monthly_match:,.0f} | ${monthly_match * 12:,.0f} |
        | IRA | ${monthly_ira:,.0f} | ${monthly_ira * 12:,.0f} |
        | **Total** | **${total_monthly:,.0f}** | **${total_monthly * 12:,.0f}** |
        """)
    
    # Guidance
    if annual_income < annual_salary * 0.7:
        st.warning(
            f"⚠️ Your projected retirement income (${annual_income:,.0f}/yr) is less than 70% "
            f"of your current salary (${annual_salary * 0.7:,.0f}). Consider increasing contributions."
        )
    else:
        st.success(
            f"🎉 Great! Your projected retirement income (${annual_income:,.0f}/yr) exceeds "
            f"70% of your current salary. You're on track!"
        )
    
    # Reference info
    with st.expander("📚 2025 Contribution Limits"):
        st.markdown("""
        | Account | Under 50 | Age 50+ |
        |---------|----------|---------|
        | 401(K) | $23,500 | $30,500 |
        | Roth IRA | $7,000 | $8,000 |
        | HSA (Individual) | $4,150 | $5,150 |
        | HSA (Family) | $8,300 | $9,300 |
        """)


def _render_education_section():
    """529 and education savings section."""
    st.subheader("🎓 Education Savings Calculator")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        num_children = st.number_input("Number of Children", 1, 10, 2, key="plan_children")
    with col2:
        child_age = st.number_input("Youngest Child's Age", 0, 18, 5, key="plan_child_age")
    with col3:
        monthly_529 = st.number_input("Monthly 529 Contribution ($)", 0, 5000, 200, step=50, key="plan_529_monthly")
    
    years_to_college = max(1, 18 - child_age)
    total_saved = monthly_529 * 12 * years_to_college
    
    # Future value with compound growth
    fv = 0
    monthly_rate = 0.07 / 12
    months = years_to_college * 12
    
    yearly_balances = []
    for m in range(months):
        fv = (fv + monthly_529) * (1 + monthly_rate)
        if (m + 1) % 12 == 0:
            yearly_balances.append({"Year": (m + 1) // 12, "Balance": fv})
    
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Contributions", f"${total_saved:,.0f}")
    with col2:
        st.metric("Projected Value (7%)", f"${fv:,.0f}")
    with col3:
        growth = fv - total_saved
        st.metric("Investment Growth", f"${growth:,.0f}")
    
    st.caption(f"Based on ${monthly_529}/month for {years_to_college} years at 7% average return")
    
    # Chart
    try:
        import plotly.graph_objects as go
        
        if yearly_balances:
            fig = go.Figure()
            years_list = [d["Year"] for d in yearly_balances]
            bal_list = [d["Balance"] for d in yearly_balances]
            contrib_list = [monthly_529 * 12 * y for y in years_list]
            
            fig.add_trace(go.Bar(
                x=years_list, y=contrib_list,
                name="Contributions",
                marker_color="rgba(99, 102, 241, 0.5)",
            ))
            fig.add_trace(go.Scatter(
                x=years_list, y=bal_list,
                name="Total Value",
                line=dict(color="#22c55e", width=2),
                fill="tonexty",
                fillcolor="rgba(34, 197, 94, 0.1)",
            ))
            
            fig.update_layout(
                title="529 Plan Growth Projection",
                xaxis_title="Year",
                yaxis_title="Value ($)",
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=350,
                yaxis=dict(tickformat="$,.0f"),
            )
            st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        pass
    
    # Cost reference
    with st.expander("📋 Monthly Activity Costs to Budget"):
        st.markdown("""
        | Activity | Monthly Cost |
        |----------|-------------|
        | AoPS/RSM Math | $200-400 |
        | Music Lessons | $150-300 |
        | Sports (Cricket, Tennis) | $100-250 |
        | Chess Club | $50-100 |
        """)


def _render_tax_section():
    """Interactive tax optimization section."""
    st.subheader("💰 Tax Optimizer")
    
    col1, col2 = st.columns(2)
    with col1:
        filing_status = st.selectbox(
            "Filing Status",
            ["Single", "Married Filing Jointly", "Head of Household"],
            key="tax_filing",
        )
        gross_income = st.number_input(
            "Annual Gross Income ($)", 0, 2_000_000, 150000, step=5000, key="tax_income"
        )
    with col2:
        pre_tax_contrib = st.number_input(
            "Pre-Tax Contributions (401k + HSA) ($)", 0, 100000, 23500, step=1000, key="tax_pretax"
        )
        itemized_deductions = st.number_input(
            "Itemized Deductions ($) (0 = standard)", 0, 500000, 0, step=1000, key="tax_deductions"
        )
    
    # 2025 standard deductions
    standard = {"Single": 15000, "Married Filing Jointly": 30000, "Head of Household": 22500}
    deduction = max(standard.get(filing_status, 15000), itemized_deductions)
    
    taxable_income = max(0, gross_income - pre_tax_contrib - deduction)
    
    # Calculate federal tax (2025 brackets - single)
    brackets_single = [
        (11925, 0.10), (48475, 0.12), (103350, 0.22),
        (197300, 0.24), (250525, 0.32), (626350, 0.35), (float("inf"), 0.37),
    ]
    brackets_married = [
        (23850, 0.10), (96950, 0.12), (206700, 0.22),
        (394600, 0.24), (501050, 0.32), (751600, 0.35), (float("inf"), 0.37),
    ]
    brackets_hoh = [
        (17000, 0.10), (64850, 0.12), (103350, 0.22),
        (197300, 0.24), (250500, 0.32), (626350, 0.35), (float("inf"), 0.37),
    ]
    
    bracket_map = {
        "Single": brackets_single,
        "Married Filing Jointly": brackets_married,
        "Head of Household": brackets_hoh,
    }
    
    tax = 0
    prev_limit = 0
    effective_bracket = 0
    for limit, rate in bracket_map.get(filing_status, brackets_single):
        if taxable_income <= 0:
            break
        taxable_in_bracket = min(taxable_income, limit) - prev_limit
        if taxable_in_bracket > 0:
            tax += taxable_in_bracket * rate
            effective_bracket = rate
        prev_limit = limit
    
    effective_rate = (tax / gross_income * 100) if gross_income > 0 else 0
    marginal_rate = effective_bracket * 100
    saved_from_pretax = pre_tax_contrib * effective_bracket
    
    st.divider()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Taxable Income", f"${taxable_income:,.0f}")
    with col2:
        st.metric("Estimated Federal Tax", f"${tax:,.0f}")
    with col3:
        st.metric("Effective Rate", f"{effective_rate:.1f}%")
    with col4:
        st.metric("Pre-Tax Savings", f"${saved_from_pretax:,.0f}", "Tax saved")
    
    st.caption(f"Marginal bracket: {marginal_rate:.0f}% • Deduction: ${deduction:,.0f} ({('Standard' if itemized_deductions == 0 else 'Itemized')})")
    
    # Strategies
    st.markdown("""
    ### 💡 Top Strategies
    1. **Maximize Pre-Tax Contributions** — 401(K), HSA reduce taxable income
    2. **Tax-Loss Harvesting** — Sell losers to offset gains
    3. **Long-Term Capital Gains** — Hold >1 year for lower rates (0%/15%/20%)
    4. **Qualified Dividends** — Taxed at capital gains rates
    5. **Municipal Bonds** — Tax-free interest income
    """)


def _render_visa_section():
    """Visa/immigration financial planning section."""
    st.subheader("🌍 Financial Planning on a Work Visa")
    
    st.markdown("""
    ### Key Considerations for H1B/L1 Visa Holders
    
    **Emergency Fund:** 6-12 months (higher than the usual 3-6 months)
    - Visa transfer can take weeks; job loss starts the 60-day grace period
    
    **Investing in the US:**
    - ✅ Brokerage accounts (Fidelity, Schwab, Vanguard) — allowed on H1B
    - ✅ 401(K) and Roth IRA — fully available
    - ✅ Real estate investment — allowed
    - ⚠️ Side income requires employer authorization
    
    **Home Country Investments (India):**
    | Account | Purpose | Tax Reporting |
    |---------|---------|---------------|
    | NRE Account | USD → INR, repatriable | FBAR + FATCA |
    | NRO Account | Indian income | FBAR + FATCA |
    | PPF/FD | Savings | Report on US taxes |
    
    **FBAR Filing:** Required if foreign accounts exceed $10,000 at any point
    
    **Remittances:** Use Wise, Remitly, or HDFC for best rates
    """)
    
    st.info("💡 Ask Finnie: *\"Help me plan my finances as an H1B visa holder\"*")


def _render_budget_section():
    """Budget and expense tracking section."""
    st.subheader("📊 Monthly Budget Planner")
    
    st.markdown("Enter your monthly expenses to see your budget breakdown:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        income = st.number_input("Monthly Take-Home Pay ($)", 0, 100000, 8000, step=500, key="budget_income")
        housing = st.number_input("Housing (Rent/Mortgage) ($)", 0, 20000, 2500, step=100, key="budget_housing")
        utilities = st.number_input("Utilities ($)", 0, 2000, 300, step=50, key="budget_utilities")
        groceries = st.number_input("Groceries ($)", 0, 5000, 800, step=50, key="budget_groceries")
    
    with col2:
        transport = st.number_input("Transportation ($)", 0, 5000, 500, step=50, key="budget_transport")
        insurance = st.number_input("Insurance ($)", 0, 5000, 400, step=50, key="budget_insurance")
        kids = st.number_input("Kids/Family ($)", 0, 10000, 1000, step=100, key="budget_kids")
        other = st.number_input("Other Expenses ($)", 0, 10000, 500, step=100, key="budget_other")
    
    total_expenses = housing + utilities + groceries + transport + insurance + kids + other
    savings = income - total_expenses
    savings_rate = (savings / income * 100) if income > 0 else 0
    
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Expenses", f"${total_expenses:,.0f}")
    with col2:
        st.metric("Monthly Savings", f"${savings:,.0f}", 
                  "Positive!" if savings > 0 else "Over budget!")
    with col3:
        st.metric("Savings Rate", f"{savings_rate:.1f}%")
    
    # Pie chart
    try:
        import plotly.graph_objects as go
        
        labels = ["Housing", "Utilities", "Groceries", "Transport", "Insurance", "Kids/Family", "Other", "Savings"]
        values = [housing, utilities, groceries, transport, insurance, kids, other, max(0, savings)]
        colors = ["#6366f1", "#818cf8", "#22c55e", "#06b6d4", "#f59e0b", "#ec4899", "#94a3b8", "#10b981"]
        
        fig = go.Figure(data=[go.Pie(
            labels=labels, values=values,
            hole=0.45,
            marker_colors=colors,
            textinfo="label+percent",
            hovertemplate="%{label}: $%{value:,.0f}<extra></extra>",
        )])
        fig.update_layout(
            title="Budget Breakdown",
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            height=380,
        )
        st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        pass
    
    if savings_rate < 15:
        st.warning("⚠️ Aim for at least 15-20% savings rate for long-term financial health.")
    elif savings_rate < 20:
        st.info("📊 Good savings rate! Consider increasing to 20%+ if possible.")
    else:
        st.success("🎉 Excellent savings rate! You're on track for financial independence.")


def _render_side_hustle_section():
    """Side hustle guidance section."""
    st.subheader("💼 Side Hustle Ideas for Tech Professionals")
    
    st.markdown("""
    | Side Hustle | Earning Potential | Time Required | Visa-Friendly |
    |-------------|------------------|---------------|---------------|
    | Tech Consulting | $100-300/hr | 5-10 hrs/wk | ⚠️ Needs auth |
    | Online Courses | $500-5000/mo passive | 40-100 hrs upfront | ✅ Yes |
    | Tech Blog/YouTube | $200-2000/mo | 5-10 hrs/wk | ✅ Yes |
    | Open Source Sponsorship | $100-1000/mo | Varies | ✅ Yes |
    | Freelance Writing | $200-500/article | 3-5 hrs/article | ⚠️ Needs auth |
    
    ⚠️ **On H1B/L1:** Side income typically requires employer authorization.
    Passive income (investments, course sales) may be permissible — consult an immigration attorney.
    """)
    
    st.info("💡 Ask Finnie: *\"What are good side hustle options for someone in tech?\"*")


def _render_goal_section():
    """Interactive goal-based savings calculator."""
    st.subheader("🎯 Savings Goal Calculator")
    
    st.markdown("Set a custom goal and see how much you need to save monthly:")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        goal_name = st.text_input("Goal Name", "Dream Home", key="goal_name")
        target = st.number_input(
            "Target Amount ($)", 1000, 10_000_000, 100000, step=5000, key="goal_target_amt"
        )
    with col2:
        current = st.number_input(
            "Already Saved ($)", 0, 5_000_000, 10000, step=1000, key="goal_current_amt"
        )
        years = st.slider("Years to Goal", 1, 30, 5, key="goal_years_slider")
    with col3:
        return_rate = st.slider(
            "Expected Return (%)", 0.0, 12.0, 7.0, step=0.5, key="goal_return"
        ) / 100
    
    months = years * 12
    monthly_rate = return_rate / 12
    
    # FV of current savings
    fv_current = current * ((1 + monthly_rate) ** months)
    remaining = max(0, target - fv_current)
    
    if monthly_rate > 0:
        monthly_needed = remaining * monthly_rate / (((1 + monthly_rate) ** months) - 1)
    else:
        monthly_needed = remaining / max(months, 1)
    
    total_contrib = current + (monthly_needed * months)
    growth = target - total_contrib
    
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(f"🎯 {goal_name}", f"${target:,.0f}")
    with col2:
        st.metric("Monthly Savings Needed", f"${monthly_needed:,.0f}/mo")
    with col3:
        st.metric("Projected Growth", f"${growth:,.0f}")
    
    st.caption(f"Starting with ${current:,.0f} • {return_rate*100:.0f}% return • {years} year horizon")
    
    # Progress chart
    try:
        import plotly.graph_objects as go
        
        balance = current
        chart_data_x = [0]
        chart_data_y = [current]
        
        for m in range(1, months + 1):
            balance = balance * (1 + monthly_rate) + monthly_needed
            if m % 12 == 0 or m == months:
                chart_data_x.append(m // 12 if m % 12 == 0 else m / 12)
                chart_data_y.append(balance)
        
        fig = go.Figure()
        fig.add_hline(y=target, line_dash="dash", line_color="#f59e0b",
                      annotation_text=f"Goal: ${target:,.0f}")
        fig.add_trace(go.Scatter(
            x=chart_data_x, y=chart_data_y,
            fill="tozeroy",
            fillcolor="rgba(34, 197, 94, 0.15)",
            line=dict(color="#22c55e", width=2),
            name="Projected Balance",
        ))
        
        fig.update_layout(
            title=f"Path to {goal_name}: ${target:,.0f}",
            xaxis_title="Year",
            yaxis_title="Balance ($)",
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=350,
            yaxis=dict(tickformat="$,.0f"),
        )
        st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        pass
    
    if monthly_needed > 0:
        st.success(
            f"💡 Save **${monthly_needed:,.0f}/month** to reach **${target:,.0f}** "
            f"in **{years} years** (at {return_rate*100:.0f}% return)."
        )
