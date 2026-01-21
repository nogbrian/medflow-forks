/**
 * MedFlow Industrial Theme - Twenty CRM Tailwind Extension
 *
 * Este arquivo estende a configuração do Tailwind do Twenty CRM
 * para aplicar o Design System Industrial.
 *
 * Uso: Merge com o tailwind.config.ts original do Twenty
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
          "orange-dark": "#DC2626",
          blue: "#0047AB",
          "blue-dark": "#1E40AF",
        },

        // Semantic mapping para Twenty
        primary: {
          DEFAULT: "#F24E1E",
          50: "rgba(242, 78, 30, 0.1)",
          100: "rgba(242, 78, 30, 0.2)",
          200: "rgba(242, 78, 30, 0.3)",
          300: "rgba(242, 78, 30, 0.5)",
          400: "#F24E1E",
          500: "#F24E1E",
          600: "#DC2626",
          700: "#B91C1C",
          800: "#991B1B",
          900: "#7F1D1D",
        },

        secondary: {
          DEFAULT: "#0047AB",
          50: "rgba(0, 71, 171, 0.1)",
          100: "rgba(0, 71, 171, 0.2)",
          500: "#0047AB",
          600: "#1E40AF",
          700: "#1E3A8A",
        },

        // Background overrides
        background: {
          primary: "#F2F0E9",
          secondary: "#FFFFFF",
          tertiary: "#F2F0E9",
        },

        // Border override
        border: {
          DEFAULT: "#000000",
          medium: "#000000",
          light: "#666666",
        },

        // Text override
        font: {
          primary: "#111111",
          secondary: "#666666",
          tertiary: "#999999",
        },
      },

      // Tipografia Industrial
      fontFamily: {
        display: ['"Inter Tight"', "Inter", "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', '"Fira Code"', "Consolas", "monospace"],
        sans: ["Inter", "system-ui", "sans-serif"],
      },

      // Tamanhos de fonte
      fontSize: {
        "display-xl": ["3rem", { lineHeight: "1.1", letterSpacing: "-0.02em" }],
        "display-lg": ["2.5rem", { lineHeight: "1.1", letterSpacing: "-0.02em" }],
        "display-md": ["2rem", { lineHeight: "1.2", letterSpacing: "-0.02em" }],
        "display-sm": ["1.5rem", { lineHeight: "1.2", letterSpacing: "-0.01em" }],
        "mono-lg": ["1rem", { lineHeight: "1.5", letterSpacing: "0" }],
        "mono-md": ["0.875rem", { lineHeight: "1.5", letterSpacing: "0" }],
        "mono-sm": ["0.75rem", { lineHeight: "1.5", letterSpacing: "0" }],
        "mono-xs": ["0.625rem", { lineHeight: "1.5", letterSpacing: "0.1em" }],
      },

      // Box Shadow Industrial (Hard Shadows)
      boxShadow: {
        none: "none",
        hard: "4px 4px 0px 0px #000000",
        "hard-sm": "2px 2px 0px 0px #000000",
        "hard-lg": "6px 6px 0px 0px #000000",
        "hard-xl": "8px 8px 0px 0px #000000",
        "hard-orange": "4px 4px 0px 0px #F24E1E",
        "hard-orange-sm": "2px 2px 0px 0px #F24E1E",
        "hard-blue": "4px 4px 0px 0px #0047AB",
        "hard-blue-sm": "2px 2px 0px 0px #0047AB",
      },

      // Border Width
      borderWidth: {
        DEFAULT: "2px",
        0: "0px",
        1: "1px",
        2: "2px",
        3: "3px",
        4: "4px",
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
        "3xl": "0px",
        full: "0px",
      },

      // Spacing
      spacing: {
        "industrial-1": "0.25rem",
        "industrial-2": "0.5rem",
        "industrial-3": "0.75rem",
        "industrial-4": "1rem",
        "industrial-6": "1.5rem",
        "industrial-8": "2rem",
        "industrial-12": "3rem",
        "industrial-16": "4rem",
      },

      // Animations
      keyframes: {
        "industrial-pulse": {
          "0%, 100%": { boxShadow: "4px 4px 0px 0px #000000" },
          "50%": { boxShadow: "6px 6px 0px 0px #000000" },
        },
        "industrial-slide-up": {
          from: { transform: "translateY(4px)", opacity: "0" },
          to: { transform: "translateY(0)", opacity: "1" },
        },
        "industrial-slide-down": {
          from: { transform: "translateY(-4px)", opacity: "0" },
          to: { transform: "translateY(0)", opacity: "1" },
        },
      },
      animation: {
        "industrial-pulse": "industrial-pulse 2s ease-in-out infinite",
        "industrial-slide-up": "industrial-slide-up 0.2s ease-out",
        "industrial-slide-down": "industrial-slide-down 0.2s ease-out",
      },

      // Transitions
      transitionDuration: {
        fast: "100ms",
        normal: "200ms",
      },
    },
  },

  // Plugins customizados
  plugins: [],
};

export default industrialConfig;

/**
 * INSTRUÇÕES DE USO:
 *
 * 1. Copie este arquivo para o diretório do Twenty CRM
 * 2. No tailwind.config.ts do Twenty, faça merge:
 *
 *    import industrialConfig from './industrial-theme/tailwind.config';
 *    import { merge } from 'lodash';
 *
 *    const config = merge(baseConfig, industrialConfig);
 *    export default config;
 *
 * 3. Importe o industrial.css no entry point principal
 */
