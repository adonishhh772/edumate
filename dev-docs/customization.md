# Customization Guide

The canvas is a single page — `apps/frontend/src/app/leads/page.tsx` — that registers a small set of frontend tools the agent calls. There's no card-renderer registry to extend; you add to the surface by registering more tools and components.

## Add a frontend tool the agent can call

Two flavors:

### 1. State mutator (no render)

Use this when you want the agent to update something on the canvas (filter, header, selection, edit) without showing anything in chat.

```tsx
useFrontendTool({
  name: "highlightLeads",
  description: "Visually highlight a subset of leads.",
  parameters: z.object({ leadIds: z.array(z.string()) }),
  handler: async ({ leadIds }) => {
    updateState((prev) => ({ ...prev, highlightedLeadIds: leadIds }));
    return `highlighted ${leadIds.length} leads`;
  },
});
```

Add the tool name + description to the `FRONTEND_TOOLS` block in `apps/agent/src/prompts.py` so the agent knows when to call it. Don't add a duplicate Python wrapper — Gemini rejects duplicate function declarations. The Python stubs in `apps/agent/src/canvas.py` are documentation only.

### 2. Controlled generative UI (named render slot)

Use this when the agent should mount a specific React component inline in chat — like the existing `renderLeadMiniCard` and `renderWorkshopDemand`. Register the tool with a `render` callback instead of a `handler`:

```tsx
useFrontendTool({
  name: "renderLeadMiniCard",
  description: "Render an inline lead card when mentioning a lead by name.",
  parameters: z.object({
    leadId: z.string(),
    name: z.string().optional(),
    /* … */
  }),
  render: ({ args }) => (
    <LeadMiniCard leadId={args.leadId} name={args.name} /* … */ />
  ),
});
```

If you want the rendered component to read live agent state (like `LiveWorkshopDemand` does), keep the `render` callback trivial and have the wrapper component call `useAgent()` itself — v2 `useFrontendTool({ render })` registers the closure once on first mount, so a render that captures state directly will go stale.

### 3. Open generative UI (wildcard fallback)

Already wired once in `apps/frontend/src/app/leads/page.tsx`:

```tsx
useDefaultRenderTool({
  render: ({ name, status, result, parameters }) => (
    <ToolFallbackCard name={name} status={status} result={result} parameters={parameters} />
  ),
});
```

Any tool the agent calls that doesn't have a dedicated `render` slot — including backend tools the agent triggers via the Notion MCP server, or new tools you add later — falls through to this card automatically. You don't need to register a per-tool renderer until you want a custom one.

## Add a HITL (human-in-the-loop) component

The email-draft card is the reference. The pattern:

1. Build a controlled component (`apps/frontend/src/components/leads/inline/EmailDraftCard.tsx`) with internal state for editable fields and explicit `onSend` / `onCancel` props.
2. Register a `renderXxx` tool with the parameters the agent supplies as the initial draft. In the `render` callback, hand the args to your component and wire `onSend` to `injectPrompt(...)` so the agent picks it up on the next turn.
3. Add a backend tool that does the actual write — see `post_lead_comment` in `apps/agent/src/notion_tools.py` (writes a comment via the Notion MCP server's `API-create-a-comment`).
4. Update the agent prompt: tell it to call your `renderXxx` tool *before* the write tool, never in the same turn.

## Swap the integration MCP server

1. Find an MCP server for your new integration (the [MCP server registry](https://github.com/modelcontextprotocol/servers) has dozens — Linear, Slack, GitHub, Google Drive, etc.).
2. Edit `apps/agent/src/notion_mcp.py` → replace the `mcpServers` config dict (`command`, `args`, `env`) with the new server's. Update the wrapper functions (`mcp_query_data_source`, `mcp_create_comment`, etc.) to call the new server's tool names.
3. Edit `apps/agent/src/notion_integration.py` → adjust the row-shaping logic if your new integration's response shape differs.
4. Edit `apps/agent/src/prompts.py` → `INTEGRATION_PROMPT`. Replace the Notion lead-form workflow prose with whatever the new integration expects (e.g. "When the user asks to file a bug, call `linear_create_issue` with…").
5. Restart the agent. Done.

## Add an MCP App tool

Three flavors depending on scope:

- **One more tool on the existing server.** Edit `apps/mcp/index.ts`, add another `server.tool({ ... }, async (input) => widget({ ... }))`. The runtime auto-discovers it on the next reload. If you want a visual widget alongside, drop a `resources/<widget-name>/widget.tsx` file using the `mcp-use/react` `useWidget()` hook (see the existing `canvas-dashboard` and `email-draft` widgets for the pattern).
- **A second MCP server alongside the kit's.** Scaffold with `npx create-mcp-use-app@latest <name>` (the official Manufact CLI) and register it in `apps/bff/src/server.ts` under `mcpApps.servers[]`. Useful when you want a clean separation between domains.
- **A remote MCP server.** Set `MCP_SERVER_URL` in `.env` to someone else's deploy (Excalidraw, etc.) — the runtime swaps without code changes.

## Add chat suggestion chips

Static chips that show before the first message are configured via `useConfigureSuggestions` inside `CanvasInner` in `apps/frontend/src/app/leads/page.tsx`. Add or change the entries in the `suggestions` array — `title` is the chip label, `message` is what gets sent when clicked. For LLM-generated suggestions (regenerated each turn), pass `instructions` instead of `suggestions`.

## Use runtime context from the UI

If you need to feed UI state (selected lead, current filter) into the agent's prompt, use `useAgentContext({ description, value })` from `@copilotkit/react-core/v2` inside a client component. The provided value is JSON-serialized and threaded into the agent's context on every turn — composing with the static `LEAD_TRIAGE_PROMPT` defined in `apps/agent/src/prompts.py`.
