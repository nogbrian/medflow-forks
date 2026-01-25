/**
 * MedFlow Intelligent Flow Theme - Chatwoot Tailwind Extension
 *
 * Design System: Intelligent Flow
 * - Glassmorphism, soft shadows, glow effects
 * - Fonts: Clash Display, Satoshi, JetBrains Mono
 * - Smooth animations and hover transitions
 */

import type { Config } from "tailwindcss";

const intelligentFlowConfig: Partial<Config> = {
  theme: {
    extend: {
      // Intelligent Flow Colors
      colors: {
        // Engineering Blue (Primary)
        "eng-blue": {
          DEFAULT: "#0F3038",
          90: "rgba(15, 48, 56, 0.9)",
          80: "rgba(15, 48, 56, 0.8)",
          60: "rgba(15, 48, 56, 0.6)",
          30: "rgba(15, 48, 56, 0.3)",
          10: "rgba(15, 48, 56, 0.1)",
          "05": "rgba(15, 48, 56, 0.05)",
          "08": "rgba(15, 48, 56, 0.08)",
          "06": "rgba(15, 48, 56, 0.06)",
        },

        // Alert Orange (Accent)
        alert: {
          DEFAULT: "#FF6400",
          90: "rgba(255, 100, 0, 0.9)",
          80: "rgba(255, 100, 0, 0.8)",
          30: "rgba(255, 100, 0, 0.3)",
          10: "rgba(255, 100, 0, 0.1)",
          "05": "rgba(255, 100, 0, 0.05)",
          "08": "rgba(255, 100, 0, 0.08)",
        },

        // Neutral colors
        concrete: "#808080",
        "tech-white": "#F5F5F2",

        // Chatwoot semantic mapping
        woot: {
          DEFAULT: "#FF6400",
          50: "#FFF7ED",
          100: "#FFEDD5",
          200: "#FED7AA",
          300: "#FDBA74",
          400: "#FB923C",
          500: "#FF6400",
          600: "#E55A00",
          700: "#CC5000",
          800: "#9A3412",
          900: "#7C2D12",
        },

        // Status colors
        success: {
          DEFAULT: "#10B981",
          light: "rgba(16, 185, 129, 0.1)",
        },
        warning: {
          DEFAULT: "#F59E0B",
          light: "rgba(245, 158, 11, 0.1)",
        },
        error: {
          DEFAULT: "#EF4444",
          light: "rgba(239, 68, 68, 0.1)",
        },

        // Background overrides
        background: {
          primary: "#F5F5F2",
          secondary: "rgba(255, 255, 255, 0.8)",
          tertiary: "#FFFFFF",
        },

        // Border override
        border: {
          DEFAULT: "rgba(15, 48, 56, 0.08)",
          medium: "rgba(15, 48, 56, 0.1)",
          light: "rgba(15, 48, 56, 0.06)",
        },

        // Text override
        font: {
          primary: "#0F3038",
          secondary: "#808080",
          tertiary: "#A0A0A0",
        },
      },

      // Intelligent Flow Typography
      fontFamily: {
        display: ['"Clash Display"', "Inter", "system-ui", "sans-serif"],
        sans: ["Satoshi", "Inter", "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', '"Fira Code"', "Consolas", "monospace"],
      },

      // Font sizes
      fontSize: {
        "display-xl": ["3rem", { lineHeight: "1.1", letterSpacing: "-0.02em" }],
        "display-lg": ["2.5rem", { lineHeight: "1.1", letterSpacing: "-0.02em" }],
        "display-md": ["2rem", { lineHeight: "1.2", letterSpacing: "-0.02em" }],
        "display-sm": ["1.5rem", { lineHeight: "1.2", letterSpacing: "-0.01em" }],
        "mono-lg": ["1rem", { lineHeight: "1.5", letterSpacing: "0" }],
        "mono-md": ["0.875rem", { lineHeight: "1.5", letterSpacing: "0" }],
        "mono-sm": ["0.75rem", { lineHeight: "1.5", letterSpacing: "0" }],
        "mono-xs": ["0.625rem", { lineHeight: "1.5", letterSpacing: "0.05em" }],
      },

      // Intelligent Flow Shadows (Soft + Glow)
      boxShadow: {
        xs: "0 1px 2px rgba(0, 0, 0, 0.04)",
        sm: "0 2px 8px rgba(0, 0, 0, 0.06)",
        md: "0 4px 16px rgba(0, 0, 0, 0.08)",
        lg: "0 8px 32px rgba(0, 0, 0, 0.10)",
        xl: "0 16px 48px rgba(0, 0, 0, 0.12)",
        "2xl": "0 24px 64px rgba(0, 0, 0, 0.16)",
        "glow-orange": "0 8px 32px rgba(255, 100, 0, 0.3)",
        "glow-blue": "0 8px 32px rgba(15, 48, 56, 0.2)",
        "message-incoming": "0 2px 8px rgba(15, 48, 56, 0.06)",
        "message-outgoing": "0 2px 8px rgba(255, 100, 0, 0.1)",
      },

      // Border Width
      borderWidth: {
        DEFAULT: "1px",
        0: "0px",
        1: "1px",
        2: "2px",
      },

      // Intelligent Flow Border Radius (Soft corners)
      borderRadius: {
        none: "0px",
        sm: "8px",
        DEFAULT: "12px",
        md: "12px",
        lg: "16px",
        xl: "24px",
        "2xl": "32px",
        "3xl": "48px",
        full: "9999px",
        message: "18px",
      },

      // Backdrop blur
      backdropBlur: {
        xs: "4px",
        sm: "8px",
        DEFAULT: "12px",
        md: "16px",
        lg: "20px",
        xl: "24px",
      },

      // Animations
      keyframes: {
        "fade-in-up": {
          "0%": { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "scale-in": {
          "0%": { opacity: "0", transform: "scale(0.95)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        "slide-in-right": {
          "0%": { opacity: "0", transform: "translateX(20px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        "message-in": {
          "0%": { opacity: "0", transform: "translateY(10px) scale(0.98)" },
          "100%": { opacity: "1", transform: "translateY(0) scale(1)" },
        },
        typing: {
          "0%, 60%, 100%": { opacity: "0.3" },
          "30%": { opacity: "1" },
        },
      },
      animation: {
        "fade-in-up": "fade-in-up 0.6s ease-out forwards",
        "scale-in": "scale-in 0.3s ease-out forwards",
        "slide-in-right": "slide-in-right 0.3s ease-out forwards",
        "message-in": "message-in 0.2s ease-out forwards",
        typing: "typing 1.4s infinite",
      },

      // Transitions
      transitionDuration: {
        fast: "150ms",
        normal: "300ms",
        slow: "400ms",
      },

      transitionTimingFunction: {
        smooth: "cubic-bezier(0.4, 0, 0.2, 1)",
      },

      // Spacing for chat
      spacing: {
        "message-gap": "8px",
        "sidebar-width": "320px",
      },
    },
  },

  plugins: [],
};

export default intelligentFlowConfig;

/**
 * INSTRUÇÕES DE USO:
 *
 * 1. Copie este arquivo para o diretório do Chatwoot
 * 2. No tailwind.config.js do Chatwoot, faça merge:
 *
 *    const intelligentFlowConfig = require('./intelligent-flow-theme/tailwind.config');
 *    const { merge } = require('lodash');
 *
 *    module.exports = merge(baseConfig, intelligentFlowConfig);
 *
 * 3. Importe o intelligent-flow.css no entry point principal
 * 4. Adicione as fontes no layout:
 *    <link href="https://api.fontshare.com/v2/css?f[]=clash-display@400,500,600,700&f[]=satoshi@400,500,600,700&display=swap" rel="stylesheet">
 *    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
 */
