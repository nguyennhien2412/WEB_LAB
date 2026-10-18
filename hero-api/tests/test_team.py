import pytest
from app.models import Team

def test_create_team_duplicate(client):
    # Test tạo team thành công (201) và tạo trùng tên (409)
    body = {"name": "Avengers", "headquarters": "New York"}
    assert client.post("/api/v1/teams", json=body).status_code == 201
    assert client.post("/api/v1/teams", json=body).status_code == 409

def test_list_team_heroes_not_found(client):
    # Test lấy danh sách hero của một team không tồn tại (404)
    assert client.get("/api/v1/teams/999/heroes").status_code == 404