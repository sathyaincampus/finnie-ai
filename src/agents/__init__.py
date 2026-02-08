"""
Finnie AI — Agent Implementations

8 specialized agents for financial intelligence.
"""

from src.agents.base import BaseFinnieAgent
from src.agents.quant import QuantAgent
from src.agents.professor import ProfessorAgent
from src.agents.analyst import AnalystAgent
from src.agents.advisor import AdvisorAgent
from src.agents.guardian import GuardianAgent
from src.agents.scribe import ScribeAgent
from src.agents.oracle import OracleAgent
from src.agents.scout import ScoutAgent

__all__ = [
    "BaseFinnieAgent",
    "QuantAgent",
    "ProfessorAgent",
    "AnalystAgent",
    "AdvisorAgent",
    "GuardianAgent",
    "ScribeAgent",
    "OracleAgent",
    "ScoutAgent",
]
