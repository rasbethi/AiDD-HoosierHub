def test_register_login_profile_access(app, client):
    register_resp = client.post(
        "/auth/register",
        data={
            "name": "Test Student",
            "email": "tester@iu.edu",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
        follow_redirects=True,
    )
    assert b"Account created successfully" in register_resp.data

    login_resp = client.post(
        "/auth/login",
        data={
            "email": "tester@iu.edu",
            "password": "Password123!",
        },
        follow_redirects=True,
    )
    assert b"Login successful" in login_resp.data

    profile_resp = client.get("/auth/profile")
    assert profile_resp.status_code == 200

