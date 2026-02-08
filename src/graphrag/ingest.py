"""
Finnie AI — Knowledge Graph Ingestion Pipeline

Populates the Neo4j/AuraDB knowledge graph with:
- Financial concepts (definitions, relationships)
- Companies (from yFinance live data)
- Sectors (GICS classification)
- ETFs (major index & sector ETFs)
- All relationships between them

Data is loaded from JSON files in src/graphrag/data/ so new entries
can be added without modifying code.

Usage:
    python -m src.graphrag.ingest          # Full ingestion
    python -m src.graphrag.ingest --dry    # Preview without writing
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import yfinance as yf

from src.graphrag.graph_client import get_graph_client, FinnieGraphClient


# =============================================================================
# Data Directory
# =============================================================================

DATA_DIR = Path(__file__).parent / "data"


def _load_json(filename: str) -> Any:
    """Load a JSON file from the data directory."""
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")
    with open(path, "r") as f:
        return json.load(f)


# =============================================================================
# Schema: Constraints & Indexes
# =============================================================================

SCHEMA_QUERIES = [
    # Unique constraints
    "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Company) REQUIRE c.ticker IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Sector) REQUIRE s.name IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (co:Concept) REQUIRE co.name IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (e:ETF) REQUIRE e.ticker IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (i:Industry) REQUIRE i.name IS UNIQUE",
    # Full-text search index for concept lookups
    """
    CREATE FULLTEXT INDEX conceptSearch IF NOT EXISTS
    FOR (co:Concept) ON EACH [co.name, co.definition, co.aliases]
    """,
]


# =============================================================================
# Ingestion Functions
# =============================================================================


def ingest_concepts(client: FinnieGraphClient, dry: bool = False) -> int:
    """Create Concept nodes and RELATED_TO edges."""
    print("\n📚 Ingesting financial concepts...")

    concepts = _load_json("concepts.json")
    relationships = _load_json("concept_relationships.json")

    count = 0
    for concept in concepts:
        if dry:
            print(f"  [DRY] Would create Concept: {concept['name']}")
            count += 1
            continue

        client.run_write(
            """
            MERGE (co:Concept {name: $name})
            SET co.aliases    = $aliases,
                co.definition = $definition,
                co.keyTakeaway = $keyTakeaway,
                co.difficulty  = $difficulty,
                co.category    = $category
            """,
            concept,
        )
        count += 1
        print(f"  ✅ {concept['name']}")

    # Create RELATED_TO edges
    if not dry:
        print("\n🔗 Creating concept relationships...")
        rel_count = 0
        for source, targets in relationships.items():
            for target in targets:
                client.run_write(
                    """
                    MATCH (a:Concept {name: $source}), (b:Concept {name: $target})
                    MERGE (a)-[:RELATED_TO]->(b)
                    """,
                    {"source": source, "target": target},
                )
                rel_count += 1
        print(f"  ✅ {rel_count} relationships created")

    return count


def ingest_sectors(client: FinnieGraphClient, dry: bool = False) -> int:
    """Create Sector nodes."""
    print("\n📊 Ingesting sectors...")

    sectors = _load_json("sectors.json")

    count = 0
    for sector in sectors:
        if dry:
            print(f"  [DRY] Would create Sector: {sector['name']}")
            count += 1
            continue

        client.run_write(
            """
            MERGE (s:Sector {name: $name})
            SET s.description = $description
            """,
            sector,
        )
        count += 1
        print(f"  ✅ {sector['name']}")

    return count


def ingest_etfs(client: FinnieGraphClient, dry: bool = False) -> int:
    """Create ETF nodes and HAS_ETF relationships to sectors."""
    print("\n🏛️ Ingesting ETFs...")

    etf_data = _load_json("etfs.json")
    etfs = etf_data["etfs"]
    sector_etf_map = etf_data["sector_etf_map"]

    count = 0
    for etf in etfs:
        if dry:
            print(f"  [DRY] Would create ETF: {etf['ticker']} ({etf['name']})")
            count += 1
            continue

        client.run_write(
            """
            MERGE (e:ETF {ticker: $ticker})
            SET e.name     = $name,
                e.category = $category
            """,
            etf,
        )
        count += 1
        print(f"  ✅ {etf['ticker']} — {etf['name']}")

    # Create Sector → ETF edges
    if not dry:
        print("\n🔗 Linking sectors to ETFs...")
        link_count = 0
        for sector_name, etf_tickers in sector_etf_map.items():
            for etf_ticker in etf_tickers:
                client.run_write(
                    """
                    MATCH (s:Sector {name: $sector}), (e:ETF {ticker: $etf})
                    MERGE (s)-[:HAS_ETF]->(e)
                    """,
                    {"sector": sector_name, "etf": etf_ticker},
                )
                link_count += 1
        print(f"  ✅ {link_count} sector-ETF links created")

    return count


def ingest_companies(client: FinnieGraphClient, dry: bool = False) -> int:
    """
    Fetch company data from yFinance and create Company nodes.

    Also creates:
    - Industry nodes
    - BELONGS_TO (Company → Sector) edges
    - IN_INDUSTRY (Company → Industry) edges
    """
    company_data = _load_json("companies.json")
    tickers = company_data["tickers"]

    print(f"\n🏢 Ingesting {len(tickers)} companies from yFinance...")

    count = 0
    errors = []

    for ticker in tickers:
        try:
            if dry:
                print(f"  [DRY] Would fetch & create Company: {ticker}")
                count += 1
                continue

            stock = yf.Ticker(ticker)
            info = stock.info

            name = info.get("shortName", ticker)
            sector = info.get("sector", "")
            industry = info.get("industry", "")
            market_cap = info.get("marketCap", 0)
            pe_ratio = info.get("trailingPE")
            dividend_yield = info.get("dividendYield")
            fifty_two_high = info.get("fiftyTwoWeekHigh")
            fifty_two_low = info.get("fiftyTwoWeekLow")

            # Create Company node
            client.run_write(
                """
                MERGE (c:Company {ticker: $ticker})
                SET c.name           = $name,
                    c.marketCap      = $marketCap,
                    c.peRatio        = $peRatio,
                    c.dividendYield  = $dividendYield,
                    c.fiftyTwoHigh   = $fiftyTwoHigh,
                    c.fiftyTwoLow    = $fiftyTwoLow
                """,
                {
                    "ticker": ticker,
                    "name": name,
                    "marketCap": market_cap,
                    "peRatio": pe_ratio,
                    "dividendYield": dividend_yield,
                    "fiftyTwoHigh": fifty_two_high,
                    "fiftyTwoLow": fifty_two_low,
                },
            )

            # Link to Sector
            if sector:
                client.run_write(
                    """
                    MATCH (c:Company {ticker: $ticker})
                    MERGE (s:Sector {name: $sector})
                    MERGE (c)-[:BELONGS_TO]->(s)
                    """,
                    {"ticker": ticker, "sector": sector},
                )

            # Link to Industry
            if industry:
                client.run_write(
                    """
                    MATCH (c:Company {ticker: $ticker})
                    MERGE (i:Industry {name: $industry})
                    MERGE (c)-[:IN_INDUSTRY]->(i)
                    """,
                    {"ticker": ticker, "industry": industry},
                )

            count += 1
            print(f"  ✅ {ticker} — {name} ({sector})")

            # Rate limit to be kind to yFinance
            time.sleep(0.3)

        except Exception as e:
            errors.append((ticker, str(e)))
            print(f"  ❌ {ticker} — Error: {e}")

    if errors:
        print(f"\n⚠️  {len(errors)} errors during company ingestion:")
        for t, err in errors:
            print(f"    {t}: {err}")

    return count


def clear_graph(client: FinnieGraphClient) -> None:
    """Delete all nodes and relationships. Use with caution!"""
    print("🗑️  Clearing entire graph...")
    client.run_write("MATCH (n) DETACH DELETE n")
    print("  ✅ Graph cleared")


# =============================================================================
# Main
# =============================================================================


def main():
    parser = argparse.ArgumentParser(description="Finnie AI Knowledge Graph Ingestion")
    parser.add_argument("--dry", action="store_true", help="Preview without writing to Neo4j")
    parser.add_argument("--clear", action="store_true", help="Clear graph before ingesting")
    parser.add_argument(
        "--only",
        choices=["concepts", "sectors", "etfs", "companies"],
        help="Ingest only a specific node type",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  Finnie AI — Knowledge Graph Ingestion Pipeline")
    print("=" * 60)
    print(f"  Data directory: {DATA_DIR}")

    if args.dry:
        print("\n🔍 DRY RUN — no data will be written\n")
        from src.config import get_settings
        settings = get_settings()
        if not settings.has_graphrag_config():
            print("⚠️  GraphRAG not configured in .env — set AURA_URI and AURA_PASSWORD")
            print("   Get a free AuraDB at: https://neo4j.com/cloud/aura-free/")
            sys.exit(1)
        client = None
    else:
        try:
            client = get_graph_client()
            if not client.verify_connection():
                print("❌ Cannot connect to Neo4j. Check your .env settings.")
                sys.exit(1)
            print(f"\n✅ Connected to Neo4j: {client}")
        except ConnectionError as e:
            print(f"\n❌ {e}")
            print("   Get a free AuraDB at: https://neo4j.com/cloud/aura-free/")
            sys.exit(1)

    # Optionally clear
    if args.clear and client:
        clear_graph(client)

    # Create schema
    if client and not args.dry:
        print("\n📋 Creating schema constraints & indexes...")
        for q in SCHEMA_QUERIES:
            try:
                client.run_write(q.strip())
            except Exception as e:
                if "already exists" not in str(e).lower():
                    print(f"  ⚠️  Schema warning: {e}")
        print("  ✅ Schema ready")

    # Ingest
    start = time.time()
    totals = {}

    if args.only in (None, "concepts"):
        totals["concepts"] = ingest_concepts(client, dry=args.dry)

    if args.only in (None, "sectors"):
        totals["sectors"] = ingest_sectors(client, dry=args.dry)

    if args.only in (None, "etfs"):
        totals["etfs"] = ingest_etfs(client, dry=args.dry)

    if args.only in (None, "companies"):
        totals["companies"] = ingest_companies(client, dry=args.dry)

    elapsed = time.time() - start

    # Summary
    print("\n" + "=" * 60)
    print("  Ingestion Complete!")
    print("=" * 60)
    for label, cnt in totals.items():
        print(f"  {label.capitalize():12s} : {cnt} nodes")
    print(f"  {'Time':12s} : {elapsed:.1f}s")

    if client and not args.dry:
        total = client.node_count()
        print(f"  {'Total nodes':12s} : {total}")


if __name__ == "__main__":
    main()
