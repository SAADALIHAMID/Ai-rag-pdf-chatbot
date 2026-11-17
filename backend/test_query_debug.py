import json
import traceback
import sys

try:
    from app.main import app
    from fastapi.testclient import TestClient
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post("/api/query", json={"query": "What is Quantum Aegis?"})
    print("STATUS_CODE:", resp.status_code)
    print("HEADERS:", dict(resp.headers))
    print("TEXT:", resp.text[:1000])
except Exception as e:
    traceback.print_exc()
