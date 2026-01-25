import type { Metadata, Viewport } from "next";
import { JetBrains_Mono } from "next/font/google";
import "@/styles/globals.css";
import { AuthProvider } from "@/components/auth/auth-provider";

/**
 * Font Configuration - Intelligent Flow Design System
 *
 * Clash Display para headlines (display) - via Fontshare
 * Satoshi para body text (sans) - via Fontshare
 * JetBrains Mono para dados e métricas
 */
const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "MedFlow | Sistema Integrado para Clínicas",
    template: "%s | MedFlow",
  },
  description:
    "Infraestrutura de aquisição de pacientes. CRM, Agendamento e Messaging integrados com agentes de IA.",
  keywords: [
    "CRM médico",
    "agendamento",
    "clínica",
    "pacientes",
    "marketing médico",
    "IA",
  ],
  authors: [{ name: "MedFlow" }],
  creator: "MedFlow",
  robots: {
    index: true,
    follow: true,
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#F2F0E9",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR" className={jetbrainsMono.variable}>
      <head>
        {/* Preconnect to font providers */}
        <link rel="preconnect" href="https://api.fontshare.com" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />

        {/* Fontshare - Clash Display (display) & Satoshi (body) */}
        <link
          href="https://api.fontshare.com/v2/css?f[]=clash-display@400,500,600,700&f[]=satoshi@400,500,700&display=swap"
          rel="stylesheet"
        />

        {/* Google Fonts - JetBrains Mono (data/metrics) */}
        <link
          href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="antialiased">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
