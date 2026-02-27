from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class StandardTicket:
    ticket_id: str
    ticket_number: str
    title: str
    description: str
    category: str
    priority: str
    source: str
    requester_location: Dict[str, Any]
    urgency: str
    impact: str
    external_metadata: Dict[str, Any] = field(default_factory=dict)
