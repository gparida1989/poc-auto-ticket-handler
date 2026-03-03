from fastapi import FastAPI, Request, HTTPException
from .agent.core import TicketAllocationAgent
from .allocation_engine.engine import AllocationEngine
import logging
from .plugins.servicenow_source import ServiceNowSource

# Placeholder: You will need to implement actual plugins
logging.basicConfig(level=logging.INFO)
# In a real app, these would be concrete implementations like ServiceNowSource()
source_plugins = {"servicenow": ServiceNowSource()}
allocation_engine = AllocationEngine()

# Handler service base URL (mock assignment handler)
handler_base_url = "http://localhost:8002"

agent = TicketAllocationAgent(source_plugins, allocation_engine, handler_base_url=handler_base_url)

app = FastAPI()


@app.on_event("startup")
def startup_event():
    logging.info("Ticketing agent started and ready to receive webhooks")

@app.post("/api/v1/webhooks/ticket")
async def webhook_ticket(request: Request):  
    payload = await request.json()
    logging.info("Received webhook payload: %s", payload)
    # source_id should be extracted from headers or payload
    source_id = request.headers.get("X-Source-ID", "servicenow")
    try:
        result = await agent.process_webhook(payload, source_id)
        return result
        # return {"status": "ok"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error("Error processing webhook: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/health")
def health():
    return {"status": "ok"}
