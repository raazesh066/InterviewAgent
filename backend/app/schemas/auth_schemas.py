"""Auth request/response schemas."""
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class UserProfileUpdate(BaseModel):
    headline: str = Field(default="", max_length=120)
    target_role: str = Field(default="Software Engineer", max_length=100)
    years_of_experience: float = Field(default=0, ge=0, le=60)
    location: str = Field(default="", max_length=100)
    bio: str = Field(default="", max_length=1000)
    skills: list[str] = Field(default_factory=list, max_length=20)
    preferred_company: str = Field(default="Generic", max_length=100)
    preferred_interview_type: str = Field(default="Technical", max_length=100)


class UserProfileResponse(UserProfileUpdate):
    id: str
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    joined_at: datetime
    total_interviews: int
    completed_interviews: int
