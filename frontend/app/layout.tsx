import type { Metadata } from "next";
import React from "react";
import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "Sohoj — AI Financial Copilot for MFS",
  description:
    "Behavior insights, financial forecasts, deterministic compound math, and grounded Upay MFS coaching in Bangladesh.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased selection:bg-upay-500/30 selection:text-navy-950 font-sans">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
