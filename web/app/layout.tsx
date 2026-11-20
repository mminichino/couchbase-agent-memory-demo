import type { Metadata, Viewport } from "next";
import { cookies, headers } from "next/headers";
import { LayoutProvider } from "@/components/layout-provider";
import {
  LAYOUT_COOKIE,
  PROJECTOR_COOKIE_VALUE,
  isMobileUserAgent,
  resolveLayout
} from "@/lib/layout";
import "./globals.css";

export const metadata: Metadata = {
  title: "Couchbase Agent Memory Console",
  description: "Secure chat console powered by gRPC and Couchbase."
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1
};

export default function RootLayout({
  children
}: Readonly<{ children: React.ReactNode }>) {
  const isMobile = isMobileUserAgent(headers().get("user-agent"));
  const projectorEnabled = cookies().get(LAYOUT_COOKIE)?.value === PROJECTOR_COOKIE_VALUE;
  const layout = resolveLayout(isMobile, projectorEnabled);

  return (
    <html lang="en" className="h-full" data-layout={layout} suppressHydrationWarning>
      <body className="h-full min-h-0">
        <LayoutProvider initialMobile={isMobile} initialProjector={projectorEnabled}>
          {children}
        </LayoutProvider>
      </body>
    </html>
  );
}
