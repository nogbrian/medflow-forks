"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * Button - Intelligent Flow Design
 *
 * Variantes:
 * - primary: Fundo alert, sombra glow laranja, hover lift
 * - secondary: Borda eng-blue, hover lift
 * - ghost: Sem fundo, hover com background sutil
 * - danger: Fundo alert mais escuro
 */

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  isLoading?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", isLoading, children, disabled, ...props }, ref) => {
    const baseStyles = cn(
      "inline-flex items-center justify-center gap-2",
      "font-sans font-semibold",
      "transition-all duration-300 ease-out",
      "disabled:opacity-50 disabled:pointer-events-none disabled:transform-none",
      // Rounded corners - Intelligent Flow
      "rounded-md"
    );

    const variants = {
      primary: cn(
        "bg-alert text-white",
        "shadow-md shadow-glow-orange",
        "hover:shadow-lg hover:-translate-y-0.5",
        "active:translate-y-0 active:shadow-md"
      ),
      secondary: cn(
        "bg-transparent text-eng-blue",
        "border-2 border-eng-blue-30",
        "hover:border-eng-blue hover:bg-eng-blue-05 hover:-translate-y-0.5",
        "active:translate-y-0"
      ),
      ghost: cn(
        "bg-transparent text-eng-blue",
        "hover:text-alert hover:bg-alert-05",
        "rounded-md"
      ),
      danger: cn(
        "bg-red-600 text-white",
        "shadow-md",
        "hover:bg-red-700 hover:-translate-y-0.5",
        "active:translate-y-0"
      ),
    };

    const sizes = {
      sm: "px-4 py-2 text-xs",
      md: "px-6 py-3 text-sm",
      lg: "px-8 py-4 text-base",
    };

    return (
      <button
        className={cn(baseStyles, variants[variant], sizes[size], className)}
        ref={ref}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading ? (
          <>
            <span className="size-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
            Processando...
          </>
        ) : (
          children
        )}
      </button>
    );
  }
);

Button.displayName = "Button";

export { Button };
