"""Canvas state schema + frontend tool reference (documentation only).

In CopilotKit v2, the **React side is the single source of truth** for
frontend tools: each `useFrontendTool({ name, parameters, handler })` call
in `apps/frontend/src/app/leads/page.tsx` declares the tool's schema to
the runtime AND provides the handler. The runtime forwards those
declarations into the agent's tool list at run time, so the LLM sees them
automatically.

The Python functions below are NOT registered with the agent — passing them
to `create_deep_agent(tools=[...])` would cause Gemini to reject the request
with "Duplicate function declaration found: <name>". They live here as a
quick contract reference for anyone reading the agent code. The actual
schema is in `apps/frontend/src/app/leads/page.tsx`.

The state shape mirrors the React `AgentState` shape; canvas state flows
through CopilotKit's shared-state mechanism (`useAgent` +
`agent.setState(...)`), not via the deepagents API. `create_deep_agent`
does not accept (and does not need) a `state_schema=` kwarg.

Frontend tool surface (all declared on the React side):

  state mutators:
    setHeader, setLeads, setSyncMeta, setFilter, clearFilters,
    highlightLeads, selectLead, commitLeadEdit
  controlled gen UI:
    renderLeadMiniCard, renderWorkshopDemand
  open gen UI:
    everything else falls through `useDefaultRenderTool` to a generic
    CopilotKit-branded card.
"""

from typing import Annotated, Any, Dict, List, Literal, Optional, TypedDict
from typing_extensions import NotRequired


# --- Lead shape (mirrors apps/frontend/src/lib/leads/types.ts) -------------


class Lead(TypedDict, total=False):
    id: str
    url: str
    name: str
    company: str
    email: str
    role: str
    phone: str
    source: str
    technical_level: str
    interested_in: List[str]
    tools: List[str]
    workshop: str
    status: str
    opt_in: bool
    message: str
    submitted_at: str


class LeadFilter(TypedDict):
    workshops: List[str]
    technical_levels: List[str]
    tools: List[str]
    opt_in: Literal["any", "yes", "no"]
    search: str


class SyncMeta(TypedDict):
    databaseId: str
    databaseTitle: str
    syncedAt: Optional[str]


class CanvasState(TypedDict):
    leads: List[Lead]
    filter: LeadFilter
    highlightedLeadIds: List[str]
    selectedLeadId: Optional[str]
    header: NotRequired[Dict[str, str]]
    sync: NotRequired[SyncMeta]


# --- Frontend tool contract (documentation only — NOT registered) ---------
#
# The functions below mirror the `useFrontendTool` registrations in
# `apps/frontend/src/app/leads/page.tsx`. They exist so reviewers can see
# the contract at a glance from the agent side. They are deliberately NOT
# included in `frontend_tool_stubs` and NOT passed to
# `create_deep_agent(tools=)`. The React side declares them to the runtime,
# which forwards them to the agent at run time.


def setHeader(
    title: Annotated[Optional[str], "New workspace heading title."] = None,
    subtitle: Annotated[Optional[str], "New workspace heading subtitle."] = None,
) -> str:
    """Set the workspace heading."""
    return f"setHeader({title}, {subtitle})"


def setLeads(
    leads: Annotated[List[Lead], "Full lead list — replaces canvas state."],
) -> str:
    """REPLACE the entire canvas lead list."""
    return f"setLeads({len(leads)} leads)"


def setSyncMeta(
    databaseId: Annotated[Optional[str], "Notion DB id (or 'local')."] = None,
    databaseTitle: Annotated[Optional[str], "Notion DB title."] = None,
    syncedAt: Annotated[Optional[str], "ISO timestamp of last sync."] = None,
) -> str:
    """Record which lead store the canvas mirrors."""
    return f"setSyncMeta({databaseId}, {databaseTitle}, {syncedAt})"


def setFilter(
    patch: Annotated[Dict[str, Any], "Partial LeadFilter patch."],
) -> str:
    """Partial-merge into the canvas filter."""
    return f"setFilter({patch})"


def clearFilters() -> str:
    """Reset all filters to their empty defaults."""
    return "clearFilters()"


def highlightLeads(
    leadIds: Annotated[List[str], "Lead ids to visually highlight."],
) -> str:
    """Highlight a set of cards (visual emphasis only — not a filter)."""
    return f"highlightLeads({leadIds})"


def selectLead(
    leadId: Annotated[Optional[str], "Lead id to open, or None to close."],
) -> str:
    """Open / close the lead detail panel."""
    return f"selectLead({leadId})"


def commitLeadEdit(
    leadId: Annotated[str, "Lead id."],
    patch: Annotated[Dict[str, Any], "Partial Lead patch."],
) -> str:
    """Persist a single-lead patch to Notion AND to canvas state."""
    return f"commitLeadEdit({leadId}, {patch})"


def renderLeadMiniCard(
    leadId: Annotated[str, "Real lead id — see find_lead."],
    name: Annotated[Optional[str], "Optional display name."] = None,
) -> str:
    """Render an inline lead card in the chat stream."""
    return f"renderLeadMiniCard({leadId}, {name})"


def renderWorkshopDemand() -> str:
    """Render an inline mini-chart of workshop demand."""
    return "renderWorkshopDemand()"


# --- Export list ----------------------------------------------------------
# Intentionally empty: tools are declared on the React side via
# `useFrontendTool` and forwarded by the runtime. See module docstring.

frontend_tool_stubs: list = []
