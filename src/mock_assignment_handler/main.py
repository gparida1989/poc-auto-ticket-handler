from fastapi import FastAPI, HTTPException
from pathlib import Path
import json
import logging

app = FastAPI()
logging.basicConfig(level=logging.INFO)

DATA_FILE = Path(__file__).resolve().parent / "assignment_groups.json"


@app.get("/api/v1/assignment_groups")
def get_assignment_groups():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {"assignment_groups": data}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="assignment_groups.json not found")


@app.post("/api/v1/assignments")
def post_assignment(mapping: dict):
    # mapping example: {"ticket_id": "...", "group_id": "...", "group_name": "..."}
    logging.info("Received assignment mapping: %s", mapping)
    resp = {"status": "ok", "message": f"Successfully mapped ticket {mapping.get('ticket_id')} to {mapping.get('group_id')}"}
    logging.info("Responding with: %s", resp)
    return resp


@app.on_event("startup")
def startup_event():
    logging.info("Mock assignment handler started and serving assignment groups from %s", DATA_FILE)
