def test_list_events_empty(client):
    res = client.get("/events")
    assert res.status_code == 200
    assert res.get_json() == []


def test_list_events_after_url_creation(client):
    user = client.post("/users", json={"username": "alice", "email": "alice@example.com"}).get_json()
    client.post("/urls", json={"user_id": user["id"], "original_url": "https://example.com"})

    res = client.get("/events")
    assert res.status_code == 200
    events = res.get_json()
    assert len(events) == 1
    assert events[0]["event_type"] == "created"
    assert "short_code" in events[0]["details"]
    assert "original_url" in events[0]["details"]
