"use client";

import { useMemo } from "react";
import type { Lead } from "@/lib/leads/types";

interface WorkshopDemandProps {
  leads: Lead[];
  onPickWorkshop?: (workshop: string) => void;
  selectedWorkshops?: string[];
  /**
   * `compact` shrinks the chart for inline-in-chat rendering: ~360px max
   * width, smaller fonts, top 5 rows only. Use `false`/omit for the
   * full-width canvas chart.
   */
  compact?: boolean;
}

/**
 * Horizontal bar chart of leads-per-workshop.
 *
 * Same component renders inside the canvas (full width) AND inline in chat
 * via the `renderWorkshopDemand` controlled-gen-UI tool. The chat path passes
 * `compact` so the chart shrinks to fit the 420px sidebar.
 */
export function WorkshopDemand({
  leads,
  onPickWorkshop,
  selectedWorkshops,
  compact,
}: WorkshopDemandProps) {
  const rows = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const l of leads) {
      const key = l.workshop?.trim() || "Not sure yet";
      counts[key] = (counts[key] ?? 0) + 1;
    }
    return Object.entries(counts)
      .map(([label, count]) => ({ label, count }))
      .sort((a, b) => b.count - a.count);
  }, [leads]);

  if (rows.length === 0) {
    return (
      <div className="rounded-xl border border-border bg-card p-4 text-sm text-muted-foreground">
        No leads loaded yet.
      </div>
    );
  }

  const visible = compact ? rows.slice(0, 6) : rows;
  const max = Math.max(1, ...visible.map((r) => r.count));
  const selected = new Set(selectedWorkshops ?? []);

  return (
    <section
      className={`flex h-full flex-col rounded-xl border border-border bg-card shadow-sm ${
        compact ? "p-4" : "p-5"
      }`}
      aria-label="Workshop demand"
    >
      <header className="mb-3 flex items-baseline justify-between gap-3">
        <span className="font-mono text-[10px] uppercase tracking-wide text-muted-foreground">
          workshop demand
        </span>
        <span className="font-mono text-[10px] uppercase tracking-wide text-muted-foreground">
          {rows.length} workshops
        </span>
      </header>
      <ul className={`flex flex-col ${compact ? "gap-1.5" : "gap-2"}`}>
        {visible.map((row) => {
          const pct = (row.count / max) * 100;
          const isSelected = selected.has(row.label);
          const interactive = Boolean(onPickWorkshop);
          const RowEl = interactive ? "button" : "div";
          return (
            <li key={row.label}>
              <RowEl
                type={interactive ? "button" : undefined}
                onClick={
                  interactive ? () => onPickWorkshop?.(row.label) : undefined
                }
                className={`group grid w-full items-center gap-3 rounded-lg px-2 py-1.5 text-left transition ${
                  interactive ? "hover:bg-[#BEC2FF1A]" : ""
                } ${
                  compact
                    ? "grid-cols-[120px_minmax(0,1fr)_32px]"
                    : "grid-cols-[180px_minmax(0,1fr)_44px]"
                }`}
              >
                <span
                  className={`truncate text-foreground ${
                    compact ? "text-[12px]" : "text-sm"
                  }`}
                  title={row.label}
                >
                  {row.label}
                </span>
                <span
                  className={`relative h-2.5 overflow-hidden rounded-full bg-[#F0F0F4] ${
                    compact ? "h-2" : ""
                  }`}
                  aria-hidden
                >
                  <span
                    className="absolute inset-y-0 left-0 rounded-full transition-all"
                    style={{
                      width: `${pct}%`,
                      background: isSelected ? "#85ECCE" : "#BEC2FF",
                    }}
                  />
                </span>
                <span
                  className={`text-right font-mono tabular-nums text-foreground ${
                    compact ? "text-[11px]" : "text-xs"
                  }`}
                >
                  {row.count}
                </span>
              </RowEl>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
