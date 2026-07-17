import os
import sys
import json
from fastapi.testclient import TestClient

# Mock LLM before importing app
import app.llm
def mock_generate_test_cases(text):
    return {
        "status": "ok",
        "raw_response": "mock",
        "parsed": [
            {"title": "Mock Test", "steps": ["1", "2"], "expected_result": "Success"}
        ]
    }
app.llm.generate_test_cases = mock_generate_test_cases

from app.main import app as fastapi_app
from app.database import engine, Base

client = TestClient(fastapi_app)

def run():
    # 1. Reset DB
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    from app.nosql import db as tinydb
    tinydb.drop_tables()
    
    output = []
    
    # 2. Ingest v1
    output.append("== 1. INGESTING V1 ==")
    with open("data/ct200_manual.pdf", "rb") as f:
        res = client.post("/ingest", files={"file": ("ct200_manual.pdf", f, "application/pdf")})
    output.append(f"Status: {res.status_code}, Response: {res.json()}")
    
    # 3. Find Node
    output.append("\n== 2. SEARCHING FOR BATTERY LIFE ==")
    res = client.get("/search?q=battery life")
    nodes = res.json()
    node = nodes[0] if nodes else None
    output.append(f"Found node ID: {node['id']}, Heading: {node['heading']}, Logical ID: {node['logical_node_id']}")
    
    # 4. Create Selection
    output.append("\n== 3. CREATING SELECTION ==")
    res = client.post("/selections", json={"name": "Cuff Tests", "node_ids": [node["id"]]})
    sel = res.json()
    output.append(f"Selection ID: {sel['id']}")
    
    # 5. Generate Test Cases
    output.append("\n== 4. GENERATING TEST CASES (Mocked) ==")
    res = client.post(f"/generate?selection_id={sel['id']}")
    gen = res.json()
    output.append(f"Generation Status: {gen['generation_status']}, Parsed count: {len(gen['parsed_test_cases'])}")
    
    # 6. Check Test Cases (Before V2)
    output.append("\n== 5. CHECKING STALENESS (V1) ==")
    res = client.get(f"/test-cases?selection_id={sel['id']}")
    tcs = res.json()
    output.append(f"Is Stale: {tcs[0]['staleness']['is_stale']}")
    
    # 7. Ingest v2
    output.append("\n== 6. INGESTING V2 ==")
    with open("data/ct200_manual_v2.pdf", "rb") as f:
        res = client.post("/ingest", files={"file": ("ct200_manual_v2.pdf", f, "application/pdf")})
    output.append(f"Status: {res.status_code}, Response: {res.json()}")
    
    # 8. Check Diff
    output.append("\n== 7. CHECKING NODE DIFF ==")
    res = client.get(f"/search?q=battery life")
    new_nodes = res.json()
    # Find the matching node by logical_node_id
    new_node = next((n for n in new_nodes if n["logical_node_id"] == node["logical_node_id"]), new_nodes[0])
    res = client.get(f"/nodes/{new_node['id']}/diff")
    output.append(f"Diff via API: \n{res.json()['diff']}")
    
    # 9. Check Test Cases Staleness (After V2)
    output.append("\n== 8. CHECKING STALENESS (V2) ==")
    res = client.get(f"/test-cases?selection_id={sel['id']}")
    tcs = res.json()
    output.append(f"Is Stale: {tcs[0]['staleness']['is_stale']}")
    diff_details = tcs[0]['staleness']['details'][0]
    output.append(f"Node stale flag: {diff_details['stale']}")
    output.append(f"Diff via staleness check: \n{diff_details['diff']}")
    
    artifact_path = "C:/Users/huesh/.gemini/antigravity/brain/358daff4-67f5-4434-ae22-5b5cffa8f634/walkthrough.md"
    os.makedirs(os.path.dirname(artifact_path), exist_ok=True)
    with open(artifact_path, "w", encoding="utf-8") as f:
        f.write("# API Flow E2E Walkthrough\n\n")
        f.write("This document demonstrates the full lifecycle from document ingestion to testing and staleness detection.\n\n")
        f.write("```text\n")
        f.write("\n".join(output))
        f.write("\n```\n")
        
    print("Walkthrough generated.")

if __name__ == '__main__':
    run()
