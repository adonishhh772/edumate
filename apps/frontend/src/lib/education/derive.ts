import type { Assignment, EducationAgentState } from "./types";
import { emptyFilter } from "./state";

export function mergeEducationAgentState(raw: unknown): EducationAgentState {
  const partial =
    raw && typeof raw === "object" ? (raw as Partial<EducationAgentState>) : {};

  return {
    profile: partial.profile ?? null,
    assignments: partial.assignments ?? [],
    filter: { ...emptyFilter, ...(partial.filter ?? {}) },
    highlightedAssignmentIds: partial.highlightedAssignmentIds ?? [],
    selectedAssignmentId: partial.selectedAssignmentId ?? null,
    header: {
      title: partial.header?.title ?? "EduMate Learning Hub",
      subtitle: partial.header?.subtitle ?? "Your AI study companion",
    },
    sync: {
      source: partial.sync?.source ?? "local seed data",
      syncedAt: partial.sync?.syncedAt ?? null,
    },
  };
}

export function applyAssignmentFilter(
  assignments: Assignment[],
  filter: EducationAgentState["filter"],
): Assignment[] {
  return assignments.filter((assignment) => {
    if (
      filter.subjects.length > 0 &&
      !filter.subjects.includes(assignment.subject)
    ) {
      return false;
    }
    if (
      filter.statuses.length > 0 &&
      !filter.statuses.includes(assignment.status)
    ) {
      return false;
    }
    if (filter.search.trim()) {
      const query = filter.search.trim().toLowerCase();
      const haystack = `${assignment.title} ${assignment.topic} ${assignment.subject}`.toLowerCase();
      if (!haystack.includes(query)) {
        return false;
      }
    }
    return true;
  });
}
