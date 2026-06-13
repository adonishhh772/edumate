"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { LeadMiniCard } from "@/components/leads/inline/LeadMiniCard";
import { EmailDraftCard } from "@/components/leads/inline/EmailDraftCard";
import { WorkshopDemand } from "@/components/leads/WorkshopDemand";
import { QuickStats } from "@/components/leads/QuickStats";
import { StatusDonut } from "@/components/leads/StatusDonut";
import { ToolFallbackCard } from "@/components/copilot/ToolFallbackCard";
import type { Lead } from "@/lib/leads/types";

const MOCK_LEADS: Lead[] = [
  mockLead("01", "Ada Lovelace", "Mango Labs", "Founder", "Agentic UI (AG-UI)", "Advanced / expert", "In progress", true),
  mockLead("02", "Grace Hopper", "Yard Robotics", "VP Eng", "Deploying Agents (prod)", "Developer", "Done", true),
  mockLead("03", "Linus Pauling", "Helix Health", "Staff Engineer", "RAG & Data Chat", "Developer", "Not started", true),
  mockLead("04", "Marie Curie", "Atom Industries", "Scientist", "Evaluations & Guardrails", "Some technical", "Not started", false),
  mockLead("05", "Alan Turing", "Cipher Bio", "Founder", "Agentic UI (AG-UI)", "Developer", "In progress", true),
  mockLead("06", "Rosa Parks", "Bus Stop AI", "PM", "MCP Apps / Tooling", "Some technical", "Not started", true),
  mockLead("07", "Nikola Tesla", "Coil Co.", "CTO", "Deploying Agents (prod)", "Advanced / expert", "Done", true),
  mockLead("08", "Hedy Lamarr", "Spread Spectrum", "Founder", "RAG & Data Chat", "Developer", "Not started", true),
  mockLead("09", "Carl Sagan", "Pale Blue", "Researcher", "MCP Apps / Tooling", "Developer", "In progress", false),
  mockLead("10", "Stephen Hawking", "Black Hole Cap.", "Investor", "Not sure yet", "Non-technical", "Not started", true),
];

function mockLead(
  id: string,
  name: string,
  company: string,
  role: string,
  workshop: string,
  technical_level: string,
  status: string = "Not started",
  opt_in: boolean = true,
): Lead {
  return {
    id,
    name,
    company,
    role,
    email: `${name.toLowerCase().replace(/\s+/g, ".")}@example.com`,
    technical_level,
    interested_in: [],
    tools: [],
    workshop,
    status,
    opt_in,
    message: "",
    submitted_at: new Date().toISOString(),
  };
}

const MUTATORS: Array<{ name: string; signature: string; blurb: string }> = [
  {
    name: "setHeader",
    signature: "{ title?, subtitle? }",
    blurb: "Sets the canvas title and subtitle.",
  },
  {
    name: "setLeads",
    signature: "{ leads: Lead[] }",
    blurb: "Replaces the lead list. Called once after the agent fetches from Notion.",
  },
  {
    name: "setSyncMeta",
    signature: "{ databaseId?, databaseTitle?, syncedAt? }",
    blurb: "Records which Notion database the canvas mirrors and when we last synced.",
  },
  {
    name: "setFilter",
    signature: "{ workshops?, technical_levels?, tools?, opt_in?, search? }",
    blurb: "Partial-merges into the filter. Empty arrays clear a single facet.",
  },
  {
    name: "clearFilters",
    signature: "{}",
    blurb: "Resets every filter facet so all loaded leads are visible.",
  },
  {
    name: "highlightLeads",
    signature: "{ leadIds: string[] }",
    blurb: "Visually highlights a subset of cards in the kanban.",
  },
  {
    name: "selectLead",
    signature: "{ leadId: string | null }",
    blurb: "Marks a single lead as the focused one (used by mini-card click-through).",
  },
  {
    name: "commitLeadEdit",
    signature: "{ leadId, patch }",
    blurb:
      "Optimistic edit — patches the canvas immediately and asks the agent to persist via update_notion_lead. Rolls back on failure.",
  },
];

export default function ShowcasePage() {
  return (
    <main className="mx-auto min-h-screen max-w-5xl px-6 py-12 md:px-12">
      <Link
        href="/"
        className="inline-flex items-center gap-1.5 font-mono text-[11px] uppercase tracking-wide text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="size-3.5" /> back
      </Link>

      <header className="mt-6 mb-12">
        <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-accent">
          Reference
        </p>
        <h1 className="text-4xl font-semibold leading-tight text-foreground md:text-5xl">
          Frontend tool surface
        </h1>
        <p className="mt-4 max-w-2xl text-base leading-relaxed text-muted-foreground">
          Every tool and gen-UI component the agent can call from{" "}
          <code className="rounded bg-muted px-1 py-0.5 font-mono text-[12px]">
            apps/frontend/src/app/leads/page.tsx
          </code>
          . State mutators run silently; controlled gen UI mounts a specific
          React component in chat; the open gen UI fallback catches anything
          else.
        </p>
      </header>

      <Section
        eyebrow="Canvas dashboard"
        title="Quick stats + status donut + workshop bars"
        blurb="The dashboard row above the kanban. Quick stats summarize the canvas at a glance; the donut shows how leads split across kanban statuses; the bars rank workshops by demand. All read directly from agent state, all click-through to filter."
      >
        <div className="grid gap-3">
          <QuickStats leads={MOCK_LEADS} />
          <div className="grid gap-3 md:grid-cols-2">
            <StatusDonut leads={MOCK_LEADS} />
            <WorkshopDemand leads={MOCK_LEADS} compact />
          </div>
        </div>
      </Section>

      <Section
        eyebrow="Open generative UI"
        title="Wildcard fallback (useDefaultRenderTool)"
        blurb="Catches every tool call that doesn't have a dedicated render slot — including backend tools the agent invokes through the Notion MCP server. One renderer, infinite tools."
      >
        <div className="grid gap-4 md:grid-cols-2">
          <ToolFallbackCard
            name="notion_query_database"
            status="executing"
            parameters={{
              database_id: "a274791c-4e1e-826d-882d-01562af74de9",
              page_size: 50,
            }}
          />
          <ToolFallbackCard
            name="update_notion_lead"
            status="complete"
            parameters={{ leadId: "abc123", patch: { status: "Done" } }}
            result='Updated "Ada Lovelace" status -> Done'
          />
        </div>
      </Section>

      <Section
        eyebrow="Controlled generative UI"
        title="renderLeadMiniCard"
        blurb="Mounted inline in chat when the agent mentions a specific lead. Clicking the card fires selectLead on the canvas."
      >
        <div className="flex flex-wrap gap-4">
          <LeadMiniCard
            leadId={MOCK_LEADS[0].id}
            name={MOCK_LEADS[0].name}
            role={MOCK_LEADS[0].role}
            company={MOCK_LEADS[0].company}
            email={MOCK_LEADS[0].email}
            workshop={MOCK_LEADS[0].workshop}
            technical_level={MOCK_LEADS[0].technical_level}
          />
          <LeadMiniCard
            leadId={MOCK_LEADS[3].id}
            name={MOCK_LEADS[3].name}
            role={MOCK_LEADS[3].role}
            company={MOCK_LEADS[3].company}
            email={MOCK_LEADS[3].email}
            workshop={MOCK_LEADS[3].workshop}
            technical_level={MOCK_LEADS[3].technical_level}
          />
        </div>
      </Section>

      <Section
        eyebrow="Controlled generative UI"
        title="renderWorkshopDemand"
        blurb="Same component used at the top of the canvas, rendered inline in chat when the agent answers a 'what's hot' question. Reads agent state — no args."
      >
        <div className="grid gap-6 md:grid-cols-2">
          <div>
            <p className="mb-2 font-mono text-[11px] uppercase tracking-wide text-muted-foreground">
              Compact (chat-inline)
            </p>
            <WorkshopDemand leads={MOCK_LEADS} compact />
          </div>
          <div>
            <p className="mb-2 font-mono text-[11px] uppercase tracking-wide text-muted-foreground">
              Full (canvas)
            </p>
            <WorkshopDemand
              leads={MOCK_LEADS}
              selectedWorkshops={["Agentic UI (AG-UI)"]}
            />
          </div>
        </div>
      </Section>

      <Section
        eyebrow="Human in the loop"
        title="renderEmailDraft"
        blurb="Mounted when the user asks the agent to draft an outreach email. Subject and body are editable in the chat; clicking Send injects a follow-up message that asks the agent to persist the approved draft as a Notion comment via post_lead_comment."
      >
        <EmailDraftCard
          leadId={MOCK_LEADS[0].id}
          leadName={MOCK_LEADS[0].name}
          leadEmail={MOCK_LEADS[0].email}
          initialSubject="Following up on your AI Agentic UI workshop interest"
          initialBody={`Hi ${MOCK_LEADS[0].name.split(" ")[0]},\n\nThanks for signing up for the Agentic UI (AG-UI) workshop — your background at ${MOCK_LEADS[0].company} is exactly the profile we're building the curriculum for.\n\nA quick question before we lock the date: are there one or two specific patterns (state sync, tool gating, HITL) you're hoping we cover?\n\nBest,\nWorkshop team`}
          onSend={() => {
            /* showcase: no-op */
          }}
          onRegenerate={() => {
            /* showcase: no-op */
          }}
        />
      </Section>

      <Section
        eyebrow="State mutators"
        title="Tools that mutate the canvas (no render)"
        blurb="The agent calls these to drive the UI. Each is registered via useFrontendTool with a Zod schema and a handler. None of them render anything in chat — the canvas reflects the change."
      >
        <div className="overflow-hidden rounded-xl border border-border">
          <table className="w-full text-left">
            <thead className="bg-muted">
              <tr>
                <th className="px-4 py-2 font-mono text-[11px] uppercase tracking-wide text-muted-foreground">
                  name
                </th>
                <th className="px-4 py-2 font-mono text-[11px] uppercase tracking-wide text-muted-foreground">
                  signature
                </th>
                <th className="px-4 py-2 font-mono text-[11px] uppercase tracking-wide text-muted-foreground">
                  description
                </th>
              </tr>
            </thead>
            <tbody>
              {MUTATORS.map((m, i) => (
                <tr
                  key={m.name}
                  className={i % 2 === 0 ? "bg-card" : "bg-background"}
                >
                  <td className="px-4 py-3 align-top font-mono text-[12px] text-foreground">
                    {m.name}
                  </td>
                  <td className="px-4 py-3 align-top font-mono text-[11px] text-muted-foreground">
                    {m.signature}
                  </td>
                  <td className="px-4 py-3 align-top text-sm text-foreground">
                    {m.blurb}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      <p className="mt-12 text-sm text-muted-foreground">
        See the wiring in{" "}
        <Link
          href="https://github.com/jerelvelarde/global-hackathon-starter-kit"
          className="font-mono text-[12px] underline decoration-dotted underline-offset-4 hover:text-foreground"
        >
          apps/frontend/src/app/leads/page.tsx
        </Link>
        .
      </p>
    </main>
  );
}

function Section({
  eyebrow,
  title,
  blurb,
  children,
}: {
  eyebrow: string;
  title: string;
  blurb: string;
  children: React.ReactNode;
}) {
  return (
    <section className="mb-12 rounded-2xl border border-border bg-card p-6 md:p-8">
      <p className="mb-2 font-mono text-[11px] uppercase tracking-widest text-accent">
        {eyebrow}
      </p>
      <h2 className="text-2xl font-semibold text-foreground">{title}</h2>
      <p className="mb-6 mt-2 max-w-2xl text-sm leading-relaxed text-muted-foreground">
        {blurb}
      </p>
      {children}
    </section>
  );
}
