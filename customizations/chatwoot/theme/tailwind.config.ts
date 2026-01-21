/**
 * MedFlow Industrial Theme - Chatwoot Tailwind Extension
 *
 * Este arquivo estende a configuração do Tailwind do Chatwoot
 * para aplicar o Design System Industrial.
 *
 * Nota: Chatwoot usa Vue.js, então a aplicação é diferente.
 * O CSS customizado é aplicado via Admin > Account Settings > Custom CSS
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

        // Chatwoot woot color override
        woot: {
          DEFAULT: "#F24E1E",
          25: "rgba(242, 78, 30, 0.05)",
          50: "rgba(242, 78, 30, 0.1)",
          75: "rgba(242, 78, 30, 0.15)",
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

        // Slate override (background/text)
        slate: {
          25: "#F2F0E9",
          50: "#E5E3DC",
          75: "#D8D6CF",
          100: "#CCCCCC",
          200: "#AAAAAA",
          300: "#888888",
          400: "#666666",
          500: "#444444",
          600: "#333333",
          700: "#222222",
          800: "#111111",
          900: "#0A0A0A",
        },

        // Status colors
        green: {
          DEFAULT: "#10B981",
          50: "rgba(16, 185, 129, 0.1)",
          500: "#10B981",
          600: "#059669",
          700: "#047857",
        },
        yellow: {
          DEFAULT: "#F59E0B",
          50: "rgba(245, 158, 11, 0.1)",
          500: "#F59E0B",
          600: "#D97706",
        },
        red: {
          DEFAULT: "#F24E1E",
          50: "rgba(242, 78, 30, 0.1)",
          500: "#F24E1E",
          600: "#DC2626",
        },
        blue: {
          DEFAULT: "#0047AB",
          50: "rgba(0, 71, 171, 0.1)",
          500: "#0047AB",
          600: "#1E40AF",
        },
      },

      // Tipografia Industrial
      fontFamily: {
        inter: ['"Inter Tight"', "Inter", "system-ui", "sans-serif"],
        display: ['"Inter Tight"', "Inter", "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', '"Fira Code"', "Consolas", "monospace"],
        sans: ["Inter", "system-ui", "sans-serif"],
      },

      // Font sizes
      fontSize: {
        xxs: ["0.625rem", { lineHeight: "1rem" }],
        xs: ["0.75rem", { lineHeight: "1rem" }],
        sm: ["0.875rem", { lineHeight: "1.25rem" }],
        base: ["1rem", { lineHeight: "1.5rem" }],
        lg: ["1.125rem", { lineHeight: "1.75rem" }],
        xl: ["1.25rem", { lineHeight: "1.75rem" }],
        "2xl": ["1.5rem", { lineHeight: "2rem" }],
        "3xl": ["1.875rem", { lineHeight: "2.25rem" }],
      },

      // Box Shadow Industrial
      boxShadow: {
        none: "none",
        hard: "4px 4px 0px 0px #000000",
        "hard-sm": "2px 2px 0px 0px #000000",
        "hard-lg": "6px 6px 0px 0px #000000",
        "hard-woot": "4px 4px 0px 0px #F24E1E",
        // Override Chatwoot shadows
        sm: "2px 2px 0px 0px #000000",
        md: "4px 4px 0px 0px #000000",
        lg: "6px 6px 0px 0px #000000",
        xl: "8px 8px 0px 0px #000000",
        dropdown: "4px 4px 0px 0px #000000",
        spread: "4px 4px 0px 0px #000000",
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
        // Chatwoot specific
        normal: "0px",
        small: "0px",
        large: "0px",
        larger: "0px",
        rounded: "0px",
      },

      // Spacing
      spacing: {
        0.5: "0.125rem",
        1: "0.25rem",
        1.5: "0.375rem",
        2: "0.5rem",
        2.5: "0.625rem",
        3: "0.75rem",
        3.5: "0.875rem",
        4: "1rem",
        5: "1.25rem",
        6: "1.5rem",
        7: "1.75rem",
        8: "2rem",
        9: "2.25rem",
        10: "2.5rem",
        11: "2.75rem",
        12: "3rem",
        14: "3.5rem",
        16: "4rem",
      },

      // Z-index
      zIndex: {
        dropdown: "50",
        modal: "100",
        overlay: "90",
        tooltip: "70",
      },

      // Transitions
      transitionDuration: {
        fast: "100ms",
        normal: "150ms",
        slow: "300ms",
      },
    },
  },
};

export default industrialConfig;

/**
 * INSTRUÇÕES DE USO PARA CHATWOOT:
 *
 * 1. OPÇÃO A - Via Dashboard Admin:
 *    - Acesse: Settings > Account Settings > Custom CSS
 *    - Cole o conteúdo do industrial.css
 *
 * 2. OPÇÃO B - Via Docker build:
 *    - Monte o arquivo CSS no container:
 *      volumes:
 *        - ./customizations/chatwoot/theme/industrial.css:/app/public/custom.css
 *    - Configure a env var:
 *      CUSTOM_STYLESHEET_URL=/custom.css
 *
 * 3. OPÇÃO C - Via fork do código:
 *    - Adicione ao app/javascript/widget/assets/scss/variables.scss
 *    - Modifique tailwind.config.js com este config
 *
 * 4. Para branding via env vars:
 *    INSTALLATION_NAME=MedFlow
 *    LOGO_URL=https://cdn.../logo.svg
 *    BRAND_URL=https://medflow.com.br
 */
