import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi import FastAPI, Request, HTTPException
from src.agent.core import TicketAllocationAgent
from src.plugins.source_plugin import SourcePlugin
from src.plugins.handler_plugin import HandlerPlugin
from src.allocation_engine.engine import AllocationEngine

# Placeholder: You will need to implement actual plugins
# In a real app, these would be concrete implementations like ServiceNowSource()
source_plugins = {"servicenow": None} 
handler_plugins = {"servicenow": None}
allocation_engine = AllocationEngine()

agent = TicketAllocationAgent(source_plugins, handler_plugins, allocation_engine)

app = FastAPI()

@app.post("/api/v1/webhooks/ticket")
async def webhook_ticket(request: Request):  
    payload = await request.json()
    # source_id should be extracted from headers or payload
    source_id = request.headers.get("X-Source-ID", "servicenow")
    try:
        result = await agent.process_webhook(payload, source_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/health")
def health():
    return {"status": "ok"}
