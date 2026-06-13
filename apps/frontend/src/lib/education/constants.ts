export const ASSIGNMENT_STATUS = {
  NOT_STARTED: "not_started",
  IN_PROGRESS: "in_progress",
  SUBMITTED: "submitted",
  GRADED: "graded",
} as const;

export type AssignmentStatus =
  (typeof ASSIGNMENT_STATUS)[keyof typeof ASSIGNMENT_STATUS];

export const ASSIGNMENT_STATUSES: readonly AssignmentStatus[] = [
  ASSIGNMENT_STATUS.NOT_STARTED,
  ASSIGNMENT_STATUS.IN_PROGRESS,
  ASSIGNMENT_STATUS.SUBMITTED,
  ASSIGNMENT_STATUS.GRADED,
] as const;

export const MASTERY_LEVEL = {
  BEGINNER: "beginner",
  DEVELOPING: "developing",
  PROFICIENT: "proficient",
  ADVANCED: "advanced",
} as const;

export type MasteryLevel =
  (typeof MASTERY_LEVEL)[keyof typeof MASTERY_LEVEL];

export const SUBJECT = {
  MATHEMATICS: "mathematics",
  SCIENCE: "science",
  ENGLISH: "english",
  HISTORY: "history",
  COMPUTER_SCIENCE: "computer_science",
} as const;

export type Subject = (typeof SUBJECT)[keyof typeof SUBJECT];

export const SUBJECTS: readonly Subject[] = [
  SUBJECT.MATHEMATICS,
  SUBJECT.SCIENCE,
  SUBJECT.ENGLISH,
  SUBJECT.HISTORY,
  SUBJECT.COMPUTER_SCIENCE,
] as const;
