def test_register_success(client):
    response = client.post("/auth/register", json={
        "full_name": "Ankitha", "email": "ankitha@example.com", "password": "Test12345",
    })
    assert response.status_code == 201
    body = response.json()
    assert body["user"]["email"] == "ankitha@example.com"
    assert "password" not in body["user"]


def test_register_missing_full_name_returns_422(client):
    response = client.post("/auth/register", json={
        "email": "ankitha@example.com", "password": "Test12345",
    })
    assert response.status_code == 422


def test_register_duplicate_email_returns_409(client):
    payload = {"full_name": "Ankitha", "email": "dupe@example.com", "password": "Test12345"}
    client.post("/auth/register", json=payload)
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 409


def test_login_success(client):
    client.post("/auth/register", json={
        "full_name": "Ankitha", "email": "login@example.com", "password": "Test12345",
    })
    response = client.post("/auth/login", json={"email": "login@example.com", "password": "Test12345"})
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_wrong_password_returns_401(client):
    client.post("/auth/register", json={
        "full_name": "Ankitha", "email": "wrongpw@example.com", "password": "Test12345",
    })
    response = client.post("/auth/login", json={"email": "wrongpw@example.com", "password": "WrongPass1"})
    assert response.status_code == 401


def test_protected_endpoint_requires_token(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_protected_endpoint_with_token(client):
    client.post("/auth/register", json={
        "full_name": "Ankitha", "email": "protected@example.com", "password": "Test12345",
    })
    login = client.post("/auth/login", json={"email": "protected@example.com", "password": "Test12345"})
    token = login.json()["access_token"]
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "protected@example.com"
