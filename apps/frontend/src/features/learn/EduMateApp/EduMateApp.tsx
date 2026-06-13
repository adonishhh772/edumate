"use client";

import { useEffect, useState } from "react";
import {
  CopilotChatConfigurationProvider,
  CopilotSidebar,
  useAgent,
  useConfigureSuggestions,
  useDefaultRenderTool,
  useFrontendTool,
} from "@copilotkit/react-core/v2";
import { z } from "zod";
import { ThreadsDrawer } from "@/components/threads-drawer";
import drawerStyles from "@/components/threads-drawer/threads-drawer.module.css";
import { EducationContextBridge } from "@/components/education/EducationContextBridge";
import { ToolFallbackCard } from "@/components/copilot/ToolFallbackCard";
import { mergeEducationAgentState } from "@/lib/education/derive";
import type { EducationAgentState } from "@/lib/education/types";

function ClientOnly({ children }: { children: React.ReactNode }) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  if (!mounted) {
    return null;
  }
  return <>{children}</>;
}

function useLiveEducationState() {
  const { agent } = useAgent();
  const state = mergeEducationAgentState(agent?.state);
  const setState = (updater: (prev: EducationAgentState) => EducationAgentState) => {
    agent?.setState(updater(mergeEducationAgentState(agent?.state)));
  };
  return { state, setState };
}

function EduMateChatPanel() {
  const { state, setState } = useLiveEducationState();

  useConfigureSuggestions({
    suggestions: [
      { title: "Study plan", message: "What should I study today?" },
      { title: "Explain a topic", message: "Explain this topic in simple steps." },
    ],
  });

  useDefaultRenderTool({
    render: ({ name, status }) => (
      <ToolFallbackCard name={name} status={status} />
    ),
  });

  useFrontendTool({
    name: "setHeader",
    description: "Set the workspace heading shown to the student.",
    parameters: z.object({
      title: z.string().optional(),
      subtitle: z.string().optional(),
    }),
    handler: ({ title, subtitle }) => {
      setState((prev) => ({
        ...prev,
        header: {
          title: title ?? prev.header.title,
          subtitle: subtitle ?? prev.header.subtitle,
        },
      }));
    },
  });

  return (
    <div className="flex min-h-screen flex-col bg-[#0a0a1a] text-slate-100">
      <EducationContextBridge state={state} />
      <header className="border-b border-white/10 px-6 py-5" data-testid="edumate-header">
        <p className="text-xs font-semibold uppercase tracking-wider text-blue-300">
          EduMate
        </p>
        <h1 className="mt-1 text-2xl font-semibold">{state.header.title}</h1>
        <p className="mt-1 text-sm text-slate-400">{state.header.subtitle}</p>
        {state.profile ? (
          <p className="mt-2 text-sm text-slate-300">
            {state.profile.name} · {state.profile.grade_level} · focus:{" "}
            {state.profile.focus_subject}
          </p>
        ) : null}
      </header>
      <div className="flex flex-1">
        <CopilotSidebar
          defaultOpen
          labels={{
            title: "EduMate Tutor",
            initial: "Ask me to explain a topic or plan your study session.",
          }}
        />
      </div>
    </div>
  );
}

function EduMateShell() {
  const [threadId, setThreadId] = useState<string | undefined>(undefined);

  return (
    <div className={drawerStyles.layout}>
      <ThreadsDrawer
        agentId="default"
        threadId={threadId}
        onThreadChange={setThreadId}
      />
      <div className={drawerStyles.mainPanel}>
        <CopilotChatConfigurationProvider agentId="default" threadId={threadId}>
          <EduMateChatPanel />
        </CopilotChatConfigurationProvider>
      </div>
    </div>
  );
}

export function EduMateApp() {
  return (
    <ClientOnly>
      <EduMateShell />
    </ClientOnly>
  );
}
