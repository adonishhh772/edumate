import type { Lead, LeadFilter } from "./types";
import { STATUSES } from "./types";

export function applyFilter(leads: Lead[], f: LeadFilter): Lead[] {
  const search = f.search.trim().toLowerCase();
  return leads.filter((l) => {
    if (f.workshops.length && !f.workshops.includes(l.workshop)) return false;
    if (
      f.technical_levels.length &&
      !f.technical_levels.includes(l.technical_level)
    )
      return false;
    if (f.tools.length && !f.tools.some((t) => l.tools.includes(t)))
      return false;
    if (f.opt_in === "yes" && !l.opt_in) return false;
    if (f.opt_in === "no" && l.opt_in) return false;
    if (search.length) {
      const blob = `${l.name} ${l.company} ${l.email} ${l.role} ${l.message}`
        .toLowerCase();
      if (!blob.includes(search)) return false;
    }
    return true;
  });
}

export function groupByStatus(leads: Lead[]): Record<string, Lead[]> {
  const groups: Record<string, Lead[]> = {};
  for (const s of STATUSES) groups[s] = [];
  for (const l of leads) {
    const key = (STATUSES as readonly string[]).includes(l.status)
      ? l.status
      : "Not started";
    (groups[key] ||= []).push(l);
  }
  return groups;
}

export function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

const TECH_RING_COLORS: Record<string, string> = {
  "Non-technical": "bg-rose-500/15 text-rose-700 dark:text-rose-300 ring-rose-500/30",
  "Some technical":
    "bg-amber-500/15 text-amber-700 dark:text-amber-300 ring-amber-500/30",
  Developer: "bg-sky-500/15 text-sky-700 dark:text-sky-300 ring-sky-500/30",
  "Advanced / expert":
    "bg-violet-500/15 text-violet-700 dark:text-violet-300 ring-violet-500/30",
};

export function techLevelClass(level: string): string {
  return (
    TECH_RING_COLORS[level] ??
    "bg-muted text-muted-foreground ring-border"
  );
}

const WORKSHOP_COLORS: Record<string, string> = {
  "Agentic UI (AG-UI)":
    "bg-violet-500/15 text-violet-700 dark:text-violet-300 ring-violet-500/30",
  "MCP Apps / Tooling":
    "bg-sky-500/15 text-sky-700 dark:text-sky-300 ring-sky-500/30",
  "RAG & Data Chat":
    "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 ring-emerald-500/30",
  "Evaluations & Guardrails":
    "bg-amber-500/15 text-amber-700 dark:text-amber-300 ring-amber-500/30",
  "Deploying Agents (prod)":
    "bg-indigo-500/15 text-indigo-700 dark:text-indigo-300 ring-indigo-500/30",
  "Not sure yet": "bg-muted text-muted-foreground ring-border",
};

export function workshopClass(workshop: string): string {
  return (
    WORKSHOP_COLORS[workshop] ??
    "bg-muted text-muted-foreground ring-border"
  );
}

const STATUS_COLORS: Record<string, string> = {
  "Not started":
    "bg-slate-500/15 text-slate-700 dark:text-slate-300 ring-slate-500/30",
  "In progress":
    "bg-amber-500/15 text-amber-700 dark:text-amber-300 ring-amber-500/30",
  Done: "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 ring-emerald-500/30",
};

export function statusClass(status: string): string {
  return (
    STATUS_COLORS[status] ?? "bg-muted text-muted-foreground ring-border"
  );
}
