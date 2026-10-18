import pytest
from app.models import Hero

def test_create_hero(client):
    # Test tạo Hero thành công -> 201[cite: 44]
    response = client.post(
        "/api/v1/heroes", json={"name": "Deadpond", "secret_name": "Dive Wilson"}
    )
    assert response.status_code == 201
    assert response.json()["status"] == "active"
    assert "secret_name" not in response.json() # Đảm bảo secret_name không bị lộ ra ngoài

def test_read_hero_not_found(client):
    # Test tìm Hero không tồn tại -> 404[cite: 26]
    response = client.get("/api/v1/heroes/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Hero not found"}

@pytest.mark.parametrize("payload", [
    {}, # Thiếu name và secret_name
    {"name": "X"}, # Thiếu secret_name
    {"name": "X", "secret_name": "y", "age": -5} # Tuổi âm vi phạm ge=0
])
def test_create_hero_invalid(client, payload):
    # Test truyền dữ liệu sai -> 422
    assert client.post("/api/v1/heroes", json=payload).status_code == 422

def test_hero_unknown_team(client):
    # Test truyền team_id không tồn tại -> 400
    response = client.post(
        "/api/v1/heroes", json={"name": "A", "secret_name": "a", "team_id": 999}
    )
    assert response.status_code == 400