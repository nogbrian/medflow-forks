import type { Metadata, Viewport } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "@/styles/globals.css";
import { AuthProvider } from "@/components/auth/auth-provider";

/**
 * Font Configuration - Industrial Design System
 *
 * Inter Tight para headlines (display)
 * JetBrains Mono para dados e métricas
 */
const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

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
    <html lang="pt-BR" className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <head>
        {/* Preconnect to Google Fonts for Inter Tight */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        {/* Inter Tight for headlines */}
        <link
          href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="antialiased">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
