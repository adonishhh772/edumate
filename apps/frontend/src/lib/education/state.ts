import type { EducationAgentState } from "./types";

export const emptyFilter: EducationAgentState["filter"] = {
  subjects: [],
  statuses: [],
  search: "",
};

export const initialEducationState: EducationAgentState = {
  profile: null,
  assignments: [],
  filter: emptyFilter,
  highlightedAssignmentIds: [],
  selectedAssignmentId: null,
  header: {
    title: "EduMate Learning Hub",
    subtitle: "Your AI study companion",
  },
  sync: {
    source: "local seed data",
    syncedAt: null,
  },
};
