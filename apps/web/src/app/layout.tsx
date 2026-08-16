import type { Metadata } from "next";
import { Inter, Manrope } from "next/font/google";
import type { ReactNode } from "react";

import { AppShell } from "@/components/app-shell";
import { Providers } from "./providers";
import "./globals.css";

const themeScript = `(function(){try{var saved=localStorage.getItem('myseo-theme');var theme=saved==='dark'||saved==='light'?saved:(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');document.documentElement.dataset.theme=theme;document.documentElement.style.colorScheme=theme;}catch(e){}})();`;
const bodyFont = Inter({ subsets: ["latin"], display: "swap" });
const displayFont = Manrope({ subsets: ["latin"], variable: "--font-display", display: "swap" });

export const metadata: Metadata = {
  applicationName: "MySEO",
  title: { default: "MySEO", template: "%s · MySEO" },
  description: "Search demand intelligence for buildable software opportunities.",
  icons: { icon: "/icon.svg?v=5" },
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head><script dangerouslySetInnerHTML={{ __html: themeScript }} /></head>
      <body className={`${bodyFont.className} ${displayFont.variable}`}>
        <Providers>
          <AppShell>{children}</AppShell>
        </Providers>
      </body>
    </html>
  );
}
