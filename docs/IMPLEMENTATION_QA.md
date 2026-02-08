# Finnie AI — Implementation Q&A Document

> **Purpose:** Running documentation of design decisions, questions, and answers throughout the development process.  
> **Last Updated:** February 5, 2026  
> **Companion Documents:** [SPEC_DEV.md](../SPEC_DEV.md) | [ROADMAP.md](../ROADMAP.md)

---

## Table of Contents

1. [Timeline & Prioritization](#1-timeline--prioritization)
2. [Data Layer & GraphRAG](#2-data-layer--graphrag)
3. [Database & Hosting Choices](#3-database--hosting-choices)
4. [LLM Provider Configuration](#4-llm-provider-configuration)
5. [Feature Scope & Comparison](#5-feature-scope--comparison)
6. [Agent Architecture](#6-agent-architecture)
7. [Performance & User Experience](#7-performance--user-experience)
8. [MCP & A2A Integration](#8-mcp--a2a-integration)
9. [Observability](#9-observability)
10. [Advanced Features](#10-advanced-features)
11. [Deployment & Cross-Platform](#11-deployment--cross-platform)

---

## 1. Timeline & Prioritization

### Q1.1: Can we defer the custom BPE/Transformer layers and focus on core features first?

**Answer:** Absolutely! Your instinct is correct. The revised approach is:

| Priority | Features | Timeline |
|----------|----------|----------|
| **P0 (Must Have)** | LangGraph agents, Memory, UI, yFinance, Cloud LLM | Days 1-7 |
| **P1 (Should Have)** | GraphRAG, Portfolio Analysis, Voice, MCP | Days 4-10 |
| **P2 (Nice to Have)** | Custom Router, Local LLM, Fine-tuning | Post-submission |

**Deferred to Later (Post-Capstone):**
- BPE Tokenizer from scratch
- Custom Transformer Router
- Llama-3 LoRA Fine-tuning
- 4-bit Quantization
- Distillation from GPT-4
- Local LLM routing (keep config flags ready)

**Why This Works:** The system works end-to-end with cloud LLMs. The local routing is an optimization, not a requirement. We'll add a `USE_LOCAL_LLM=false` config flag that can be enabled later.

### Q1.2: What's the presentation vs submission timeline?

| Milestone | Date | Deliverables |
|-----------|------|--------------|
| **Presentation** | Sunday, Feb 9, 2026 | Architecture diagrams, UI/UX mocks, flow demos |
| **Submission** | Sunday, Feb 16, 2026 | Working app, deployed to Google Cloud, documentation |

---

## 2. Data Layer & GraphRAG

### Q2.1: How much data will we ingest and how long will it take?

**Initial Knowledge Base (MVP):**

| Data Type | Volume | Ingestion Time | Storage |
|-----------|--------|----------------|---------|
| Financial Articles | 100-150 articles | ~30 min | ~50 MB vectors |
| Company Entities | 500+ companies | ~10 min | ~5 MB graph |
| Sector/Industry Nodes | ~50 sectors | ~2 min | ~1 MB graph |
| Concept Definitions | ~200 concepts | ~5 min | ~2 MB graph |

**Total Initial Ingestion:** ~45 minutes, ~60 MB storage

### Q2.2: What happens when users ask questions not in our GraphRAG?

**Fallback Strategy:**

```mermaid
flowchart TB
    Query["User Query"]
    GraphRAG{"Found in<br/>GraphRAG?"}
    LLM["Cloud LLM<br/>(GPT-4/Gemini/Claude)"]
    Hybrid["Combine GraphRAG +<br/>LLM Knowledge"]
    Response["Response"]
    
    Query --> GraphRAG
    GraphRAG -->|"Yes (score > 0.7)"| Hybrid
    GraphRAG -->|"No (score < 0.7)"| LLM
    LLM --> Hybrid
    Hybrid --> Response
```

The LLM acts as the **universal fallback**. If GraphRAG doesn't have the answer, the LLM's training data fills the gap. The response indicates the source:
- 📚 "Based on our knowledge base..." (GraphRAG hit)
- 🤖 "Based on my training data..." (LLM fallback)

### Q2.3: How do we handle live market data?

**Real-Time Data Strategy:**

| Data Type | Source | Update Frequency | Storage |
|-----------|--------|------------------|---------|
| Stock Prices | yFinance API | Real-time on request | Not stored (fetched live) |
| Company Fundamentals | yFinance API | Daily cache | Redis (24h TTL) |
| News Headlines | News API / RSS | Every 15 min | Last 100 per topic |

**Key Insight:** Market prices are **never stored** in GraphRAG—they're fetched live. GraphRAG stores **static knowledge** (definitions, company relationships, sector structures).

### Q2.4: What about historical data volume?

| History Depth | Data Points | Approx Size | Use Case |
|---------------|-------------|-------------|----------|
| 1 year daily | ~252 per stock | ~10 KB/stock | Charts, technical analysis |
| 5 years daily | ~1,260 per stock | ~50 KB/stock | Long-term trends |
| 10 years daily | ~2,520 per stock | ~100 KB/stock | Major cycle analysis |

**Recommendation:** Fetch on-demand via yFinance, cache in Redis for 1 hour. For 500 stocks × 5 years = ~25 MB if fully cached.

### Q2.5: Can we phase GraphRAG implementation?

**Yes! Phased Approach:**

| Phase | Capability | When |
|-------|------------|------|
| **Phase A** | LLM-only (no RAG) | Days 1-3 |
| **Phase B** | Vector RAG (ChromaDB/Redis) | Days 4-6 |
| **Phase C** | Full GraphRAG (Neo4j + Vectors) | Days 7-10 |

Each phase is independently functional. Phase A already works for the presentation!

---

## 3. Database & Hosting Choices

### Q3.1: Can we use AuraDB instead of local Neo4j?

**Yes! Recommended for deployment:**

| Option | Pros | Cons | Recommendation |
|--------|------|------|----------------|
| **Neo4j AuraDB Free** | Cloud-hosted, 200K nodes, no setup | Limited to 200K nodes | ✅ Use for MVP |
| **Local Neo4j Docker** | Full control, unlimited | Must manage, can't deploy easily | Dev only |

**Decision:** Use **AuraDB Free Tier** for both dev and production.

### Q3.2: NeonDB for PostgreSQL?

**Yes! Perfect choice:**

| Feature | Neon Free Tier |
|---------|----------------|
| Storage | 512 MB |
| Compute | 0.25 vCPU |
| Branches | 10 |
| Auto-suspend | After 5 min idle |

**Use Cases:** User accounts, portfolios, conversation history, settings.

### Q3.3: ChromaDB vs Redis for vectors?

**Comparison:**

| Feature | ChromaDB | Redis Stack |
|---------|----------|-------------|
| **Vector Search** | ✅ Native | ✅ RediSearch module |
| **Free Cloud Tier** | ❌ No official cloud | ✅ Redis Cloud (30MB free) |
| **Ease of Use** | ✅ Very simple | ⚠️ More setup |
| **Additional Features** | Vectors only | Caching, pub/sub, sessions |
| **Instructor Preference** | - | ✅ Liked by instructor |

**Recommendation:** Use **Redis Stack** for vectors + caching + session storage. This consolidates 3 services into 1 and earns "instructor points" 😄

### Q3.3a: Where can I get free Redis Cloud hosting?

**Redis Cloud Free Tier:**

| Provider | Link | Free Tier |
|----------|------|-----------|
| **Redis Cloud (Official)** | [redis.io/try-free](https://redis.io/try-free) | 30 MB, 30 connections |
| **Upstash Redis** | [upstash.com](https://upstash.com) | 10K commands/day, 256 MB |
| **Railway** | [railway.app](https://railway.app) | $5 credit/month (covers Redis) |

**Recommended: Redis Cloud (Official)** — Best integration, RediSearch + RedisJSON included.

**How to Get Started:**
1. Go to [redis.io/try-free](https://redis.io/try-free)
2. Sign up with Google/GitHub
3. Create a "Free" subscription
4. Select your cloud region (us-east-1 recommended)
5. Create a database with "RediSearch" and "RedisJSON" modules enabled
6. Copy the connection URL (format: `redis://default:PASSWORD@HOST:PORT`)

**Free Tier Includes:**
- 30 MB storage
- 30 concurrent connections
- RediSearch (vector similarity search)
- RedisJSON (JSON document storage)
- SSL/TLS encryption
- No credit card required

### Q3.4: Final Database Architecture

```mermaid
flowchart LR
    subgraph Cloud["Cloud Services (All Free Tier)"]
        Neon[("NeonDB<br/>PostgreSQL<br/>Users, Portfolios")]
        Aura[("AuraDB<br/>Neo4j<br/>Knowledge Graph")]
        Redis[("Redis Cloud<br/>Vectors + Cache")]
    end
    
    subgraph App["Finnie AI App"]
        API["FastAPI Backend"]
    end
    
    API --> Neon
    API --> Aura
    API --> Redis
```

---

## 4. LLM Provider Configuration

### Q4.1: How do we let users select their LLM provider?

**Settings UI Design:**

```
┌─────────────────────────────────────────────────────┐
│  ⚙️ LLM Provider Settings                          │
├─────────────────────────────────────────────────────┤
│  Provider:  [OpenAI ▼]                              │
│                                                     │
│  Model:     [gpt-4o ▼]                              │
│                                                     │
│  API Key:   [••••••••••••••••] 👁️                  │
│                                                     │
│  Temperature: [0.7] ─────●─────                     │
│                                                     │
│  [Test Connection]  [Save Settings]                 │
└─────────────────────────────────────────────────────┘
```

**Supported Providers & Models:**

| Provider | Models | Notes |
|----------|--------|-------|
| **OpenAI** | `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`, `gpt-3.5-turbo` | Most popular |
| **Anthropic** | `claude-sonnet-4-20250514`, `claude-3-5-sonnet-20241022`, `claude-3-haiku-20240307` | Best for reasoning |
| **Google** | `gemini-2.0-flash`, `gemini-1.5-pro`, `gemini-1.5-flash` | Good free tier |
| **Local (Future)** | `llama-3-8b-instruct` | Requires local setup |

### Q4.2: How do we handle prompt differences between models?

**Abstraction Layer:**

```python
class LLMAdapter:
    """Unified interface for all LLM providers"""
    
    def __init__(self, provider: str, model: str, api_key: str):
        self.provider = provider
        self.model = model
        self.client = self._init_client(api_key)
    
    def chat(self, messages: list, **kwargs) -> str:
        # Normalize messages to provider format
        normalized = self._normalize_messages(messages)
        return self.client.chat(normalized, **kwargs)
    
    def _normalize_messages(self, messages):
        # Handle system prompt differences
        # Claude: system is separate parameter
        # OpenAI: system is first message
        # Gemini: system_instruction parameter
        pass
```

**Key Normalizations:**
1. **System Prompts:** Claude uses separate `system` param, others use message role
2. **Tool Calling:** Unified function calling format → provider-specific
3. **Streaming:** Normalize SSE format across providers

---

## 5. Feature Scope & Comparison

### Q5.1: What exactly does Finnie AI do?

**Core Value Proposition:** Finnie AI is a **Financial Education & Analysis Assistant** that helps users:

1. **Learn** - Understand financial concepts at their level
2. **Analyze** - Get real-time market data and analysis
3. **Plan** - Build and optimize portfolios
4. **Project** - Visualize investment growth scenarios
5. **Discover** - Find opportunities based on market trends

### Q5.2: How does Finnie compare to existing products?

| Feature | Finnie AI | Robinhood | E*Trade | ChatGPT |
|---------|-----------|-----------|---------|---------|
| **Trading** | ❌ No | ✅ Yes | ✅ Yes | ❌ No |
| **Education** | ✅ AI-adaptive | ⚠️ Basic | ⚠️ Basic | ✅ Generic |
| **Real-time Data** | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No |
| **Portfolio Analysis** | ✅ AI-powered | ⚠️ Basic | ✅ Good | ❌ No |
| **Projections** | ✅ Scenario-based | ❌ No | ⚠️ Basic | ❌ No |
| **Multi-Agent AI** | ✅ 6+ Specialists | ❌ No | ❌ No | ❌ Single |
| **Voice Interface** | ✅ Yes | ❌ No | ❌ No | ✅ Yes |
| **Knowledge Graph** | ✅ GraphRAG | ❌ No | ❌ No | ❌ No |

**Unique Position:** Finnie AI is like having a **team of financial advisors** (educational, analytical, compliance-focused) accessible via conversation, without the ability to execute trades (keeping us out of regulatory scope).

### Q5.3: Complete Feature List

**Core Features (MVP):**
- 💬 Conversational AI with memory
- 📊 Real-time stock quotes & charts
- 📚 Financial concept education
- 📈 Basic portfolio tracking
- 🛡️ Compliance disclaimers
- ⚙️ LLM provider settings

**Enhanced Features (Submission):**
- 🎤 Voice chat (Whisper + TTS)
- 🔮 Investment projections (3mo → 10yr)
- ⚖️ Portfolio risk balancing
- 📰 Market news & sentiment
- 🌐 GraphRAG knowledge retrieval
- 🔗 MCP tool integration

**Future Features (Post-Capstone):**
- 🏦 Bank account integration
- 📱 Native mobile apps
- 🤖 Local LLM routing
- 🚀 Startup/IPO analysis
- 💹 Real-time trading alerts

---

## 6. Agent Architecture

### Q6.1: Are 6 agents enough?

**Current 6 agents are sufficient for MVP.** However, we can add 2 more for differentiation:

| Agent | Role | Priority |
|-------|------|----------|
| 📊 The Quant | Market data & technicals | P0 |
| 📚 The Professor | Financial education | P0 |
| 🔍 The Analyst | Research & sentiment | P0 |
| 💼 The Advisor | Portfolio management | P0 |
| 🛡️ The Guardian | Compliance & risk | P0 |
| ✍️ The Scribe | Synthesis & formatting | P0 |
| **🔮 The Oracle** | **Projections & forecasting** | **P1 (NEW)** |
| **🌍 The Scout** | **Startup/trend discovery** | **P2 (NEW)** |

**The Oracle** handles investment projections, scenario modeling, and growth forecasting.
**The Scout** discovers emerging trends, startups, and sector rotations.

### Q6.2: Updated Agent Architecture

```mermaid
mindmap
  root((Finnie AI<br/>8 Agents))
    Core Agents
      📊 The Quant
        Real-time prices
        Technical indicators
        Chart generation
      📚 The Professor
        Concept education
        Adaptive complexity
        Quiz & learning
      🔍 The Analyst
        News aggregation
        Sentiment analysis
        Sector correlations
      💼 The Advisor
        Portfolio construction
        Risk assessment
        Rebalancing
    Support Agents
      🛡️ The Guardian
        Compliance checks
        Disclaimers
        Risk warnings
      ✍️ The Scribe
        Response synthesis
        Visualization
        Multi-modal output
    Advanced Agents
      🔮 The Oracle
        Investment projections
        Growth scenarios
        Monte Carlo sims
      🌍 The Scout
        Startup discovery
        Trend spotting
        Sector rotation
```

---

## 7. Performance & User Experience

### Q7.1: How do we ensure fast response times?

**Target Metrics:**

| Metric | Target | Strategy |
|--------|--------|----------|
| **TTFT (Time to First Token)** | < 500ms | Streaming responses |
| **Full Response** | < 3s for simple | Agent parallelization |
| **Chart Rendering** | < 1s | Pre-computed layouts |

**UX During Processing:**

```
┌─────────────────────────────────────────────────────┐
│  🔵 Finnie is thinking...                           │
│                                                     │
│  ├─ 📊 Fetching AAPL data...        ✓ Done         │
│  ├─ 🔍 Analyzing market trends...   ⏳ In progress  │
│  ├─ 📚 Preparing explanation...     ⏳ Waiting      │
│                                                     │
│  ▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░ 60%                          │
└─────────────────────────────────────────────────────┘
```

**Streaming Strategy:**
1. Start streaming text immediately
2. Show agent activity indicators
3. Load charts asynchronously
4. Never show a blank screen

### Q7.2: Progressive Response Pattern

```python
async def stream_response(query: str):
    # 1. Instant acknowledgment
    yield "💭 Let me look into that...\n\n"
    
    # 2. Stream agent activities
    async for agent_update in run_agents(query):
        yield f"_{agent_update}_\n"
    
    # 3. Stream main response
    async for token in generate_response():
        yield token
    
    # 4. Append visualizations
    yield "\n\n[Chart Loading...]"
    chart = await generate_chart()
    yield chart
```

---

## 8. MCP & A2A Integration

### Q8.1: What is MCP and why is it critical?

**MCP (Model Context Protocol)** is Anthropic's standard for connecting AI to external tools. It's critical because:
1. **Standardized tool interface** - Agents can call any MCP-compatible tool
2. **Future-proof** - Industry is adopting MCP
3. **Rubric points** - Demonstrates advanced integration

### Q8.2: MCP Architecture in Finnie AI

```mermaid
flowchart TB
    subgraph Finnie["Finnie AI Application"]
        LangGraph["LangGraph Orchestrator"]
        MCPClient["MCP Client"]
    end
    
    subgraph MCPServers["MCP Tool Servers"]
        Finance["finance-tools-mcp<br/>yFinance, calculators"]
        News["news-mcp<br/>NewsAPI, RSS"]
        Charts["charts-mcp<br/>Plotly generation"]
        DB["database-mcp<br/>Neo4j, Redis queries"]
    end
    
    LangGraph --> MCPClient
    MCPClient --> Finance
    MCPClient --> News
    MCPClient --> Charts
    MCPClient --> DB
```

### Q8.3: MCP Tool Definitions

```python
# MCP Tool Schema for Finance Tools
FINANCE_TOOLS = {
    "get_stock_price": {
        "description": "Get current stock price and basic info",
        "parameters": {
            "ticker": {"type": "string", "required": True}
        }
    },
    "get_historical_data": {
        "description": "Get historical price data",
        "parameters": {
            "ticker": {"type": "string", "required": True},
            "period": {"type": "string", "enum": ["1d", "5d", "1mo", "3mo", "1y", "5y"]}
        }
    },
    "calculate_portfolio_metrics": {
        "description": "Calculate portfolio risk metrics",
        "parameters": {
            "holdings": {"type": "array", "items": {"type": "object"}}
        }
    }
}
```

### Q8.4: What is A2A and when do we add it?

**A2A (Agent-to-Agent)** is Google's protocol for agents to communicate across systems. 

**Phase:** Add after core functionality, before deployment. Enables:
- Other AI systems to query Finnie
- Finnie to delegate to specialized external agents
- Multi-system orchestration

```python
# A2A Agent Card (for discovery)
FINNIE_AGENT_CARD = {
    "name": "Finnie AI",
    "description": "Financial education and analysis assistant",
    "capabilities": ["market_data", "portfolio_analysis", "education"],
    "endpoint": "https://finnie-ai.run.app/a2a",
    "authentication": "bearer"
}
```

---

## 9. Observability

### Q9.1: How do we implement observability?

**Tool Choice: LangFuse** (open-source, free tier available)

**What We Track:**

| Metric | Purpose |
|--------|---------|
| **Traces** | Full request lifecycle |
| **Latency** | Per-agent timing |
| **Token Usage** | Cost tracking |
| **Error Rates** | Reliability monitoring |
| **User Satisfaction** | Thumbs up/down feedback |

### Q9.2: LangFuse Integration

```python
from langfuse import Langfuse
from langfuse.callback import CallbackHandler

# Initialize LangFuse
langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host="https://cloud.langfuse.com"
)

# Use with LangChain
handler = CallbackHandler()

# Every LLM call is automatically traced
response = llm.invoke(prompt, callbacks=[handler])
```

**Dashboard Views:**
- Request traces with agent breakdown
- Cost per conversation
- Error rates by agent
- Latency percentiles

---

## 10. Advanced Features

### Q10.1: Investment Projection Feature

**Projection Scenarios:**

| Timeframe | Data Points | Variables |
|-----------|-------------|-----------|
| 3 months | 63 trading days | Recent volatility |
| 6 months | 126 trading days | Sector trends |
| 1 year | 252 trading days | Economic cycles |
| 3 years | 756 trading days | Major market phases |
| 5 years | 1,260 trading days | Historical returns |
| 10 years | 2,520 trading days | Long-term averages |

**Projection Model:**

```python
def project_investment(
    initial_amount: float,
    monthly_contribution: float,
    years: int,
    expected_return: float = 0.08,  # 8% annual
    volatility: float = 0.15,        # 15% std dev
    simulations: int = 1000
) -> dict:
    """Monte Carlo simulation for investment projections"""
    # Returns: {
    #   "median": [...],
    #   "p10": [...],  # 10th percentile (pessimistic)
    #   "p90": [...],  # 90th percentile (optimistic)
    # }
```

**Interactive UI:**

```
┌─────────────────────────────────────────────────────┐
│  🔮 Investment Projection Calculator                │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Initial Investment:  $[10,000    ]                 │
│  Monthly Addition:    $[500       ]                 │
│                                                     │
│  Timeframe: ○3mo ○6mo ○1yr ○3yr ●5yr ○10yr         │
│                                                     │
│  Risk Level:  Low ────●──── High                    │
│                                                     │
│  ┌────────────────────────────────────────────┐    │
│  │ 📈 Projected Growth                        │    │
│  │                                    ╱╱╱     │    │
│  │                              ╱╱╱╱╱╱        │    │
│  │                        ╱╱╱╱╱╱              │    │
│  │                  ╱╱╱╱╱╱   ← Optimistic     │    │
│  │            ─────────────  ← Median         │    │
│  │      ─────────────        ← Conservative   │    │
│  │ $10K                                       │    │
│  └────────────────────────────────────────────┘    │
│                                                     │
│  Projected Value (5yr):                             │
│  Conservative: $52,340 | Median: $68,920 | High: $89,100|
└─────────────────────────────────────────────────────┘
```

### Q10.2: Portfolio Balancing Suggestions

**Factors Considered:**

| Factor | Weight | Adjustment |
|--------|--------|------------|
| **Age** | High | Younger → more equity |
| **Risk Tolerance** | High | Conservative → more bonds |
| **Time Horizon** | Medium | Longer → more growth |
| **Current Holdings** | Medium | Rebalance to targets |
| **Market Conditions** | Low | Tactical shifts |

**Asset Allocation Templates:**

```python
ALLOCATION_TEMPLATES = {
    "aggressive": {
        "US Stocks": 50,
        "International Stocks": 30,
        "Bonds": 10,
        "Alternatives": 10
    },
    "moderate": {
        "US Stocks": 40,
        "International Stocks": 20,
        "Bonds": 30,
        "Alternatives": 10
    },
    "conservative": {
        "US Stocks": 25,
        "International Stocks": 10,
        "Bonds": 55,
        "Alternatives": 10
    }
}
```

### Q10.3: Startup & Trend Discovery

**The Scout Agent Capabilities:**

1. **Sector Rotation Detection** - Which sectors are gaining/losing momentum
2. **Emerging Theme Identification** - AI data centers, clean energy, etc.
3. **IPO/SPAC Analysis** - Upcoming public offerings
4. **Trend Explanation** - "Why is X happening?"

**Example Interaction:**
> 🌍 **The Scout:** "I've noticed increased activity in nuclear energy stocks (CEG, VST, NRG) — up 45% YTD. This aligns with the AI data center boom, as nuclear provides reliable baseload power for 24/7 computing. Companies like Crusoe are building data centers near power sources. Would you like me to analyze this sector?"

---

## 11. Deployment & Cross-Platform

### Q11.1: How do we deploy to Google Cloud?

**Deployment Architecture:**

```mermaid
flowchart TB
    subgraph GCP["Google Cloud Platform"]
        CloudRun["Cloud Run<br/>(FastAPI + Streamlit)"]
        Secrets["Secret Manager<br/>(API Keys)"]
    end
    
    subgraph External["External Services"]
        Neon["NeonDB"]
        Aura["AuraDB"]
        Redis["Redis Cloud"]
        LLMs["LLM APIs"]
    end
    
    Users["Users"] --> CloudRun
    CloudRun --> Secrets
    CloudRun --> Neon
    CloudRun --> Aura
    CloudRun --> Redis
    CloudRun --> LLMs
```

**Cloud Run Configuration:**
```yaml
# service.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: finnie-ai
spec:
  template:
    spec:
      containers:
        - image: gcr.io/PROJECT_ID/finnie-ai
          ports:
            - containerPort: 8080
          resources:
            limits:
              memory: 2Gi
              cpu: "2"
          env:
            - name: ENVIRONMENT
              value: production
```

### Q11.2: How do we make the UI responsive for mobile?

**Responsive Design Strategy:**

1. **Streamlit with Custom CSS** - Mobile-first breakpoints
2. **Flexible Layouts** - Stacked on mobile, side-by-side on desktop
3. **Touch-Friendly** - Large tap targets, swipe gestures
4. **PWA Support** - Add to home screen capability

**CSS Breakpoints:**
```css
/* Mobile First */
.chat-container {
    width: 100%;
    padding: 1rem;
}

/* Tablet */
@media (min-width: 768px) {
    .chat-container {
        width: 80%;
        padding: 2rem;
    }
}

/* Desktop */
@media (min-width: 1024px) {
    .chat-container {
        width: 60%;
        max-width: 800px;
    }
}
```

### Q11.3: Cross-Platform Roadmap

| Platform | Approach | Timeline |
|----------|----------|----------|
| **Web (Desktop)** | Streamlit/React | MVP |
| **Web (Mobile)** | Responsive CSS | MVP |
| **Android** | PWA → Capacitor | Post-MVP |
| **iOS** | PWA → Capacitor | Post-MVP |
| **Desktop Apps** | Electron wrapper | Future |

**PWA Benefits:**
- Install from browser
- Offline capability (cached assets)
- Push notifications
- Native-like experience

---

## Changelog

| Date | Changes |
|------|---------|
| Feb 5, 2026 | Initial Q&A document created with 11 sections |

---

*This document is maintained throughout the development process.*  
*Last Updated: February 5, 2026*
