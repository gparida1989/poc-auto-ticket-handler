import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi import FastAPI, Request, HTTPException
from src.agent.core import TicketAllocationAgent
from src.plugins.source_plugin import SourcePlugin
from src.plugins.handler_plugin import HandlerPlugin
from src.allocation_engine.engine import AllocationEngine
import logging

from src.plugins.servicenow_source import ServiceNowSource
from src.plugins.servicenow_handler import ServiceNowHandler

# Placeholder: You will need to implement actual plugins
logging.basicConfig(level=logging.INFO)
# In a real app, these would be concrete implementations like ServiceNowSource()
source_plugins = {"servicenow": ServiceNowSource()} 
handler_plugins = {"servicenow": ServiceNowHandler()}
allocation_engine = AllocationEngine()

agent = TicketAllocationAgent(source_plugins, handler_plugins, allocation_engine)

app = FastAPI()

@app.post("/api/v1/webhooks/ticket")
async def webhook_ticket(request: Request):  
    payload = await request.json()
    logging.info("Received webhook payload: %s", payload)
    # source_id should be extracted from headers or payload
    source_id = request.headers.get("X-Source-ID", "servicenow")
    try:
        # result = await agent.process_webhook(payload, source_id)
        # return result
        return {"status": "ok"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error("Error processing webhook: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/health")
def health():
    return {"status": "ok"}
