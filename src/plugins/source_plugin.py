from abc import ABC, abstractmethod
from typing import Dict, Any
from src.models.standard_ticket import StandardTicket

class SourcePlugin(ABC):
    @abstractmethod
    async def validate_ticket(self, ticket: Dict[str, Any]) -> StandardTicket:
        pass

    @abstractmethod
    def get_ticket_metadata(self, ticket_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_group_id_for_assignment(self, ticket_id: str) -> str:
        pass
