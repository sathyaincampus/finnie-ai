# Finnie AI — Test & Demo Guide

> **Last Updated:** February 22, 2026  
> **App Version:** Phase 3.0  
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
| 🔮 Projections — Forward Monte Carlo | ✅ Working | No |
| 🔮 Projections — Goal-Based (Reverse) | ✅ Working | No |
| 📋 Planner — Retirement/529/Tax/Visa | ✅ Working | No |
| 🪙 Crypto — Live Prices (CoinGecko) | ✅ Working | No |
| 🪙 Crypto — Allocation Guide & Tax | ✅ Working | No |
| ⚙️ Settings — Provider Config | ✅ Working | No |
| 🔐 Auth — OAuth (Google) + Guest | ✅ Working | OAuth setup |
| 🗄️ Chat Memory — SQLite Persistence | ✅ Working | No |
| 🔧 MCP Tool Servers (7 tools) | ✅ Working | No |
| 🔗 FastAPI API (13 endpoints) | ✅ Working | No |
| 🗣️ Voice Interface (TTS + STT) | ✅ Working | No |
| 📊 Arize Phoenix Observability | ✅ Working | No (auto-launches) |
| ✨ Prompt Enhancer Agent | ✅ Working | **Yes** |
| 🐳 Docker + Cloud Run | ✅ Ready | GCP project |
| 🧪 Pytest Suite (47+ tests) | ✅ Passing | No |
| 🧪 Phoenix Evaluations | ✅ Ready | `pip install arize-phoenix` |

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

### 9. Planner Tab — Financial Life Planning

**Steps:**
1. Click the **📋 Planner** tab
2. Explore sections: Retirement, Education Savings, Tax Optimization

**Expected:**
- **Retirement:** Calculator with 401(k)/IRA contribution limits
- **Education:** 529 plan calculator with growth projection
- **Tax:** Optimization strategies with bracket details
- **Visa/Immigration:** H1B financial planning considerations
- **Budget:** Interactive expense tracker categories
- **Side Hustles:** Income ideas with earnings estimates
- **Goals:** Savings goal calculator with timeline

### 10. Crypto Tab — Cryptocurrency Dashboard

**Steps:**
1. Click the **🪙 Crypto** tab

**Expected:**
- **Live Prices:** Top 5 crypto (BTC, ETH, BNB, SOL, ADA) with 24h change and market cap
- **Allocation Guide:** Conservative/Moderate/Aggressive allocations
- **Tax Guide:** Short-term vs long-term capital gains, taxable events

### 11. Projections Tab — Goal-Based (New)

**Steps:**
1. Click the **🔮 Projections** tab
2. Select **🎯 Goal-Based** mode
3. Set inputs:
   - Target Amount: `$1,000,000`
   - Current Savings: `$50,000`
   - Years to Goal: `20`
4. Click **Calculate Required Investment**

**Expected:**
- Shows required monthly investment for Conservative, Moderate, and Aggressive strategies
- Moderate required amount should be less than Conservative

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

## 9. MCP Tool Servers

**What it is:** Model Context Protocol — standardized tool discovery and execution for agents.

**Steps:**
1. In a terminal, test MCP directly:
   ```bash
   python -c "
   from src.mcp.server import get_mcp_server, call_tool
   server = get_mcp_server()
   print(f'{server.tool_count} tools registered')
   
   # Call a tool
   result = call_tool('get_stock_price', ticker='AAPL')
   print(result)
   "
   ```

**Expected:**
- `7 tools registered`
- Returns dict with price, change, market cap, PE ratio

**Available Tools:**
| Tool | Description |
|------|-------------|
| `get_stock_price` | Current price + metrics |
| `get_historical_data` | OHLCV price history |
| `get_company_info` | Sector, industry, financials |
| `get_sector_performance` | Sector ETF performance |
| `create_price_chart` | Line or candlestick chart |
| `create_comparison_chart` | Multi-ticker normalized chart |
| `create_sector_heatmap` | Sector performance bar chart |

### 10. FastAPI API

**Steps:**
1. Start the API server:
   ```bash
   uvicorn src.api.main:app --port 8000 --reload
   ```
2. Open the auto-generated docs: http://localhost:8000/api/docs
3. Test endpoints:
   ```bash
   # Health check
   curl http://localhost:8000/api/health
   
   # Market data
   curl http://localhost:8000/api/market/AAPL
   
   # List MCP tools
   curl http://localhost:8000/api/tools
   
   # Sector performance
   curl http://localhost:8000/api/sectors?period=1mo
   
   # Call MCP tool via API
   curl -X POST http://localhost:8000/api/tools/call \
     -H 'Content-Type: application/json' \
     -d '{"tool_name": "get_stock_price", "arguments": {"ticker": "NVDA"}}'
   ```

**Expected:**
- `/api/health` returns `{"status": "healthy", "mcp_tools": 7}`
- `/api/market/AAPL` returns live price data
- `/api/docs` shows interactive Swagger UI with all 13 endpoints

### 11. Voice Interface

**What it is:** Text-to-Speech (edge-tts) + browser Speech-to-Text (Web Speech API).

**Steps (TTS — works anywhere):**
1. In the Chat tab, toggle **🎤 Voice Mode** on
2. Select a voice (6 options: US/UK/AU, male/female)
3. Enable **Auto-speak**
4. Ask a question — the response will be read aloud

**Steps (STT — Chrome/Edge only):**
1. With Voice Mode on, click the **🎤 microphone button**
2. Speak your query (e.g., "What is Apple trading at?")
3. Transcribed text appears and is sent to chat

**Note:** STT requires Chrome or Edge browser (uses `webkitSpeechRecognition`).

### 12. Arize Phoenix Observability

**Setup:**
Phoenix launches automatically when the app starts (no external account needed).

1. Phoenix dashboard available at `http://localhost:6006`
2. All LLM calls and agent traces are automatically captured

**Without Phoenix installed:** Falls back to local logging — no errors.

**Test locally:**
```bash
python -c "
from src.observability import get_observer
observer = get_observer()
trace = observer.create_trace('test-session', input_text='hello')
with observer.span(trace, 'test_span'):
    pass
observer.end_trace(trace, output='world')
print(f'Latency: {trace.total_latency_ms}ms, Spans: {len(trace.spans)}')
"
```

### 13. Docker + Cloud Run Deployment

**Local Docker test:**
```bash
# Build
docker build -t finnie-ai .

# Run locally
docker run -p 8080:8080 finnie-ai

# Open http://localhost:8080
```

**Deploy to Google Cloud Run:**
```bash
# Set your GCP project
gcloud config set project YOUR_PROJECT_ID

# Build and deploy
gcloud builds submit --config cloudbuild.yaml .
```

---

## Running Automated Tests

```bash
# All tests (MCP, agents, observability)
pytest tests/ -v

# Specific test suites
pytest tests/test_agents.py -v                          # Agent unit tests
pytest tests/eval/test_phoenix_eval.py -v               # Phoenix evaluations
pytest tests/ --cov=src --cov-report=term                # With coverage

# Phoenix evaluation tests (requires arize-phoenix + LLM API key)
pytest tests/eval/test_phoenix_eval.py -v -k "relevancy or hallucination or faithfulness"
```

**Expected:** 113+ passed, some skipped (eval tests skip without LLM API key)

---

## Demo Script (7-Minute Walkthrough)

| Step | Action | Talking Point |
|------|--------|---------------|
| 1 | Open app, show welcome card | "Multi-agent financial AI with 11 specialized agents" |
| 2 | Ask `What's AAPL trading at?` | "Real-time yFinance data, no API key needed" |
| 3 | Ask `What is P/E ratio?` | "Financial education with LLM + fallback" |
| 4 | Market tab → look up `NVDA` | "Interactive Plotly charts, 6-month history" |
| 5 | Market tab → look up `BRK-B` | "Handles special tickers (hyphens/dots)" |
| 6 | Portfolio → add AAPL, GOOGL, BRK-B | "Live pricing, gain/loss, allocation chart" |
| 7 | Projections → forward + goal-based | "Monte Carlo — forward and reverse projections" |
| 8 | Planner tab → retirement, 529 | "Financial life planning: retirement, education, visa, tax" |
| 9 | Crypto tab → live prices | "CoinGecko API, allocation guides, crypto tax info" |
| 10 | Toggle Voice Mode on, ask a question | "Edge-TTS voice output, browser STT input" |
| 11 | Open `/api/docs` in new tab | "FastAPI with 13 endpoints, auto Swagger docs" |
| 12 | Settings tab → show Phoenix | "Arize Phoenix observability at localhost:6006" |
| 13 | Help tab → Knowledge Explorer | "105 concepts from our Knowledge Graph, searchable, filterable, click Ask Finnie" |
| 14 | Mention architecture | "LangGraph, MCP, 11 agents, GraphRAG, Phoenix, Docker, 113+ tests" |

---

## Known Limitations

- Market data may be **delayed 15–20 min** (yFinance limitation)
- Portfolio shows current gain/loss but **not historical growth over time** (future)
- Ticker extraction may occasionally misidentify words (improved but not perfect)
- Voice STT requires **Chrome or Edge** (Web Speech API limitation)
- CoinGecko API has rate limits on free tier (∼10-50 calls/min)
- Phoenix evaluations require `arize-phoenix` package

---

## Changelog

| Date | Changes |
|------|---------|
| Feb 11, 2026 | **Phase 2.5:** 3 new agents (Enhancer, Planner, Crypto) — 11 total |
| Feb 11, 2026 | Arize Phoenix replaces LangFuse for observability |
| Feb 11, 2026 | Phoenix evaluations replace DeepEval |
| Feb 11, 2026 | Goal-based projections (reverse Monte Carlo) |
| Feb 11, 2026 | Modular UI tabs (`src/ui/tabs/`) — 7 tabs total |
| Feb 11, 2026 | CoinGecko integration for live crypto prices |
| Feb 8, 2026 | **Phase 2.0:** MCP tool servers (7 tools), FastAPI API (13 routes) |
| Feb 8, 2026 | Voice interface (edge-tts TTS + browser STT) |
| Feb 8, 2026 | LangFuse observability (traces, spans, metrics) |
| Feb 8, 2026 | Docker + Cloud Run deployment config |
| Feb 8, 2026 | DeepEval test suite (relevancy, hallucination, faithfulness) |
| Feb 22, 2026 | Knowledge Explorer: 105-concept browser with search, category/difficulty filters, Ask Finnie |
| Feb 22, 2026 | Performance: @st.fragment + @st.cache_data for Knowledge Explorer |
| Feb 22, 2026 | Auth: Fixed session persistence, removed GitHub (OIDC-only), improved logout |
| Feb 22, 2026 | GraphRAG: Cached is_graph_available in session_state, RAG badge on responses |
| Feb 22, 2026 | Routing: Fixed "dollar cost averaging" misroute to Quant agent |
| Feb 11, 2026 | Test count: 33 → 113 (added MCP + agent + eval + integration tests) |
| Feb 7, 2026 | Auth: OAuth (Google/GitHub) + guest mode, SQLite chat memory |
| Feb 7, 2026 | Portfolio: live pricing, gain/loss, allocation chart |
| Feb 7, 2026 | Market: BRK-B / BRK.B ticker normalization |
| Feb 7, 2026 | Chat: fixed routing — education before ticker extraction |
| Feb 7, 2026 | UI redesign — purple theme, native chat, price charts |
| Feb 5, 2026 | Phase 1 complete — all 8 agents, LangGraph, Streamlit UI |
