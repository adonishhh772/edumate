"""EducationStateMiddleware — student canvas state schema and hydration."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Any, Optional

from langchain.agents.middleware.types import AgentMiddleware, AgentState
from typing_extensions import NotRequired, TypedDict


class _Header(TypedDict, total=False):
    title: str
    subtitle: str


class _SyncMeta(TypedDict, total=False):
    source: str
    syncedAt: Optional[str]


class _AssignmentFilter(TypedDict, total=False):
    subjects: list[str]
    statuses: list[str]
    search: str


class _StudentProfile(TypedDict, total=False):
    id: str
    name: str
    grade_level: str
    email: str
    subjects: list[str]
    mastery_level: str
    streak_days: int
    focus_subject: str
    next_assignment_id: str
    message: str


class _Assignment(TypedDict, total=False):
    id: str
    student_id: str
    title: str
    subject: str
    status: str
    due_at: str
    progress_percent: int
    topic: str


def _replace(_left: Any, right: Any) -> Any:
    return right


class EducationCanvasState(AgentState):
    profile: NotRequired[Annotated[_StudentProfile, _replace]]
    assignments: NotRequired[Annotated[list[_Assignment], _replace]]
    filter: NotRequired[Annotated[_AssignmentFilter, _replace]]
    highlightedAssignmentIds: NotRequired[Annotated[list[str], _replace]]
    selectedAssignmentId: NotRequired[Annotated[Optional[str], _replace]]
    header: NotRequired[Annotated[_Header, _replace]]
    sync: NotRequired[Annotated[_SyncMeta, _replace]]


class EducationStateMiddleware(AgentMiddleware[EducationCanvasState, Any]):  # type: ignore[type-arg]
    state_schema = EducationCanvasState

    def before_agent(self, state: Any, runtime: Any) -> dict[str, Any] | None:
        existing_assignments = (
            (state or {}).get("assignments") if isinstance(state, dict) else None
        )
        if existing_assignments:
            return None

        try:
            from .student_store import list_assignments, list_students

            students = list_students()
            assignments = list_assignments()
        except Exception:
            return None

        if not students:
            return None

        profile = students[0]
        student_id = profile.get("id", "")
        student_assignments = [
            row for row in assignments if row.get("student_id") == student_id
        ]
        focus_subject = profile.get("focus_subject", "general studies")

        return {
            "profile": profile,
            "assignments": student_assignments,
            "header": {
                "title": "EduMate Learning Hub",
                "subtitle": (
                    f"Welcome back, {profile.get('name', 'Student')} · "
                    f"focus: {focus_subject} · "
                    f"{len(student_assignments)} assignments"
                ),
            },
            "sync": {
                "source": "local seed data",
                "syncedAt": datetime.now(timezone.utc).isoformat(),
            },
        }
