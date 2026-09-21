"""Integration tests for the auth API (register/login/refresh) against an in-memory DB."""
import uuid

import pytest

pytestmark = pytest.mark.asyncio

from app.core.security import create_access_token


async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_register_login_refresh_flow(client):
    register_payload = {"email": "candidate@example.com", "password": "Str0ngPass!123", "full_name": "Jane Doe"}
    register_response = await client.post("/api/v1/auth/register", json=register_payload)
    assert register_response.status_code == 201
    body = register_response.json()
    assert body["email"] == "candidate@example.com"
    assert body["role"] == "candidate"

    login_response = await client.post(
        "/api/v1/auth/login", json={"email": "candidate@example.com", "password": "Str0ngPass!123"}
    )
    assert login_response.status_code == 200
    tokens = login_response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    refresh_response = await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refresh_response.status_code == 200
    assert "access_token" in refresh_response.json()


async def test_login_with_wrong_password_fails(client):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "bob@example.com", "password": "CorrectPass123", "full_name": "Bob"},
    )
    response = await client.post("/api/v1/auth/login", json={"email": "bob@example.com", "password": "WrongPass"})
    assert response.status_code == 401


async def test_stale_access_token_is_rejected(client):
    token = create_access_token(str(uuid.uuid4()), "candidate")

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Session is no longer valid. Please sign in again."


async def test_duplicate_registration_conflicts(client):
    payload = {"email": "dupe@example.com", "password": "Str0ngPass!123", "full_name": "Dupe User"}
    first = await client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201
    second = await client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 409


async def test_get_and_update_candidate_profile(client):
    email = "profile@example.com"
    password = "Str0ngPass!123"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Profile User"},
    )
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    initial = await client.get("/api/v1/auth/me", headers=headers)
    assert initial.status_code == 200
    assert initial.json()["full_name"] == "Profile User"
    assert initial.json()["target_role"] == "Software Engineer"

    payload = {
        "headline": "Cloud engineer building reliable platforms",
        "target_role": "Azure Architect",
        "years_of_experience": 7.5,
        "location": "Seattle, WA",
        "bio": "I design secure distributed systems and mentor engineering teams.",
        "skills": ["Azure", "System Design", "Python"],
        "preferred_company": "Microsoft",
        "preferred_interview_type": "Mixed",
    }
    updated = await client.put("/api/v1/auth/me", json=payload, headers=headers)
    assert updated.status_code == 200
    assert updated.json()["skills"] == payload["skills"]
    assert updated.json()["years_of_experience"] == 7.5
    assert updated.json()["total_interviews"] == 0
