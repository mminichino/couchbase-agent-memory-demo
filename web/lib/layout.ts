/**
 * Layout modes for the web console.
 *
 * - `default`:   the standard desktop layout.
 * - `projector`: larger text, higher contrast and full-width panels for low-resolution
 *                projectors in meeting/conference rooms. Opt-in via a toggle.
 * - `mobile`:    single-column, touch-friendly layout. Enabled automatically on mobile devices.
 */
export type LayoutMode = "default" | "projector" | "mobile";

/** Cookie that stores the user's projector preference so the server can render it without a flash. */
export const LAYOUT_COOKIE = "camd_layout";
export const PROJECTOR_COOKIE_VALUE = "projector";
export const LAYOUT_COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 365;

const MOBILE_USER_AGENT = /Android|iPhone|iPad|iPod|Mobi|Opera Mini|IEMobile|BlackBerry|webOS/i;

export function isMobileUserAgent(userAgent: string | null | undefined): boolean {
  return Boolean(userAgent && MOBILE_USER_AGENT.test(userAgent));
}

/** Mobile always wins: the projector preference is remembered but ignored on mobile devices. */
export function resolveLayout(isMobile: boolean, projectorEnabled: boolean): LayoutMode {
  if (isMobile) return "mobile";
  return projectorEnabled ? "projector" : "default";
}

type NavigatorWithUAData = Navigator & { userAgentData?: { mobile?: boolean } };

/** Client-side detection; also catches iPadOS, which reports a desktop (Macintosh) user agent. */
export function detectMobileClient(nav: NavigatorWithUAData = navigator): boolean {
  if (nav.userAgentData?.mobile === true) return true;
  if (isMobileUserAgent(nav.userAgent)) return true;
  return /Macintosh/i.test(nav.userAgent) && (nav.maxTouchPoints ?? 0) > 1;
}
