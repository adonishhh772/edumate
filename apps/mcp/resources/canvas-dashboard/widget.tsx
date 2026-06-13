import { McpUseProvider, useWidget, type WidgetMetadata } from "mcp-use/react";
import React, { useMemo } from "react";
import { z } from "zod";
import { leadSchema, STATUSES, type Lead } from "../../src/lib/leads/types";
import { SAMPLE_LEADS } from "../../src/lib/leads/sample";

export const propSchema = z.object({
  leads: z
    .array(leadSchema)
    .default([])
    .describe(
      "Lead rows. Pass an empty array (or omit) to render with the sample dataset.",
    ),
});

export type CanvasDashboardWidgetProps = z.infer<typeof propSchema>;

export const widgetMetadata: WidgetMetadata = {
  description:
    "Render the Workshop Lead Triage canvas dashboard: 4 quick-stat tiles (total / opt-in % / top workshop / developers), a status donut, and a workshop-demand bar chart.",
  props: propSchema,
  exposeAsTool: false,
  metadata: {
    prefersBorder: false,
    invoking: "Aggregating leads…",
    invoked: "Dashboard ready",
  },
};

const ACCENTS = {
  lilac: "#BEC2FF",
  mint: "#85ECCE",
  blue: "#3D92E8",
  orange: "#FFAC4D",
  track: "#F0F0F4",
} as const;

const STATUS_COLOR: Record<string, string> = {
  "Not started": ACCENTS.lilac,
  "In progress": ACCENTS.mint,
  Done: ACCENTS.blue,
};

const CanvasDashboardWidget: React.FC = () => {
  const { props, isPending } = useWidget<CanvasDashboardWidgetProps>();

  if (isPending) {
    return (
      <McpUseProvider autoSize>
        <div className="p-6 text-sm text-neutral-500">Loading dashboard…</div>
      </McpUseProvider>
    );
  }

  const leads: Lead[] = props?.leads?.length ? props.leads : SAMPLE_LEADS;

  return (
    <McpUseProvider autoSize>
      <div className="w-full p-4 text-neutral-900">
        <div className="grid gap-3">
          <QuickStats leads={leads} />
          <div className="grid gap-3 md:grid-cols-2">
            <StatusDonut leads={leads} />
            <WorkshopBars leads={leads} />
          </div>
        </div>
      </div>
    </McpUseProvider>
  );
};

export default CanvasDashboardWidget;

// ---------- QuickStats ----------

interface Tile {
  label: string;
  value: string;
  meta?: string;
  accent: keyof typeof ACCENTS;
}

function QuickStats({ leads }: { leads: Lead[] }) {
  const tiles = useMemo<Tile[]>(() => {
    const total = leads.length;
    const optIns = leads.filter((l) => l.opt_in).length;
    const optInPct = total === 0 ? 0 : Math.round((optIns / total) * 100);

    const counts = new Map<string, number>();
    for (const l of leads) {
      const w = l.workshop || "Not sure yet";
      counts.set(w, (counts.get(w) ?? 0) + 1);
    }
    let top: { name: string; count: number } | null = null;
    for (const [name, count] of counts) {
      if (!top || count > top.count) top = { name, count };
    }

    const developers = leads.filter(
      (l) =>
        l.technical_level === "Developer" ||
        l.technical_level === "Advanced / expert",
    ).length;

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
        value: top?.name ?? "—",
        meta: top ? `${top.count} interested` : "no leads yet",
        accent: "blue",
      },
      {
        label: "developers",
        value: developers.toString(),
        meta:
          total === 0 ? "—" : `${Math.round((developers / total) * 100)}% of canvas`,
        accent: "orange",
      },
    ];
  }, [leads]);

  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
      {tiles.map((t) => (
        <div
          key={t.label}
          className="rounded-xl border border-[#DBDBE5] bg-white p-4 shadow-sm"
        >
          <div className="flex items-center gap-2">
            <span
              className="size-2 rounded-full"
              style={{ background: ACCENTS[t.accent] }}
              aria-hidden
            />
            <span
              className="text-[10px] uppercase tracking-wide text-neutral-500"
              style={{ fontFamily: "ui-monospace, SFMono-Regular, monospace" }}
            >
              {t.label}
            </span>
          </div>
          <div className="mt-2 truncate text-2xl font-semibold leading-tight text-neutral-900">
            {t.value}
          </div>
          {t.meta ? (
            <div
              className="mt-1 truncate text-[11px] text-neutral-500"
              style={{ fontFamily: "ui-monospace, SFMono-Regular, monospace" }}
            >
              {t.meta}
            </div>
          ) : null}
        </div>
      ))}
    </div>
  );
}

// ---------- StatusDonut ----------

function StatusDonut({ leads }: { leads: Lead[] }) {
  const segments = useMemo(() => {
    const counts = new Map<string, number>();
    for (const s of STATUSES) counts.set(s, 0);
    for (const l of leads) {
      const s = (STATUSES as readonly string[]).includes(l.status)
        ? l.status
        : "Not started";
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
    <div className="flex h-full items-center gap-5 rounded-xl border border-[#DBDBE5] bg-white p-4 shadow-sm">
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
              stroke={ACCENTS.track}
              strokeWidth={stroke}
            />
            {total > 0
              ? arcs.map((arc) => (
                  <circle
                    key={arc.status}
                    r={radius}
                    fill="none"
                    stroke={STATUS_COLOR[arc.status] ?? ACCENTS.lilac}
                    strokeWidth={stroke}
                    strokeDasharray={arc.dasharray}
                    strokeDashoffset={arc.dashoffset}
                  />
                ))
              : null}
          </g>
          <text
            x="50%"
            y="50%"
            dominantBaseline="middle"
            textAnchor="middle"
            fill="#010507"
            style={{ fontSize: 22, fontWeight: 600 }}
          >
            {total}
          </text>
          <text
            x="50%"
            y="62%"
            dominantBaseline="middle"
            textAnchor="middle"
            fill="#838389"
            style={{
              fontSize: 9,
              letterSpacing: 0.5,
              fontFamily: "ui-monospace, SFMono-Regular, monospace",
              textTransform: "uppercase",
            }}
          >
            leads
          </text>
        </svg>
      </div>

      <div className="min-w-0 flex-1">
        <div
          className="text-[10px] uppercase tracking-wide text-neutral-500"
          style={{ fontFamily: "ui-monospace, SFMono-Regular, monospace" }}
        >
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
                  style={{
                    background: STATUS_COLOR[seg.status] ?? ACCENTS.lilac,
                  }}
                  aria-hidden
                />
                <span className="min-w-0 flex-1 truncate text-neutral-900">
                  {seg.status}
                </span>
                <span
                  className="text-[12px] text-neutral-500"
                  style={{
                    fontFamily: "ui-monospace, SFMono-Regular, monospace",
                  }}
                >
                  {seg.count}
                </span>
                <span
                  className="w-9 text-right text-[10px] text-neutral-500"
                  style={{
                    fontFamily: "ui-monospace, SFMono-Regular, monospace",
                  }}
                >
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

// ---------- WorkshopBars ----------

function WorkshopBars({ leads }: { leads: Lead[] }) {
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
      <div className="rounded-xl border border-[#DBDBE5] bg-white p-4 text-sm text-neutral-500 shadow-sm">
        No leads loaded yet.
      </div>
    );
  }

  const visible = rows.slice(0, 6);
  const max = Math.max(1, ...visible.map((r) => r.count));

  return (
    <section className="flex h-full flex-col rounded-xl border border-[#DBDBE5] bg-white p-4 shadow-sm">
      <header className="mb-3 flex items-baseline justify-between gap-3">
        <span
          className="text-[10px] uppercase tracking-wide text-neutral-500"
          style={{ fontFamily: "ui-monospace, SFMono-Regular, monospace" }}
        >
          workshop demand
        </span>
        <span
          className="text-[10px] uppercase tracking-wide text-neutral-500"
          style={{ fontFamily: "ui-monospace, SFMono-Regular, monospace" }}
        >
          {rows.length} workshops
        </span>
      </header>
      <ul className="flex flex-col gap-1.5">
        {visible.map((row) => {
          const pct = (row.count / max) * 100;
          return (
            <li
              key={row.label}
              className="grid grid-cols-[120px_minmax(0,1fr)_32px] items-center gap-3 px-2 py-1.5"
            >
              <span
                className="truncate text-[12px] text-neutral-900"
                title={row.label}
              >
                {row.label}
              </span>
              <span
                className="relative h-2 overflow-hidden rounded-full"
                style={{ background: ACCENTS.track }}
                aria-hidden
              >
                <span
                  className="absolute inset-y-0 left-0 rounded-full"
                  style={{
                    width: `${pct}%`,
                    background: ACCENTS.lilac,
                  }}
                />
              </span>
              <span
                className="text-right text-[11px] tabular-nums text-neutral-900"
                style={{ fontFamily: "ui-monospace, SFMono-Regular, monospace" }}
              >
                {row.count}
              </span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
