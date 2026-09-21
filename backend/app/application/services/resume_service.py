"""Resume upload + intelligence application service."""
from __future__ import annotations

import uuid

from fastapi import HTTPException, status

from app.infrastructure.db.models.resume import Resume
from app.infrastructure.db.repositories.resume_repository import ResumeRepository
from app.infrastructure.db.session import DbSession
from app.infrastructure.resume.resume_intelligence import parse_resume_text
from app.infrastructure.resume.text_extractor import extract_resume_text
from app.infrastructure.storage import save_file
from app.schemas.resume_schemas import ParsedResume


class ResumeService:
    def __init__(self, session: DbSession):
        self.session = session
        self.resumes = ResumeRepository(session)

    async def upload_and_parse(self, user_id: uuid.UUID | None, file_name: str, content: bytes) -> tuple[Resume, ParsedResume]:
        if not (file_name.lower().endswith(".pdf") or file_name.lower().endswith(".docx")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF and DOCX resumes are supported"
            )

        raw_text = extract_resume_text(file_name, content)
        parsed = await parse_resume_text(raw_text)
        storage_path = save_file("resumes", file_name, content)

        resume = Resume(
            id=uuid.uuid4(),
            user_id=user_id,
            file_name=file_name,
            storage_path=storage_path,
            raw_text=raw_text,
            extracted_skills=parsed.skills,
            extracted_projects=[p.model_dump() for p in parsed.projects],
            experience_years=parsed.experience_years,
            certifications=parsed.certifications,
            education=[e.model_dump() for e in parsed.education],
        )
        resume = await self.resumes.add(resume)
        await self.session.commit()
        return resume, parsed
