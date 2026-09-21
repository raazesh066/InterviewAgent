-- =====================================================================
-- AI Mock Interview Platform — SQL Server / Azure SQL Schema
-- =====================================================================

-- ---------------------------------------------------------------------
-- USERS & AUTH
-- ---------------------------------------------------------------------
CREATE TABLE users (
    id              UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    email           NVARCHAR(255) UNIQUE NOT NULL,
    hashed_password NVARCHAR(255) NOT NULL,
    full_name       NVARCHAR(255) NOT NULL,
    role            NVARCHAR(32) NOT NULL DEFAULT 'candidate', -- candidate | interviewer | admin
    is_active       BIT NOT NULL DEFAULT 1,
    created_at      DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    updated_at      DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE TABLE user_profiles (
    user_id                    UNIQUEIDENTIFIER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    headline                   NVARCHAR(120) NOT NULL DEFAULT '',
    target_role                NVARCHAR(100) NOT NULL DEFAULT 'Software Engineer',
    years_of_experience        NUMERIC(4,1) NOT NULL DEFAULT 0,
    location                   NVARCHAR(100) NOT NULL DEFAULT '',
    bio                        NVARCHAR(1000) NOT NULL DEFAULT '',
    skills                     NVARCHAR(MAX) NOT NULL DEFAULT '[]',
    preferred_company          NVARCHAR(100) NOT NULL DEFAULT 'Generic',
    preferred_interview_type   NVARCHAR(100) NOT NULL DEFAULT 'Technical',
    updated_at                 DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

-- ---------------------------------------------------------------------
-- RESUMES
-- ---------------------------------------------------------------------
CREATE TABLE resumes (
    id                 UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    user_id            UNIQUEIDENTIFIER REFERENCES users(id) ON DELETE CASCADE,
    file_name          NVARCHAR(512) NOT NULL,
    storage_path       NVARCHAR(1024) NOT NULL,
    raw_text           NVARCHAR(MAX),
    extracted_skills   NVARCHAR(MAX) DEFAULT '[]',
    extracted_projects NVARCHAR(MAX) DEFAULT '[]',
    experience_years   NUMERIC(4,1),
    certifications     NVARCHAR(MAX) DEFAULT '[]',
    education          NVARCHAR(MAX) DEFAULT '[]',
    created_at         DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

-- ---------------------------------------------------------------------
-- SKILLS (master catalog)
-- ---------------------------------------------------------------------
CREATE TABLE skills (
    id          UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    name        NVARCHAR(128) UNIQUE NOT NULL,
    category    NVARCHAR(64), -- e.g. Cloud, Language, Database, AI
    created_at  DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

-- Candidate-selected skill + proficiency for a given interview
CREATE TABLE candidate_skills (
    id            UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    interview_id  UNIQUEIDENTIFIER NOT NULL,
    skill_name    NVARCHAR(128) NOT NULL,
    level         NVARCHAR(32) NOT NULL, -- Beginner | Intermediate | Advanced | Expert
    created_at    DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

-- ---------------------------------------------------------------------
-- INTERVIEWS
-- ---------------------------------------------------------------------
CREATE TABLE interviews (
    id                  UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    user_id             UNIQUEIDENTIFIER REFERENCES users(id) ON DELETE SET NULL,
    resume_id           UNIQUEIDENTIFIER REFERENCES resumes(id) ON DELETE SET NULL,
    candidate_name      NVARCHAR(255) NOT NULL,
    category            NVARCHAR(64) NOT NULL, -- Software Engineer | .NET Developer | ...
    target_company      NVARCHAR(64) NOT NULL DEFAULT 'Generic',
    interview_type       NVARCHAR(32) NOT NULL, -- Technical | Behavioral | System Design | Leadership | Mixed
    duration_minutes    INT NOT NULL,
    years_of_experience NUMERIC(4,1),
    status              NVARCHAR(32) NOT NULL DEFAULT 'in_progress', -- in_progress | completed | abandoned
    current_difficulty  NVARCHAR(32) NOT NULL DEFAULT 'intermediate',
    plan                NVARCHAR(MAX) DEFAULT '{}',
    started_at          DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    completed_at        DATETIME2,
    created_at          DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    updated_at          DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE INDEX idx_interviews_user ON interviews(user_id);
CREATE INDEX idx_interviews_status ON interviews(status);

-- ---------------------------------------------------------------------
-- QUESTIONS
-- ---------------------------------------------------------------------
CREATE TABLE questions (
    id               UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    interview_id     UNIQUEIDENTIFIER NOT NULL REFERENCES interviews(id) ON DELETE CASCADE,
    parent_question_id UNIQUEIDENTIFIER REFERENCES questions(id),
    agent_type       NVARCHAR(32) NOT NULL, -- technical | behavioral | system_design | coding
    skill            NVARCHAR(128),
    text             NVARCHAR(MAX) NOT NULL,
    difficulty       NVARCHAR(32) NOT NULL, -- beginner | intermediate | advanced | expert
    expected_topics  NVARCHAR(MAX) DEFAULT '[]',
    is_followup      BIT NOT NULL DEFAULT 0,
    sequence_number  INT NOT NULL,
    asked_at         DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE INDEX idx_questions_interview ON questions(interview_id);

-- ---------------------------------------------------------------------
-- ANSWERS
-- ---------------------------------------------------------------------
CREATE TABLE answers (
    id                  UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    question_id         UNIQUEIDENTIFIER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    interview_id        UNIQUEIDENTIFIER NOT NULL REFERENCES interviews(id) ON DELETE CASCADE,
    answer_text         NVARCHAR(MAX),
    answer_audio_path   NVARCHAR(1024),
    time_taken_seconds  INT,
    submitted_at        DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE INDEX idx_answers_interview ON answers(interview_id);

-- ---------------------------------------------------------------------
-- EVALUATIONS
-- ---------------------------------------------------------------------
CREATE TABLE evaluations (
    id                   UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    answer_id            UNIQUEIDENTIFIER NOT NULL REFERENCES answers(id) ON DELETE CASCADE,
    interview_id         UNIQUEIDENTIFIER NOT NULL REFERENCES interviews(id) ON DELETE CASCADE,
    technical_score      NUMERIC(4,1) NOT NULL,
    communication_score  NUMERIC(4,1) NOT NULL,
    confidence_score     NUMERIC(4,1) NOT NULL,
    problem_solving_score NUMERIC(4,1) NOT NULL,
    depth_score          NUMERIC(4,1) NOT NULL,
    completeness_score   NUMERIC(4,1),
    missing_points       NVARCHAR(MAX) DEFAULT '[]',
    strengths            NVARCHAR(MAX) DEFAULT '[]',
    followup_question    NVARCHAR(MAX),
    difficulty_adjustment NVARCHAR(16), -- increase | maintain | decrease
    created_at           DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE INDEX idx_evaluations_interview ON evaluations(interview_id);

-- ---------------------------------------------------------------------
-- REPORTS
-- ---------------------------------------------------------------------
CREATE TABLE reports (
    id                UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    interview_id      UNIQUEIDENTIFIER NOT NULL REFERENCES interviews(id) ON DELETE CASCADE,
    final_rating      NUMERIC(5,2),
    grade             NVARCHAR(32),
    executive_summary NVARCHAR(MAX),
    strengths         NVARCHAR(MAX) DEFAULT '[]',
    weaknesses        NVARCHAR(MAX) DEFAULT '[]',
    learning_path     NVARCHAR(MAX) DEFAULT '[]',
    ideal_answers     NVARCHAR(MAX) DEFAULT '[]',
    hiring_recommendation NVARCHAR(MAX),
    pdf_storage_path  NVARCHAR(1024),
    generated_at      DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

-- ---------------------------------------------------------------------
-- ANALYTICS (aggregated, denormalized for dashboard reads)
-- ---------------------------------------------------------------------
CREATE TABLE analytics (
    id                UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    interview_id      UNIQUEIDENTIFIER NOT NULL REFERENCES interviews(id) ON DELETE CASCADE,
    skill_performance NVARCHAR(MAX) DEFAULT '[]',
    confidence_trend  NVARCHAR(MAX) DEFAULT '[]',
    score_trend       NVARCHAR(MAX) DEFAULT '[]',
    question_timeline NVARCHAR(MAX) DEFAULT '[]',
    updated_at        DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

-- ---------------------------------------------------------------------
-- AUDIT LOGS
-- ---------------------------------------------------------------------
CREATE TABLE audit_logs (
    id           UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    user_id      UNIQUEIDENTIFIER REFERENCES users(id) ON DELETE SET NULL,
    action       NVARCHAR(128) NOT NULL,
    resource     NVARCHAR(128),
    resource_id  NVARCHAR(128),
    metadata     NVARCHAR(MAX) DEFAULT '{}',
    ip_address   NVARCHAR(64),
    created_at   DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);

