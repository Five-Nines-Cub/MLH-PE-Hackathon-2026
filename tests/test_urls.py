import pytest

pytestmark = pytest.mark.system


@pytest.fixture
def user(client):
    res = client.post("/users", json={"username": "alice", "email": "alice@example.com"})
    return res.get_json()


def test_list_urls_empty(client):
    res = client.get("/urls")
    assert res.status_code == 200
    assert res.get_json() == []


def test_create_url_missing_original_url(client, user):
    res = client.post("/urls", json={"user_id": user["id"]})
    assert res.status_code == 422
    assert "original_url" in res.get_json()["error"]


def test_create_url_missing_user_id(client):
    res = client.post("/urls", json={"original_url": "https://example.com"})
    assert res.status_code == 422
    assert "user_id" in res.get_json()["error"]


def test_create_url_user_not_found(client):
    res = client.post("/urls", json={"user_id": 999, "original_url": "https://example.com"})
    assert res.status_code == 404


def test_create_url_valid(client, user):
    res = client.post("/urls", json={
        "user_id": user["id"],
        "original_url": "https://example.com",
        "title": "Example",
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data["original_url"] == "https://example.com"
    assert data["title"] == "Example"
    assert data["user_id"] == user["id"]
    assert len(data["short_code"]) == 6
    assert data["is_active"] is True


def test_create_url_fires_event(client, user):
    client.post("/urls", json={"user_id": user["id"], "original_url": "https://example.com"})
    events = client.get("/events").get_json()
    assert len(events) == 1
    assert events[0]["event_type"] == "created"


def test_get_url_not_found(client):
    res = client.get("/urls/999")
    assert res.status_code == 404


def test_get_url_found(client, user):
    created = client.post("/urls", json={"user_id": user["id"], "original_url": "https://example.com"})
    url_id = created.get_json()["id"]

    res = client.get(f"/urls/{url_id}")
    assert res.status_code == 200
    assert res.get_json()["id"] == url_id


def test_list_urls_filter_by_user(client, user):
    other = client.post("/users", json={"username": "bob", "email": "bob@example.com"}).get_json()

    client.post("/urls", json={"user_id": user["id"], "original_url": "https://alice.com"})
    client.post("/urls", json={"user_id": other["id"], "original_url": "https://bob.com"})

    res = client.get(f"/urls?user_id={user['id']}")
    assert res.status_code == 200
    urls = res.get_json()
    assert len(urls) == 1
    assert urls[0]["user_id"] == user["id"]


def test_update_url(client, user):
    created = client.post("/urls", json={"user_id": user["id"], "original_url": "https://example.com"})
    url_id = created.get_json()["id"]

    res = client.put(f"/urls/{url_id}", json={"title": "Updated", "is_active": False})
    assert res.status_code == 200
    data = res.get_json()
    assert data["title"] == "Updated"
    assert data["is_active"] is False


def test_update_url_not_found(client):
    res = client.put("/urls/999", json={"title": "Ghost"})
    assert res.status_code == 404


def test_list_urls_no_filter_returns_all(client, user):
    client.post("/urls", json={"user_id": user["id"], "original_url": "https://one.com"})
    client.post("/urls", json={"user_id": user["id"], "original_url": "https://two.com"})

    res = client.get("/urls")
    assert res.status_code == 200
    assert len(res.get_json()) == 2
