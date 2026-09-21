"""User repository."""
from typing import Optional

from app.infrastructure.db.models.user import User
from app.infrastructure.db.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User
    table_name = "users"

    async def get_by_email(self, email: str) -> Optional[User]:
        columns = [f.name for f in self._fields()]
        sql = f"SELECT {', '.join(columns)} FROM {self.table_name} WHERE email = ?"
        row = await self.session.fetchone(sql, (email,))
        return self._row_to_model(row) if row else None
