import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Couchbase Agent Memory Console",
  description: "Secure chat console powered by gRPC and Couchbase."
};

export default function RootLayout({
  children
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="h-full">
      <body className="h-full min-h-0">{children}</body>
    </html>
  );
}
