"use client";

import { useEffect, useState } from "react";
import { THEMES, THEME_HINTS, THEME_LABELS, THEME_STORAGE_KEY, isTheme, type Theme } from "@/lib/theme";
import { cn } from "@/lib/utils";

function applyTheme(theme: Theme) {
  document.documentElement.setAttribute("data-theme", theme);
  try {
    window.localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch {
    // Private browsing or blocked storage: the theme still applies for this page.
  }
}

/**
 * Three-way segmented control. Deliberately not a cycling button — on stage you
 * want one click to reach the projector theme, not two.
 */
export function ThemeToggle({ className }: { className?: string }) {
  // Null until mounted: the server has no way to know which theme the inline
  // script picked, so no segment is marked active during hydration.
  const [theme, setTheme] = useState<Theme | null>(null);

  useEffect(() => {
    const current = document.documentElement.getAttribute("data-theme");
    setTheme(isTheme(current) ? current : "dark");
  }, []);

  return (
    <div
      role="group"
      aria-label="Colour theme"
      className={cn(
        "inline-flex shrink-0 items-center gap-0.5 rounded-md border border-border bg-panelMuted p-0.5",
        className
      )}
    >
      {THEMES.map((option) => {
        const isActive = theme === option;
        return (
          <button
            key={option}
            type="button"
            title={THEME_HINTS[option]}
            aria-pressed={isActive}
            onClick={() => {
              applyTheme(option);
              setTheme(option);
            }}
            className={cn(
              "rounded px-2 py-1 text-xs font-medium transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand",
              isActive
                ? "bg-brand text-brandFg"
                : "text-muted hover:bg-panelHover hover:text-foreground"
            )}
          >
            {THEME_LABELS[option]}
          </button>
        );
      })}
    </div>
  );
}
