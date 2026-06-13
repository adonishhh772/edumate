"use client";

import { useMemo, useState } from "react";

export interface ToolFallbackCardProps {
  name: string;
  status: string;
  result?: string | undefined;
  parameters?: unknown;
}

export function ToolFallbackCard({
  name,
  status,
  result,
  parameters,
}: ToolFallbackCardProps) {
  const [open, setOpen] = useState(false);
  const dotColor = status === "complete" ? "#BEC2FF" : "#F4D35E";
  const payload = useMemo(() => {
    const value = status === "complete" ? result ?? parameters : parameters;
    if (value === undefined || value === null) return "";
    if (typeof value === "string") {
      try {
        return JSON.stringify(JSON.parse(value), null, 2);
      } catch {
        return value;
      }
    }
    try {
      return JSON.stringify(value, null, 2);
    } catch {
      return String(value);
    }
  }, [parameters, result, status]);

  return (
    <div className="my-2 max-w-[420px] rounded-xl border border-[#DBDBE5] bg-white p-3 text-sm shadow-sm">
      <div className="flex items-center gap-2">
        <span
          className="size-2 shrink-0 rounded-full"
          style={{ background: dotColor }}
          aria-hidden
        />
        <span className="font-mono text-[12px] text-foreground">{name}</span>
        <span className="ml-auto font-mono text-[10px] uppercase tracking-wide text-muted-foreground">
          {status}
        </span>
      </div>
      {payload ? (
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          className="mt-2 inline-flex items-center gap-1 font-mono text-[10px] uppercase tracking-wide text-muted-foreground hover:text-foreground"
        >
          {open ? "hide" : "show"} payload
        </button>
      ) : null}
      {open && payload ? (
        <pre className="mt-2 max-h-48 overflow-auto rounded-md bg-[#F7F7F9] p-2 font-mono text-[11px] leading-snug text-foreground">
          {payload}
        </pre>
      ) : null}
    </div>
  );
}
