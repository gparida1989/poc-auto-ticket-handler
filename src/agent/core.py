from typing import Dict, Any, Optional
from src.models.standard_ticket import StandardTicket
from src.models.assignment_group import AssignmentGroup
from src.models.allocation_decision import AllocationDecision
from src.plugins.source_plugin import SourcePlugin
from src.plugins.handler_plugin import HandlerPlugin
from src.allocation_engine.engine import AllocationEngine
import datetime

class TicketAllocationAgent:
    def __init__(self, source_plugins: Dict[str, SourcePlugin], handler_plugins: Dict[str, HandlerPlugin], allocation_engine: AllocationEngine):
        self.source_plugins = source_plugins
        self.handler_plugins = handler_plugins
        self.allocation_engine = allocation_engine

    async def process_webhook(self, payload: Dict[str, Any], source_id: str) -> Dict[str, Any]:
        # 0. Resolve Plugins
        source_plugin = self.source_plugins.get(source_id)
        if not source_plugin:
            raise ValueError(f"No source plugin registered for source_id: {source_id}")
        
        # For POC, we assume the handler matches the source, or use a default
        # In a real scenario, routing logic might determine the handler_id
        handler_id = source_id 
        handler_plugin = self.handler_plugins.get(handler_id)
        if not handler_plugin:
             raise ValueError(f"No handler plugin registered for handler_id: {handler_id}")

        # 1. Validate ticket
        ticket = await source_plugin.validate_ticket(payload)
        # 2. Get assignment groups
        groups = await handler_plugin.get_assignment_groups(ticket.category)
        # 3. Run allocation algorithm
        decision = await self.allocation_engine.allocate(ticket, groups)
        # 4. Assign ticket
        await handler_plugin.assign_ticket(decision)
        # 5. Return allocation decision
        return {
            "ticket_id": ticket.ticket_id,
            "allocation": decision.allocation,
            "scores": decision.scores,
            "rationale": decision.rationale,
            "confidence": decision.confidence,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
