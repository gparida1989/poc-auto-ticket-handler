Start-Process uvicorn -ArgumentList "src.ticketing-agent.main:app --reload"
Start-Process uvicorn -ArgumentList "src.mock-source.main:app --reload"