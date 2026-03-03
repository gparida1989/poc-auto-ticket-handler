from typing import Dict, Any, List
from types import SimpleNamespace
from .handler_plugin import HandlerPlugin

class ServiceNowHandler(HandlerPlugin):
    async def get_assignment_groups(self, category: str) -> List[Any]:
        # Return lightweight objects compatible with agent expectations (has .group_id and .name)
        return [
            SimpleNamespace(group_id="L1-Support", name="L1 Support"),
            SimpleNamespace(group_id="L2-Support", name="L2 Support"),
            SimpleNamespace(group_id="L3-Support", name="L3 Support"),
        ]

    async def assign_ticket(self, decision: Dict[str, Any]):
        # In a real handler this would call external APIs to perform assignment.
        print(f"Assigning ticket {decision.get('ticket_id')} to {decision.get('allocation')} with rationale: {decision.get('rationale')}")
        return True
