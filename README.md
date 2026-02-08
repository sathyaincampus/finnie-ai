# Finnie AI — Autonomous Financial Intelligence System

> **"Hedge Fund in a Box"** — A multi-agent financial assistant for education and analysis

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🦈 Overview

Finnie AI is a conversational AI assistant that democratizes financial literacy through specialized agents, real-time market data, and personalized portfolio guidance.

**Key Features:**
- 💬 **Multi-Agent Chat** — 8 specialized agents for different financial queries
- 📊 **Real-Time Market Data** — Live stock prices via yFinance
- 📈 **Portfolio Analysis** — Holdings tracking, risk metrics
- 🔮 **Investment Projections** — Monte Carlo simulations
- 🎤 **Voice Interface** — Whisper STT + TTS
- 🔗 **MCP Tools** — Standardized tool integration

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ (optional, for development)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/finnie-ai.git
cd finnie-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your API keys
```

### Configuration

Edit `.env` with your credentials:

```env
# LLM Providers (at least one required)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...

# Databases (for full features)
NEON_DATABASE_URL=postgresql://...
AURA_URI=neo4j+s://...
AURA_USER=neo4j
AURA_PASSWORD=...
REDIS_URL=redis://...

# Observability (optional)
LANGFUSE_PUBLIC_KEY=...
LANGFUSE_SECRET_KEY=...
```

### Running the App

```bash
# Start Streamlit UI
streamlit run src/ui/app.py

# Or start FastAPI backend
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

## 📁 Project Structure

```
finnie-ai/
├── src/
│   ├── agents/           # 8 specialized agents
│   ├── orchestration/    # LangGraph state machine
│   ├── llm/              # Multi-provider LLM adapters
│   ├── mcp/              # MCP tool servers
│   ├── data/             # Database clients
│   ├── api/              # FastAPI backend
│   └── ui/               # Streamlit frontend
├── tests/                # Test suite
├── docs/                 # Documentation
│   ├── ARCHITECTURE.md   # System architecture
│   ├── IMPLEMENTATION_QA.md  # Design decisions
│   └── images/           # Diagrams and mockups
├── SPEC_DEV.md           # Technical specification
├── ROADMAP.md            # Execution roadmap
└── requirements.txt
```

## 🤖 Agent Roster

| Agent | Role | Triggers |
|-------|------|----------|
| 📊 **The Quant** | Market data & technicals | Stock tickers, prices |
| 📚 **The Professor** | Financial education | "What is...", "Explain..." |
| 🔍 **The Analyst** | News & sentiment | "News about...", research |
| 💼 **The Advisor** | Portfolio management | Holdings, allocation |
| 🛡️ **The Guardian** | Compliance & disclaimers | All responses |
| ✍️ **The Scribe** | Response formatting | All responses |
| 🔮 **The Oracle** | Investment projections | "If I invest..." |
| 🌍 **The Scout** | Trend discovery | "What's trending..." |

## 📖 Documentation

- [Technical Specification](./SPEC_DEV.md)
- [Execution Roadmap](./ROADMAP.md)
- [Architecture Overview](./docs/ARCHITECTURE.md)
- [Implementation Q&A](./docs/IMPLEMENTATION_QA.md)

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## 🚢 Deployment

### Docker

```bash
docker build -t finnie-ai -f docker/Dockerfile .
docker run -p 8080:8080 --env-file .env finnie-ai
```

### Google Cloud Run

```bash
gcloud run deploy finnie-ai \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

## 📄 License

MIT License — see [LICENSE](./LICENSE) for details.

---

**Finnie AI** — *Your personal financial intelligence team* 🦈
