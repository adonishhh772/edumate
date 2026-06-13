"use client";

import { useAgentContext } from "@copilotkit/react-core/v2";

import type { EducationAgentState } from "@/lib/education/types";

interface EducationContextBridgeProps {
  state: EducationAgentState;
}

function buildEducationContextPayload(state: EducationAgentState): string {
  return JSON.stringify({
    student: state.profile
      ? {
          id: state.profile.id,
          name: state.profile.name,
          grade_level: state.profile.grade_level,
          focus_subject: state.profile.focus_subject,
          mastery_level: state.profile.mastery_level,
          streak_days: state.profile.streak_days,
        }
      : null,
    assignment_count: state.assignments.length,
    selected_assignment_id: state.selectedAssignmentId,
    active_subjects: state.filter.subjects,
  });
}

export function EducationContextBridge({ state }: EducationContextBridgeProps) {
  useAgentContext({
    description:
      "Active student profile, assignment focus, and learning workspace context.",
    value: buildEducationContextPayload(state),
  });

  return null;
}
