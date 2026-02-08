"""
Finnie AI — GraphRAG Retriever

Query functions that agents call to get knowledge-graph context before
sending a prompt to the LLM.  Results are formatted as plain-text
paragraphs suitable for injection into an LLM system/user message.

Usage:
    from src.graphrag.retriever import retrieve_concept_context

    context = retrieve_concept_context("P/E ratio")
    # → "P/E Ratio: The P/E ratio measures ... Related: EPS, Market Cap ..."
"""

from __future__ import annotations

from typing import Optional

from src.graphrag.graph_client import get_graph_client, is_graph_available


# =============================================================================
# Public Retrieval Functions
# =============================================================================


def retrieve_concept_context(topic: str) -> Optional[str]:
    """
    Retrieve knowledge-graph context for a financial concept.

    Searches by name and aliases using full-text or CONTAINS matching.
    Returns the concept definition, key takeaway, related concepts,
    and applicable sectors — formatted as plain text for LLM injection.

    Args:
        topic: The concept to look up (e.g., "P/E ratio", "dividends").

    Returns:
        Formatted context string, or None if not found / graph unavailable.
    """
    if not is_graph_available():
        return None

    client = get_graph_client()
    topic_lower = topic.lower().strip()

    # Try full-text search first (uses the conceptSearch index)
    results = _fulltext_concept_search(client, topic_lower)

    # Fallback to CONTAINS match on name/aliases
    if not results:
        results = _contains_concept_search(client, topic_lower)

    if not results:
        return None

    concept = results[0]

    # Fetch related concepts
    related = client.run_query(
        """
        MATCH (co:Concept {name: $name})-[:RELATED_TO]->(r:Concept)
        RETURN r.name AS name, r.definition AS definition
        LIMIT 5
        """,
        {"name": concept["name"]},
    )

    # Fetch sectors this concept applies to
    sectors = client.run_query(
        """
        MATCH (co:Concept {name: $name})-[:APPLIES_TO]->(s:Sector)
        RETURN s.name AS name
        """,
        {"name": concept["name"]},
    )

    # Format context
    lines = [
        f"**{concept['name']}** (Difficulty: {concept.get('difficulty', 'N/A')})",
        f"Definition: {concept.get('definition', '')}",
        f"Key Takeaway: {concept.get('keyTakeaway', '')}",
    ]

    if related:
        related_names = [r["name"] for r in related]
        lines.append(f"Related concepts: {', '.join(related_names)}")

    if sectors:
        sector_names = [s["name"] for s in sectors]
        lines.append(f"Applies to sectors: {', '.join(sector_names)}")

    return "\n".join(lines)


def retrieve_company_context(ticker: str) -> Optional[str]:
    """
    Retrieve knowledge-graph context for a company.

    Returns company details, sector, industry, and related ETFs.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL").

    Returns:
        Formatted context string, or None if not found / graph unavailable.
    """
    if not is_graph_available():
        return None

    client = get_graph_client()
    ticker_upper = ticker.upper().strip()

    # Fetch company + sector + industry in one query
    results = client.run_query(
        """
        MATCH (c:Company {ticker: $ticker})
        OPTIONAL MATCH (c)-[:BELONGS_TO]->(s:Sector)
        OPTIONAL MATCH (c)-[:IN_INDUSTRY]->(i:Industry)
        RETURN c.ticker AS ticker,
               c.name AS name,
               c.marketCap AS marketCap,
               c.peRatio AS peRatio,
               c.dividendYield AS dividendYield,
               c.fiftyTwoHigh AS fiftyTwoHigh,
               c.fiftyTwoLow AS fiftyTwoLow,
               s.name AS sector,
               i.name AS industry
        """,
        {"ticker": ticker_upper},
    )

    if not results:
        return None

    co = results[0]

    # Fetch sector ETFs
    etfs = []
    if co.get("sector"):
        etf_results = client.run_query(
            """
            MATCH (s:Sector {name: $sector})-[:HAS_ETF]->(e:ETF)
            RETURN e.ticker AS ticker, e.name AS name
            """,
            {"sector": co["sector"]},
        )
        etfs = etf_results

    # Fetch peer companies in the same sector
    peers = []
    if co.get("sector"):
        peer_results = client.run_query(
            """
            MATCH (c:Company)-[:BELONGS_TO]->(s:Sector {name: $sector})
            WHERE c.ticker <> $ticker
            RETURN c.ticker AS ticker, c.name AS name
            LIMIT 5
            """,
            {"sector": co["sector"], "ticker": ticker_upper},
        )
        peers = peer_results

    # Format
    lines = [
        f"**{co['name']}** ({co['ticker']})",
        f"Sector: {co.get('sector', 'N/A')} | Industry: {co.get('industry', 'N/A')}",
    ]

    if co.get("marketCap"):
        cap_b = co["marketCap"] / 1e9
        lines.append(f"Market Cap: ${cap_b:.1f}B")

    if co.get("peRatio"):
        lines.append(f"P/E Ratio: {co['peRatio']:.1f}")

    if co.get("fiftyTwoHigh") and co.get("fiftyTwoLow"):
        lines.append(f"52-Week Range: ${co['fiftyTwoLow']:.2f} – ${co['fiftyTwoHigh']:.2f}")

    if etfs:
        etf_strs = [f"{e['ticker']} ({e['name']})" for e in etfs]
        lines.append(f"Sector ETFs: {', '.join(etf_strs)}")

    if peers:
        peer_strs = [f"{p['ticker']}" for p in peers]
        lines.append(f"Sector peers: {', '.join(peer_strs)}")

    return "\n".join(lines)


def retrieve_sector_context(sector_name: str) -> Optional[str]:
    """
    Retrieve knowledge-graph context for a market sector.

    Returns sector description, top companies, and ETFs.

    Args:
        sector_name: Sector name (e.g., "Technology").

    Returns:
        Formatted context string, or None if not found / graph unavailable.
    """
    if not is_graph_available():
        return None

    client = get_graph_client()

    # Find sector (case-insensitive)
    results = client.run_query(
        """
        MATCH (s:Sector)
        WHERE toLower(s.name) CONTAINS toLower($name)
        RETURN s.name AS name, s.description AS description
        LIMIT 1
        """,
        {"name": sector_name.strip()},
    )

    if not results:
        return None

    sector = results[0]

    # Companies in this sector (sorted by market cap)
    companies = client.run_query(
        """
        MATCH (c:Company)-[:BELONGS_TO]->(s:Sector {name: $name})
        RETURN c.ticker AS ticker, c.name AS name, c.marketCap AS marketCap
        ORDER BY c.marketCap DESC
        LIMIT 10
        """,
        {"name": sector["name"]},
    )

    # ETFs tracking this sector
    etfs = client.run_query(
        """
        MATCH (s:Sector {name: $name})-[:HAS_ETF]->(e:ETF)
        RETURN e.ticker AS ticker, e.name AS name
        """,
        {"name": sector["name"]},
    )

    # Format
    lines = [
        f"**{sector['name']}** Sector",
        f"Description: {sector.get('description', 'N/A')}",
    ]

    if companies:
        company_strs = [f"{c['ticker']} ({c['name']})" for c in companies]
        lines.append(f"Top companies: {', '.join(company_strs)}")

    if etfs:
        etf_strs = [f"{e['ticker']} ({e['name']})" for e in etfs]
        lines.append(f"Sector ETFs: {', '.join(etf_strs)}")

    return "\n".join(lines)


# =============================================================================
# Internal Helpers
# =============================================================================


def _fulltext_concept_search(client, topic: str) -> list[dict]:
    """Try full-text index search (best for multi-word queries)."""
    try:
        return client.run_query(
            """
            CALL db.index.fulltext.queryNodes("conceptSearch", $query)
            YIELD node, score
            WHERE score > 0.5
            RETURN node.name AS name,
                   node.definition AS definition,
                   node.keyTakeaway AS keyTakeaway,
                   node.difficulty AS difficulty,
                   node.category AS category,
                   score
            ORDER BY score DESC
            LIMIT 3
            """,
            {"query": topic},
        )
    except Exception:
        # Full-text index may not exist yet
        return []


def _contains_concept_search(client, topic: str) -> list[dict]:
    """Fallback: case-insensitive CONTAINS on name and aliases."""
    return client.run_query(
        """
        MATCH (co:Concept)
        WHERE toLower(co.name) CONTAINS $topic
           OR toLower(co.aliases) CONTAINS $topic
        RETURN co.name AS name,
               co.definition AS definition,
               co.keyTakeaway AS keyTakeaway,
               co.difficulty AS difficulty,
               co.category AS category
        LIMIT 3
        """,
        {"topic": topic},
    )
