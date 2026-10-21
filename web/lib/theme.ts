export const THEMES = ["dark", "light", "projector"] as const;

export type Theme = (typeof THEMES)[number];

export const THEME_STORAGE_KEY = "cb-memory-demo-theme";

export const THEME_LABELS: Record<Theme, string> = {
  dark: "Dark",
  light: "Light",
  projector: "Projector"
};

export const THEME_HINTS: Record<Theme, string> = {
  dark: "Dark theme",
  light: "Light theme",
  projector: "High-contrast theme for projectors and bright rooms"
};

export function isTheme(value: unknown): value is Theme {
  return typeof value === "string" && (THEMES as readonly string[]).includes(value);
}

/**
 * Runs before first paint so the page never flashes the wrong theme.
 * Falls back to the OS preference until the user picks a theme explicitly.
 */
export const THEME_INIT_SCRIPT = `(function(){try{var k=${JSON.stringify(
  THEME_STORAGE_KEY
)};var t=window.localStorage.getItem(k);if(t!=="dark"&&t!=="light"&&t!=="projector"){t=window.matchMedia("(prefers-color-scheme: light)").matches?"light":"dark";}document.documentElement.setAttribute("data-theme",t);}catch(e){document.documentElement.setAttribute("data-theme","dark");}})();`;
