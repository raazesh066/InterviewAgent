"""Domain-level enumerations shared across layers."""
from enum import Enum


class InterviewCategory(str, Enum):
    SOFTWARE_ENGINEER = "Software Engineer"
    DOTNET_DEVELOPER = ".NET Developer"
    AZURE_ARCHITECT = "Azure Architect"
    FULL_STACK_ENGINEER = "Full Stack Engineer"
    DATA_ENGINEER = "Data Engineer"
    AI_ENGINEER = "AI Engineer"
    ENGINEERING_MANAGER = "Engineering Manager"


class ProficiencyLevel(str, Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"
    EXPERT = "Expert"


class TargetCompany(str, Enum):
    MICROSOFT = "Microsoft"
    GOOGLE = "Google"
    AMAZON = "Amazon"
    META = "Meta"
    APPLE = "Apple"
    GENERIC = "Generic"


class InterviewType(str, Enum):
    TECHNICAL = "Technical"
    BEHAVIORAL = "Behavioral"
    SYSTEM_DESIGN = "System Design"
    LEADERSHIP = "Leadership"
    MIXED = "Mixed"


class InterviewStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

    @classmethod
    def ordered(cls) -> list["DifficultyLevel"]:
        return [cls.BEGINNER, cls.INTERMEDIATE, cls.ADVANCED, cls.EXPERT]

    def step(self, delta: int) -> "DifficultyLevel":
        order = DifficultyLevel.ordered()
        idx = order.index(self)
        new_idx = max(0, min(len(order) - 1, idx + delta))
        return order[new_idx]


class AgentType(str, Enum):
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    SYSTEM_DESIGN = "system_design"
    CODING = "coding"


class DifficultyAdjustment(str, Enum):
    INCREASE = "increase"
    MAINTAIN = "maintain"
    DECREASE = "decrease"


class UserRole(str, Enum):
    CANDIDATE = "candidate"
    INTERVIEWER = "interviewer"
    ADMIN = "admin"


class Grade(str, Enum):
    OUTSTANDING = "Outstanding"
    STRONG_HIRE = "Strong Hire"
    HIRE = "Hire"
    BORDERLINE = "Borderline"
    NEEDS_IMPROVEMENT = "Needs Improvement"

    @staticmethod
    def from_score(score: float) -> "Grade":
        if score >= 90:
            return Grade.OUTSTANDING
        if score >= 80:
            return Grade.STRONG_HIRE
        if score >= 70:
            return Grade.HIRE
        if score >= 60:
            return Grade.BORDERLINE
        return Grade.NEEDS_IMPROVEMENT
