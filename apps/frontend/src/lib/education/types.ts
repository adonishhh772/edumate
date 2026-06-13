import type { AssignmentStatus, MasteryLevel, Subject } from "./constants";

export interface StudentProfile {
  id: string;
  name: string;
  grade_level: string;
  email: string;
  subjects: Subject[];
  mastery_level: MasteryLevel | string;
  streak_days: number;
  focus_subject: string;
  next_assignment_id?: string;
  message: string;
}

export interface Assignment {
  id: string;
  student_id: string;
  title: string;
  subject: Subject | string;
  status: AssignmentStatus | string;
  due_at: string;
  progress_percent: number;
  topic: string;
}

export interface AssignmentFilter {
  subjects: string[];
  statuses: string[];
  search: string;
}

export interface SyncMeta {
  source: string;
  syncedAt: string | null;
}

export interface EducationAgentState {
  profile: StudentProfile | null;
  assignments: Assignment[];
  filter: AssignmentFilter;
  highlightedAssignmentIds: string[];
  selectedAssignmentId: string | null;
  header: {
    title: string;
    subtitle: string;
  };
  sync: SyncMeta;
}

export interface StudyTipPayload {
  title: string;
  body: string;
  subject?: string;
}

export interface AssignmentCardPayload {
  assignmentId: string;
  title?: string;
  subject?: string;
  status?: string;
  due_at?: string;
}
