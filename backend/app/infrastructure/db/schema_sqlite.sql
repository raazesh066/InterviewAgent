CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'candidate',
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS user_profiles (
    user_id TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    headline TEXT NOT NULL DEFAULT '',
    target_role TEXT NOT NULL DEFAULT 'Software Engineer',
    years_of_experience REAL NOT NULL DEFAULT 0,
    location TEXT NOT NULL DEFAULT '',
    bio TEXT NOT NULL DEFAULT '',
    skills TEXT NOT NULL DEFAULT '[]',
    preferred_company TEXT NOT NULL DEFAULT 'Generic',
    preferred_interview_type TEXT NOT NULL DEFAULT 'Technical',
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS resumes (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    file_name TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    raw_text TEXT,
    extracted_skills TEXT DEFAULT '[]',
    extracted_projects TEXT DEFAULT '[]',
    experience_years REAL,
    certifications TEXT DEFAULT '[]',
    education TEXT DEFAULT '[]',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS skills (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    category TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS candidate_skills (
    id TEXT PRIMARY KEY,
    interview_id TEXT NOT NULL,
    skill_name TEXT NOT NULL,
    level TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS interviews (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id) ON DELETE SET NULL,
    resume_id TEXT REFERENCES resumes(id) ON DELETE SET NULL,
    candidate_name TEXT NOT NULL,
    category TEXT NOT NULL,
    target_company TEXT NOT NULL DEFAULT 'Generic',
    interview_type TEXT NOT NULL,
    duration_minutes INTEGER NOT NULL,
    years_of_experience REAL,
    status TEXT NOT NULL DEFAULT 'in_progress',
    current_difficulty TEXT NOT NULL DEFAULT 'intermediate',
    plan TEXT DEFAULT '{}',
    started_at TEXT NOT NULL,
    completed_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_interviews_user ON interviews(user_id);
CREATE INDEX IF NOT EXISTS idx_interviews_status ON interviews(status);

CREATE TABLE IF NOT EXISTS questions (
    id TEXT PRIMARY KEY,
    interview_id TEXT NOT NULL REFERENCES interviews(id) ON DELETE CASCADE,
    parent_question_id TEXT REFERENCES questions(id),
    agent_type TEXT NOT NULL,
    skill TEXT,
    text TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    expected_topics TEXT DEFAULT '[]',
    is_followup INTEGER NOT NULL DEFAULT 0,
    sequence_number INTEGER NOT NULL,
    asked_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_questions_interview ON questions(interview_id);

CREATE TABLE IF NOT EXISTS answers (
    id TEXT PRIMARY KEY,
    question_id TEXT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    interview_id TEXT NOT NULL REFERENCES interviews(id) ON DELETE CASCADE,
    answer_text TEXT,
    answer_audio_path TEXT,
    time_taken_seconds INTEGER,
    submitted_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_answers_interview ON answers(interview_id);

CREATE TABLE IF NOT EXISTS evaluations (
    id TEXT PRIMARY KEY,
    answer_id TEXT NOT NULL REFERENCES answers(id) ON DELETE CASCADE,
    interview_id TEXT NOT NULL REFERENCES interviews(id) ON DELETE CASCADE,
    technical_score REAL NOT NULL,
    communication_score REAL NOT NULL,
    confidence_score REAL NOT NULL,
    problem_solving_score REAL NOT NULL,
    depth_score REAL NOT NULL,
    completeness_score REAL,
    missing_points TEXT DEFAULT '[]',
    strengths TEXT DEFAULT '[]',
    followup_question TEXT,
    difficulty_adjustment TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_evaluations_interview ON evaluations(interview_id);

CREATE TABLE IF NOT EXISTS reports (
    id TEXT PRIMARY KEY,
    interview_id TEXT NOT NULL REFERENCES interviews(id) ON DELETE CASCADE,
    final_rating REAL,
    grade TEXT,
    executive_summary TEXT,
    strengths TEXT DEFAULT '[]',
    weaknesses TEXT DEFAULT '[]',
    learning_path TEXT DEFAULT '[]',
    ideal_answers TEXT DEFAULT '[]',
    hiring_recommendation TEXT,
    pdf_storage_path TEXT,
    generated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS analytics (
    id TEXT PRIMARY KEY,
    interview_id TEXT NOT NULL REFERENCES interviews(id) ON DELETE CASCADE,
    skill_performance TEXT DEFAULT '[]',
    confidence_trend TEXT DEFAULT '[]',
    score_trend TEXT DEFAULT '[]',
    question_timeline TEXT DEFAULT '[]',
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    resource TEXT,
    resource_id TEXT,
    metadata TEXT DEFAULT '{}',
    ip_address TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);