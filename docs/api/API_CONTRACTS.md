# API Contracts — AI Mock Interview Platform

Base URL: `/api/v1`
Auth: `Authorization: Bearer <JWT>` (except `/auth/register`, `/auth/login`)
Content-Type: `application/json` unless noted (multipart for uploads).

## Conventions

- All timestamps are ISO-8601 UTC.
- All list endpoints support `page` and `page_size` query params.
- Error shape:
```json
{ "error": { "code": "STRING_CODE", "message": "human readable", "details": {} } }
```

---

## Auth

### POST /auth/register
Request:
```json
{ "email": "a@b.com", "password": "Str0ngPass!", "full_name": "Jane Doe" }
```
Response `201`:
```json
{ "id": "uuid", "email": "a@b.com", "full_name": "Jane Doe", "role": "candidate" }
```

### POST /auth/login
Request: `{ "email": "a@b.com", "password": "Str0ngPass!" }`
Response `200`:
```json
{ "access_token": "jwt", "refresh_token": "jwt", "token_type": "bearer", "expires_in": 3600 }
```

### POST /auth/refresh
Request: `{ "refresh_token": "jwt" }` → Response: same shape as login.

---

## Resume

### POST /upload-resume  (multipart/form-data: `file`)
Response `201`:
```json
{
  "resume_id": "uuid",
  "file_name": "resume.pdf",
  "parsed": {
    "skills": ["Azure", "C#", ".NET Core", "Microservices"],
    "projects": [{ "name": "Payments Platform", "description": "...", "technologies": ["Azure", "SQL Server"] }],
    "experience_years": 6.5,
    "certifications": ["AZ-305"],
    "education": [{ "degree": "B.Tech CSE", "institution": "...", "year": 2017 }]
  }
}
```

---

## Interview Setup / Lifecycle

### POST /start-interview
Request:
```json
{
  "candidate_name": "Jane Doe",
  "resume_id": "uuid|null",
  "target_company": "Microsoft",
  "category": "Full Stack Engineer",
  "interview_type": "Mixed",
  "duration_minutes": 45,
  "years_of_experience": 6.5,
  "skills": [
    { "name": ".NET Core", "level": "Expert" },
    { "name": "Azure", "level": "Advanced" },
    { "name": "SQL Server", "level": "Advanced" },
    { "name": "GenAI", "level": "Intermediate" }
  ]
}
```
Response `201`:
```json
{
  "interview_id": "uuid",
  "status": "in_progress",
  "plan": { "stages": ["technical", "system_design", "behavioral"], "estimated_questions": 12 },
  "first_question": {
    "question_id": "uuid",
    "text": "Explain how you implemented managed identities in Azure.",
    "skill": "Azure",
    "difficulty": "advanced",
    "type": "technical",
    "expected_topics": ["Managed Identity", "RBAC", "Key Vault"]
  }
}
```

### POST /submit-answer
Request:
```json
{
  "interview_id": "uuid",
  "question_id": "uuid",
  "answer_text": "We used system-assigned managed identity to authenticate to Key Vault...",
  "answer_audio_url": null,
  "time_taken_seconds": 95
}
```
Response `200` (evaluation + next question decision):
```json
{
  "evaluation": {
    "technical_score": 8,
    "communication_score": 7,
    "confidence_score": 8,
    "problem_solving_score": 9,
    "depth_score": 7,
    "missing_points": ["Key rotation strategy"],
    "strengths": ["Clear explanation of RBAC model"],
    "followup_question": "How would you rotate secrets without downtime?"
  },
  "difficulty_adjustment": "increase",
  "interview_status": "in_progress"
}
```

### GET /next-question?interview_id=uuid
Response `200`:
```json
{
  "question_id": "uuid",
  "text": "How would you rotate secrets without downtime?",
  "skill": "Azure",
  "difficulty": "expert",
  "type": "technical",
  "expected_topics": ["Key Vault rotation", "Zero downtime"],
  "is_followup": true
}
```
When the interview duration/plan is exhausted: `204 No Content` with header `X-Interview-Status: completed`.

### GET /interview-score?interview_id=uuid
Response `200`:
```json
{
  "final_rating": 82.4,
  "grade": "Strong Hire",
  "breakdown": {
    "technical_score": 85,
    "communication_score": 78,
    "problem_solving_score": 80,
    "confidence_score": 84,
    "depth_score": 79
  },
  "weights": { "technical": 0.4, "communication": 0.2, "problem_solving": 0.2, "confidence": 0.1, "depth": 0.1 }
}
```

---

## Analytics

### GET /analytics?interview_id=uuid
Response `200`:
```json
{
  "progress_percent": 100,
  "current_score": 82.4,
  "skill_performance": [{ "skill": "Azure", "average_score": 8.1 }],
  "strengths": ["System design trade-off reasoning"],
  "weaknesses": ["Edge case handling in coding rounds"],
  "question_timeline": [{ "question_id": "uuid", "asked_at": "...", "score": 8, "difficulty": "advanced" }],
  "confidence_trend": [7, 8, 8, 6, 9],
  "score_trend": [7, 7.5, 8, 6.5, 9]
}
```

---

## Report

### GET /report?interview_id=uuid&format=pdf
Response: `200` binary `application/pdf` stream (Content-Disposition attachment) OR `format=json` returns structured report body used to render the PDF.

---

## Voice

### POST /voice/speech-to-text (multipart: `audio`)
Response: `{ "text": "transcribed answer" }`

### POST /voice/text-to-speech
Request: `{ "text": "Explain your approach to..." }` → Response: `audio/mpeg` binary stream.

---

## WebSocket (optional real-time channel)
`ws://.../ws/interview/{interview_id}` — streams question/answer/evaluation events for live UI updates.
