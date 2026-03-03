Start-Process uvicorn -ArgumentList "ticketing_agent.main:app --reload --port 8000" -WorkingDirectory "src"
Start-Process uvicorn -ArgumentList "mock_source.main:app --reload --port 8001" -WorkingDirectory "src"
Start-Process uvicorn -ArgumentList "mock_assignment_handler.main:app --reload --port 8002" -WorkingDirectory "src"