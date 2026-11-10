def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_version_is_exposed(client):
    response = client.get("/version")
    assert response.status_code == 200
    assert "version" in response.json()


def test_index_page_renders(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Полка игр" in response.text


def test_add_game_and_list(client):
    created = client.post("/games", json={"title": "Hades", "platform": "PC"})
    assert created.status_code == 201
    assert created.json() == {
        "id": 1,
        "title": "Hades",
        "platform": "PC",
        "status": "backlog",
        "rating": None,
    }

    listing = client.get("/games")
    assert listing.status_code == 200
    assert [game["title"] for game in listing.json()] == ["Hades"]


def test_game_can_be_created_with_rating(client):
    created = client.post("/games", json={"title": "Hades", "platform": "PC", "rating": 9})
    assert created.status_code == 201
    assert created.json()["rating"] == 9


def test_rating_out_of_range_is_rejected(client):
    assert (
        client.post("/games", json={"title": "Hades", "platform": "PC", "rating": 11}).status_code
        == 422
    )
    assert (
        client.post("/games", json={"title": "Hades", "platform": "PC", "rating": 0}).status_code
        == 422
    )


def test_patch_updates_rating(client):
    game_id = client.post("/games", json={"title": "Hades", "platform": "PC"}).json()["id"]

    updated = client.patch(f"/games/{game_id}", json={"rating": 8})
    assert updated.status_code == 200
    assert updated.json()["rating"] == 8


def test_list_filters_by_status(client):
    client.post("/games", json={"title": "Hades", "platform": "PC"})
    client.post("/games", json={"title": "Celeste", "platform": "Switch", "status": "completed"})

    completed = client.get("/games", params={"status": "completed"})
    assert [game["title"] for game in completed.json()] == ["Celeste"]


def test_patch_updates_status(client):
    game_id = client.post("/games", json={"title": "Hades", "platform": "PC"}).json()["id"]

    updated = client.patch(f"/games/{game_id}", json={"status": "playing"})
    assert updated.status_code == 200
    assert updated.json()["status"] == "playing"


def test_patch_unknown_game_returns_404(client):
    response = client.patch("/games/999", json={"status": "playing"})
    assert response.status_code == 404


def test_delete_removes_game(client):
    game_id = client.post("/games", json={"title": "Hades", "platform": "PC"}).json()["id"]

    assert client.delete(f"/games/{game_id}").status_code == 204
    assert client.get("/games").json() == []


def test_delete_unknown_game_returns_404(client):
    assert client.delete("/games/999").status_code == 404


def test_unknown_status_is_rejected(client):
    response = client.post("/games", json={"title": "Hades", "platform": "PC", "status": "dropped"})
    assert response.status_code == 422


def test_empty_title_is_rejected(client):
    response = client.post("/games", json={"title": "", "platform": "PC"})
    assert response.status_code == 422
