from abc import ABC, abstractmethod
from typing import List, Dict, Any
from src.models.assignment_group import AssignmentGroup
from src.models.allocation_decision import AllocationDecision

class HandlerPlugin(ABC):
    @abstractmethod
    async def get_assignment_groups(self, category: str = None) -> List[AssignmentGroup]:
        pass

    @abstractmethod
    async def assign_ticket(self, decision: AllocationDecision) -> bool:
        pass
