from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class AllocationDecision:
    ticket_id: str
    decision_timestamp: str
    allocation: Dict[str, Any]
    scores: Dict[str, float]
    rationale: str
    confidence: float
