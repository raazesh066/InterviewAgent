"""Resume repository."""
from app.infrastructure.db.models.resume import Resume
from app.infrastructure.db.repositories.base_repository import BaseRepository


class ResumeRepository(BaseRepository[Resume]):
    model = Resume
    table_name = "resumes"
