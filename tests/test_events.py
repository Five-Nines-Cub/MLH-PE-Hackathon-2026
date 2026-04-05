import pytest

pytestmark = pytest.mark.system
from app.models import User

@pytest.fixture
def user(client):
    return client.post("/users", json={"username": "alice", "email": "alice@example.com"}).get_json()


@pytest.fixture
def url(client, user):
    return client.post("/urls", json={"user_id": user["id"], "original_url": "https://example.com"}).get_json()


def test_list_events_empty(client):
    res = client.get("/events")
    assert res.status_code == 200
    assert res.get_json() == []


def test_list_events_after_url_creation(client, url):  # url fixture creates the event
    events = client.get("/events").get_json()
    assert len(events) == 1
    assert events[0]["event_type"] == "created"
    assert "short_code" in events[0]["details"]
    assert "original_url" in events[0]["details"]


def test_create_event_valid(client, user, url):
    res = client.post("/events", json={
        "url_id": url["id"],
        "user_id": user["id"],
        "event_type": "click",
        "details": {"referrer": "https://google.com"},
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data["event_type"] == "click"
    assert data["url_id"] == url["id"]
    assert data["user_id"] == user["id"]
    assert data["details"]["referrer"] == "https://google.com"


def test_create_event_missing_url_id(client):
    res = client.post("/events", json={"event_type": "click"})
    assert res.status_code == 422
    assert "url_id" in res.get_json()["error"]


def test_create_event_missing_event_type(client, url):
    res = client.post("/events", json={"url_id": url["id"]})
    assert res.status_code == 422
    assert "event_type" in res.get_json()["error"]


def test_create_event_url_not_found(client):
    res = client.post("/events", json={"url_id": 999, "event_type": "click"})
    assert res.status_code == 404


def test_create_event_user_not_found(client, url):
    res = client.post("/events", json={"url_id": url["id"], "user_id": 999, "event_type": "click"})
    assert res.status_code == 404

def test_create_event_user_not_found_exception(client, url, monkeypatch):
    def raise_not_found(*_):
        raise User.DoesNotExist()

    monkeypatch.setattr("app.models.user.User.get_by_id", raise_not_found)
    res = client.post("/events", json={"url_id": url["id"], "user_id": 999, "event_type": "click"})
    assert res.status_code == 404

def test_create_event_without_user(client, url):
    res = client.post("/events", json={"url_id": url["id"], "event_type": "view"})
    assert res.status_code == 201
    assert res.get_json()["user_id"] is None


def test_filter_events_by_url_id(client, user, url):
    other_url = client.post("/urls", json={"user_id": user["id"], "original_url": "https://other.com"}).get_json()
    client.post("/events", json={"url_id": url["id"], "event_type": "click"})
    client.post("/events", json={"url_id": other_url["id"], "event_type": "click"})

    res = client.get(f"/events?url_id={url['id']}")
    assert res.status_code == 200
    events = res.get_json()
    assert all(e["url_id"] == url["id"] for e in events)


def test_filter_events_by_event_type(client, user, url):
    client.post("/events", json={"url_id": url["id"], "event_type": "click"})
    client.post("/events", json={"url_id": url["id"], "event_type": "view"})

    res = client.get("/events?event_type=click")
    assert res.status_code == 200
    events = res.get_json()
    assert all(e["event_type"] == "click" for e in events)


def test_filter_events_by_url_and_type(client, user, url):
    other_url = client.post("/urls", json={"user_id": user["id"], "original_url": "https://other.com"}).get_json()
    client.post("/events", json={"url_id": url["id"], "event_type": "click"})
    client.post("/events", json={"url_id": url["id"], "event_type": "view"})
    client.post("/events", json={"url_id": other_url["id"], "event_type": "click"})

    res = client.get(f"/events?url_id={url['id']}&event_type=click")
    assert res.status_code == 200
    events = res.get_json()
    assert len(events) == 1
    assert events[0]["url_id"] == url["id"]
    assert events[0]["event_type"] == "click"


def test_filter_events_by_user_id(client, user, url):
    other_user = client.post("/users", json={"username": "bob", "email": "bob@example.com"}).get_json()
    client.post("/events", json={"url_id": url["id"], "user_id": user["id"], "event_type": "click"})
    client.post("/events", json={"url_id": url["id"], "user_id": other_user["id"], "event_type": "click"})

    res = client.get(f"/events?user_id={user['id']}")
    assert res.status_code == 200
    events = res.get_json()
    assert all(e["user_id"] == user["id"] for e in events)


def test_filter_events_by_url_id_via_body(client, user, url):
    other_url = client.post("/urls", json={"user_id": user["id"], "original_url": "https://other.com"}).get_json()
    client.post("/events", json={"url_id": url["id"], "event_type": "click"})
    client.post("/events", json={"url_id": other_url["id"], "event_type": "click"})

    res = client.get("/events", json={"url_id": url["id"]})
    assert res.status_code == 200
    assert all(e["url_id"] == url["id"] for e in res.get_json())


def test_filter_events_by_event_type_via_body(client, url):
    client.post("/events", json={"url_id": url["id"], "event_type": "click"})
    client.post("/events", json={"url_id": url["id"], "event_type": "view"})

    res = client.get("/events", json={"event_type": "click"})
    assert res.status_code == 200
    assert all(e["event_type"] == "click" for e in res.get_json())


def test_filter_events_by_user_id_via_body(client, user, url):
    other_user = client.post("/users", json={"username": "bob", "email": "bob@example.com"}).get_json()
    client.post("/events", json={"url_id": url["id"], "user_id": user["id"], "event_type": "click"})
    client.post("/events", json={"url_id": url["id"], "user_id": other_user["id"], "event_type": "click"})

    res = client.get("/events", json={"user_id": user["id"]})
    assert res.status_code == 200
    assert all(e["user_id"] == user["id"] for e in res.get_json())


def test_redirect_fires_event(client, url):
    short_code = url["short_code"]
    client.get(f"/{short_code}", follow_redirects=False)

    events = client.get(f"/events?url_id={url['id']}&event_type=redirect").get_json()
    assert len(events) == 1
    assert events[0]["event_type"] == "redirect"


def test_create_event_details_string_rejected(client, url):
    res = client.post("/events", json={"url_id": url["id"], "event_type": "click", "details": "bad"})
    assert res.status_code == 422
    assert "details" in res.get_json()["error"]


def test_create_event_details_list_rejected(client, url):
    res = client.post("/events", json={"url_id": url["id"], "event_type": "click", "details": ["bad"]})
    assert res.status_code == 422
    assert "details" in res.get_json()["error"]


def test_create_event_without_details(client, user, url):
    res = client.post("/events", json={"url_id": url["id"], "user_id": user["id"], "event_type": "click"})
    assert res.status_code == 201
    assert res.get_json()["details"] == {}
