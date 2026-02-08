# Finnie AI — Test & Demo Guide

> **Last Updated:** February 7, 2026  
> **App Version:** Phase 1.1  
> This guide is updated as new features are added.

---

## Quick Start

```bash
cd /Users/sathya/web/python/finnie-ai
source venv/bin/activate
pip install -e .               # Only needed once (or after pulling new code)
streamlit run src/ui/app.py    # Opens at http://localhost:8501
```

---

## Feature Status

| Feature | Status | API Key Needed? |
|---------|--------|-----------------|
| 💬 Chat — Stock Prices | ✅ Working | No |
| 💬 Chat — Education (fallback) | ✅ Working | No |
| 💬 Chat — Education (LLM) | ✅ Working | **Yes** |
| 💬 Chat — Trends | ✅ Working | No |
| 📊 Portfolio — Live Pricing & Gain/Loss | ✅ Working | No |
| 📊 Portfolio — Allocation Chart | ✅ Working | No |
| 📈 Market — Stock Lookup (incl. BRK-B) | ✅ Working | No |
| 📈 Market — 6-Month Chart | ✅ Working | No |
| 🔮 Projections — Monte Carlo | ✅ Working | No |
| ⚙️ Settings — Provider Config | ✅ Working | No |
| 🧪 Pytest Suite (33 tests) | ✅ Passing | No |
| 🗣️ Voice Interface | ⬜ Phase 2 | — |
| 🔗 FastAPI Backend | ⬜ Phase 2 | — |
| 🗄️ Database Persistence | ⬜ Phase 2 | — |

---

## Test Script (No API Key Required)

Follow these steps in order for a complete demo.

### 1. Chat Tab — Stock Price Query

**Steps:**
1. Open the app → You'll see the **Welcome Card** with feature grid
2. In the chat input, type: `What's AAPL trading at?`
3. Press Enter

**Expected:**
- Shows current Apple stock price, change %, market cap
- Includes formatted table with key metrics
- Ends with ⚠️ educational disclaimer

**Also try:**
- `Tell me about MSFT` — Microsoft data
- `$TSLA` — Dollar-sign ticker format

### 2. Chat Tab — Financial Education

**Steps:**
1. Type: `What is P/E ratio?`
2. Press Enter

**Expected:**
- Returns a clear definition of P/E ratio
- Works without API key (uses fallback definitions)

**Also try:**
- `What is market cap?`
- `Explain dividends`
- `How does compound interest work?`

### 3. Chat Tab — Greetings

**Steps:**
1. Type: `Hello` or `Help`
2. Press Enter

**Expected:**
- Shows the feature table with all available commands
- Lists example queries for each capability

### 4. Market Tab — Stock Lookup

**Steps:**
1. Click the **📈 Market** tab
2. Type `NVDA` in the ticker input, press Enter

**Expected:**
- Shows "NVIDIA Corporation (NVDA)"
- 4 metric cards: Price, Market Cap, P/E Ratio, 52W High
- Interactive 6-month price chart (purple line with gradient fill)

**Also try:**
- `AAPL`, `AMZN`, `META` — major tech stocks
- `BRK-B` or `brk.b` or `BRK.B` — all normalized to BRK-B ✅
- `FAKE123` — Should show "No data found" warning

### 5. Portfolio Tab — Add Holdings with Live Pricing

**How it works:**
Enter your **current position** as it appears in your brokerage (e.g., Fidelity). Enter today's share count and your average cost basis per share. Finnie fetches live prices to calculate gain/loss.

> If you bought 100 shares of AAPL in 2017 and they split 4:1, your brokerage now shows 400 shares. Enter `400` as shares and your split-adjusted cost basis.

**Steps:**
1. Click the **📊 Portfolio** tab
2. Enter:
   - Ticker: `AAPL`
   - Current Shares: `100`
   - Avg Cost / Share: `35` (split-adjusted cost from Fidelity)
3. Click **Add Position**
4. Add more positions:
   - `GOOGL` / `20` / `105`
   - `BRK-B` / `5` / `320`

**Expected:**
- "Fetching live prices..." spinner appears
- **Summary row** shows: Total Value, Total Cost, Total Gain/Loss (with %), Positions
- **Per-position rows** show: ticker, name, shares, current price vs cost, current value vs cost, gain/loss with %
- 🟢 green for gains, 🔴 red for losses
- **Allocation donut chart** with actual portfolio weights
- **🗑️ Clear All Holdings** button at bottom

### 6. Projections Tab — Monte Carlo

**Steps:**
1. Click the **🔮 Projections** tab
2. You'll see the "How it works" explanation card
3. Set inputs:
   - Initial Investment: `$10,000`
   - Monthly Contribution: `$500`
   - Time Horizon: `10 years`
4. Click **🔮 Calculate Projection**

**Expected:**
- Three outcome cards: Conservative, Expected, Optimistic
- Conservative < Expected < Optimistic
- Total contributions: $70,000
- Growth percentages and Monte Carlo disclaimer

**Try different scenarios:**
- `$50,000` / `$1,000`/mo / `20 years` — Long-term wealth building
- `$1,000` / `$100`/mo / `5 years` — Starter investor

### 7. Settings Tab

**Steps:**
1. Click the **⚙️ Settings** tab
2. Switch between OpenAI / Anthropic / Google providers
3. See models update based on provider
4. Check Feature Status section at bottom

**Expected:**
- Models change per provider
- Warning: "No API key — market data & projections still work"
- Feature checklist shows what's active vs upcoming

### 8. Chat — Trends

**Steps:**
1. Go back to **💬 Chat** tab
2. Type: `What's trending today?`

**Expected:**
- Shows market movers / trending stocks from yfinance

---

## Test Script (With API Key)

### Setup

1. Go to **⚙️ Settings**
2. Select your provider (e.g., `openai`)
3. Paste your API key
4. Click **Save Settings**
5. Verify: "✅ Connected"

### LLM-Powered Education

1. Type: `Explain dollar-cost averaging in simple terms`
2. Should return a rich, detailed LLM-generated explanation (much more nuanced than fallback)

**More to try:**
- `What is the difference between stocks and bonds?`
- `Explain what a hedge fund does`

---

## Running Automated Tests

```bash
pytest tests/ -v                              # All tests
pytest tests/test_agents.py -v                # Agent tests only
pytest tests/ --cov=src --cov-report=term     # With coverage
```

**Expected:** 33 passed, 1 skipped

---

## Demo Script (5-Minute Walkthrough)

| Step | Action | Talking Point |
|------|--------|---------------|
| 1 | Open app, show welcome card | "Multi-agent financial AI with 8 specialized agents" |
| 2 | Ask `What's AAPL trading at?` | "Real-time yFinance data, no API key needed" |
| 3 | Ask `What is P/E ratio?` | "Financial education with LLM + fallback" |
| 4 | Market tab → look up `NVDA` | "Interactive Plotly charts, 6-month history" |
| 5 | Market tab → look up `BRK-B` | "Handles special tickers (hyphens/dots)" |
| 6 | Portfolio → add AAPL, GOOGL, BRK-B | "Live pricing, gain/loss, allocation chart" |
| 7 | Projections → $10k / $500/mo / 10yr | "Monte Carlo — 1,000 simulations" |
| 8 | Settings tab | "Multi-provider LLM (OpenAI/Anthropic/Google)" |
| 9 | Mention architecture | "LangGraph orchestration, 33 tests passing" |

---

## Known Limitations (Phase 1)

- Chat/portfolio data **resets on page refresh** (session-only, no DB yet)
- Market data may be **delayed 15–20 min** (yFinance limitation)
- Portfolio shows current gain/loss but **not historical growth over time** (Phase 2)
- Ticker extraction may occasionally misidentify words (improved but not perfect)

---

## Changelog

| Date | Changes |
|------|---------|
| Feb 7, 2026 | Portfolio: live pricing, gain/loss, allocation chart |
| Feb 7, 2026 | Market: BRK-B / BRK.B ticker normalization |
| Feb 7, 2026 | Chat: fixed routing — education before ticker extraction |
| Feb 7, 2026 | UI redesign — purple theme, native chat, price charts |
| Feb 5, 2026 | Phase 1 complete — all 8 agents, LangGraph, Streamlit UI |
