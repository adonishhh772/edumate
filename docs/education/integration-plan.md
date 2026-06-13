# EduMate × copilotkitui-hackathon integration plan

## Comparison at a glance

| Area | copilotkitui-hackathon (Acme) | EduMate (current) |
|------|-------------------------------|-------------------|
| Domain | Enterprise customer ops | Student learning (pivot in progress) |
| CopilotKit path | React → Express runtime → FastAPI AG-UI | Next.js → Hono BFF → LangGraph dev |
| Agent model | Single ReAct + optional multi-agent supervisor | Deep Agent (Gemini) + education/leads domains |
| Prompts | Versioned YAML + Langfuse | Python constants (education module added) |
| Skills | Registry of structured workflows | Not yet (port candidate) |
| Context | `useAgentContext` workspace bridge | `EducationContextBridge` added |
| Data | Postgres + MCP + RAG | Local seed JSON (students/assignments) |
| Auth | Keycloak RBAC | Hackathon default user (seed) |

## What we ported now (initial setup)

1. **Education domain scaffold** — student profile, assignments, filters, sync metadata
2. **`AGENT_DOMAIN=education`** — switches agent prompts and state middleware
3. **`/learn` route** — student workspace with CopilotKit sidebar and frontend tools
4. **`EducationContextBridge`** — mirrors Acme's context injection pattern
5. **Seed data** — `students.seed.json`, `assignments.seed.json`

## Patterns to port next (from hackathon)

| Priority | Pattern | Hackathon source | EduMate target |
|----------|---------|------------------|----------------|
| High | Skills registry | `apps/api/skills/` | `apps/agent/src/education/skills/` |
| High | YAML prompt versions | `apps/api/prompts/*.yaml` | `apps/agent/prompts/education/*.yaml` |
| Medium | Multi-agent routing | `multi_agent.py` + `routing.py` | Tutor / quiz / planner specialists |
| Medium | Fast-path bundled queries | `operational_fast_path.py` | "Summarize my week" study briefing |
| Low | Keycloak RBAC | `apps/api/auth/` | Real student/teacher roles |

## EduMate routes

| Route | Purpose |
|-------|---------|
| `/` | **Only UI** — student chat + threads sidebar |

Legacy demo routes (`/leads`, `/showcase`, `/about`) remain in the repo but are not linked in the app shell.

## Env switches

```bash
# Student education mode (default)
AGENT_DOMAIN=education

# Legacy lead-triage demo
AGENT_DOMAIN=leads
```

## Open questions (for your detailed requirements)

1. Single student profile or multi-student classroom view?
2. Data source: local JSON, Postgres, LMS API, or Notion?
3. Agent personas: one tutor vs. specialist agents (quiz, planner, explainer)?
4. Teacher/admin dashboard needed in v1?
5. Authentication model for students?

## Next implementation slice (recommended)

1. Define final student entities and persistence layer
2. Add backend tools (`fetch_assignments`, `update_progress`)
3. Port one skill workflow (e.g. study plan generator)
4. Replace seed hydration with real API/store
5. Add tests for `/learn` frontend tools and education middleware
