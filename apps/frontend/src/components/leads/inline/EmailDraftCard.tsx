"use client";

import { useState } from "react";
import { Send, X, RefreshCw, Check } from "lucide-react";

export interface EmailDraftCardProps {
  leadId: string;
  leadName?: string;
  leadEmail?: string;
  initialSubject: string;
  initialBody: string;
  /** Called when the user clicks Send. The card resolves to a "sent" view. */
  onSend: (final: { subject: string; body: string }) => void;
  /** Called when the user clicks Cancel/Discard. */
  onCancel?: () => void;
  /** Called when the user clicks Regenerate. The card stays editable. */
  onRegenerate?: () => void;
}

type Status = "editing" | "sending" | "sent" | "cancelled";

export function EmailDraftCard({
  leadId,
  leadName,
  leadEmail,
  initialSubject,
  initialBody,
  onSend,
  onCancel,
  onRegenerate,
}: EmailDraftCardProps) {
  const [subject, setSubject] = useState(initialSubject);
  const [body, setBody] = useState(initialBody);
  const [status, setStatus] = useState<Status>("editing");

  if (status === "sent") {
    return (
      <div className="my-2 max-w-[420px] rounded-xl border border-[#DBDBE5] bg-white p-3 text-sm shadow-sm">
        <div className="flex items-center gap-2 text-foreground">
          <span className="grid size-5 place-items-center rounded-full bg-[#85ECCE]">
            <Check className="size-3 text-[#010507]" />
          </span>
          <span className="font-mono text-[11px] uppercase tracking-wide text-muted-foreground">
            posted to notion
          </span>
        </div>
        <p className="mt-2 line-clamp-2 text-foreground">{subject}</p>
      </div>
    );
  }

  if (status === "cancelled") {
    return (
      <div className="my-2 max-w-[420px] rounded-xl border border-dashed border-[#DBDBE5] bg-[#F7F7F9] p-3 text-sm">
        <span className="font-mono text-[11px] uppercase tracking-wide text-muted-foreground">
          draft discarded
        </span>
      </div>
    );
  }

  const sending = status === "sending";

  return (
    <div className="my-2 w-full max-w-[460px] overflow-hidden rounded-xl border border-[#DBDBE5] bg-white text-sm shadow-sm">
      <div className="flex items-center gap-2 border-b border-[#DBDBE5] bg-[#FAFAFC] px-3 py-2">
        <span
          className="size-2 shrink-0 rounded-full bg-[#BEC2FF]"
          aria-hidden
        />
        <span className="font-mono text-[11px] uppercase tracking-wide text-muted-foreground">
          email draft
        </span>
        <span className="ml-auto truncate font-mono text-[11px] text-muted-foreground">
          {leadName ?? leadEmail ?? leadId}
        </span>
      </div>

      <div className="p-3">
        <label className="mb-1 block font-mono text-[10px] uppercase tracking-wide text-muted-foreground">
          subject
        </label>
        <input
          type="text"
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
          disabled={sending}
          className="w-full rounded-md border border-[#DBDBE5] bg-white px-2.5 py-1.5 text-foreground outline-none transition focus:border-[#BEC2FF] focus:ring-2 focus:ring-[#BEC2FF]/40 disabled:bg-muted disabled:text-muted-foreground"
        />

        <label className="mb-1 mt-3 block font-mono text-[10px] uppercase tracking-wide text-muted-foreground">
          body
        </label>
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          disabled={sending}
          rows={7}
          className="w-full resize-y rounded-md border border-[#DBDBE5] bg-white px-2.5 py-1.5 leading-relaxed text-foreground outline-none transition focus:border-[#BEC2FF] focus:ring-2 focus:ring-[#BEC2FF]/40 disabled:bg-muted disabled:text-muted-foreground"
        />
      </div>

      <div className="flex items-center gap-2 border-t border-[#DBDBE5] bg-[#FAFAFC] px-3 py-2">
        {onRegenerate ? (
          <button
            type="button"
            onClick={() => onRegenerate()}
            disabled={sending}
            className="inline-flex items-center gap-1.5 rounded-md px-2 py-1 font-mono text-[11px] uppercase tracking-wide text-muted-foreground transition hover:bg-[#BEC2FF1A] hover:text-foreground disabled:opacity-50"
          >
            <RefreshCw className="size-3" /> regenerate
          </button>
        ) : null}
        <button
          type="button"
          onClick={() => {
            setStatus("cancelled");
            onCancel?.();
          }}
          disabled={sending}
          className="ml-auto inline-flex items-center gap-1.5 rounded-md px-2 py-1 font-mono text-[11px] uppercase tracking-wide text-muted-foreground transition hover:bg-[#BEC2FF1A] hover:text-foreground disabled:opacity-50"
        >
          <X className="size-3" /> discard
        </button>
        <button
          type="button"
          onClick={() => {
            setStatus("sending");
            onSend({ subject, body });
            setStatus("sent");
          }}
          disabled={sending || !subject.trim() || !body.trim()}
          className="inline-flex items-center gap-1.5 rounded-md bg-[#010507] px-3 py-1.5 font-mono text-[11px] uppercase tracking-wide text-white transition hover:bg-[#2B2B2B] disabled:bg-muted disabled:text-muted-foreground"
        >
          <Send className="size-3" /> send
        </button>
      </div>
    </div>
  );
}
