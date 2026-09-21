"""Answer repository."""
from app.infrastructure.db.models.answer import Answer
from app.infrastructure.db.repositories.base_repository import BaseRepository


class AnswerRepository(BaseRepository[Answer]):
    model = Answer
    table_name = "answers"
