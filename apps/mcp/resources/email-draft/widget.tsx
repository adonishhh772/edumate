import {
  McpUseProvider,
  useCallTool,
  useWidget,
  type WidgetMetadata,
} from "mcp-use/react";
import React, { useState } from "react";
import { z } from "zod";

export const propSchema = z.object({
  leadId: z.string().describe("Notion page id of the lead to email."),
  leadName: z.string().optional().describe("Lead's full name."),
  leadEmail: z.string().optional().describe("Lead's email address."),
  leadCompany: z.string().optional(),
  leadRole: z.string().optional(),
  subject: z.string().describe("Initial subject line — user can edit."),
  body: z.string().describe("Initial email body — user can edit."),
});

export type EmailDraftWidgetProps = z.infer<typeof propSchema>;

export const widgetMetadata: WidgetMetadata = {
  description:
    "Render a human-in-the-loop email draft. The user can edit subject and body in place; clicking Send calls the post-email-comment tool to persist the message as a Notion page comment.",
  props: propSchema,
  exposeAsTool: false,
  metadata: {
    prefersBorder: false,
    invoking: "Drafting email…",
    invoked: "Draft ready",
  },
};

const EmailDraftWidget: React.FC = () => {
  const { props, isPending } = useWidget<EmailDraftWidgetProps>();
  const post = useCallTool("post-email-comment");

  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [seeded, setSeeded] = useState(false);
  const [view, setView] = useState<"editing" | "sent" | "discarded">("editing");

  if (isPending) {
    return (
      <McpUseProvider autoSize>
        <div className="p-6 text-sm text-neutral-500">Drafting email…</div>
      </McpUseProvider>
    );
  }

  if (!seeded && (props.subject || props.body)) {
    setSubject(props.subject ?? "");
    setBody(props.body ?? "");
    setSeeded(true);
  }

  const leadLabel = props.leadName ?? props.leadEmail ?? props.leadId;

  if (view === "sent") {
    return (
      <McpUseProvider autoSize>
        <div className="p-4">
          <div className="max-w-[460px] rounded-xl border border-[#DBDBE5] bg-white p-3 text-sm shadow-sm">
            <div className="flex items-center gap-2">
              <span className="grid size-5 place-items-center rounded-full bg-[#85ECCE]">
                <svg
                  width="12"
                  height="12"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="#010507"
                  strokeWidth="3"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              </span>
              <span
                className="text-[11px] uppercase tracking-wide text-neutral-500"
                style={{ fontFamily: "ui-monospace, SFMono-Regular, monospace" }}
              >
                posted to notion
              </span>
            </div>
            <p className="mt-2 line-clamp-2 text-neutral-900">{subject}</p>
          </div>
        </div>
      </McpUseProvider>
    );
  }

  if (view === "discarded") {
    return (
      <McpUseProvider autoSize>
        <div className="p-4">
          <div className="max-w-[460px] rounded-xl border border-dashed border-[#DBDBE5] bg-[#F7F7F9] p-3 text-sm">
            <span
              className="text-[11px] uppercase tracking-wide text-neutral-500"
              style={{ fontFamily: "ui-monospace, SFMono-Regular, monospace" }}
            >
              draft discarded
            </span>
          </div>
        </div>
      </McpUseProvider>
    );
  }

  const sending = post.isPending;
  const canSend =
    !sending && subject.trim().length > 0 && body.trim().length > 0;

  return (
    <McpUseProvider autoSize>
      <div className="p-4">
        <div className="w-full max-w-[460px] overflow-hidden rounded-xl border border-[#DBDBE5] bg-white text-sm shadow-sm">
          <div className="flex items-center gap-2 border-b border-[#DBDBE5] bg-[#FAFAFC] px-3 py-2">
            <span
              className="size-2 shrink-0 rounded-full bg-[#BEC2FF]"
              aria-hidden
            />
            <span
              className="text-[11px] uppercase tracking-wide text-neutral-500"
              style={{ fontFamily: "ui-monospace, SFMono-Regular, monospace" }}
            >
              email draft
            </span>
            <span
              className="ml-auto truncate text-[11px] text-neutral-500"
              style={{ fontFamily: "ui-monospace, SFMono-Regular, monospace" }}
            >
              {leadLabel}
            </span>
          </div>

          <div className="p-3">
            <label
              className="mb-1 block text-[10px] uppercase tracking-wide text-neutral-500"
              style={{ fontFamily: "ui-monospace, SFMono-Regular, monospace" }}
            >
              subject
            </label>
            <input
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              disabled={sending}
              className="w-full rounded-md border border-[#DBDBE5] bg-white px-2.5 py-1.5 text-neutral-900 outline-none transition focus:border-[#BEC2FF] focus:ring-2 focus:ring-[#BEC2FF]/40 disabled:bg-neutral-100"
            />

            <label
              className="mb-1 mt-3 block text-[10px] uppercase tracking-wide text-neutral-500"
              style={{ fontFamily: "ui-monospace, SFMono-Regular, monospace" }}
            >
              body
            </label>
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              disabled={sending}
              rows={7}
              className="w-full resize-y rounded-md border border-[#DBDBE5] bg-white px-2.5 py-1.5 leading-relaxed text-neutral-900 outline-none transition focus:border-[#BEC2FF] focus:ring-2 focus:ring-[#BEC2FF]/40 disabled:bg-neutral-100"
            />
          </div>

          <div className="flex items-center gap-2 border-t border-[#DBDBE5] bg-[#FAFAFC] px-3 py-2">
            <button
              type="button"
              onClick={() => setView("discarded")}
              disabled={sending}
              className="ml-auto inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-[11px] uppercase tracking-wide text-neutral-500 transition hover:bg-[#BEC2FF1A] hover:text-neutral-900 disabled:opacity-50"
              style={{ fontFamily: "ui-monospace, SFMono-Regular, monospace" }}
            >
              discard
            </button>
            <button
              type="button"
              disabled={!canSend}
              onClick={() => {
                post.callTool(
                  { leadId: props.leadId, subject, body },
                  {
                    onSuccess: () => setView("sent"),
                  },
                );
              }}
              className="inline-flex items-center gap-1.5 rounded-md bg-[#010507] px-3 py-1.5 text-[11px] uppercase tracking-wide text-white transition hover:bg-[#2B2B2B] disabled:bg-neutral-200 disabled:text-neutral-400"
              style={{ fontFamily: "ui-monospace, SFMono-Regular, monospace" }}
            >
              {sending ? "sending…" : "send"}
            </button>
          </div>
        </div>
      </div>
    </McpUseProvider>
  );
};

export default EmailDraftWidget;
