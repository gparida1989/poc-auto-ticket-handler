from typing import Dict, Any, List
from ..plugins.source_plugin import SourcePlugin
from ..allocation_engine.engine import AllocationEngine
from ..models.assignment_group import AssignmentGroup
import asyncio
import requests
import logging
import datetime

class TicketAllocationAgent:
    def __init__(self, source_plugins: Dict[str, SourcePlugin], allocation_engine: AllocationEngine, handler_base_url: str = "http://localhost:8002"):
        self.source_plugins = source_plugins
        self.allocation_engine = allocation_engine
        self.handler_base_url = handler_base_url

    async def process_webhook(self, payload: Dict[str, Any], source_id: str) -> Dict[str, Any]:
        # 0. Resolve Plugins
        source_plugin = self.source_plugins.get(source_id)
        if not source_plugin:
            raise ValueError(f"No source plugin registered for source_id: {source_id}")
        
        # For POC, we assume the handler matches the source, or use a default
        # In a real scenario, routing logic might determine the handler_id
        # 1. Validate ticket
        ticket = await source_plugin.validate_ticket(payload)
        # 2. Get assignment groups from assignment-handler service
        resp = await asyncio.to_thread(requests.get, f"{self.handler_base_url}/api/v1/assignment_groups")
        if resp.status_code != 200:
            raise ValueError(f"Failed to fetch assignment groups: {resp.status_code}")
        payload = resp.json()
        groups_data = payload.get("assignment_groups", [])
        groups: List[AssignmentGroup] = []
        for g in groups_data:
            # map incoming dict into AssignmentGroup dataclass (fill missing fields with defaults)
            ag = AssignmentGroup(
                group_id=g.get("group_id"),
                name=g.get("name"),
                location=g.get("location", {}),
                capabilities=g.get("capabilities", []),
                status=g.get("status", "active"),
                max_bandwidth=g.get("max_bandwidth", 0),
                current_load=g.get("current_load", 0),
                metrics=g.get("metrics", {})
            )
            groups.append(ag)
        # 3. Run allocation algorithm
        decision = await self.allocation_engine.allocate(ticket, groups)
        # 4. Notify assignment-handler service of assignment
        mapping = {
            "ticket_id": decision.ticket_id,
            "group_id": decision.allocation.get("group_id") if isinstance(decision.allocation, dict) else None,
            "group_name": decision.allocation.get("group_name") if isinstance(decision.allocation, dict) else None,
            "rationale": decision.rationale,
            "confidence": decision.confidence,
        }
        post_resp = await asyncio.to_thread(requests.post, f"{self.handler_base_url}/api/v1/assignments", json=mapping)
        try:
            resp_json = post_resp.json()
        except Exception:
            resp_json = None
        logging.info("Assignment-handler response: status=%s, body=%s", post_resp.status_code, resp_json)
        # 5. Return allocation decision
        return {
            "ticket_id": ticket.ticket_id,
            "allocation": decision.allocation,
            "scores": decision.scores,
            "rationale": decision.rationale,
            "confidence": decision.confidence,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
