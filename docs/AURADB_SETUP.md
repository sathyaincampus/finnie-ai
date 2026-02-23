# AuraDB Setup Guide — Finnie AI GraphRAG

## 1. Create Free AuraDB Instance

1. Go to [console.neo4j.io](https://console.neo4j.io)
2. Sign up / login (Google or email)
3. Click **"New Instance"** → Choose **"AuraDB Free"**
4. Name it: `finnie-ai`
5. Region: Choose closest to you (e.g., `us-east-1`)
6. **IMPORTANT:** Save the generated password — it's only shown once!
7. Click **"Create"** and wait ~60 seconds

## 2. Copy Connection Details

After creation, you'll see:
- **Connection URI**: `neo4j+s://xxxxxxxx.databases.neo4j.io`
- **Username**: `neo4j` (default)
- **Password**: The one you saved in step 6

## 3. Configure Environment

Add to your `.env` file:

```env
AURA_URI=neo4j+s://xxxxxxxx.databases.neo4j.io
AURA_USER=neo4j
AURA_PASSWORD=your-password-here
```

## 4. Run Ingestion

```bash
# Preview what will be ingested (dry run)
python -m src.graphrag.ingest --dry

# Full ingestion
python -m src.graphrag.ingest
```

**What gets ingested:**
| Data | Count | Source |
|------|-------|--------|
| Financial Concepts | 105 | `src/graphrag/data/concepts.json` |
| Concept Relationships | 50+ | `src/graphrag/data/concept_relationships.json` |
| Sectors | 11 | `src/graphrag/data/sectors.json` |
| ETFs | 19 | `src/graphrag/data/etfs.json` |
| Companies | 58 | `src/graphrag/data/companies.json` + yfinance live data |

## 5. Verify

Open [console.neo4j.io](https://console.neo4j.io) → your instance → **Query** tab:

```cypher
// Count all nodes
MATCH (n) RETURN labels(n)[0] AS type, count(n) AS count ORDER BY count DESC

// Browse concepts
MATCH (c:Concept) RETURN c.name, c.category, c.difficulty LIMIT 20

// See relationships
MATCH (a:Concept)-[r:RELATED_TO]->(b:Concept) RETURN a.name, b.name LIMIT 20
```

## Troubleshooting

- **Connection refused**: Check that the instance is running (green status in console)
- **Auth failed**: Re-generate password in console → Settings → Reset Password
- **Free tier limits**: 200K nodes, 400K relationships — more than enough for Finnie AI
