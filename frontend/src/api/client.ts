import type {
  InterviewScore,
  Question,
  ResumeUploadResponse,
  StartInterviewRequest,
  StartInterviewResponse,
  SubmitAnswerResponse,
  TokenResponse,
  UserProfile,
  UserProfileUpdate,
  UserResponse,
} from '../types'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'
const TOKEN_KEY = 'interview-room-access-token'

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message)
  }
}

function token() {
  return localStorage.getItem(TOKEN_KEY)
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  const accessToken = token()
  if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`)
  if (init.body && !(init.body instanceof FormData)) headers.set('Content-Type', 'application/json')

  const response = await fetch(`${API_BASE}${path}`, { ...init, headers })
  if (response.status === 401 && accessToken) {
    localStorage.removeItem(TOKEN_KEY)
    window.dispatchEvent(new Event('auth-expired'))
  }
  if (response.status === 204) return undefined as T
  const body = await response.json().catch(() => null)
  if (!response.ok) {
    const detail = body?.error?.message ?? body?.detail ?? 'The request could not be completed.'
    throw new ApiError(typeof detail === 'string' ? detail : JSON.stringify(detail), response.status)
  }
  return body as T
}

async function requestBlob(path: string, init: RequestInit): Promise<Blob> {
  const headers = new Headers(init.headers)
  const accessToken = token()
  if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`)
  headers.set('Content-Type', 'application/json')
  const response = await fetch(`${API_BASE}${path}`, { ...init, headers })
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new ApiError(body?.error?.message ?? body?.detail ?? 'Voice playback failed.', response.status)
  }
  return response.blob()
}

export const api = {
  saveToken(value: string) {
    localStorage.setItem(TOKEN_KEY, value)
  },
  clearToken() {
    localStorage.removeItem(TOKEN_KEY)
  },
  hasToken() {
    return Boolean(token())
  },
  login(email: string, password: string) {
    return request<TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
  },
  register(email: string, password: string, fullName: string) {
    return request<UserResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name: fullName }),
    })
  },
  getProfile() {
    return request<UserProfile>('/auth/me')
  },
  updateProfile(profile: UserProfileUpdate) {
    return request<UserProfile>('/auth/me', {
      method: 'PUT',
      body: JSON.stringify(profile),
    })
  },
  uploadResume(file: File) {
    const body = new FormData()
    body.append('file', file)
    return request<ResumeUploadResponse>('/upload-resume', { method: 'POST', body })
  },
  startInterview(payload: StartInterviewRequest) {
    return request<StartInterviewResponse>('/start-interview', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  submitAnswer(interviewId: string, questionId: string, answerText: string, timeTakenSeconds: number) {
    return request<SubmitAnswerResponse>('/submit-answer', {
      method: 'POST',
      body: JSON.stringify({
        interview_id: interviewId,
        question_id: questionId,
        answer_text: answerText,
        time_taken_seconds: timeTakenSeconds,
      }),
    })
  },
  nextQuestion(interviewId: string) {
    return request<Question>(`/next-question?interview_id=${encodeURIComponent(interviewId)}`)
  },
  score(interviewId: string) {
    return request<InterviewScore>(`/interview-score?interview_id=${encodeURIComponent(interviewId)}`)
  },
  synthesizeSpeech(text: string) {
    return requestBlob('/voice/text-to-speech', {
      method: 'POST',
      body: JSON.stringify({ text }),
    })
  },
}