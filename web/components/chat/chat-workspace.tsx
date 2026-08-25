"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useSyncChatErrorState } from "@/components/chat/chat-health-context";
import { ChatComposer } from "@/components/chat/chat-composer";
import { ChatThread } from "@/components/chat/chat-thread";
import { ToolAuditPane } from "@/components/chat/tool-audit-pane";
import type { AuditEvent, ChatEvent } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

type WorkspaceProps = {
  userId: string;
  /** Stable per page load; must be generated on the server to avoid hydration mismatches. */
  sessionId: string;
};

type StreamEvent = {
  type: ChatEvent["type"];
  [key: string]: unknown;
};

function isAuditEvent(event: ChatEvent): event is AuditEvent {
  return event.type === "audit";
}

/** Prefer Agent Catalog audit events; also keep tool_call / tool_result for completeness. */
function toAuditEvents(events: ChatEvent[]): AuditEvent[] {
  const fromCatalog = events.filter(isAuditEvent);
  const derived: AuditEvent[] = [];
  for (const event of events) {
    if (event.type === "tool_call") {
      derived.push({
        type: "audit",
        event_type: "tool_call",
        title: event.name,
        summary: event.args,
        status: "running",
        timestamp: event.started_at
      });
    } else if (event.type === "tool_result") {
      derived.push({
        type: "audit",
        event_type: "tool_result",
        title: event.name,
        summary: event.content.slice(0, 500),
        status: "success",
        duration_ms: event.runtime_ms,
        timestamp: Date.now()
      });
    }
  }
  return [...fromCatalog, ...derived];
}

export function ChatWorkspace({ userId, sessionId }: WorkspaceProps) {
  const [events, setEvents] = useState<ChatEvent[]>([]);
  const [isStreaming, setStreaming] = useState(false);
  const [showAuditPane, setShowAuditPane] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const auditEvents = useMemo(() => toAuditEvents(events), [events]);

  const hasError = useMemo(
    () => events.some((evt) => evt.type === "error"),
    [events]
  );

  useSyncChatErrorState(hasError);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    try {
      el.scrollTo({
        top: el.scrollHeight,
        behavior: isStreaming ? "auto" : "smooth"
      });
    } catch {
      el.scrollTop = el.scrollHeight;
    }
  }, [events, isStreaming]);

  async function sendPrompt(prompt: string) {
    setStreaming(true);
    setEvents((prev) => [
      ...prev,
      {
        type: "message",
        role: "user",
        content: prompt,
        raw: null
      }
    ]);
    try {
      const response = await fetch("/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: prompt, session_id: sessionId, user_id: userId })
      });
      if (!response.ok || !response.body) {
        const text = await response.text();
        throw new Error(text || "Unable to stream response.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const chunks = buffer.split("\n\n");
        buffer = chunks.pop() ?? "";

        for (const chunk of chunks) {
          if (!chunk.startsWith("data: ")) continue;
          const payload = chunk.replace(/^data: /, "");
          let parsed: StreamEvent;
          try {
            parsed = JSON.parse(payload) as StreamEvent;
          } catch {
            setEvents((prev) => [
              ...prev,
              {
                type: "error",
                message: "Received malformed stream data from the server."
              }
            ]);
            continue;
          }
          setEvents((prev) => [...prev, parsed as ChatEvent]);
        }
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown stream error";
      setEvents((prev) => [...prev, { type: "error", message }]);
    } finally {
      setStreaming(false);
    }
  }

  return (
    <section className="flex min-h-0 flex-1 flex-col gap-4">
      <div className="mx-auto w-full max-w-6xl shrink-0">
        <Card className="p-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <h3 className="text-sm font-semibold text-foreground">Session details</h3>
            <Button
              type="button"
              variant="secondary"
              className="h-8 px-3 text-xs"
              aria-pressed={showAuditPane}
              aria-controls="tool-audit-stream"
              onClick={() => setShowAuditPane((open) => !open)}
            >
              {showAuditPane ? "Hide tool audit" : "Show tool audit"}
            </Button>
          </div>
          <div className="mt-3 grid gap-2 text-xs text-muted sm:grid-cols-2">
            <div className="rounded-md border border-border bg-panelMuted/60 px-3 py-2">
              <p className="text-[11px] uppercase tracking-wide text-muted">User ID</p>
              <p className="mt-1 truncate font-mono text-sm text-foreground">{userId}</p>
            </div>
            <div className="rounded-md border border-border bg-panelMuted/60 px-3 py-2">
              <p className="text-[11px] uppercase tracking-wide text-muted">Session ID</p>
              <p className="mt-1 break-all font-mono text-sm text-foreground">{sessionId}</p>
            </div>
          </div>
        </Card>
      </div>

      <div className="mx-auto flex min-h-0 w-full max-w-6xl flex-1 flex-col gap-4 lg:flex-row">
        {showAuditPane ? (
          <ToolAuditPane events={auditEvents} isStreaming={isStreaming} />
        ) : null}

        <div className="flex min-h-0 min-w-0 flex-1 flex-col">
          <div
            ref={scrollRef}
            className="flex min-h-0 flex-1 flex-col overflow-y-auto rounded-lg border border-border bg-panel/40 shadow-inner"
          >
            <div className="p-4 pb-8">
              <ChatThread events={events} isStreaming={isStreaming} />
            </div>
          </div>

          <div className="mt-4 shrink-0 border-t border-border bg-panel/95 shadow-panel backdrop-blur-sm">
            <ChatComposer onSubmit={sendPrompt} isLoading={isStreaming} />
          </div>
        </div>
      </div>
    </section>
  );
}
