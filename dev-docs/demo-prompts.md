# Demo prompts

Drop these into the chat to exercise each layer:

**Notion MCP (external integration)**
- "Import the workshop leads from Notion."

**Canvas (agent-driven UI — state mutators)**
- "Highlight every lead with technical_level Developer or Advanced / expert."
- "Show me only the AG-UI workshop leads."
- "Open Ada Lovelace."
- "Move Ada to In progress."

**Controlled generative UI (named renderers)**
- "What workshops are most in demand right now?" → mounts `<WorkshopDemand>` inline in chat.
- "Tell me about Ada Lovelace and show her mini card." → mounts `<LeadMiniCard>` inline.

**Open generative UI (wildcard fallback)**
- Any backend tool the agent calls (e.g. `find_lead`, `update_notion_lead`, `notion_health_check`) renders in the `ToolFallbackCard` automatically. Try: "Run the Notion health check." — you'll see the running → complete card with the JSON payload.

**Human-in-the-loop**
- "Draft an outreach email to Ada Lovelace." → mounts the editable `EmailDraftCard`. Edit subject/body, click Send, the agent posts the approved draft to the lead's Notion page via `post_lead_comment`.

**Multi-step planning (Deep Agents)**
- "Find the top 3 hottest leads and draft an email to each."

**Intelligence (durable threads)**
- "Open my last thread from earlier."
- *(Reload the browser. The conversation is still in the sidebar.)*

**Manufact MCP** *(requires `npm run dev:full` so the MCP server is running)*
- "Show me the canvas dashboard." → `show-canvas-dashboard` widget
- "Show me an email draft." → `show-email-draft` widget (HITL — Send fires `post-email-comment`)
- "Show me the workshop lead list." → `show-lead-list` widget
