# Finnie AI — Autonomous Financial Intelligence System 🦈

> **"Hedge Fund in a Box"** — A multi-agent AI assistant that democratizes financial literacy through real-time market data, personalized planning, and intelligent conversation.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-ff4b4b.svg)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 What Can You Do With Finnie AI?

### 💬 Chat with AI Agents
Ask anything financial — Finnie routes your question to the best specialist:

| You Say | Finnie Does |
|---------|------------|
| *"What is a 401K?"* | 📚 Professor explains with examples |
| *"Show me AAPL stock"* | 📊 Quant fetches real-time price + chart |
| *"What's trending in the market?"* | 🌍 Scout shows top gainers/losers |
| *"If I invest $500/month for 20 years"* | 🔮 Oracle runs Monte Carlo simulation |
| *"Help me plan for retirement"* | 📋 Planner builds a full financial plan |
| *"How do companies enter the NASDAQ-100?"* | 🌍 Scout explains rebalancing strategies |

### 📋 Plan Builder
- Build personalized financial plans with **multiple goals** (retirement, college, home, emergency)
- **AI-powered**: Ask Finnie a complex question and the plan auto-populates
- Interactive controls: adjust targets, timelines, expected returns
- **Scenario comparison**: Conservative (5%) vs Moderate (7%) vs Aggressive (10%)
- Year-over-year projections with interactive Plotly charts
- Quarter-by-quarter savings breakdown

### 📊 Portfolio Analysis
- Track holdings with real-time prices via yfinance
- Allocation donut chart with sector breakdown
- Risk metrics: beta, Sharpe ratio, volatility
- Rebalancing suggestions

### 🏛️ Market Overview
- **Live market indices**: S&P 500, Dow Jones, NASDAQ, Russell 2000
- **Stock lookup**: Search any ticker for price, P/E, market cap, 52W range
- **Market movers**: Top 10 gainers and losers from 50 major stocks
- Timeframe tabs: Today / This Week / This Month

### 🪙 Crypto Dashboard
- **Search any cryptocurrency** by name or symbol (powered by CoinGecko)
- Quick-select buttons for popular coins
- Price history charts (7D / 30D / 90D / 1Y / Max)
- Allocation calculator and tax guidance

### 🔮 Investment Projections
- Monte Carlo simulations for investment growth
- Risk level slider (conservative → aggressive)
- Time horizon selection
- Percentile-based outcome bands

### 🎤 Voice Interface
- Hands-free interaction via Whisper STT + edge-tts
- Speak your financial questions naturally

---

## 🤖 Agent Roster (11 Specialists)

| Agent | Role | Example Triggers |
|-------|------|-----------------|
| 🔧 **Enhancer** | Query optimization | Automatically enhances all queries |
| 📊 **Quant** | Market data & technicals | Stock tickers, prices, charts |
| 📚 **Professor** | Financial education | "What is...", "Explain..." |
| 🔍 **Analyst** | News & sentiment | "News about...", research |
| 💼 **Advisor** | Portfolio management | Holdings, allocation, rebalancing |
| 🛡️ **Guardian** | Compliance & disclaimers | Appended to all responses |
| ✍️ **Scribe** | Response formatting | Formats all output |
| 🔮 **Oracle** | Investment projections | "If I invest...", Monte Carlo |
| 🌍 **Scout** | Trends & index rebalancing | "What's trending...", movers |
| 📋 **Planner** | Financial planning | Retirement, college, home, visa |
| 🪙 **Crypto** | Cryptocurrency data | Bitcoin, Ethereum, any token |

---

## 🏗️ Architecture Highlights

- **Multi-Agent Orchestration**: LangGraph state machine routes queries to the right specialist
- **LLM Gateway**: Smart 3-tier routing (Free → Cheap → Full) for cost optimization
- **Context Management**: Keeps original intent + summarizes middle + recent messages
- **MCP Tools**: Standardized tool integration (yfinance, CoinGecko, news, calculator)
- **Observability**: Arize Phoenix + OpenTelemetry tracing with 4 AI evaluators
- **Real-time Data**: Live stock prices, crypto data, market indices

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- API key for at least one LLM provider (Google Gemini, OpenAI, or Anthropic)

### Installation

```bash
git clone https://github.com/your-username/finnie-ai.git
cd finnie-ai

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env with your API keys
```

### Configuration

Edit `.env`:

```env
# LLM Providers (at least one required)
GOOGLE_API_KEY=...          # Gemini (recommended — free tier)
OPENAI_API_KEY=sk-...       # GPT-4o / GPT-4o-mini
ANTHROPIC_API_KEY=sk-ant-...

# Observability (optional)
PHOENIX_ENABLED=true

# Databases (optional, for full features)
NEON_DATABASE_URL=postgresql://...
AURA_URI=neo4j+s://...
REDIS_URL=redis://...
```

### Running

```bash
# Start the app
streamlit run src/ui/app.py

# Open http://localhost:8501
```

---

## 📁 Project Structure

```
finnie-ai/
├── src/
│   ├── agents/           # 11 specialized agents
│   ├── orchestration/    # LangGraph state machine
│   ├── llm/              # Multi-provider LLM adapters
│   ├── llm_gateway.py    # Smart routing + budget tracking
│   ├── mcp/              # MCP tool servers
│   ├── evals.py          # Phoenix evaluations (4 evaluators)
│   ├── data/             # Database clients
│   ├── api/              # FastAPI backend
│   └── ui/
│       ├── app.py        # Main Streamlit app
│       ├── auth.py       # Google OAuth authentication
│       └── tabs/         # Tab modules (market, crypto, plan_builder, help, etc.)
├── docs/
│   ├── ARCHITECTURE.md   # System architecture v3.0
│   ├── presentation.html # Slide deck
│   └── images/           # Diagrams and mockups
├── Requirements/         # Grading rubric
├── Dockerfile            # Production container
├── requirements.txt
└── README.md
```

---

## 🧪 Testing

```bash
pytest tests/ -v
pytest tests/ --cov=src --cov-report=html
```

---

## ☁️ Deployment

### Docker

```bash
docker build -t finnie-ai .
docker run -p 8080:8080 --env-file .env finnie-ai
```

### Google Cloud Run

```bash
# Build and deploy
gcloud run deploy finnie-ai \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_API_KEY=...,OPENAI_API_KEY=...,PHOENIX_ENABLED=false"
```

---

## 📊 Technology Stack

| Category | Technology |
|----------|-----------|
| Frontend | Streamlit, Plotly, Custom CSS |
| Backend | FastAPI, LangGraph, MCP |
| LLM Gateway | 3-tier smart routing (Gemini Flash / GPT-4o-mini / GPT-4o) |
| Agents | 11 specialists with inter-agent communication |
| Databases | NeonDB (Postgres), AuraDB (Neo4j), Redis Cloud |
| Voice | OpenAI Whisper, edge-tts |
| Observability | Arize Phoenix + OpenTelemetry |
| Evaluations | 4 AI evaluators (Relevance, QA Quality, Hallucination, Toxicity) — 113+ tests |
| Knowledge Explorer | 105 concepts searchable/filterable from Knowledge Graph |
| Deployment | Google Cloud Run, Docker |

---

## 📄 License

MIT License — see [LICENSE](./LICENSE) for details.

---

**Finnie AI** — *Your personal financial intelligence team* 🦈
