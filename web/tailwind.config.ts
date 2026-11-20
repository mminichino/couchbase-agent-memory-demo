import type { Config } from "tailwindcss";
import typography from "@tailwindcss/typography";
import plugin from "tailwindcss/plugin";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        canvas: "#0A0D12",
        panel: "#111721",
        panelMuted: "#151D29",
        border: "rgb(var(--color-border) / <alpha-value>)",
        foreground: "rgb(var(--color-foreground) / <alpha-value>)",
        muted: "rgb(var(--color-muted) / <alpha-value>)",
        brand: "#3B82F6",
        success: "#22C55E",
        danger: "#EF4444"
      },
      boxShadow: {
        panel: "0 8px 30px rgba(5, 10, 20, 0.24)"
      }
    }
  },
  plugins: [
    typography,
    // Layout variants driven by <html data-layout="...">, e.g. `projector:text-base`, `mobile:px-2`.
    plugin(({ addVariant }) => {
      addVariant("projector", '[data-layout="projector"] &');
      addVariant("mobile", '[data-layout="mobile"] &');
    })
  ]
};

export default config;
