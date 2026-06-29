from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    original_activities = deepcopy(activities)
    yield
    activities.clear()
    activities.update(deepcopy(original_activities))


def test_root_redirects_to_static_index(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_catalog(client):
    response = client.get("/activities")

    assert response.status_code == 200
    body = response.json()
    assert "Chess Club" in body
    assert body["Chess Club"]["participants"]


def test_signup_adds_participant(client):
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "new.student@mergington.edu"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Signed up new.student@mergington.edu for Chess Club"
    assert "new.student@mergington.edu" in activities["Chess Club"]["participants"]


def test_signup_rejects_duplicate_participant(client):
    email = activities["Chess Club"]["participants"][0]

    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_rejects_full_activity(client):
    activity = activities["Chess Club"]
    activity["participants"] = [f"student{i}@mergington.edu" for i in range(activity["max_participants"])]

    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "overflow@mergington.edu"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"


def test_signup_rejects_unknown_activity(client):
    response = client.post(
        "/activities/Robotics Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client):
    email = activities["Chess Club"]["participants"][0]

    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json()["message"] == f"Unregistered {email} from Chess Club"
    assert email not in activities["Chess Club"]["participants"]


def test_unregister_rejects_missing_participant(client):
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "missing@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_rejects_unknown_activity(client):
    response = client.delete(
        "/activities/Robotics Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"