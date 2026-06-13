"use client";

import { useMemo } from "react";
import type { Lead } from "@/lib/leads/types";

export interface QuickStatsProps {
  leads: Lead[];
}

interface Tile {
  label: string;
  value: string;
  meta?: string;
  accent?: "lilac" | "mint" | "blue" | "orange";
}

const ACCENT: Record<NonNullable<Tile["accent"]>, string> = {
  lilac: "#BEC2FF",
  mint: "#85ECCE",
  blue: "#3D92E8",
  orange: "#FFAC4D",
};

export function QuickStats({ leads }: QuickStatsProps) {
  const tiles = useMemo<Tile[]>(() => {
    const total = leads.length;

    const optIns = leads.filter((l) => l.opt_in).length;
    const optInPct = total === 0 ? 0 : Math.round((optIns / total) * 100);

    const workshopCounts = new Map<string, number>();
    for (const l of leads) {
      const w = l.workshop || "Not sure yet";
      workshopCounts.set(w, (workshopCounts.get(w) ?? 0) + 1);
    }
    let topWorkshop: { name: string; count: number } | null = null;
    for (const [name, count] of workshopCounts) {
      if (!topWorkshop || count > topWorkshop.count) {
        topWorkshop = { name, count };
      }
    }

    const developers = leads.filter((l) => {
      const t = l.technical_level;
      return t === "Developer" || t === "Advanced / expert";
    }).length;

    return [
      {
        label: "total leads",
        value: total.toString(),
        meta: total === 1 ? "lead in canvas" : "leads in canvas",
        accent: "lilac",
      },
      {
        label: "opt-in",
        value: `${optInPct}%`,
        meta: `${optIns} / ${total}`,
        accent: "mint",
      },
      {
        label: "top workshop",
        value: topWorkshop?.name ?? "—",
        meta: topWorkshop ? `${topWorkshop.count} interested` : "no leads yet",
        accent: "blue",
      },
      {
        label: "developers",
        value: developers.toString(),
        meta: total === 0 ? "—" : `${Math.round((developers / total) * 100)}% of canvas`,
        accent: "orange",
      },
    ];
  }, [leads]);

  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
      {tiles.map((t) => (
        <div
          key={t.label}
          className="relative overflow-hidden rounded-xl border border-border bg-card p-4 shadow-sm"
        >
          <div className="flex items-center gap-2">
            <span
              className="size-2 rounded-full"
              style={{ background: ACCENT[t.accent ?? "lilac"] }}
              aria-hidden
            />
            <span className="font-mono text-[10px] uppercase tracking-wide text-muted-foreground">
              {t.label}
            </span>
          </div>
          <div className="mt-2 truncate text-2xl font-semibold leading-tight text-foreground">
            {t.value}
          </div>
          {t.meta ? (
            <div className="mt-1 truncate font-mono text-[11px] text-muted-foreground">
              {t.meta}
            </div>
          ) : null}
        </div>
      ))}
    </div>
  );
}
