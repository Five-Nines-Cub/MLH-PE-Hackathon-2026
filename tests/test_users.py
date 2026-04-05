import pytest

pytestmark = pytest.mark.system


def test_list_users_empty(client):
    res = client.get("/users")
    assert res.status_code == 200
    assert res.get_json() == []


def test_create_user_valid(client):
    res = client.post("/users", json={"username": "alice", "email": "alice@example.com"})
    assert res.status_code == 201
    data = res.get_json()
    assert data["username"] == "alice"
    assert data["email"] == "alice@example.com"
    assert "id" in data
    assert "created_at" in data


def test_create_user_missing_username(client):
    res = client.post("/users", json={"email": "alice@example.com"})
    assert res.status_code == 422
    assert "username" in res.get_json()["error"]


def test_create_user_missing_email(client):
    res = client.post("/users", json={"username": "alice"})
    assert res.status_code == 422
    assert "email" in res.get_json()["error"]


def test_create_user_non_string_username(client):
    res = client.post("/users", json={"username": 123, "email": "alice@example.com"})
    assert res.status_code == 422
    assert "username" in res.get_json()["error"]


def test_get_user_not_found(client):
    res = client.get("/users/999")
    assert res.status_code == 404


def test_get_user_found(client):
    created = client.post("/users", json={"username": "bob", "email": "bob@example.com"})
    user_id = created.get_json()["id"]

    res = client.get(f"/users/{user_id}")
    assert res.status_code == 200
    assert res.get_json()["username"] == "bob"


def test_update_user(client):
    created = client.post("/users", json={"username": "carol", "email": "carol@example.com"})
    user_id = created.get_json()["id"]

    res = client.put(f"/users/{user_id}", json={"username": "carol_updated"})
    assert res.status_code == 200
    assert res.get_json()["username"] == "carol_updated"


def test_create_user_boolean_username(client):
    res = client.post("/users", json={"username": True, "email": "alice@example.com"})
    assert res.status_code == 422
    assert "username" in res.get_json()["error"]


def test_create_user_duplicate(client):
    client.post("/users", json={"username": "alice", "email": "alice@example.com"})
    res = client.post("/users", json={"username": "alice", "email": "alice@example.com"})
    assert res.status_code == 409


def test_update_user_not_found(client):
    res = client.put("/users/999", json={"username": "ghost"})
    assert res.status_code == 404


def test_list_users_pagination(client):
    for i in range(5):
        client.post("/users", json={"username": f"user{i}", "email": f"user{i}@example.com"})

    res = client.get("/users?page=1&per_page=3")
    assert res.status_code == 200
    assert len(res.get_json()) == 3


def test_delete_user(client):
    created = client.post("/users", json={"username": "dave", "email": "dave@example.com"})
    user_id = created.get_json()["id"]

    res = client.delete(f"/users/{user_id}")
    assert res.status_code == 204

    assert client.get(f"/users/{user_id}").status_code == 404


def test_delete_user_not_found(client):
    res = client.delete("/users/999")
    assert res.status_code == 204


def test_bulk_import(client):
    from io import BytesIO

    csv_data = "id,username,email,created_at\n1,alice,alice@example.com,2025-01-01 00:00:00\n2,bob,bob@example.com,2025-01-01 00:00:00\n"
    res = client.post(
        "/users/bulk",
        data={"file": (BytesIO(csv_data.encode()), "users.csv")},
        content_type="multipart/form-data",
    )
    assert res.status_code == 201
    assert res.get_json()["imported"] == 2
