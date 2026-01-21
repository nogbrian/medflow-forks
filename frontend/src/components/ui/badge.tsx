"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * Badge Industrial
 *
 * Etiqueta técnica com borda e fonte mono.
 */

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "active" | "warning" | "success" | "info";
}

const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = "default", ...props }, ref) => {
    const variants = {
      default: "bg-white text-ink border-graphite",
      active: "bg-ink text-white border-ink",
      warning: "bg-accent-orange text-white border-accent-orange",
      success: "bg-[#22C55E] text-white border-[#22C55E]",
      info: "bg-accent-blue text-white border-accent-blue",
    };

    return (
      <span
        ref={ref}
        className={cn(
          "inline-flex items-center gap-1.5",
          "border px-2 py-1",
          "font-mono text-[10px] uppercase tracking-wider",
          "rounded-none",
          variants[variant],
          className
        )}
        {...props}
      />
    );
  }
);

Badge.displayName = "Badge";

export { Badge };
