"use client";

import { useLayout } from "@/components/layout-provider";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

/** Switches the projector layout on/off. Hidden on mobile devices, where the mobile layout applies. */
export function LayoutToggle({ className }: { className?: string }) {
  const { isMobile, projectorEnabled, setProjectorEnabled } = useLayout();
  if (isMobile) return null;

  return (
    <Button
      type="button"
      variant={projectorEnabled ? "primary" : "secondary"}
      className={cn("h-8 shrink-0 px-3 text-xs projector:h-10 projector:text-sm", className)}
      aria-pressed={projectorEnabled}
      title="Larger text and higher contrast for projectors and conference rooms"
      onClick={() => setProjectorEnabled(!projectorEnabled)}
    >
      Projector mode: {projectorEnabled ? "On" : "Off"}
    </Button>
  );
}
