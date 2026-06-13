"use client";

import { useMemo } from "react";
import type { Lead } from "@/lib/leads/types";
import { STATUSES } from "@/lib/leads/types";

export interface StatusDonutProps {
  leads: Lead[];
}

const STATUS_COLOR: Record<string, string> = {
  "Not started": "#BEC2FF", // lilac
  "In progress": "#85ECCE", // mint
  Done: "#3D92E8", // blue
};

const STATUS_TRACK = "#F0F0F4";

export function StatusDonut({ leads }: StatusDonutProps) {
  const segments = useMemo(() => {
    const counts = new Map<string, number>();
    for (const s of STATUSES) counts.set(s, 0);
    for (const l of leads) {
      const s = l.status || "Not started";
      counts.set(s, (counts.get(s) ?? 0) + 1);
    }
    return STATUSES.map((s) => ({ status: s, count: counts.get(s) ?? 0 }));
  }, [leads]);

  const total = leads.length;
  const radius = 56;
  const stroke = 14;
  const circumference = 2 * Math.PI * radius;

  let offset = 0;
  const arcs = segments.map((seg) => {
    const fraction = total === 0 ? 0 : seg.count / total;
    const length = fraction * circumference;
    const dasharray = `${length} ${circumference - length}`;
    const dashoffset = -offset;
    offset += length;
    return { ...seg, dasharray, dashoffset };
  });

  return (
    <div className="flex h-full items-center gap-5 rounded-xl border border-border bg-card p-4 shadow-sm">
      <div className="relative shrink-0">
        <svg
          width={radius * 2 + stroke * 2}
          height={radius * 2 + stroke * 2}
          viewBox={`0 0 ${radius * 2 + stroke * 2} ${radius * 2 + stroke * 2}`}
        >
          <g
            transform={`translate(${radius + stroke}, ${radius + stroke}) rotate(-90)`}
          >
            <circle
              r={radius}
              fill="none"
              stroke={STATUS_TRACK}
              strokeWidth={stroke}
            />
            {total > 0
              ? arcs.map((arc) => (
                  <circle
                    key={arc.status}
                    r={radius}
                    fill="none"
                    stroke={STATUS_COLOR[arc.status] ?? "#BEC2FF"}
                    strokeWidth={stroke}
                    strokeDasharray={arc.dasharray}
                    strokeDashoffset={arc.dashoffset}
                    strokeLinecap="butt"
                  />
                ))
              : null}
          </g>
          <text
            x="50%"
            y="50%"
            dominantBaseline="middle"
            textAnchor="middle"
            className="fill-foreground"
            style={{ fontSize: 22, fontWeight: 600 }}
          >
            {total}
          </text>
          <text
            x="50%"
            y="62%"
            dominantBaseline="middle"
            textAnchor="middle"
            className="fill-muted-foreground"
            style={{ fontSize: 9, letterSpacing: 0.5, fontFamily: "var(--font-mono)", textTransform: "uppercase" }}
          >
            leads
          </text>
        </svg>
      </div>

      <div className="min-w-0 flex-1">
        <div className="font-mono text-[10px] uppercase tracking-wide text-muted-foreground">
          status
        </div>
        <ul className="mt-2 grid gap-1.5">
          {segments.map((seg) => {
            const pct = total === 0 ? 0 : Math.round((seg.count / total) * 100);
            return (
              <li
                key={seg.status}
                className="flex items-center gap-2 text-sm"
              >
                <span
                  className="size-2.5 shrink-0 rounded-full"
                  style={{ background: STATUS_COLOR[seg.status] ?? "#BEC2FF" }}
                  aria-hidden
                />
                <span className="min-w-0 flex-1 truncate text-foreground">
                  {seg.status}
                </span>
                <span className="font-mono text-[12px] text-muted-foreground">
                  {seg.count}
                </span>
                <span className="w-9 text-right font-mono text-[10px] text-muted-foreground">
                  {pct}%
                </span>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}
