"""Abstract repository interfaces (Ports) — implemented by infrastructure layer (Adapters).

Following the Repository Pattern + Dependency Inversion (Clean Architecture / SOLID).
"""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import Generic, Optional, Sequence, TypeVar

T = TypeVar("T")


class IRepository(ABC, Generic[T]):
    @abstractmethod
    async def get_by_id(self, entity_id: uuid.UUID) -> Optional[T]: ...

    @abstractmethod
    async def add(self, entity: T) -> T: ...

    @abstractmethod
    async def list(self, **filters) -> Sequence[T]: ...


class IUserRepository(IRepository, ABC):
    @abstractmethod
    async def get_by_email(self, email: str): ...


class IResumeRepository(IRepository, ABC):
    ...


class IInterviewRepository(IRepository, ABC):
    @abstractmethod
    async def update_status(self, interview_id: uuid.UUID, status: str) -> None: ...

    @abstractmethod
    async def update_difficulty(self, interview_id: uuid.UUID, difficulty: str) -> None: ...


class IQuestionRepository(IRepository, ABC):
    @abstractmethod
    async def list_by_interview(self, interview_id: uuid.UUID) -> Sequence[T]: ...

    @abstractmethod
    async def count_by_interview(self, interview_id: uuid.UUID) -> int: ...


class IAnswerRepository(IRepository, ABC):
    ...


class IEvaluationRepository(IRepository, ABC):
    @abstractmethod
    async def list_by_interview(self, interview_id: uuid.UUID) -> Sequence[T]: ...


class IReportRepository(IRepository, ABC):
    ...


class IAnalyticsRepository(IRepository, ABC):
    @abstractmethod
    async def get_by_interview(self, interview_id: uuid.UUID) -> Optional[T]: ...


class IAuditLogRepository(IRepository, ABC):
    ...
