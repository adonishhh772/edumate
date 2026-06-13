"""Domain constants for the EduMate student-facing agent."""

from enum import StrEnum


class AssignmentStatus(StrEnum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    GRADED = "graded"


class MasteryLevel(StrEnum):
    BEGINNER = "beginner"
    DEVELOPING = "developing"
    PROFICIENT = "proficient"
    ADVANCED = "advanced"


class Subject(StrEnum):
    MATHEMATICS = "mathematics"
    SCIENCE = "science"
    ENGLISH = "english"
    HISTORY = "history"
    COMPUTER_SCIENCE = "computer_science"


AGENT_DOMAIN_EDUCATION = "education"
AGENT_DOMAIN_LEADS = "leads"
