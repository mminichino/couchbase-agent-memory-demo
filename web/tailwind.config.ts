import type { Config } from "tailwindcss";
import typography from "@tailwindcss/typography";

/** Channel-based token so Tailwind's `/opacity` modifiers keep working. */
const channel = (name: string) => `rgb(var(${name}) / <alpha-value>)`;

const config: Config = {
  // Values live in app/globals.css; `dark:` targets the dark theme explicitly
  // rather than the OS setting, since the theme is user-selected.
  darkMode: ["class", '[data-theme="dark"]'],
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        canvas: channel("--canvas"),
        codeBg: channel("--code-bg"),
        panel: channel("--panel"),
        panelMuted: channel("--panel-muted"),
        panelHover: channel("--panel-hover"),
        border: channel("--border"),
        foreground: channel("--foreground"),
        muted: channel("--muted"),
        brand: channel("--brand"),
        brandHover: channel("--brand-hover"),
        brandFg: channel("--brand-fg"),
        success: channel("--success"),
        successText: channel("--success-text"),
        warningText: channel("--warning-text"),
        danger: channel("--danger"),
        dangerHover: channel("--danger-hover"),
        dangerFg: channel("--danger-fg"),
        dangerText: channel("--danger-text"),
        chip: {
          runBg: "var(--chip-run-bg)",
          runBorder: "var(--chip-run-border)",
          runFg: "var(--chip-run-fg)",
          okBg: "var(--chip-ok-bg)",
          okBorder: "var(--chip-ok-border)",
          okFg: "var(--chip-ok-fg)",
          errBg: "var(--chip-err-bg)",
          errBorder: "var(--chip-err-border)",
          errFg: "var(--chip-err-fg)",
          infoBg: "var(--chip-info-bg)",
          infoBorder: "var(--chip-info-border)",
          infoFg: "var(--chip-info-fg)",
          overlay: "var(--chip-overlay-strong)",
          overlaySoft: "var(--chip-overlay-soft)"
        }
      },
      boxShadow: {
        panel: "var(--shadow-panel)"
      }
    }
  },
  plugins: [typography]
};

export default config;
