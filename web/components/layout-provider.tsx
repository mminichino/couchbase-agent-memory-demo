"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import {
  LAYOUT_COOKIE,
  LAYOUT_COOKIE_MAX_AGE_SECONDS,
  PROJECTOR_COOKIE_VALUE,
  detectMobileClient,
  resolveLayout,
  type LayoutMode
} from "@/lib/layout";

type LayoutContextValue = {
  layout: LayoutMode;
  isMobile: boolean;
  isProjector: boolean;
  /** The stored projector preference (may be inactive while on a mobile device). */
  projectorEnabled: boolean;
  setProjectorEnabled: (enabled: boolean) => void;
};

const LayoutContext = createContext<LayoutContextValue | null>(null);

type LayoutProviderProps = {
  initialMobile: boolean;
  initialProjector: boolean;
  children: React.ReactNode;
};

function persistProjector(enabled: boolean) {
  const secure = window.location.protocol === "https:" ? "; Secure" : "";
  document.cookie = enabled
    ? `${LAYOUT_COOKIE}=${PROJECTOR_COOKIE_VALUE}; Path=/; Max-Age=${LAYOUT_COOKIE_MAX_AGE_SECONDS}; SameSite=Lax${secure}`
    : `${LAYOUT_COOKIE}=; Path=/; Max-Age=0; SameSite=Lax${secure}`;
}

export function LayoutProvider({ initialMobile, initialProjector, children }: LayoutProviderProps) {
  const [isMobile, setMobile] = useState(initialMobile);
  const [projectorEnabled, setProjector] = useState(initialProjector);

  // The server detects mobile from the User-Agent; confirm on the client (e.g. iPadOS, UA-CH).
  useEffect(() => {
    if (detectMobileClient()) setMobile(true);
  }, []);

  const layout = resolveLayout(isMobile, projectorEnabled);

  useEffect(() => {
    document.documentElement.dataset.layout = layout;
  }, [layout]);

  const setProjectorEnabled = useCallback((enabled: boolean) => {
    setProjector(enabled);
    try {
      persistProjector(enabled);
    } catch {
      // Cookies disabled: the preference simply applies for this page view.
    }
  }, []);

  const value = useMemo<LayoutContextValue>(
    () => ({
      layout,
      isMobile: layout === "mobile",
      isProjector: layout === "projector",
      projectorEnabled,
      setProjectorEnabled
    }),
    [layout, projectorEnabled, setProjectorEnabled]
  );

  return <LayoutContext.Provider value={value}>{children}</LayoutContext.Provider>;
}

export function useLayout(): LayoutContextValue {
  const ctx = useContext(LayoutContext);
  if (!ctx) throw new Error("useLayout must be used within a LayoutProvider.");
  return ctx;
}
