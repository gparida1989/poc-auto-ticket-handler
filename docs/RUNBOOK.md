# Runbook / README — How to run the POC and message flow

## Quick start
- Prerequisites:
  - Python 3.11 or newer (the project was developed on Python 3.13; 3.11+ recommended).
  - Git (optional) and a virtual environment tool (venv, virtualenv, or similar).

- Install dependencies: `pip install -r src/requirements.txt` (recommended inside a venv).
- Start all services on Windows PowerShell:

```powershell
.\start-app.ps1
```

This launches three Uvicorn processes (by default):
- `ticketing_agent` on http://127.0.0.1:8000
- `mock_source` on http://127.0.0.1:8001
- `mock_assignment_handler` on http://127.0.0.1:8002

You can also start individual apps from the `src` directory:

```powershell
cd src
uvicorn ticketing_agent.main:app --reload --port 8000
uvicorn mock_source.main:app --reload --port 8001
uvicorn mock_assignment_handler.main:app --reload --port 8002
```

## Endpoints
- ticketing agent
  - POST /api/v1/webhooks/ticket — receives ticket payloads from sources
  - GET /health — health check
- mock assignment handler
  - GET /api/v1/assignment_groups — returns JSON array of available assignment groups
  - POST /api/v1/assignments — receives mapping {ticket_id, group_id, group_name, rationale, confidence}
- mock source
  - Posts tickets periodically to the ticketing agent webhook (no public endpoint)

## Message examples
- Webhook ticket payload (example) — sent by `mock_source` to `ticketing_agent`:

```
{
  "ticket_id": "TICKET-026",
  "ticket_number": "INC0000026",
  "title": "Coupon code not working",
  "description": "My coupon code is not working.",
  "category": "billing",
  "priority": "medium",
  "source": "email",
  "requester_location": {"country": "USA", "city": "Dallas"},
  "urgency": "medium",
  "impact": "low",
  "external_metadata": {"department": "Marketing", "account_id": "ACC026"}
}
```

- Assignment mapping (agent -> assignment handler):

```
{
  "ticket_id": "TICKET-026",
  "group_id": "L1-Support",
  "group_name": "L1 Support",
  "rationale": "Best match for network expertise in Eastern timezone",
  "confidence": 0.87
}
```

- Assignment handler response (JSON):

```
{"status":"ok","message":"Successfully mapped ticket TICKET-026 to L1-Support"}
```

## Logs to watch
- mock source: logs
  - `Mock source is starting up and will post tickets to http://localhost:8000/api/v1/webhooks/ticket`
  - `Mock source started`
  - `Posted ticket <id> — response <status>`
- ticketing agent: logs
  - `Ticketing agent started and ready to receive webhooks`
  - `Received webhook payload: ...`
  - `Assignment-handler response: status=..., body=...` (shows handler reply)
- mock assignment handler: logs
  - `Mock assignment handler started and serving assignment groups from <path>`
  - `Received assignment mapping: {...}`
  - `Responding with: {...}`

## Notes and next improvements
- The POC uses synchronous `requests` in background threads. Replace with `httpx` for async HTTP if you need true async I/O.
- Handlers and sources are swappable: you can implement real ServiceNow connectors or a real assignments backend and point `handler_base_url` in `ticketing_agent.main`.
- Consider adding retries/backoff and error handling around the assignment-post to ensure idempotency and reliability.
- Recommended developer workflow:
  1. Create a venv: `python -m venv .venv`
  2. Activate it (Windows PowerShell): `. .venv\Scripts\Activate.ps1`
  3. Install requirements: `pip install -r src/requirements.txt`
  4. Start services: `.\start-app.ps1` or start individual services from `src`.
