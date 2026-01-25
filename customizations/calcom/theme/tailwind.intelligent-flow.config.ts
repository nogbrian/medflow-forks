/**
 * MedFlow Intelligent Flow Theme - Cal.com Tailwind Extension
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

        // Alert Orange (Accent/Brand)
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

        // Cal.com brand mapping
        brand: {
          DEFAULT: "#FF6400",
          emphasis: "#E55A00",
          subtle: "rgba(255, 100, 0, 0.1)",
          muted: "rgba(255, 100, 0, 0.05)",
        },

        // Status colors for booking
        success: {
          DEFAULT: "#10B981",
          emphasis: "#059669",
          subtle: "rgba(16, 185, 129, 0.1)",
        },
        attention: {
          DEFAULT: "#F59E0B",
          emphasis: "#D97706",
          subtle: "rgba(245, 158, 11, 0.1)",
        },
        error: {
          DEFAULT: "#EF4444",
          emphasis: "#DC2626",
          subtle: "rgba(239, 68, 68, 0.1)",
        },

        // Background overrides
        default: "#F5F5F2",
        subtle: "rgba(255, 255, 255, 0.8)",
        muted: "rgba(15, 48, 56, 0.03)",
        emphasis: "#FFFFFF",
        inverted: "#0F3038",

        // Border override
        "border-default": "rgba(15, 48, 56, 0.08)",
        "border-emphasis": "rgba(15, 48, 56, 0.12)",
        "border-subtle": "rgba(15, 48, 56, 0.06)",

        // Text override
        "text-default": "#0F3038",
        "text-emphasis": "#0F3038",
        "text-subtle": "#808080",
        "text-muted": "#A0A0A0",
        "text-inverted": "#F5F5F2",
      },

      // Intelligent Flow Typography
      fontFamily: {
        display: ['"Clash Display"', "Inter", "system-ui", "sans-serif"],
        sans: ["Satoshi", "Inter", "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', '"Fira Code"', "Consolas", "monospace"],
        cal: ["Satoshi", "Inter", "system-ui", "sans-serif"],
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
        "calendar-day": "0 2px 8px rgba(15, 48, 56, 0.06)",
        "time-slot": "0 2px 12px rgba(15, 48, 56, 0.08)",
        "booking-card": "0 4px 24px rgba(15, 48, 56, 0.10)",
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
        "calendar-day": "10px",
        "time-slot": "12px",
        card: "16px",
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
        "calendar-fade": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        "slot-appear": {
          "0%": { opacity: "0", transform: "translateX(-10px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        "booking-success": {
          "0%": { opacity: "0", transform: "scale(0.9)" },
          "50%": { transform: "scale(1.02)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
      },
      animation: {
        "fade-in-up": "fade-in-up 0.6s ease-out forwards",
        "scale-in": "scale-in 0.3s ease-out forwards",
        "calendar-fade": "calendar-fade 0.3s ease-out",
        "slot-appear": "slot-appear 0.2s ease-out forwards",
        "booking-success": "booking-success 0.4s ease-out forwards",
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

      // Calendar-specific spacing
      spacing: {
        "calendar-cell": "40px",
        "time-slot-height": "44px",
      },
    },
  },

  plugins: [],
};

export default intelligentFlowConfig;

/**
 * INSTRUÇÕES DE USO:
 *
 * 1. Copie este arquivo para o diretório do Cal.com
 * 2. No tailwind.config.js do Cal.com, faça merge:
 *
 *    import intelligentFlowConfig from './intelligent-flow-theme/tailwind.config';
 *    import { merge } from 'lodash';
 *
 *    const config = merge(baseConfig, intelligentFlowConfig);
 *    export default config;
 *
 * 3. Importe o intelligent-flow.css no entry point principal
 * 4. Adicione as fontes no layout:
 *    <link href="https://api.fontshare.com/v2/css?f[]=clash-display@400,500,600,700&f[]=satoshi@400,500,600,700&display=swap" rel="stylesheet">
 *    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
 */
