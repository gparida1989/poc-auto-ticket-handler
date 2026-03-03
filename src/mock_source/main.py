from fastapi import FastAPI
import requests
import json
import random
import threading
import time
import logging
from pathlib import Path

app = FastAPI()

# Resolve tickets file relative to this module so it works regardless of working directory
TICKETS_FILE = str(Path(__file__).resolve().parent / "tickets.json")
WEBHOOK_URL = "http://localhost:8000/api/v1/webhooks/ticket"
logging.basicConfig(level=logging.INFO)

def get_tickets():
    try:
        with open(TICKETS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def post_ticket():
    tickets = get_tickets()
    if not tickets:
        logging.warning("No tickets found in %s — mock poster will not run", TICKETS_FILE)
        return

    logging.info("Mock poster started, posting to %s", WEBHOOK_URL)
    while True:
        ticket = random.choice(tickets)
        try:
            resp = requests.post(WEBHOOK_URL, json=ticket)
            logging.info("Posted ticket %s — response %s", ticket.get('ticket_id', '<nil>'), resp.status_code)
            time.sleep(10)
        except requests.exceptions.RequestException as e:
            logging.error("Error posting ticket: %s", e)
            time.sleep(10)


@app.on_event("startup")
async def startup_event():
    threading.Thread(target=post_ticket, daemon=True).start()
