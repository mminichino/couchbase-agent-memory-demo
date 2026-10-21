"use client";

import type { ChatEvent } from "@/lib/types";
import { MarkdownContent } from "@/components/chat/markdown-content";
import { Card } from "@/components/ui/card";

type ChatThreadProps = {
  events: ChatEvent[];
  isStreaming: boolean;
};

/** Chat pane shows only conversational Q&A; tools/audit live in the audit stream. */
function isConversationEvent(event: ChatEvent): boolean {
  if (event.type === "error") return true;
  if (event.type !== "message") return false;
  const role = event.role.toLowerCase();
  if (role !== "user" && role !== "human" && role !== "assistant" && role !== "ai") {
    return false;
  }
  return Boolean(event.content?.trim());
}

function displayRole(role: string): string {
  const normalized = role.toLowerCase();
  if (normalized === "user" || normalized === "human") return "You";
  if (normalized === "assistant" || normalized === "ai") return "Assistant";
  return role;
}

export function ChatThread({ events, isStreaming }: ChatThreadProps) {
  const visibleEvents = events.filter(isConversationEvent);

  if (!events.length) {
    return (
      <Card className="p-6">
        <p className="text-sm text-muted">
          Start a conversation. Tool calls and Agent Catalog activity appear in the audit stream.
        </p>
      </Card>
    );
  }

  if (!visibleEvents.length) {
    return (
      <Card className="p-6">
        <p className="text-sm text-muted">
          {isStreaming
            ? "Waiting for the assistant response..."
            : "No assistant replies yet. Ask a question to begin."}
        </p>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      {visibleEvents.map((event, idx) => (
        <Card key={`${event.type}-${idx}`} className="p-4">
          {event.type === "message" ? (
            <div>
              <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
                <p className="text-xs uppercase tracking-wide text-muted">
                  {displayRole(event.role)}
                </p>
                {typeof event.runtime_ms === "number" ? (
                  <p className="text-xs tabular-nums text-muted">
                    {(event.runtime_ms / 1000).toFixed(2)}s elapsed
                  </p>
                ) : null}
              </div>
              <div className="mt-1">
                <MarkdownContent markdown={event.content} />
              </div>
            </div>
          ) : null}
          {event.type === "error" ? (
            <p className="text-sm text-dangerText">{event.message}</p>
          ) : null}
        </Card>
      ))}
      {isStreaming ? <p className="text-xs text-muted">Streaming response...</p> : null}
    </div>
  );
}
