"use client";

import { useEffect, useRef } from "react";
import type { AuditEvent } from "@/lib/types";
import { Card } from "@/components/ui/card";

type ToolAuditPaneProps = {
  events: AuditEvent[];
  isStreaming: boolean;
};

const STATUS_STYLES: Record<string, string> = {
  running: "border-chip-runBorder bg-chip-runBg text-chip-runFg",
  success: "border-chip-okBorder bg-chip-okBg text-chip-okFg",
  error: "border-chip-errBorder bg-chip-errBg text-chip-errFg",
  info: "border-chip-infoBorder bg-chip-infoBg text-chip-infoFg"
};

const EVENT_LABELS: Record<string, string> = {
  turn_start: "Turn started",
  turn_complete: "Turn completed",
  turn_error: "Turn failed",
  tool_call: "Tool call",
  tool_result: "Tool result"
};

function statusStyle(status: string): string {
  return STATUS_STYLES[status] ?? STATUS_STYLES.info;
}

function eventLabel(eventType: string): string {
  return EVENT_LABELS[eventType] ?? eventType.replaceAll("_", " ");
}

export function ToolAuditPane({ events, isStreaming }: ToolAuditPaneProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [events, isStreaming]);

  return (
    <aside
      id="tool-audit-stream"
      className="flex min-h-0 w-full flex-col lg:max-w-sm lg:flex-none lg:basis-80 xl:basis-96"
    >
      <Card className="flex min-h-0 flex-1 flex-col overflow-hidden border-border/80 bg-panel/70 shadow-panel backdrop-blur-sm">
        <div className="border-b border-border/80 px-4 py-3">
          <p className="text-[11px] uppercase tracking-[0.18em] text-muted">Agent Catalog</p>
          <h2 className="mt-1 text-sm font-semibold text-foreground">Tool audit stream</h2>
          <p className="mt-1 text-xs text-muted">
            Live tool calls and results traced through Agent Catalog
          </p>
        </div>

        <div ref={scrollRef} className="min-h-0 flex-1 overflow-y-auto px-3 py-3">
          {!events.length ? (
            <p className="rounded-lg border border-dashed border-border/80 bg-canvas/40 px-3 py-4 text-xs text-muted">
              Send a message to watch Agent Catalog record tool activity in real time.
            </p>
          ) : (
            <ol className="space-y-3">
              {events.map((event, index) => (
                <li
                  key={`${event.timestamp}-${event.event_type}-${event.title}-${index}`}
                  className={`rounded-xl border px-3 py-3 ${statusStyle(event.status)}`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-[11px] uppercase tracking-wide opacity-[var(--chip-label-opacity)]">
                        {eventLabel(event.event_type)}
                      </p>
                      <p className="mt-1 text-sm font-medium">{event.title}</p>
                    </div>
                    {typeof event.duration_ms === "number" ? (
                      <span className="shrink-0 rounded-full bg-chip-overlay px-2 py-0.5 text-[11px] tabular-nums">
                        {(event.duration_ms / 1000).toFixed(2)}s
                      </span>
                    ) : null}
                  </div>
                  {event.summary ? (
                    <pre className="mt-2 max-h-40 overflow-auto whitespace-pre-wrap break-words rounded-md bg-chip-overlaySoft p-2 text-[11px] leading-relaxed text-inherit">
                      {event.summary}
                    </pre>
                  ) : null}
                  <p className="mt-2 text-[10px] uppercase tracking-wide opacity-[var(--chip-meta-opacity)]">
                    {new Date(event.timestamp).toLocaleTimeString()}
                  </p>
                </li>
              ))}
            </ol>
          )}
        </div>

        {isStreaming ? (
          <div className="border-t border-border/80 px-4 py-2 text-xs text-warningText">
            Recording agent activity...
          </div>
        ) : null}
      </Card>
    </aside>
  );
}
