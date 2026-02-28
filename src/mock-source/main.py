from fastapi import FastAPI, HTTPException
import requests
import json
import random
import threading
import time

app = FastAPI()

TICKETS_FILE = "src/mock-source/tickets.json"
WEBHOOK_URL = "http://localhost:8000/api/v1/webhooks/ticket"

def get_tickets():
    try:
        with open(TICKETS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def post_ticket():
    tickets = get_tickets()
    if not tickets:
        return

    while True:
        ticket = random.choice(tickets)
        try:
            requests.post(WEBHOOK_URL, json=ticket)
            time.sleep(10)
        except requests.exceptions.RequestException as e:
            print(f"Error posting ticket: {e}")
            time.sleep(10)


@app.on_event("startup")
async def startup_event():
    threading.Thread(target=post_ticket, daemon=True).start()
