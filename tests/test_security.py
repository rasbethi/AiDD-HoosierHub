from src.models.models import db, User


def _create_student():
    user = User(name="Secure User", email="secure@iu.edu", role="student")
    user.set_password("Password123!")
    db.session.add(user)
    db.session.commit()
    return user


def test_search_with_injection_string(app, client):
    with app.app_context():
        _create_student()
    client.post(
        "/auth/login",
        data={"email": "secure@iu.edu", "password": "Password123!"},
        follow_redirects=True,
    )

    response = client.get("/resources/?search=' OR 1=1;--", follow_redirects=True)
    assert response.status_code == 200
    assert b"Resources" in response.data or b"Hoosier Hub" in response.data

