# Finnie AI — Capstone Submission Guide

> **Project:** Finnie AI — Autonomous Financial Intelligence System  
> **Author:** Sathya Narayanan Srinivasan  
> **Submission Date:** February 23, 2026

---

## Quick Links

| Item | Link / Location |
|------|----------------|
| **Git Repository** | [github.com/sathyaincampus/finnie-ai](https://github.com/sathyaincampus/finnie-ai) |
| **Git Branch** | `main` |
| **Live App (Cloud Run)** | [finnie-ai-480987910366.us-central1.run.app](https://finnie-ai-480987910366.us-central1.run.app) |
| **README** | [`README.md`](./README.md) |
| **Architecture** | [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) |
| **Technical Spec** | [`SPEC_DEV.md`](./SPEC_DEV.md) |
| **Roadmap** | [`ROADMAP.md`](./ROADMAP.md) |
| **Code Walkthrough** | [`docs/CODE_WALKTHROUGH.md`](./docs/CODE_WALKTHROUGH.md) |
| **Test & Demo Guide** | [`docs/TEST_GUIDE.md`](./docs/TEST_GUIDE.md) |
| **Deployment Guide** | [`docs/DEPLOYMENT.md`](./docs/DEPLOYMENT.md) |
| **Presentation** | [`docs/CAPSTONE_PRESENTATION.html`](./docs/CAPSTONE_PRESENTATION.html) |
| **Grading Rubric** | [`Requirements/Grading Rubric_AI Finance Assistant.xlsx`](./Requirements/Grading%20Rubric_AI%20Finance%20Assistant.xlsx) |
| **Project Requirements** | [`Requirements/IK Capstone Project - Finnie.pdf`](./Requirements/IK%20Capstone%20Project%20-%20Finnie.pdf) |

---

## How to Run Locally

```bash
git clone git@github.com:sathyaincampus/finnie-ai.git
cd finnie-ai
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Add your API keys
streamlit run src/ui/app.py
# Open http://localhost:8501
```

---

## Rubric Alignment — Where to Find Everything

### 1. Technical Implementation (40%)

#### Multi-Agent System — 11 Specialized Agents

| Agent | File | Purpose |
|-------|------|---------|
| ✨ Enhancer | [`src/agents/enhancer.py`](./src/agents/enhancer.py) | Pre-processes and optimizes user prompts before routing |
| 📊 Quant | [`src/agents/quant.py`](./src/agents/quant.py) | Real-time stock data via yFinance |
| 📚 Professor | [`src/agents/professor.py`](./src/agents/professor.py) | Financial education with GraphRAG enrichment |
| 🌍 Scout | [`src/agents/scout.py`](./src/agents/scout.py) | Market trends, movers, sector analysis |
| 🔮 Oracle | [`src/agents/oracle.py`](./src/agents/oracle.py) | Monte Carlo simulations + goal-based projections |
| 💼 Advisor | [`src/agents/advisor.py`](./src/agents/advisor.py) | Portfolio analysis and rebalancing |
| 📰 Analyst | [`src/agents/analyst.py`](./src/agents/analyst.py) | News and research synthesis |
| 📋 Planner | [`src/agents/planner.py`](./src/agents/planner.py) | Financial life planning (529, Roth IRA, retirement, visa) |
| 🪙 Crypto | [`src/agents/crypto.py`](./src/agents/crypto.py) | CoinGecko live crypto prices, tax guidance |
| 🛡️ Guardian | [`src/agents/guardian.py`](./src/agents/guardian.py) | Compliance disclaimers (always runs) |
| ✍️ Scribe | [`src/agents/scribe.py`](./src/agents/scribe.py) | Response synthesis and formatting (always runs) |
| — Base class | [`src/agents/base.py`](./src/agents/base.py) | `BaseFinnieAgent` ABC with shared LLM calling |

#### LangGraph Orchestration (State Machine)

| File | Purpose |
|------|---------|
| [`src/orchestration/state.py`](./src/orchestration/state.py) | `FinnieState` TypedDict, `IntentType` and `AgentName` enums |
| [`src/orchestration/graph.py`](./src/orchestration/graph.py) | `StateGraph`: enhancer → parse_intent → route → agents → guardian → scribe |
| [`src/orchestration/nodes.py`](./src/orchestration/nodes.py) | Node functions for each agent in the graph |

#### MCP (Model Context Protocol) Integration

| File | Tools |
|------|-------|
| [`src/mcp/server.py`](./src/mcp/server.py) | `MCPToolRegistry` — tool discovery, schema validation, execution |
| [`src/mcp/tools/finance_tools.py`](./src/mcp/tools/finance_tools.py) | `get_stock_price`, `get_historical_data`, `get_company_info`, `get_sector_performance` |
| [`src/mcp/tools/chart_tools.py`](./src/mcp/tools/chart_tools.py) | `create_price_chart`, `create_comparison_chart`, `create_sector_heatmap` |

#### GraphRAG (Neo4j Knowledge Graph)

| File | Purpose |
|------|---------|
| [`src/graphrag/graph_client.py`](./src/graphrag/graph_client.py) | Neo4j/AuraDB driver wrapper (singleton, retry logic) |
| [`src/graphrag/ingest.py`](./src/graphrag/ingest.py) | CLI ingestion pipeline: `python -m src.graphrag.ingest` |
| [`src/graphrag/retriever.py`](./src/graphrag/retriever.py) | `retrieve_concept_context()`, `retrieve_company_context()` |
| [`src/graphrag/data/concepts.json`](./src/graphrag/data/concepts.json) | 105 financial concepts (13 categories, 3 difficulty levels) |
| [`src/graphrag/data/companies.json`](./src/graphrag/data/companies.json) | 55+ companies with tickers and sectors |
| [`src/graphrag/data/sectors.json`](./src/graphrag/data/sectors.json) | 11 GICS sectors with descriptions |
| [`src/graphrag/data/etfs.json`](./src/graphrag/data/etfs.json) | 18 sector ETFs |
| [`src/graphrag/data/concept_relationships.json`](./src/graphrag/data/concept_relationships.json) | Cross-concept relationships |
| [`docs/AURADB_SETUP.md`](./docs/AURADB_SETUP.md) | AuraDB setup instructions |

#### LLM Gateway (Multi-Provider Abstraction)

| File | Purpose |
|------|---------|
| [`src/llm/adapter.py`](./src/llm/adapter.py) | `BaseLLMAdapter` ABC + `get_llm_adapter()` factory |
| [`src/llm/openai_provider.py`](./src/llm/openai_provider.py) | OpenAI: GPT-4o, GPT-4o Mini |
| [`src/llm/anthropic_provider.py`](./src/llm/anthropic_provider.py) | Anthropic: Claude Sonnet 4, Claude 3.5 |
| [`src/llm/google_provider.py`](./src/llm/google_provider.py) | Google: Gemini 2.5 Flash Lite, 2.0 Flash, 1.5 Pro |

#### Observability & Evaluations

| File | Purpose |
|------|---------|
| [`src/observability.py`](./src/observability.py) | Arize Phoenix + OpenTelemetry tracing (auto-launches at `localhost:6006`) |
| [`src/evals.py`](./src/evals.py) | Phoenix-based evaluation framework |
| [`tests/eval/test_phoenix_eval.py`](./tests/eval/test_phoenix_eval.py) | 4 AI evaluators: Relevance, QA Quality, Hallucination, Toxicity |
| [`tests/eval/test_agent_quality.py`](./tests/eval/test_agent_quality.py) | Agent response quality tests |

#### Testing — 113 Tests (14 skipped without API keys)

| Test Suite | File | What It Tests |
|------------|------|---------------|
| Agent Unit Tests | [`tests/test_agents.py`](./tests/test_agents.py) | Agent instantiation, ticker extraction, process() |
| New Agent Tests | [`tests/test_new_agents.py`](./tests/test_new_agents.py) | Enhancer, Planner, Crypto agents |
| LLM Adapters | [`tests/test_llm_adapters.py`](./tests/test_llm_adapters.py) | Provider factory, API calls, error handling |
| Orchestration | [`tests/test_orchestration.py`](./tests/test_orchestration.py) | Graph compilation, state management, intent routing |
| Calculators | [`tests/test_calculators.py`](./tests/test_calculators.py) | Monte Carlo, projections, financial math |
| Phoenix Evals | [`tests/eval/test_phoenix_eval.py`](./tests/eval/test_phoenix_eval.py) | AI evaluation with Gemini judge |
| Agent Quality | [`tests/eval/test_agent_quality.py`](./tests/eval/test_agent_quality.py) | Response quality, hallucination detection |

```bash
# Run all tests
pytest tests/ -v                    # 113 passed, 14 skipped
pytest tests/ --cov=src --cov-report=term   # With coverage
```

---

### 2. User Experience (25%)

#### UI — 8 Tabs (Streamlit + Custom CSS)

| Tab | File | Features |
|-----|------|----------|
| 💬 Chat | [`src/ui/app.py`](./src/ui/app.py) | AI chat with intent routing, streaming, voice I/O |
| 💼 Portfolio | [`src/ui/tabs/portfolio.py`](./src/ui/tabs/portfolio.py) | Holdings tracker, live prices, allocation donut chart |
| 📈 Market | [`src/ui/tabs/market.py`](./src/ui/tabs/market.py) | Stock lookup, indices, top gainers/losers |
| 🔮 Projections | [`src/ui/tabs/projections.py`](./src/ui/tabs/projections.py) | Monte Carlo simulator with interactive controls |
| 📋 Planner | [`src/ui/tabs/planner.py`](./src/ui/tabs/planner.py) | Retirement, 529, Roth IRA planning |
| 🪙 Crypto | [`src/ui/tabs/crypto.py`](./src/ui/tabs/crypto.py) | CoinGecko search, price charts, allocation guide |
| ⚙️ Settings | [`src/ui/tabs/settings.py`](./src/ui/tabs/settings.py) | LLM provider config, connection status |
| ❓ Help | [`src/ui/tabs/help.py`](./src/ui/tabs/help.py) | Knowledge Explorer (105 concepts), agent architecture |

#### Auth, Voice & Core UI

| File | Purpose |
|------|---------|
| [`src/ui/auth.py`](./src/ui/auth.py) | Google OAuth + Guest login, session management |
| [`src/ui/voice.py`](./src/ui/voice.py) | TTS (edge-tts, 6 voices) + STT control |
| [`src/ui/stt_component/index.html`](./src/ui/stt_component/index.html) | Custom Streamlit component for browser speech-to-text |
| [`.streamlit/config.toml`](./.streamlit/config.toml) | Dark theme, glassmorphism styling |

---

### 3. Financial Domain Knowledge (20%)

| Feature | Where |
|---------|-------|
| **105 Financial Concepts** | [`src/graphrag/data/concepts.json`](./src/graphrag/data/concepts.json) — 13 categories, 3 difficulty levels |
| **Knowledge Explorer** | [`src/ui/tabs/help.py`](./src/ui/tabs/help.py) — Search, filter, "Ask Finnie" integration |
| **GraphRAG Enrichment** | [`src/agents/professor.py`](./src/agents/professor.py) — RAG badge 🧠 on enhanced responses |
| **Real-Time Market Data** | [`src/mcp/tools/finance_tools.py`](./src/mcp/tools/finance_tools.py) — yFinance, live prices |
| **Crypto Data** | [`src/agents/crypto.py`](./src/agents/crypto.py) — CoinGecko API, 10K+ coins |
| **Portfolio Analysis** | [`src/ui/tabs/portfolio.py`](./src/ui/tabs/portfolio.py) — Live pricing, gain/loss, allocation |
| **Financial Planning** | [`src/agents/planner.py`](./src/agents/planner.py) — 529, Roth IRA, retirement, visa/H1B |
| **Monte Carlo Projections** | [`src/agents/oracle.py`](./src/agents/oracle.py) — Forward + goal-based simulations |

---

### 4. Code Quality (15%)

| Aspect | Evidence |
|--------|----------|
| **Modular Architecture** | 11 agents, each in its own file under `src/agents/` |
| **Config Management** | [`src/config.py`](./src/config.py) — Pydantic-settings, `.env` validation |
| **Memory Layer** | [`src/memory.py`](./src/memory.py) — SQLite chat persistence |
| **Test Coverage** | 113 tests across 7 test files |
| **Documentation** | 8 docs (README, Architecture, Code Walkthrough, Test Guide, etc.) |
| **Type Hints** | TypedDict state, enum-based intents, Pydantic models |
| **Error Handling** | Retry logic in GraphRAG, graceful fallbacks, connection caching |

---

### 5. Innovation (Bonus)

| Innovation | Where |
|------------|-------|
| **Knowledge Explorer** | [`src/ui/tabs/help.py`](./src/ui/tabs/help.py) — Interactive concept browser with `@st.fragment` for performance |
| **Voice Interface** | [`src/ui/voice.py`](./src/ui/voice.py) — Hands-free TTS + STT |
| **LLM Gateway** | [`src/llm/adapter.py`](./src/llm/adapter.py) — Multi-provider routing (OpenAI, Anthropic, Google) |
| **GraphRAG + RAG Badge** | [`src/agents/professor.py`](./src/agents/professor.py) — 🧠 indicator on RAG-enhanced responses |
| **Prompt Enhancer** | [`src/agents/enhancer.py`](./src/agents/enhancer.py) — Auto-optimizes queries before routing |
| **Google OAuth** | [`src/ui/auth.py`](./src/ui/auth.py) — OIDC-based authentication |
| **Cloud Deployment** | [`Dockerfile`](./Dockerfile) + [`docs/DEPLOYMENT.md`](./docs/DEPLOYMENT.md) — Google Cloud Run |
| **Arize Phoenix** | [`src/observability.py`](./src/observability.py) — OpenTelemetry tracing at `localhost:6006` |

---

## Project Structure Overview

```
finnie-ai/
├── src/
│   ├── config.py                    # Pydantic-settings configuration
│   ├── memory.py                    # SQLite chat persistence
│   ├── observability.py             # Arize Phoenix tracing
│   ├── evals.py                     # Phoenix evaluation framework
│   ├── agents/                      # 11 specialized AI agents
│   │   ├── base.py                  #   BaseFinnieAgent ABC
│   │   ├── enhancer.py              #   ✨ Prompt optimizer
│   │   ├── quant.py                 #   📊 Market data (yFinance)
│   │   ├── professor.py             #   📚 Education (GraphRAG-enhanced)
│   │   ├── scout.py                 #   🌍 Trends & movers
│   │   ├── oracle.py                #   🔮 Monte Carlo projections
│   │   ├── advisor.py               #   💼 Portfolio advisor
│   │   ├── analyst.py               #   📰 Research & news
│   │   ├── planner.py               #   📋 Financial life planner
│   │   ├── crypto.py                #   🪙 Crypto (CoinGecko)
│   │   ├── guardian.py              #   🛡️ Compliance
│   │   └── scribe.py                #   ✍️ Response synthesis
│   ├── orchestration/               # LangGraph state machine
│   │   ├── state.py                 #   FinnieState, IntentType, AgentName
│   │   ├── graph.py                 #   StateGraph workflow
│   │   └── nodes.py                 #   Agent node functions
│   ├── llm/                         # Multi-provider LLM abstraction
│   │   ├── adapter.py               #   BaseLLMAdapter + factory
│   │   ├── openai_provider.py       #   GPT-4o, GPT-4o Mini
│   │   ├── anthropic_provider.py    #   Claude Sonnet 4
│   │   └── google_provider.py       #   Gemini 2.5 Flash
│   ├── mcp/                         # Model Context Protocol
│   │   ├── server.py                #   MCPToolRegistry
│   │   └── tools/
│   │       ├── finance_tools.py     #   Stock data tools (4)
│   │       └── chart_tools.py       #   Chart tools (3)
│   ├── graphrag/                    # Knowledge Graph (Neo4j/AuraDB)
│   │   ├── graph_client.py          #   Neo4j driver wrapper
│   │   ├── ingest.py                #   Ingestion pipeline
│   │   ├── retriever.py             #   Query functions
│   │   └── data/                    #   105 concepts, 55 companies, etc.
│   ├── api/
│   │   └── main.py                  # FastAPI REST API
│   └── ui/
│       ├── app.py                   # Main Streamlit app (~1500 lines)
│       ├── auth.py                  # Google OAuth + Guest
│       ├── voice.py                 # TTS + STT
│       └── tabs/                    # 8 modular tab files
├── tests/                           # 113 tests (7 test files)
├── docs/
│   ├── ARCHITECTURE.md              # System architecture v3.0
│   ├── CODE_WALKTHROUGH.md          # Developer guide
│   ├── TEST_GUIDE.md                # Testing & demo script
│   ├── DEPLOYMENT.md                # Google Cloud Run deployment
│   ├── AURADB_SETUP.md              # Neo4j setup
│   ├── IMPLEMENTATION_QA.md         # Design decisions Q&A
│   ├── PROMPT_JOURNAL.md            # How I prompted to build this
│   ├── INITIAL_PROMPTS.md           # The two founding prompts
│   └── CAPSTONE_PRESENTATION.html   # Slide deck
├── Requirements/
│   ├── Grading Rubric_AI Finance Assistant.xlsx
│   └── IK Capstone Project - Finnie.pdf
├── .streamlit/
│   ├── config.toml                  # Theme configuration
│   └── secrets.toml                 # OAuth credentials (not in git)
├── Dockerfile                       # Production container
├── .gcloudignore                    # Cloud Build ignore rules
├── requirements.txt                 # Python dependencies
└── .env                             # API keys (not in git)
```

---

## Technology Stack Summary

| Category | Technology |
|----------|-----------|
| **Frontend** | Streamlit 1.54, Plotly, Custom CSS (dark glassmorphism) |
| **Backend** | FastAPI, LangGraph, MCP |
| **LLM Gateway** | Multi-provider: OpenAI, Anthropic, Google Gemini |
| **Agents** | 11 specialists with LangGraph orchestration |
| **Knowledge Graph** | Neo4j AuraDB — 105 concepts, 55 companies, 11 sectors |
| **Databases** | NeonDB (Postgres), AuraDB (Neo4j), Redis Cloud |
| **Voice** | edge-tts (6 voices) + Web Speech API STT |
| **Observability** | Arize Phoenix + OpenTelemetry |
| **Evaluations** | 4 AI evaluators — 113 tests total |
| **Authentication** | Google OAuth (OIDC) + Guest mode |
| **Deployment** | Google Cloud Run, Docker |

---

## Key Metrics

| Metric | Count |
|--------|-------|
| Agents | 11 |
| MCP Tools | 7 |
| UI Tabs | 8 |
| Financial Concepts | 105 |
| Test Cases | 113 passed, 14 skipped |
| LLM Providers | 3 (OpenAI, Anthropic, Google) |
| Documentation Files | 8 |
| Cloud Databases | 3 (NeonDB, AuraDB, Redis) |
