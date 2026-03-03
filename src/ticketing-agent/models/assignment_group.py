from dataclasses import dataclass, field
from typing import Dict, Any, List

@dataclass
class AssignmentGroup:
    group_id: str
    name: str
    location: Dict[str, Any]
    capabilities: List[str]
    status: str
    max_bandwidth: int
    current_load: int
    metrics: Dict[str, Any] = field(default_factory=dict)
