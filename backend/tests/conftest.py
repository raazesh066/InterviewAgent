"""Pytest fixtures: in-memory SQLite test DB (via DbSession) + FastAPI TestClient with
Azure OpenAI mocked."""
import os

# Use in-memory rate limit storage for tests so no real Redis instance is required.
# Must be set before app.core.config.get_settings() is first evaluated (import-time).
os.environ.setdefault("REDIS_URL", "memory://")

import pathlib
import sqlite3
import uuid
from typing import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.infrastructure.db.session import DbSession, get_db_session

SCHEMA_PATH = pathlib.Path(__file__).parent / "schema_sqlite.sql"


def _new_sqlite_connection() -> sqlite3.Connection:
    # check_same_thread=False: DbSession dispatches each DB-API call via asyncio.to_thread,
    # which may run on a different worker thread per call. Calls are still awaited
    # sequentially (never concurrently) against a given connection, so this is safe here.
    connection = sqlite3.connect(":memory:", check_same_thread=False)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    return connection


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[DbSession]:
    connection = _new_sqlite_connection()
    try:
        yield DbSession(connection)
    finally:
        connection.close()


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    from app.main import app

    connection = _new_sqlite_connection()

    async def _override_get_db_session():
        session = DbSession(connection)
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

    app.dependency_overrides[get_db_session] = _override_get_db_session
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    finally:
        app.dependency_overrides.clear()
        connection.close()


@pytest.fixture
def new_uuid() -> str:
    return str(uuid.uuid4())


class FakeAzureOpenAIClient:
    """Deterministic stand-in for AzureOpenAIClient used in tests (no real API calls)."""

    _question_counter = 0

    async def generate_structured(self, system_prompt: str, user_prompt: str, schema):
        from app.agents.schemas import AnswerEvaluation, FeedbackReport, GeneratedQuestion
        from app.schemas.resume_schemas import ParsedResume

        if schema is GeneratedQuestion:
            FakeAzureOpenAIClient._question_counter += 1
            return GeneratedQuestion(
                question=f"Fake generated question #{FakeAzureOpenAIClient._question_counter}",
                difficulty="intermediate",
                skill="Azure",
                expected_topics=["Managed Identity", "RBAC"],
            )
        if schema is AnswerEvaluation:
            return AnswerEvaluation(
                technical_score=8,
                communication_score=7,
                confidence_score=8,
                problem_solving_score=9,
                depth_score=7,
                completeness_score=7,
                missing_points=["Key rotation strategy"],
                strengths=["Clear explanation"],
                followup_question="How would you rotate secrets without downtime?",
            )
        if schema is FeedbackReport:
            return FeedbackReport(
                executive_summary="Solid overall performance with room to deepen security practices.",
                strengths=["Clear communicator", "Strong Azure fundamentals"],
                weaknesses=["Limited depth on secret rotation"],
                learning_path=["Azure Key Vault rotation patterns", "Zero-downtime secret management"],
                communication_assessment="Clear and structured.",
                technical_assessment="Strong fundamentals, some depth gaps.",
                behavioral_assessment="Not assessed.",
                hiring_recommendation="Hire",
                sample_ideal_answers=[{"question": "Explain managed identities", "ideal_answer": "..."}],
            )
        if schema is ParsedResume:
            return ParsedResume(
                skills=["Azure", "C#", ".NET Core", "Microservices"],
                projects=[],
                experience_years=6.5,
                certifications=["AZ-305"],
                education=[],
            )
        raise AssertionError(f"Unexpected schema requested from FakeAzureOpenAIClient: {schema}")

    async def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        return "Fake response"


@pytest.fixture(autouse=True)
def mock_azure_openai(monkeypatch):
    """Automatically replace the Azure OpenAI client everywhere it's used so tests never
    make real network calls."""
    fake_client = FakeAzureOpenAIClient()
    for module_path in (
        "app.agents.question_agents",
        "app.agents.evaluation_agent",
        "app.agents.feedback_agent",
        "app.infrastructure.resume.resume_intelligence",
    ):
        module = __import__(module_path, fromlist=["get_azure_openai_client"])
        monkeypatch.setattr(module, "get_azure_openai_client", lambda: fake_client)
    yield fake_client

