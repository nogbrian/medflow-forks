/**
 * MedFlow Intelligent Flow Theme - Twenty CRM Tailwind Extension
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

        // Semantic mapping for Twenty
        primary: {
          DEFAULT: "#FF6400",
          50: "rgba(255, 100, 0, 0.05)",
          100: "rgba(255, 100, 0, 0.1)",
          200: "rgba(255, 100, 0, 0.2)",
          300: "rgba(255, 100, 0, 0.3)",
          400: "#FF6400",
          500: "#FF6400",
          600: "#E55A00",
          700: "#CC5000",
          800: "#B34600",
          900: "#993D00",
        },

        secondary: {
          DEFAULT: "#0F3038",
          50: "rgba(15, 48, 56, 0.05)",
          100: "rgba(15, 48, 56, 0.1)",
          500: "#0F3038",
          600: "#1A4A55",
          700: "#0D2A30",
        },

        // Background overrides
        background: {
          primary: "#F5F5F2",
          secondary: "rgba(255, 255, 255, 0.8)",
          tertiary: "#F5F5F2",
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
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-10px)" },
        },
      },
      animation: {
        "fade-in-up": "fade-in-up 0.6s ease-out forwards",
        "scale-in": "scale-in 0.3s ease-out forwards",
        float: "float 6s ease-in-out infinite",
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
    },
  },

  plugins: [],
};

export default intelligentFlowConfig;

/**
 * INSTRUÇÕES DE USO:
 *
 * 1. Copie este arquivo para o diretório do Twenty CRM
 * 2. No tailwind.config.ts do Twenty, faça merge:
 *
 *    import intelligentFlowConfig from './intelligent-flow-theme/tailwind.config';
 *    import { merge } from 'lodash';
 *
 *    const config = merge(baseConfig, intelligentFlowConfig);
 *    export default config;
 *
 * 3. Importe o intelligent-flow.css no entry point principal
 * 4. Adicione as fontes no HTML:
 *    <link href="https://api.fontshare.com/v2/css?f[]=clash-display@400,500,600,700&f[]=satoshi@400,500,600,700&display=swap" rel="stylesheet">
 *    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
 */
