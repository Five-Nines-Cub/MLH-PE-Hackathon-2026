import pytest


@pytest.fixture
def url(client):
    user = client.post("/users", json={"username": "alice", "email": "alice@example.com"}).get_json()
    res = client.post("/urls", json={"user_id": user["id"], "original_url": "https://example.com"})
    return res.get_json()


def test_redirect_valid_short_code(client, url):
    res = client.get(f"/{url['short_code']}")
    assert res.status_code == 301
    assert res.headers["Location"] == "https://example.com"


def test_redirect_inactive_url(client, url):
    client.put(f"/urls/{url['id']}", json={"is_active": False})
    res = client.get(f"/{url['short_code']}")
    assert res.status_code == 404


def test_redirect_unknown_short_code(client):
    res = client.get("/doesnotexist")
    assert res.status_code == 404
