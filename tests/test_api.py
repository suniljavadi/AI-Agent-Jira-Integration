def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200 and response.json()["mode"] == "mock"


def test_api_crud_and_auth(client):
    issue = client.post("/api/v1/issues", json={"summary": "Investigate database performance", "issue_type": "Task"})
    assert issue.status_code == 200
    key = issue.json()["key"]
    assert client.get(f"/api/v1/issues/{key}").status_code == 200
    assert client.get("/api/v1/issues/ENG-999").status_code == 404
    assert client.get("/api/v1/issues/ENG-1", headers={"Authorization": "Bearer wrong"}).status_code == 401


def test_chat_approval_round_trip(client):
    proposal = client.post("/api/v1/chat", json={"message": "Create a high priority bug for payment timeout"}).json()
    assert proposal["requires_approval"]
    result = client.post("/api/v1/chat", json={"message": "Approve", "conversation_id": proposal["conversation_id"], "approve": True}).json()
    assert result["data"]["key"] == "ENG-1"
