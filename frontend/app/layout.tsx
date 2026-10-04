import type { Metadata } from "next";
import React from "react";
import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "Shohoj Upay — AI Financial Coach for MFS Users",
  description:
    "Behavior insights, financial forecasts, deterministic math, and grounded coaching for MFS users in Bangladesh.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased selection:bg-emerald-500 selection:text-white">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
