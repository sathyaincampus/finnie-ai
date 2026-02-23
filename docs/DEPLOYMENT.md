# Finnie AI — Deployment Guide

> **Last Updated:** February 22, 2026  
> Deploy Finnie AI to Google Cloud Run in under 10 minutes.

---

## Prerequisites

| Tool | Install |
|------|---------|
| **Google Cloud CLI** | `brew install google-cloud-sdk` |
| **Google Cloud Project** | [console.cloud.google.com](https://console.cloud.google.com) |
| **Billing Enabled** | Required for Cloud Run (free tier available) |

```bash
# Login and set project
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

---

## Step 1: Enable Services

```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com
```

---

## Step 2: Deploy to Cloud Run

Cloud Run builds from your `Dockerfile` and deploys in one command:

```bash
cd /Users/sathya/web/python/finnie-ai

gcloud run deploy finnie-ai \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --set-env-vars="\
GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY,\
DEFAULT_LLM_PROVIDER=google,\
DEFAULT_LLM_MODEL=gemini-2.5-flash-lite,\
AURA_URI=YOUR_AURA_URI,\
AURA_USER=YOUR_AURA_USER,\
AURA_PASSWORD=YOUR_AURA_PASSWORD,\
GRAPHRAG_ENABLED=true,\
VOICE_ENABLED=true,\
PHOENIX_ENABLED=false,\
ENVIRONMENT=production,\
LOG_LEVEL=INFO"
```

> [!IMPORTANT]
> Replace `YOUR_*` values with your actual credentials from `.env`.
> Set `PHOENIX_ENABLED=false` for initial deploy (see Phoenix section below).

---

## Step 3: Get Your URL

```bash
gcloud run services describe finnie-ai \
  --region us-central1 \
  --format="value(status.url)"
```

You'll get something like: `https://finnie-ai-xxxxxxxxxx-uc.a.run.app`

---

## Step 4: Update OAuth for Cloud Run

For Google login to work on your deployed app, update `.streamlit/secrets.toml`:

```toml
[auth]
redirect_uri = "https://YOUR-CLOUD-RUN-URL/oauth2callback"
```

Then update the **Google Cloud Console** OAuth credentials:
1. Go to [console.cloud.google.com/apis/credentials](https://console.cloud.google.com/apis/credentials)
2. Edit your OAuth 2.0 Client ID
3. Add `https://YOUR-CLOUD-RUN-URL/oauth2callback` to **Authorized redirect URIs**
4. Redeploy: `gcloud run deploy finnie-ai --source . --region us-central1`

---

## Step 5: Verify Deployment

```bash
# Health check
curl https://YOUR-CLOUD-RUN-URL/_stcore/health

# Open in browser
open https://YOUR-CLOUD-RUN-URL
```

---

## Environment Variables Reference

| Variable | Required | Example | Purpose |
|----------|----------|---------|---------|
| `GOOGLE_API_KEY` | ✅ Yes | `AIzaSy...` | Gemini LLM provider |
| `DEFAULT_LLM_PROVIDER` | ✅ Yes | `google` | Which LLM to use |
| `DEFAULT_LLM_MODEL` | ✅ Yes | `gemini-2.5-flash-lite` | Model name |
| `AURA_URI` | Optional | `neo4j+s://xxx.neo4j.io` | GraphRAG knowledge graph |
| `AURA_USER` | Optional | `neo4j` | AuraDB username |
| `AURA_PASSWORD` | Optional | `xxx` | AuraDB password |
| `GRAPHRAG_ENABLED` | Optional | `true` | Enable Knowledge Graph |
| `VOICE_ENABLED` | Optional | `true` | Enable TTS/STT |
| `PHOENIX_ENABLED` | Optional | `false` | Arize Phoenix tracing |
| `ENVIRONMENT` | Optional | `production` | App environment |
| `NEON_DATABASE_URL` | Optional | `postgresql://...` | Chat memory persistence |

---

## Arize Phoenix — Observability Deployment

Phoenix is the observability dashboard (localhost:6006) that traces all LLM calls, agent activity, and latency.

### Option A: Disable in Production (Simplest — $0)

```bash
PHOENIX_ENABLED=false
```

Phoenix runs in-process and writes to local storage. On Cloud Run (ephemeral containers), traces would be lost on restart. For a demo, just show Phoenix running locally.

**Best for:** Capstone demo — run locally, show the dashboard on `localhost:6006`.

---

### Option B: Arize Cloud Free Tier ($0)

Arize offers a **free hosted Phoenix** with trace persistence:

1. Sign up at [app.arize.com](https://app.arize.com) (free tier)
2. Get your API key and Space ID
3. Add to your deploy command:

```bash
--set-env-vars="\
PHOENIX_ENABLED=true,\
ARIZE_API_KEY=YOUR_ARIZE_API_KEY,\
ARIZE_SPACE_ID=YOUR_SPACE_ID,\
PHOENIX_COLLECTOR_ENDPOINT=https://otlp.arize.com/v1"
```

Then update `src/observability.py` to send traces to Arize Cloud instead of local Phoenix:

```python
# In src/observability.py — change the exporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

exporter = OTLPSpanExporter(
    endpoint="https://otlp.arize.com/v1",
    headers={"api_key": os.getenv("ARIZE_API_KEY"), "space_id": os.getenv("ARIZE_SPACE_ID")}
)
```

**Free tier includes:** 1M spans/month, 30-day retention, dashboards.

**Best for:** Persistent observability in production without extra infrastructure.

---

### Option C: Self-Hosted Phoenix on Cloud Run ($0–5/month)

Deploy Phoenix as a separate Cloud Run service:

```bash
# Deploy Phoenix as its own service
gcloud run deploy phoenix \
  --image arizephoenix/phoenix:latest \
  --region us-central1 \
  --allow-unauthenticated \
  --port 6006 \
  --memory 1Gi

# Get Phoenix URL
PHOENIX_URL=$(gcloud run services describe phoenix --region us-central1 --format="value(status.url)")

# Redeploy Finnie with Phoenix endpoint
gcloud run deploy finnie-ai \
  --source . \
  --region us-central1 \
  --set-env-vars="PHOENIX_ENABLED=true,PHOENIX_COLLECTOR_ENDPOINT=$PHOENIX_URL"
```

**Cost:** Cloud Run free tier gives 2M requests/month + 360K vCPU-seconds. Phoenix is lightweight and would likely stay within free tier.

**Best for:** Full self-hosted observability with persistent traces.

---

### Recommendation

| Scenario | Option | Cost |
|----------|--------|------|
| **Capstone demo** | A (local only) | $0 |
| **Want cloud traces** | B (Arize Cloud) | $0 |
| **Full self-hosted** | C (Cloud Run) | $0–5/month |

For the capstone, **Option A is sufficient** — demo Phoenix locally at `localhost:6006` while showing the Cloud Run app is deployed and accessible.

---

## Cost Summary

| Service | Free Tier | Finnie Usage |
|---------|-----------|-------------|
| **Cloud Run** | 2M requests/month, 360K vCPU-sec | Well within free tier |
| **AuraDB** | 200K nodes, 400K relationships | ~500 nodes used |
| **NeonDB** | 512 MB storage, 0.25 vCPU | Minimal usage |
| **Gemini API** | 15 RPM free, 1M tokens/day | Primary LLM |

> [!TIP]
> For a capstone demo with light usage, **total cost is $0** using all free tiers.

---

## Redeploying After Changes

```bash
# Redeploy with latest code
gcloud run deploy finnie-ai --source . --region us-central1

# Update a single env var
gcloud run services update finnie-ai \
  --region us-central1 \
  --set-env-vars="PHOENIX_ENABLED=true"
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| **Build fails** | Check `Dockerfile` — ensure `requirements.txt` is up to date |
| **App crashes on start** | Check logs: `gcloud run logs read finnie-ai --region us-central1` |
| **OAuth not working** | Update redirect URI in both `secrets.toml` AND Google Cloud Console |
| **AuraDB timeout** | AuraDB free tier auto-pauses after 72h — visit AuraDB console to resume |
| **Slow cold starts** | Cloud Run spins down idle containers. Add `--min-instances=1` (costs more) |

```bash
# View real-time logs
gcloud run logs tail finnie-ai --region us-central1
```

---

*See [README.md](../README.md) for local development setup.*
