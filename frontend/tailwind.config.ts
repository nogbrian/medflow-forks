import type { Config } from "tailwindcss";

/**
 * MedFlow Intelligent Flow Design System
 *
 * Estilo: Fluido / Tech-Forward / Premium
 * Filosofia: "IA Inteligente, Design Elegante"
 *
 * Bordas suaves, sombras com cor, glassmorphism sutil.
 * Transições fluidas, animações de entrada.
 */
const config: Config = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      // =========================================
      // CORES (Intelligent Flow)
      // =========================================
      colors: {
        // Engineering Blue - Primary brand color
        "eng-blue": {
          DEFAULT: "#0F3038",
          90: "rgba(15, 48, 56, 0.9)",
          70: "rgba(15, 48, 56, 0.7)",
          50: "rgba(15, 48, 56, 0.5)",
          30: "rgba(15, 48, 56, 0.3)",
          10: "rgba(15, 48, 56, 0.1)",
          "05": "rgba(15, 48, 56, 0.05)",
        },

        // Alert Orange - CTAs and highlights
        alert: {
          DEFAULT: "#FF6400",
          90: "rgba(255, 100, 0, 0.9)",
          70: "rgba(255, 100, 0, 0.7)",
          50: "rgba(255, 100, 0, 0.5)",
          30: "rgba(255, 100, 0, 0.3)",
          10: "rgba(255, 100, 0, 0.1)",
          "05": "rgba(255, 100, 0, 0.05)",
        },

        // Neutrals
        concrete: "#808080",
        "tech-white": "#F5F5F2",

        // Legacy aliases for compatibility
        paper: "#F5F5F2",
        ink: "#0F3038",
        graphite: "rgba(15, 48, 56, 0.1)",
        steel: "#808080",
        accent: {
          orange: "#FF6400",
          blue: "#0F3038",
        },
      },

      // =========================================
      // TIPOGRAFIA
      // =========================================
      fontFamily: {
        display: ["Clash Display", "sans-serif"],
        sans: ["Satoshi", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },

      fontSize: {
        // Display (Títulos grandes)
        "display-xl": ["5rem", { lineHeight: "1.05", letterSpacing: "-0.02em", fontWeight: "600" }],
        "display-lg": ["4rem", { lineHeight: "1.08", letterSpacing: "-0.02em", fontWeight: "600" }],
        "display": ["3rem", { lineHeight: "1.1", letterSpacing: "-0.02em", fontWeight: "600" }],

        // Labels (Mono, uppercase)
        "label": ["0.75rem", { lineHeight: "1", letterSpacing: "0.05em", fontWeight: "500" }],
        "label-sm": ["0.625rem", { lineHeight: "1", letterSpacing: "0.05em", fontWeight: "500" }],
      },

      // =========================================
      // SOMBRAS (Soft with color tint)
      // =========================================
      boxShadow: {
        "xs": "0 1px 2px rgba(15, 48, 56, 0.04)",
        "sm": "0 2px 4px rgba(15, 48, 56, 0.06)",
        "md": "0 4px 12px rgba(15, 48, 56, 0.08)",
        "lg": "0 8px 24px rgba(15, 48, 56, 0.1)",
        "xl": "0 16px 48px rgba(15, 48, 56, 0.12)",
        "2xl": "0 24px 64px rgba(15, 48, 56, 0.16)",
        "glow-orange": "0 8px 32px rgba(255, 100, 0, 0.3)",
        "glow-blue": "0 8px 32px rgba(15, 48, 56, 0.2)",
        // Legacy hard shadows for backwards compatibility
        "hard": "4px 4px 0px 0px #0F3038",
        "hard-sm": "2px 2px 0px 0px #0F3038",
        "hard-orange": "4px 4px 0px 0px #FF6400",
        "hard-orange-sm": "2px 2px 0px 0px #FF6400",
        "hard-active": "2px 2px 0px 0px #0F3038",
        "hard-orange-active": "2px 2px 0px 0px #FF6400",
      },

      // =========================================
      // ESPAÇAMENTO (Grid 8px)
      // =========================================
      spacing: {
        "18": "4.5rem",
        "22": "5.5rem",
      },

      // =========================================
      // BORDAS (Soft rounded)
      // =========================================
      borderRadius: {
        "none": "0px",
        "sm": "8px",
        "DEFAULT": "8px",
        "md": "12px",
        "lg": "16px",
        "xl": "24px",
        "2xl": "32px",
        "3xl": "40px",
        "full": "9999px",
      },

      // =========================================
      // Z-INDEX (Escala fixa)
      // =========================================
      zIndex: {
        "header": "50",
        "sidebar": "40",
        "dropdown": "60",
        "modal": "70",
        "toast": "80",
      },

      // =========================================
      // ANIMAÇÕES (Fluid, elegant)
      // =========================================
      keyframes: {
        "fade-in": {
          from: { opacity: "0", transform: "translateY(4px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in-up": {
          "0%": { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "scale-in": {
          "0%": { opacity: "0", transform: "scale(0.9)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        "float": {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-20px)" },
        },
        "pulse-glow": {
          "0%, 100%": { boxShadow: "0 8px 32px rgba(255, 100, 0, 0.3)" },
          "50%": { boxShadow: "0 8px 40px rgba(255, 100, 0, 0.5)" },
        },
      },

      animation: {
        "fade-in": "fade-in 150ms cubic-bezier(0.4, 0, 0.2, 1)",
        "fade-in-up": "fade-in-up 0.6s ease-out forwards",
        "scale-in": "scale-in 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards",
        "float": "float 6s ease-in-out infinite",
        "pulse-glow": "pulse-glow 2s ease-in-out infinite",
      },

      transitionDuration: {
        "fast": "100ms",
        "normal": "150ms",
        "300": "300ms",
        "400": "400ms",
      },

      transitionTimingFunction: {
        "industrial": "cubic-bezier(0.4, 0, 0.2, 1)",
        "bounce-out": "cubic-bezier(0.175, 0.885, 0.32, 1.275)",
      },

      // =========================================
      // BACKGROUND PATTERNS
      // =========================================
      backgroundImage: {
        "grid-pattern": "url(\"data:image/svg+xml,%3Csvg width='80' height='80' viewBox='0 0 80 80' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%230F3038' fill-opacity='0.03'%3E%3Cpath d='M0 0h80v1H0zM0 0h1v80H0z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E\")",
        "mesh-gradient": "radial-gradient(ellipse 80% 50% at 20% -10%, rgba(255,100,0,0.08) 0%, transparent 50%), radial-gradient(ellipse 60% 40% at 85% 110%, rgba(15,48,56,0.06) 0%, transparent 50%), linear-gradient(180deg, #F5F5F2 0%, #FFFFFF 100%)",
      },

      // =========================================
      // BACKDROP BLUR
      // =========================================
      backdropBlur: {
        xs: "2px",
        sm: "4px",
        md: "8px",
        lg: "12px",
        xl: "16px",
      },
    },
  },
  plugins: [],
};

export default config;
