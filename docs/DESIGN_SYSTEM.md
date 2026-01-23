# Design System - MedFlow

## Philosophy

**Industrial / Swiss Design** - "Infraestrutura, não Criatividade"

Cores de materiais, não de tela. Bordas expostas, sombras sólidas. The interface communicates precision, reliability, and professional infrastructure.

## Colors

### Base
| Token | Hex | Usage |
|-------|-----|-------|
| `paper` | `#F2F0E9` | Background principal (drafting paper) |
| `ink` | `#111111` | Texto primário |
| `graphite` | `#000000` | Bordas, estruturas |

### Accents
| Token | Hex | Usage |
|-------|-----|-------|
| `accent-orange` | `#F24E1E` | Safety Orange - ação crítica, active state |
| `accent-blue` | `#0047AB` | System Blue - links, informação técnica |

### Neutrals
| Token | Hex | Usage |
|-------|-----|-------|
| `steel` | `#666666` | Metadados, labels secundários |

### Feedback (via standard Tailwind)
| Context | Color |
|---------|-------|
| Success | `green-600` |
| Error | `red-600` |
| Warning | `amber-600` |
| Info | `accent-blue` |

## Typography

### Fonts
| Family | Token | Usage |
|--------|-------|-------|
| Inter Tight | `font-sans` | Headlines, body text |
| JetBrains Mono | `font-mono` | Data, labels, metrics, code |

### Scale
| Name | Size | Usage |
|------|------|-------|
| `display-xl` | 5rem | Hero headlines |
| `display-lg` | 4rem | Page titles |
| `display` | 3rem | Section headers |
| `label` | 0.75rem | Labels (uppercase, tracked) |
| `label-sm` | 0.625rem | Micro labels |

### Conventions
- Labels: `font-mono text-[10px] uppercase tracking-wider text-steel`
- Headings: `font-bold tracking-tight uppercase`
- Data values: `font-mono text-xs font-bold`

## Spacing

8px grid system. All spacing uses Tailwind's default scale (multiples of 4px/8px).

## Borders

- **Border radius:** 0px (default) - sharp industrial corners
- **Border color:** `graphite` (black) for structure
- **Border width:** 1px standard

## Shadows

Hard drop shadows (no blur, solid offset):

| Token | Value | Usage |
|-------|-------|-------|
| `shadow-hard` | `4px 4px 0px #000` | Cards, buttons |
| `shadow-hard-sm` | `2px 2px 0px #000` | Small elements |
| `shadow-hard-orange` | `4px 4px 0px #F24E1E` | CTA, primary action |
| `shadow-hard-active` | `2px 2px 0px #000` | Pressed state |

## Background Patterns

| Class | Effect |
|-------|--------|
| `bg-grid` | Subtle 40px grid pattern (3% opacity) |
| `bg-noise` | Fractal noise texture (2% opacity) |

## Z-Index Scale

| Token | Value | Element |
|-------|-------|---------|
| `z-header` | 50 | Top navigation |
| `z-sidebar` | 40 | Side navigation |
| `z-dropdown` | 60 | Dropdown menus |
| `z-modal` | 70 | Modal dialogs |
| `z-toast` | 80 | Toast notifications |

## UI Components

### Badge (`src/components/ui/badge.tsx`)
Variants: default, active, warning, success, info

### Button (`src/components/ui/button.tsx`)
Variants: primary (ink bg), secondary (border), ghost (no border)

### Card (`src/components/ui/card.tsx`)
Optional `folded` prop for decorative corner fold effect.

### Input (`src/components/ui/input.tsx`)
Standard text input with border and mono font.

### Metric (`src/components/ui/metric.tsx`)
KPI display with label, value, trend indicator (↑/↓).

### Table (`src/components/ui/table.tsx`)
Standard HTML table with Tailwind styling.

## Animation

- **Duration:** 100ms (fast), 150ms (normal)
- **Easing:** `cubic-bezier(0.4, 0, 0.2, 1)` (industrial - no bounce/elasticity)
- **Transitions:** Colors and transforms only. No opacity fades on primary elements.

## Application to Embedded Modules

The shell provides consistent chrome (header, sidebar) around embedded services. Individual services (Twenty, Chatwoot, Cal.com, Creative Studio) maintain their own internal styling. Visual cohesion is achieved through:

1. Consistent navigation chrome
2. Matching border/background treatment on iframe containers
3. Service headers with consistent badge + action button patterns
