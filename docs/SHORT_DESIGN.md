# Short Design Summary

Purpose
- Provide a concise description of the architecture and responsibilities for the POC auto-ticket handler.

Components
- mock_source: lightweight FastAPI app that reads example tickets and posts them to the ticketing agent webhook.
- ticketing_agent: FastAPI app that receives webhook payloads, validates/massages each ticket via a SourcePlugin (POC uses ServiceNowSource), obtains assignment groups from the assignment-handler, runs the AllocationEngine, and posts the chosen assignment back to the assignment-handler.
- mock_assignment_handler: FastAPI app exposing assignment groups via `GET /api/v1/assignment_groups` and accepting assignment mappings via `POST /api/v1/assignments`.

Responsibilities
- mock_source: simulate external ticket sources; posts sample ticket JSON to the agent.
- ticketing_agent:
  - Validate and normalize incoming tickets to `StandardTicket`.
  - Fetch assignment groups from `mock_assignment_handler` over HTTP.
  - Use `AllocationEngine.allocate()` to compute best group and rationale.
  - Notify assignment-handler with mapping and rationale.
- mock_assignment_handler: serve assignment group data and accept assignment mapping; meant to be swappable for a real handler backend.

Data model (POC)
- `StandardTicket`: ticket_id, ticket_number, title, description, category, priority, source, requester_location, urgency, impact, external_metadata.
- `AssignmentGroup` (JSON): group_id, name, location, capabilities, status, max_bandwidth, current_load, metrics.
- `AllocationDecision` (POC result): ticket_id, allocation (group_id/group_name), scores, rationale, confidence, timestamp.

Integration flow
1. `mock_source` posts a ticket to `ticketing_agent` at `/api/v1/webhooks/ticket`.
2. `ticketing_agent` validates and normalizes the ticket.
3. `ticketing_agent` fetches assignment groups from `mock_assignment_handler` (`GET /api/v1/assignment_groups`).
4. `AllocationEngine` selects the best group and produces an `AllocationDecision`.
5. `ticketing_agent` posts mapping to `mock_assignment_handler` (`POST /api/v1/assignments`) containing ticket_id, group_id, group_name, rationale, confidence.

Notes
- All plugin implementations (source or handler) are swappable; for POC they are simple in-process or mock HTTP services.
- The POC uses simple synchronous HTTP calls via `requests` wrapped with `asyncio.to_thread`; consider `httpx` for async clients in production.
