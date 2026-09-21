"""Resume Intelligence — extracts structured skills/projects/experience/certifications/
education from raw resume text using Azure OpenAI (GPT-4o) structured outputs.
"""
from __future__ import annotations

from app.core.logging import get_logger
from app.infrastructure.azure_openai.client import get_azure_openai_client
from app.schemas.resume_schemas import ParsedResume

logger = get_logger(__name__)

EXTRACTION_SYSTEM_PROMPT = """You are a resume parsing engine for a technical interview platform. \
Extract structured information precisely. Do not invent information not present in the resume text. \
Respond ONLY with the structured fields requested."""


async def parse_resume_text(raw_text: str) -> ParsedResume:
    client = get_azure_openai_client()
    user_prompt = f"""Extract the following from this resume text:
- skills: flat list of technical skills/technologies mentioned (e.g. "Azure", "C#", ".NET Core", "Microservices", "SQL Server", "GenAI")
- projects: notable projects with a short description and technologies used
- experience_years: total professional experience in years (best estimate, a number)
- certifications: professional certifications mentioned
- education: degrees with institution and year if available

Resume text:
\"\"\"{raw_text[:12000]}\"\"\"
"""
    parsed: ParsedResume = await client.generate_structured(EXTRACTION_SYSTEM_PROMPT, user_prompt, ParsedResume)
    logger.info("resume_parsed", skill_count=len(parsed.skills), experience_years=parsed.experience_years)
    return parsed
