"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * Badge - Intelligent Flow Design
 *
 * Pill-style badge com bordas arredondadas e cores suaves.
 */

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "active" | "warning" | "success" | "info";
}

const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = "default", ...props }, ref) => {
    const variants = {
      default: "bg-eng-blue-05 text-eng-blue border-eng-blue-10",
      active: "bg-eng-blue text-white border-eng-blue",
      warning: "bg-alert-10 text-alert border-alert-30",
      success: "bg-green-50 text-green-700 border-green-200",
      info: "bg-blue-50 text-blue-700 border-blue-200",
    };

    return (
      <span
        ref={ref}
        className={cn(
          "inline-flex items-center gap-1.5",
          "border px-3 py-1",
          "font-mono text-xs font-medium uppercase tracking-wide",
          "rounded-full",
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
