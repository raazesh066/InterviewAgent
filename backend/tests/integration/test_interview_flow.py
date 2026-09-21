"""Integration tests for the end-to-end interview lifecycle (start -> answer -> score)."""
import pytest

pytestmark = pytest.mark.asyncio


async def _register_and_login(client, email="candidate@example.com"):
    await client.post(
        "/api/v1/auth/register", json={"email": email, "password": "Str0ngPass!123", "full_name": "Jane Doe"}
    )
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": "Str0ngPass!123"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_start_interview_returns_first_question(client):
    headers = await _register_and_login(client)
    payload = {
        "candidate_name": "Jane Doe",
        "target_company": "Microsoft",
        "category": "Full Stack Engineer",
        "interview_type": "Mixed",
        "duration_minutes": 45,
        "years_of_experience": 6.5,
        "skills": [
            {"name": ".NET Core", "level": "Expert"},
            {"name": "Azure", "level": "Advanced"},
        ],
    }
    response = await client.post("/api/v1/start-interview", json=payload, headers=headers)
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "in_progress"
    assert body["first_question"]["text"].startswith("Fake generated question")
    return body, headers


async def test_submit_answer_and_get_score(client):
    body, headers = await test_start_interview_returns_first_question(client)
    interview_id = body["interview_id"]
    question_id = body["first_question"]["question_id"]

    answer_payload = {
        "interview_id": interview_id,
        "question_id": question_id,
        "answer_text": "We used a system-assigned managed identity to authenticate to Key Vault.",
        "time_taken_seconds": 90,
    }
    submit_response = await client.post("/api/v1/submit-answer", json=answer_payload, headers=headers)
    assert submit_response.status_code == 200
    submit_body = submit_response.json()
    assert submit_body["evaluation"]["technical_score"] == 8
    assert submit_body["difficulty_adjustment"] == "increase"

    score_response = await client.get(
        "/api/v1/interview-score", params={"interview_id": interview_id}, headers=headers
    )
    assert score_response.status_code == 200
    score_body = score_response.json()
    assert score_body["grade"] in {"Outstanding", "Strong Hire", "Hire", "Borderline", "Needs Improvement"}
    assert score_body["final_rating"] > 0


async def test_next_question_returns_followup_then_new_question(client):
    body, headers = await test_start_interview_returns_first_question(client)
    interview_id = body["interview_id"]
    question_id = body["first_question"]["question_id"]

    await client.post(
        "/api/v1/submit-answer",
        json={
            "interview_id": interview_id,
            "question_id": question_id,
            "answer_text": "Some answer",
            "time_taken_seconds": 60,
        },
        headers=headers,
    )

    next_q_response = await client.get(
        "/api/v1/next-question", params={"interview_id": interview_id}, headers=headers
    )
    assert next_q_response.status_code == 200
    next_q_body = next_q_response.json()
    assert next_q_body["is_followup"] is True
    assert "rotate secrets" in next_q_body["text"]
