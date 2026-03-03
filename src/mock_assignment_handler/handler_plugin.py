from abc import ABC, abstractmethod
from typing import List, Dict, Any

# Use generic types here to avoid tight coupling to ticketing-agent model classes.
class HandlerPlugin(ABC):
    @abstractmethod
    async def get_assignment_groups(self, category: str = None) -> List[Any]:
        pass

    @abstractmethod
    async def assign_ticket(self, decision: Dict[str, Any]) -> bool:
        pass
