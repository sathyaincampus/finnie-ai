"""
Finnie AI — GraphRAG Module

Knowledge graph powered by Neo4j/AuraDB for retrieval-augmented generation.
Stores financial concepts, companies, sectors, and their relationships.
"""

from src.graphrag.graph_client import get_graph_client, FinnieGraphClient
from src.graphrag.retriever import (
    retrieve_concept_context,
    retrieve_company_context,
    retrieve_sector_context,
)

__all__ = [
    "get_graph_client",
    "FinnieGraphClient",
    "retrieve_concept_context",
    "retrieve_company_context",
    "retrieve_sector_context",
]
