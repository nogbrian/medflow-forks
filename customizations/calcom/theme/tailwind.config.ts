/**
 * MedFlow Industrial Theme - Cal.com Tailwind Extension
 *
 * Este arquivo estende a configuração do Tailwind do Cal.com
 * para aplicar o Design System Industrial.
 *
 * Uso: Merge com o tailwind.config.ts original do Cal.com
 */

import type { Config } from "tailwindcss";

const industrialConfig: Partial<Config> = {
  theme: {
    extend: {
      // Cores Industrial
      colors: {
        // Base colors
        paper: "#F2F0E9",
        ink: "#111111",
        graphite: "#000000",
        steel: "#666666",

        // Accent colors
        accent: {
          orange: "#F24E1E",
          blue: "#0047AB",
        },

        // Cal.com brand override
        brand: {
          DEFAULT: "#F24E1E",
          50: "rgba(242, 78, 30, 0.05)",
          100: "rgba(242, 78, 30, 0.1)",
          200: "rgba(242, 78, 30, 0.2)",
          300: "rgba(242, 78, 30, 0.4)",
          400: "#F24E1E",
          500: "#F24E1E",
          600: "#DC2626",
          700: "#B91C1C",
          800: "#991B1B",
          900: "#7F1D1D",
        },

        // Cal.com specific overrides
        "cal-bg": "#F2F0E9",
        "cal-bg-emphasis": "#FFFFFF",
        "cal-bg-subtle": "#F2F0E9",
        "cal-bg-muted": "#F2F0E9",
        "cal-bg-inverted": "#111111",

        "cal-border": "#000000",
        "cal-border-emphasis": "#000000",
        "cal-border-subtle": "#666666",

        "cal-text": "#111111",
        "cal-text-emphasis": "#111111",
        "cal-text-subtle": "#666666",
        "cal-text-muted": "#666666",
        "cal-text-inverted": "#FFFFFF",

        // Emphasis colors
        emphasis: {
          50: "#F2F0E9",
          100: "#E5E3DC",
          200: "#CCCCCC",
          300: "#999999",
          400: "#666666",
          500: "#333333",
          600: "#222222",
          700: "#111111",
          800: "#0A0A0A",
          900: "#000000",
        },

        // Success/Error/Warning
        success: {
          DEFAULT: "#10B981",
          50: "rgba(16, 185, 129, 0.1)",
          500: "#10B981",
          600: "#059669",
        },
        error: {
          DEFAULT: "#F24E1E",
          50: "rgba(242, 78, 30, 0.1)",
          500: "#F24E1E",
          600: "#DC2626",
        },
        attention: {
          DEFAULT: "#F59E0B",
          50: "rgba(245, 158, 11, 0.1)",
          500: "#F59E0B",
          600: "#D97706",
        },
        info: {
          DEFAULT: "#0047AB",
          50: "rgba(0, 71, 171, 0.1)",
          500: "#0047AB",
          600: "#1E40AF",
        },
      },

      // Tipografia Industrial
      fontFamily: {
        cal: ['"Inter Tight"', "Inter", "system-ui", "sans-serif"],
        display: ['"Inter Tight"', "Inter", "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', '"Fira Code"', "Consolas", "monospace"],
        sans: ["Inter", "system-ui", "sans-serif"],
      },

      // Font sizes
      fontSize: {
        "display-2xl": ["4rem", { lineHeight: "1", letterSpacing: "-0.02em" }],
        "display-xl": ["3rem", { lineHeight: "1.1", letterSpacing: "-0.02em" }],
        "display-lg": ["2.5rem", { lineHeight: "1.1", letterSpacing: "-0.02em" }],
        "display-md": ["2rem", { lineHeight: "1.2", letterSpacing: "-0.02em" }],
        "display-sm": ["1.5rem", { lineHeight: "1.2", letterSpacing: "-0.01em" }],
      },

      // Box Shadow Industrial
      boxShadow: {
        none: "none",
        hard: "4px 4px 0px 0px #000000",
        "hard-sm": "2px 2px 0px 0px #000000",
        "hard-lg": "6px 6px 0px 0px #000000",
        "hard-xl": "8px 8px 0px 0px #000000",
        "hard-brand": "4px 4px 0px 0px #F24E1E",
        // Override Cal.com shadows
        dropdown: "4px 4px 0px 0px #000000",
        "up-md": "-4px -4px 0px 0px #000000",
      },

      // Border Width
      borderWidth: {
        DEFAULT: "2px",
        0: "0px",
        1: "1px",
        2: "2px",
      },

      // CRÍTICO: Border Radius zerado
      borderRadius: {
        none: "0px",
        DEFAULT: "0px",
        sm: "0px",
        md: "0px",
        lg: "0px",
        xl: "0px",
        "2xl": "0px",
        full: "0px",
        // Cal.com specific
        "cal-sm": "0px",
        "cal-md": "0px",
        "cal-lg": "0px",
      },

      // Animations
      keyframes: {
        "fade-in-up": {
          from: { opacity: "0", transform: "translateY(4px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in-down": {
          from: { opacity: "0", transform: "translateY(-4px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "fade-in-up": "fade-in-up 0.2s ease-out",
        "fade-in-down": "fade-in-down 0.2s ease-out",
      },
    },
  },
};

export default industrialConfig;

/**
 * INSTRUÇÕES DE USO:
 *
 * 1. No Cal.com, localize o tailwind.config.ts
 * 2. Faça merge das configurações:
 *
 *    import industrialConfig from './customizations/calcom/theme/tailwind.config';
 *    import merge from 'deepmerge';
 *
 *    const config = merge(baseConfig, industrialConfig);
 *
 * 3. Adicione o industrial.css ao head ou importe no globals.css:
 *    @import './customizations/calcom/theme/industrial.css';
 *
 * 4. Para white-label via env vars, configure:
 *    NEXT_PUBLIC_BRAND_COLOR=#F24E1E
 *    NEXT_PUBLIC_DARK_BRAND_COLOR=#DC2626
 */
