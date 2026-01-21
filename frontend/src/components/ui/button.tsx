"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * Button Industrial
 *
 * Variantes:
 * - primary: Fundo preto, sombra laranja
 * - secondary: Fundo branco, sombra preta
 * - ghost: Sem fundo, sem sombra
 * - danger: Fundo laranja
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
      "font-medium uppercase tracking-wide",
      "transition-all duration-100 ease-out",
      "disabled:opacity-50 disabled:pointer-events-none",
      // Sem border-radius
      "rounded-none"
    );

    const variants = {
      primary: cn(
        "bg-ink text-white border border-ink",
        "shadow-[4px_4px_0px_0px_#F24E1E]",
        "hover:bg-accent-orange hover:border-accent-orange",
        "active:translate-x-0.5 active:translate-y-0.5 active:shadow-[2px_2px_0px_0px_#F24E1E]"
      ),
      secondary: cn(
        "bg-white text-ink border border-graphite",
        "shadow-[4px_4px_0px_0px_#000000]",
        "hover:bg-paper",
        "active:translate-x-0.5 active:translate-y-0.5 active:shadow-[2px_2px_0px_0px_#000000]"
      ),
      ghost: cn(
        "bg-transparent text-ink border-none",
        "hover:text-accent-orange"
      ),
      danger: cn(
        "bg-accent-orange text-white border border-accent-orange",
        "shadow-[4px_4px_0px_0px_#000000]",
        "hover:bg-[#D9451B]",
        "active:translate-x-0.5 active:translate-y-0.5 active:shadow-[2px_2px_0px_0px_#000000]"
      ),
    };

    const sizes = {
      sm: "px-3 py-1.5 text-xs",
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
            <span className="size-4 border-2 border-current border-t-transparent animate-spin" />
            PROCESSANDO...
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
