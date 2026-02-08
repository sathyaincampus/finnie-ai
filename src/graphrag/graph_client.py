"""
Finnie AI — Neo4j Graph Client

Provides a thin wrapper around the Neo4j Python driver for connecting to
AuraDB (or local Neo4j). Follows the singleton pattern used by MCP and
Observability modules.

Usage:
    from src.graphrag.graph_client import get_graph_client

    client = get_graph_client()
    results = client.run_query("MATCH (c:Company) RETURN c.ticker LIMIT 5")
"""

from __future__ import annotations

from typing import Any, Optional
from neo4j import GraphDatabase, Driver

from src.config import get_settings


# =============================================================================
# Graph Client
# =============================================================================


class FinnieGraphClient:
    """
    Neo4j driver wrapper for the Finnie knowledge graph.

    Handles connection lifecycle, query execution, and error handling.
    """

    def __init__(self, uri: str, user: str, password: str):
        self._driver: Driver = GraphDatabase.driver(uri, auth=(user, password))
        self._uri = uri

    # ── Query Execution ──────────────────────────────────────────

    def run_query(
        self,
        query: str,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Execute a read query and return results as list of dicts.

        Args:
            query: Cypher query string.
            params: Optional query parameters.

        Returns:
            List of result records as dictionaries.
        """
        with self._driver.session() as session:
            result = session.run(query, params or {})
            return [record.data() for record in result]

    def run_write(
        self,
        query: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Execute a write query (CREATE, MERGE, DELETE).

        Args:
            query: Cypher write query.
            params: Optional query parameters.

        Returns:
            Summary counters from the query execution.
        """
        with self._driver.session() as session:
            result = session.run(query, params or {})
            summary = result.consume()
            return {
                "nodes_created": summary.counters.nodes_created,
                "relationships_created": summary.counters.relationships_created,
                "properties_set": summary.counters.properties_set,
            }

    def run_write_batch(
        self,
        query: str,
        batch: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Execute a write query for each item in a batch.

        Uses UNWIND for efficient batch operations.
        """
        wrapped = f"UNWIND $batch AS item\n{query}"
        return self.run_write(wrapped, {"batch": batch})

    # ── Lifecycle ─────────────────────────────────────────────────

    def verify_connection(self) -> bool:
        """Test the connection to Neo4j."""
        try:
            self._driver.verify_connectivity()
            return True
        except Exception:
            return False

    def close(self):
        """Close the driver connection."""
        self._driver.close()

    def node_count(self) -> int:
        """Return total node count in the graph."""
        result = self.run_query("MATCH (n) RETURN count(n) AS cnt")
        return result[0]["cnt"] if result else 0

    def __repr__(self) -> str:
        return f"<FinnieGraphClient(uri='{self._uri}')>"


# =============================================================================
# Singleton
# =============================================================================

_client: FinnieGraphClient | None = None


def get_graph_client() -> FinnieGraphClient:
    """
    Get or create the global graph client.

    Reads connection details from settings (.env).

    Raises:
        ConnectionError: If Neo4j/AuraDB is not configured.
    """
    global _client
    if _client is not None:
        return _client

    settings = get_settings()

    if not settings.has_graphrag_config():
        raise ConnectionError(
            "GraphRAG is not configured. "
            "Set AURA_URI, AURA_USER, and AURA_PASSWORD in .env"
        )

    _client = FinnieGraphClient(
        uri=settings.aura_uri,
        user=settings.aura_user,
        password=settings.aura_password,
    )

    return _client


def is_graph_available() -> bool:
    """Check if the graph database is reachable."""
    try:
        client = get_graph_client()
        return client.verify_connection()
    except (ConnectionError, Exception):
        return False
