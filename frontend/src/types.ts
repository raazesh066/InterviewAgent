export type ProficiencyLevel = 'Beginner' | 'Intermediate' | 'Advanced' | 'Expert'

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface UserResponse {
  id: string
  email: string
  full_name: string
  role: string
}

export interface UserProfile {
  id: string
  email: string
  full_name: string
  role: string
  is_active: boolean
  joined_at: string
  headline: string
  target_role: string
  years_of_experience: number
  location: string
  bio: string
  skills: string[]
  preferred_company: string
  preferred_interview_type: string
  total_interviews: number
  completed_interviews: number
}

export type UserProfileUpdate = Pick<
  UserProfile,
  | 'headline'
  | 'target_role'
  | 'years_of_experience'
  | 'location'
  | 'bio'
  | 'skills'
  | 'preferred_company'
  | 'preferred_interview_type'
>

export interface SkillSelection {
  name: string
  level: ProficiencyLevel
}

export interface Question {
  question_id: string
  text: string
  skill?: string
  difficulty: string
  type: string
  expected_topics: string[]
  is_followup: boolean
}

export interface StartInterviewRequest {
  candidate_name: string
  resume_id?: string
  target_company: string
  category: string
  interview_type: string
  duration_minutes: number
  years_of_experience: number
  skills: SkillSelection[]
}

export interface StartInterviewResponse {
  interview_id: string
  status: string
  plan: { stages: string[]; estimated_questions: number }
  first_question: Question
}

export interface EvaluationResult {
  technical_score: number
  communication_score: number
  confidence_score: number
  problem_solving_score: number
  depth_score: number
  missing_points: string[]
  strengths: string[]
  followup_question?: string
}

export interface SubmitAnswerResponse {
  evaluation: EvaluationResult
  difficulty_adjustment: string
  interview_status: string
}

export interface InterviewScore {
  final_rating: number
  grade: string
  breakdown: Record<string, number>
  weights: Record<string, number>
}

export interface ResumeUploadResponse {
  resume_id: string
  file_name: string
  parsed: Record<string, unknown>
}