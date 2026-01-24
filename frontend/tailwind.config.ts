import type { Config } from "tailwindcss";

/**
 * MedFlow Industrial Design System
 *
 * Estilo: Industrial / Suíço
 * Filosofia: "Infraestrutura, não Criatividade"
 *
 * Cores de materiais, não de tela.
 * Bordas expostas, sombras sólidas.
 */
const config: Config = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      // =========================================
      // CORES (Materiais)
      // =========================================
      colors: {
        // Base (Papel & Tinta)
        paper: "#F2F0E9",      // Drafting Paper - Fundo principal
        ink: "#111111",        // Ink Black - Texto primário
        graphite: "#000000",   // Graphite - Estruturas/bordas

        // Acentos (Sinalização Industrial)
        accent: {
          orange: "#F24E1E",   // Safety Orange - Ação crítica
          blue: "#0047AB",     // System Blue - Links/info técnica
        },

        // Neutros
        steel: "#666666",      // Steel Gray - Metadados
      },

      // =========================================
      // TIPOGRAFIA
      // =========================================
      fontFamily: {
        sans: ["Inter Tight", "Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },

      fontSize: {
        // Display (Títulos grandes)
        "display-xl": ["5rem", { lineHeight: "0.9", letterSpacing: "-0.04em", fontWeight: "700" }],
        "display-lg": ["4rem", { lineHeight: "0.95", letterSpacing: "-0.04em", fontWeight: "700" }],
        "display": ["3rem", { lineHeight: "1", letterSpacing: "-0.03em", fontWeight: "700" }],

        // Labels (Mono, uppercase)
        "label": ["0.75rem", { lineHeight: "1", letterSpacing: "0.05em", fontWeight: "500" }],
        "label-sm": ["0.625rem", { lineHeight: "1", letterSpacing: "0.05em", fontWeight: "500" }],
      },

      // =========================================
      // SOMBRAS (Hard Shadow - Industrial)
      // =========================================
      boxShadow: {
        "hard": "4px 4px 0px 0px #000000",
        "hard-sm": "2px 2px 0px 0px #000000",
        "hard-orange": "4px 4px 0px 0px #F24E1E",
        "hard-orange-sm": "2px 2px 0px 0px #F24E1E",
        // Estado ativo (pressed)
        "hard-active": "2px 2px 0px 0px #000000",
        "hard-orange-active": "2px 2px 0px 0px #F24E1E",
      },

      // =========================================
      // ESPAÇAMENTO (Grid 8px)
      // =========================================
      spacing: {
        "18": "4.5rem",
        "22": "5.5rem",
      },

      // =========================================
      // BORDAS (Cantos retos por padrão)
      // =========================================
      borderRadius: {
        "none": "0px",
        "sm": "2px",
        "DEFAULT": "0px",
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
      // ANIMAÇÕES (Mecânicas, não elásticas)
      // =========================================
      keyframes: {
        "fade-in": {
          from: { opacity: "0", transform: "translateY(4px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
      },

      animation: {
        "fade-in": "fade-in 150ms cubic-bezier(0.4, 0, 0.2, 1)",
      },

      transitionDuration: {
        "fast": "100ms",
        "normal": "150ms",
      },

      transitionTimingFunction: {
        "industrial": "cubic-bezier(0.4, 0, 0.2, 1)",
      },

      // =========================================
      // BACKGROUND PATTERNS
      // =========================================
      backgroundImage: {
        "grid-pattern": "url(\"data:image/svg+xml,%3Csvg width='40' height='40' viewBox='0 0 40 40' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23000000' fill-opacity='0.03'%3E%3Cpath d='M0 0h40v1H0zM0 0h1v40H0z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E\")",
        "noise": "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.02'/%3E%3C/svg%3E\")",
      },
    },
  },
  plugins: [],
};

export default config;
