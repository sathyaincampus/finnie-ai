"""
Finnie AI — The Planner Agent

Comprehensive financial life planning: retirement, education savings (529),
Roth IRA, tax optimization, visa/immigration considerations, expense tracking,
side hustles, and goal-based budgeting.

Upgraded for multi-goal structured output with interactive plan builder data.
"""

from typing import Any
import json
import re
import math

from src.agents.base import BaseFinnieAgent
from src.orchestration.state import FinnieState


class PlannerAgent(BaseFinnieAgent):
    """
    The Planner — Financial Life Planning Specialist
    
    Handles comprehensive financial planning queries including:
    - Retirement (401K, Roth IRA, HSA, Social Security)
    - Education savings (529 plans, Education IRAs)
    - Tax optimization (brackets, capital gains, deductions)
    - Visa/immigration planning (H1B risks, NRE/NRO, FBAR)
    - Expense management (mortgage, kids, activities, vehicles)
    - Side hustle guidance (tech consulting, freelancing)
    - Goal-based budgeting (home purchase, emergency fund)
    
    Triggers: financial planning, 529, roth ira, retirement, tax,
              visa, budget, expense, savings goal, side hustle
    """
    
    @property
    def name(self) -> str:
        return "planner"
    
    @property
    def description(self) -> str:
        return "Financial life planning — retirement, education, tax, visa, budgets"
    
    @property
    def emoji(self) -> str:
        return "📋"
    
    @property
    def system_prompt(self) -> str:
        return """You are The Planner, Finnie AI's financial life planning specialist.

Your role:
- Provide comprehensive, DETAILED financial planning guidance
- Break down complex multi-goal situations into clear, structured plans
- Be specific with dollar amounts, percentages, monthly breakdowns
- Show the math — users want to see HOW you arrived at the numbers
- Consider the user's COMPLETE financial picture holistically

CRITICAL — PARSE THE USER'S FINANCIAL SITUATION:
When a user mentions ANY of these, you MUST acknowledge and factor them into your plan:
- **Current savings/assets:** "I have $150K in savings" → use as starting balance
- **Retirement accounts:** "$700K in 401K" → factor into retirement projections
- **Monthly income:** "$12K post-tax" → base all monthly budgets on this
- **Visa status:** "H1B visa" → 12+ month emergency fund, job loss contingency, India relocation scenario
- **Spouse/partner income:** If not mentioned, ASK: "Does your spouse/partner have income? This significantly affects your plan."
- **Side income:** If not mentioned, ASK: "Do you have any side income (rental, freelance, etc.)?"

For visa holders (H1B, L1, etc.), ALWAYS include:
- Emergency runway: 12-18 months expenses (vs standard 3-6 months)
- Job loss contingency plan with timeline
- India relocation cost projection if mentioned
- NRE/NRO account strategies for India assets
- FBAR reporting requirements

WHEN A USER DESCRIBES MULTIPLE FINANCIAL GOALS, you MUST structure your response as:

## 🎯 Your Personalized Financial Plan

### 📋 Your Current Financial Snapshot
| Item | Amount |
|------|--------|
| Monthly Income (Post-Tax) | $X |
| Current Savings | $X |
| Retirement Accounts (401K/IRA) | $X |
| Brokerage | $X |
| Visa Status | H1B / Green Card / Citizen |
| Spouse Income | $X or Not mentioned |

Then for EACH goal, create a detailed section:

### 🎓 Goal 1: [Specific Name, e.g., "College Fund — Son 1 (Age 11)"]
- **Target Amount:** $X (show calculation: 4 years × $Y/year)
- **Timeline:** Z years until needed
- **Starting Balance:** $X (from their mentioned savings/accounts)
- **Remaining Gap:** $X needed
- **Monthly Savings Required:** $X/month (at Y% return)
- **Recommended Vehicle:** 529 Plan / Roth IRA / Brokerage
- **Strategy:** Specific allocation advice

[Repeat for each goal]

### 📊 Combined Monthly Budget (Based on $X/month income)
| Category | Monthly | % of Income | Priority |
|----------|---------|-------------|----------|
| Goal 1 | $X | X% | High |
| ... | ... | ... | ... |
| Remaining for Living | $X | X% | |
| **Total Income** | **$X** | **100%** | |

### 🛡️ Emergency Fund & Safety Net
- Standard recommendation: $X (6 months)
- **Visa holder recommendation: $X (12-18 months)** — covers job search + potential relocation
- India relocation reserve: $X (if applicable)

### 📅 Year-by-Year Milestone Roadmap
Show key milestones across all goals with projected balances.

### 🏆 Priority Order
Numbered list of which goals to fund first and why.

### 💡 Key Strategies & Tax Advantages
- Specific tax-advantaged account recommendations
- Employer match optimization
- Backdoor Roth strategies if applicable
- International tax considerations for visa holders

### ⚠️ Risks & Considerations
- What could go wrong (job loss, visa denial, market downturn)
- Specific adjustments for each risk scenario
- India fallback plan projection if mentioned

IMPORTANT RULES:
- ALWAYS use the user's stated income/savings — NEVER assume from scratch
- Show monthly AND annual breakdowns relative to their stated income
- Use current 2025 contribution limits (401K: $23,500, IRA: $7,000, HSA: $4,150/$8,300)
- College costs: use $50K-$100K+ per year depending on public vs private
- Home down payment: default 20% unless user specifies
- Retirement: use 4% safe withdrawal rule
- Investment returns: assume 7% for moderate, 5% conservative, 10% aggressive
- Always caveat: "⚠️ This is educational guidance, not professional financial advice."

Domains you cover:

1. RETIREMENT PLANNING:
   - 401(K): contribution limits ($23,500 for 2025, $30,500 if 50+), employer match
   - Roth IRA: income limits, backdoor Roth strategy, $7,000/$8,000 limits
   - HSA: triple tax advantage, $4,150/$8,300 limits
   - Social Security: benefit estimation, claiming strategies

2. EDUCATION SAVINGS:
   - 529 Plans: tax-free growth, state tax deductions, $18,000/year gift limit
   - Coverdell ESA: $2,000/year limit, more flexible spending
   - Per-child planning: age-based allocation, public vs private school costs
   - Activity costs: AOPS/RSM math ($200-400/mo), music, sports

3. TAX OPTIMIZATION:
   - Federal bracket optimization, standard vs itemized deductions
   - Capital gains: short-term vs long-term, tax-loss harvesting

4. VISA & IMMIGRATION PLANNING (H1B, L1, etc.):
   - Risk factors, job loss contingency, Grace Period (60 days H1B)
   - NRE/NRO accounts, FBAR reporting, FATCA compliance
   - India relocation: cost of living comparison, rupee conversion planning
   - Dual-country retirement planning

5. GOAL-BASED PLANNING:
   - Home purchase: down payment (20%), closing costs, DTI ratio
   - Emergency fund: 3-6 months (12-18 for visa holders)
   - Spouse/partner income integration"""
    
    async def process(self, state: FinnieState) -> dict[str, Any]:
        """
        Process a financial planning query.
        
        Uses LLM to generate comprehensive, structured planning advice.
        Also extracts structured goal data for the Plan Builder tab.
        """
        user_input = state.get("enhanced_input", state.get("user_input", ""))
        portfolio = state.get("portfolio_data", {})
        
        # Extract structured goals and financial context from the user's text
        parsed_goals = self._extract_goals(user_input)
        financial_context = self._extract_financial_context(user_input)
        
        # Build context-rich prompt
        context_parts = [f"User query: {user_input}"]
        
        if financial_context:
            context_parts.append(
                f"User's financial situation extracted from their query: {json.dumps(financial_context, default=str)}. "
                "USE THESE EXACT NUMBERS in your plan — do NOT make assumptions."
            )
        
        if portfolio:
            context_parts.append(f"Portfolio context: {json.dumps(portfolio, default=str)}")
        
        if parsed_goals:
            # Build an explicit goal summary so the LLM doesn't re-interpret raw text
            goal_lines = []
            for g in parsed_goals:
                goal_lines.append(
                    f"  - {g['name']}: target=${g['target']:,.0f}, "
                    f"timeline={g.get('timeline_years', '?')} years, "
                    f"current_savings=${g.get('current_savings', 0):,.0f}"
                )
            goals_summary = "\n".join(goal_lines)
            context_parts.append(
                f"PARSED GOALS (use THESE exact amounts — do NOT re-interpret from the raw text):\n"
                f"{goals_summary}\n"
                f"IMPORTANT: The amounts above were carefully extracted using proximity matching. "
                f"For example, if the user said '$2M home' and '$2.5M retirement', "
                f"the home target is $2,000,000 and retirement is $2,500,000. "
                f"DO NOT swap or re-assign these amounts."
            )
        
        context = "\n".join(context_parts)
        
        try:
            response = await self._call_llm(
                state=state,
                messages=[
                    {"role": "user", "content": context}
                ],
            )
            
            return {
                "content": response,
                "data": {
                    "planning_type": self._detect_planning_type(user_input),
                    "query": user_input,
                    "goals": parsed_goals,
                    "financial_context": financial_context,
                },
            }
        except Exception as e:
            return {
                "content": self._get_fallback_response(user_input, parsed_goals),
                "data": {
                    "planning_type": self._detect_planning_type(user_input),
                    "query": user_input,
                    "goals": parsed_goals,
                    "error": str(e),
                },
            }
    
    def _extract_goals(self, text: str) -> list[dict]:
        """
        Extract structured financial goals from free-form text.
        
        Parses mentions of retirement, college, home purchase, etc.
        and extracts dollar amounts, timelines, and other parameters.
        Uses proximity-based matching to associate amounts with the right goals.
        """
        text_lower = text.lower()
        goals = []
        
        # Extract all dollar amounts WITH their positions in the text
        amounts_with_pos = []
        
        # Millions: "2.5 million", "2.5M", "2.5 mil"
        for m in re.finditer(r'\$?(\d[\d,]*(?:\.\d+)?)\s*(?:million|mil|m)\b', text_lower):
            val = float(m.group(1).replace(',', '')) * 1_000_000
            amounts_with_pos.append((val, m.start()))
        
        # Thousands: "150K", "150 thousand"
        for m in re.finditer(r'\$?(\d[\d,]*(?:\.\d+)?)\s*(?:thousand|k)\b', text_lower):
            val = float(m.group(1).replace(',', '')) * 1_000
            amounts_with_pos.append((val, m.start()))
        
        # Plain dollar amounts: "$100,000"
        for m in re.finditer(r'\$(\d[\d,]*(?:\.\d+)?)\b', text_lower):
            val = float(m.group(1).replace(',', ''))
            if val >= 1000:
                amounts_with_pos.append((val, m.start()))
        
        def _find_amount_near(keywords: list[str], min_val: float = 0, max_val: float = float('inf')) -> float | None:
            """Find the dollar amount closest to any of the given keywords in the text."""
            # Find positions of all keyword occurrences
            keyword_positions = []
            for kw in keywords:
                for m in re.finditer(re.escape(kw), text_lower):
                    keyword_positions.append(m.start())
            
            if not keyword_positions:
                return None
            
            # Find the amount closest to any keyword position, within value range
            best_amount = None
            best_distance = float('inf')
            for val, pos in amounts_with_pos:
                if min_val <= val <= max_val:
                    dist = min(abs(pos - kp) for kp in keyword_positions)
                    if dist < best_distance:
                        best_distance = dist
                        best_amount = val
            
            return best_amount
        
        # --- Retirement Goal ---
        if any(w in text_lower for w in ["retire", "retirement"]):
            target = _find_amount_near(
                ["retirement", "retire"], min_val=500_000
            ) or 2_500_000
            
            # Try to extract age/timeline
            timeline = 25  # default years to retirement
            age_match = re.search(r'(?:age|by)\s*(\d{2})', text_lower)
            current_age_match = re.search(r'(?:i am|i\'m|currently)\s*(\d{2})', text_lower)
            
            if age_match:
                target_age = int(age_match.group(1))
                current_age = int(current_age_match.group(1)) if current_age_match else 35
                timeline = max(1, target_age - current_age)
            
            goals.append({
                "name": "Retirement",
                "icon": "🏦",
                "target": target,
                "timeline_years": timeline,
                "current_savings": 0,
                "annual_return": 0.07,
                "vehicle": "401(k) + IRA + Brokerage",
                "priority": 3,
                "category": "retirement",
            })
        
        # --- College / Education Goals ---
        if any(w in text_lower for w in ["college", "education", "529", "tuition", "university"]):
            # Detect number of children
            num_children = 1
            child_match = re.search(r'(\d+)\s*(?:sons?|daughters?|kids?|children)', text_lower)
            if child_match:
                num_children = int(child_match.group(1))
            elif "two" in text_lower:
                num_children = 2
            elif "three" in text_lower:
                num_children = 3
            
            # Detect ages
            ages = re.findall(r'(?:age[s]?\s*(?:of\s*)?|aged?\s*)(\d{1,2})', text_lower)
            # Also try patterns like "11 and 4"
            if not ages:
                ages = re.findall(r'\b(\d{1,2})\s*(?:and|&)\s*(\d{1,2})\b', text_lower)
                if ages:
                    ages = list(ages[0])
            
            # Parse per-year college cost
            annual_college_cost = 100_000  # default
            cost_match = re.search(r'(\d+)\s*k?\s*(?:per year|per annum|/year|a year|annually)\s*(?:for college|for each|each)', text_lower)
            if cost_match:
                cost_val = int(cost_match.group(1))
                annual_college_cost = cost_val * 1000 if cost_val < 1000 else cost_val
            elif re.search(r'(?:atleast|at least)\s*(?:\$)?(\d+)k?\s*(?:per year)', text_lower):
                match = re.search(r'(?:atleast|at least)\s*(?:\$)?(\d+)k?\s*(?:per year)', text_lower)
                cost_val = int(match.group(1))
                annual_college_cost = cost_val * 1000 if cost_val < 1000 else cost_val
            
            total_college_cost = annual_college_cost * 4  # 4 years of college
            
            for i in range(num_children):
                child_age = int(ages[i]) if i < len(ages) else (5 if i == 0 else 3)
                years_to_college = max(1, 18 - child_age)
                
                goals.append({
                    "name": f"College Fund — Child {i+1} (Age {child_age})",
                    "icon": "🎓",
                    "target": total_college_cost,
                    "timeline_years": years_to_college,
                    "current_savings": 0,
                    "annual_return": 0.07,
                    "vehicle": "529 Plan",
                    "priority": 2,
                    "category": "education",
                    "child_age": child_age,
                    "annual_cost": annual_college_cost,
                })
        
        # --- Home Purchase Goal ---
        if any(w in text_lower for w in ["home", "house", "down payment", "mortgage"]):
            home_price = _find_amount_near(
                ["home", "house", "down payment", "mortgage"],
                min_val=100_000, max_val=10_000_000
            ) or 2_000_000
            
            # Down payment percentage
            down_pct = 0.20  # default 20%
            pct_match = re.search(r'(\d+)\s*%\s*(?:down|dp)', text_lower)
            if pct_match:
                down_pct = int(pct_match.group(1)) / 100
            
            down_payment = home_price * down_pct
            
            # Timeline
            home_timeline = 3  # default
            year_match = re.search(r'(?:next|in|within)\s*(\d+)\s*year', text_lower)
            if year_match:
                home_timeline = int(year_match.group(1))
            
            goals.append({
                "name": "Home Down Payment",
                "icon": "🏠",
                "target": down_payment,
                "timeline_years": home_timeline,
                "current_savings": 0,
                "annual_return": 0.04,  # low risk for short timeline
                "vehicle": "High-Yield Savings / CDs / Treasury",
                "priority": 1,
                "category": "home",
                "home_price": home_price,
                "down_pct": down_pct,
            })
        
        # --- Emergency Fund ---
        if "emergency" in text_lower:
            goals.append({
                "name": "Emergency Fund",
                "icon": "🛡️",
                "target": 50_000,
                "timeline_years": 1,
                "current_savings": 0,
                "annual_return": 0.045,
                "vehicle": "High-Yield Savings Account",
                "priority": 0,
                "category": "emergency",
            })
        
        # Sort by priority
        goals.sort(key=lambda g: g["priority"])
        
        return goals
    
    def _extract_financial_context(self, text: str) -> dict:
        """
        Extract the user's current financial situation from free-form text.
        
        Parses income, savings, retirement accounts, visa status, etc.
        """
        text_lower = text.lower()
        context = {}
        
        # --- Monthly income ---
        income_match = re.search(
            r'(?:income|earn|salary|make|get)\s+(?:of\s+)?'
            r'(?:is\s+)?(?:\$)?(\d[\d,]*(?:\.\d+)?)\s*k?\s*'
            r'(?:per month|/month|monthly|a month|post.?tax|after.?tax)?',
            text_lower
        )
        if income_match:
            val = float(income_match.group(1).replace(',', ''))
            context["monthly_income"] = val * 1000 if val < 100 else val
        
        # Also try "12K per month" or "$12K post tax per month"
        if "monthly_income" not in context:
            income_match2 = re.search(r'(\d[\d,]*(?:\.\d+)?)\s*k\s*(?:post.?tax|after.?tax|per month|/month|a month)', text_lower)
            if income_match2:
                context["monthly_income"] = float(income_match2.group(1).replace(',', '')) * 1000
        
        # --- Current savings ---
        savings_match = re.search(
            r'(\d[\d,]*(?:\.\d+)?)\s*k?\s*(?:in\s+)?(?:savings?|saved|cash|bank)',
            text_lower
        )
        if savings_match:
            val = float(savings_match.group(1).replace(',', ''))
            context["current_savings"] = val * 1000 if val < 1000 else val
        
        # --- 401K / retirement accounts ---
        retirement_match = re.search(
            r'(\d[\d,]*(?:\.\d+)?)\s*k?\s*(?:in\s+)?(?:401\s*k|401\(k\)|retirement|ira|brokerage)',
            text_lower
        )
        if retirement_match:
            val = float(retirement_match.group(1).replace(',', ''))
            context["retirement_accounts"] = val * 1000 if val < 1000 else val
        
        # --- Visa status ---
        visa_patterns = {
            "H1B": r'h[-\s]?1\s*b',
            "L1": r'l[-\s]?1',
            "H4 EAD": r'h[-\s]?4',
            "Green Card": r'green\s*card',
            "OPT": r'\bopt\b',
            "F1": r'f[-\s]?1',
        }
        for visa, pattern in visa_patterns.items():
            if re.search(pattern, text_lower):
                context["visa_status"] = visa
                context["visa_holder"] = True
                break
        
        # --- Spouse/partner mention ---
        if any(w in text_lower for w in ["spouse", "wife", "husband", "partner", "married"]):
            context["has_spouse"] = True
            spouse_income = re.search(
                r'(?:spouse|wife|husband|partner)\s+(?:makes?|earns?|income)\s+(?:\$)?(\d[\d,]*(?:\.\d+)?)\s*k?',
                text_lower
            )
            if spouse_income:
                val = float(spouse_income.group(1).replace(',', ''))
                context["spouse_income"] = val * 1000 if val < 100 else val
        
        # --- Side income ---
        if any(w in text_lower for w in ["side income", "rental", "freelance", "side hustle", "passive income"]):
            context["has_side_income"] = True
        
        # --- India relocation ---
        if any(w in text_lower for w in ["india", "go back", "relocation", "relocate"]):
            context["india_relocation"] = True
        
        return context

    def _detect_planning_type(self, text: str) -> str:
        """Detect which planning domain the query falls into."""
        text_lower = text.lower()
        
        # Multi-goal detection
        categories = []
        if any(w in text_lower for w in ["retire", "401k", "401(k)", "roth", "ira", "pension"]):
            categories.append("retirement")
        if any(w in text_lower for w in ["529", "college", "education", "tuition"]):
            categories.append("education")
        if any(w in text_lower for w in ["home", "house", "down payment", "mortgage"]):
            categories.append("home")
        if any(w in text_lower for w in ["tax", "deduction", "1099", "bracket"]):
            categories.append("tax")
        if any(w in text_lower for w in ["visa", "h1b", "immigration"]):
            categories.append("visa")
        if any(w in text_lower for w in ["budget", "expense"]):
            categories.append("expense")
        if any(w in text_lower for w in ["emergency"]):
            categories.append("emergency")
        
        if len(categories) >= 2:
            return "multi_goal"
        elif categories:
            return categories[0]
        else:
            return "general"
    
    def _get_fallback_response(self, user_input: str, goals: list[dict] | None = None) -> str:
        """Return a helpful fallback when LLM is unavailable, using parsed goals."""
        if goals:
            lines = ["## 🎯 Your Financial Plan\n"]
            lines.append("I've identified the following goals from your query:\n")
            
            total_monthly = 0
            for goal in goals:
                target = goal["target"]
                years = goal["timeline_years"]
                monthly_rate = goal["annual_return"] / 12
                months = years * 12
                
                if monthly_rate > 0:
                    monthly_needed = target * monthly_rate / (((1 + monthly_rate) ** months) - 1)
                else:
                    monthly_needed = target / max(months, 1)
                
                total_monthly += monthly_needed
                
                lines.append(f"### {goal['icon']} {goal['name']}")
                lines.append(f"- **Target:** ${target:,.0f}")
                lines.append(f"- **Timeline:** {years} years")
                lines.append(f"- **Monthly Savings Needed:** ${monthly_needed:,.0f}/mo")
                lines.append(f"- **Recommended Vehicle:** {goal['vehicle']}")
                lines.append("")
            
            lines.append("### 📊 Combined Monthly Budget")
            lines.append("| Goal | Monthly | Priority |")
            lines.append("|------|---------|----------|")
            for goal in goals:
                target = goal["target"]
                years = goal["timeline_years"]
                monthly_rate = goal["annual_return"] / 12
                months = years * 12
                if monthly_rate > 0:
                    monthly = target * monthly_rate / (((1 + monthly_rate) ** months) - 1)
                else:
                    monthly = target / max(months, 1)
                prio = ["🔴 Critical", "🟠 High", "🟡 Medium", "🟢 Normal"][min(goal["priority"], 3)]
                lines.append(f"| {goal['icon']} {goal['name']} | ${monthly:,.0f} | {prio} |")
            lines.append(f"| **Total** | **${total_monthly:,.0f}** | |")
            lines.append("")
            lines.append("⚠️ *This is educational guidance, not professional financial advice.*")
            
            return "\n".join(lines)
        
        planning_type = self._detect_planning_type(user_input)
        
        responses = {
            "retirement": """**📋 Retirement Planning Overview**

**Key accounts to maximize:**
| Account | 2025 Limit | Tax Benefit |
|---------|-----------|-------------|
| 401(K) | $23,500 | Pre-tax / Roth |
| Roth IRA | $7,000 | Tax-free growth |
| HSA | $4,150 (ind) | Triple tax advantage |

**Priority order:** Employer match → HSA → Roth IRA → Max 401K

⚠️ *This is educational guidance, not professional financial advice.*""",
            
            "education": """**📋 Education Savings Options**

| Plan | Annual Limit | Tax Benefit |
|------|-------------|-------------|
| 529 Plan | $18,000/yr (gift) | Tax-free growth for education |
| Coverdell ESA | $2,000/yr | More flexible spending |

**Tip:** Start early — a $200/month 529 contribution at birth grows to ~$80K by age 18.

⚠️ *This is educational guidance, not professional financial advice.*""",
            
            "visa": """**📋 Financial Planning on a Work Visa**

**Key considerations:**
- **Emergency fund:** 6-12 months (higher than usual due to visa risk)
- **US investments:** Brokerage accounts are allowed on H1B
- **Home country:** NRE/NRO accounts for India, FBAR reporting if >$10K abroad
- **Side income:** Must have employer authorization on H1B

⚠️ *This is educational guidance, not professional financial advice.*""",
        }
        
        return responses.get(planning_type, """**📋 Financial Life Planner**

I can help you with:
- 🏦 **Retirement:** 401K, Roth IRA, HSA strategies
- 🎓 **Education:** 529 plans, saving for kids' college
- 💰 **Tax optimization:** Bracket management, deductions
- 🌍 **Visa planning:** H1B considerations, cross-border investing
- 📊 **Budgeting:** Expense tracking, goal-based saving
- 💼 **Side hustles:** Freelancing, consulting, passive income

Ask me about any of these topics!

⚠️ *This is educational guidance, not professional financial advice.*""")
