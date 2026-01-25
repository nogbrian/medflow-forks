"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * Metric - Intelligent Flow Design
 *
 * Exibição de métricas/KPIs com glassmorphism e hover lift.
 * Números grandes com fonte display, label mono.
 */

export interface MetricProps extends React.HTMLAttributes<HTMLDivElement> {
  label: string;
  value: string | number;
  change?: {
    value: number;
    trend: "up" | "down" | "neutral";
  };
  icon?: React.ReactNode;
}

const Metric = React.forwardRef<HTMLDivElement, MetricProps>(
  ({ className, label, value, change, icon, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "flex flex-col justify-end p-6",
          "bg-white/80 backdrop-blur-sm",
          "border border-eng-blue/[0.08]",
          "rounded-lg shadow-md",
          "group hover:shadow-xl hover:-translate-y-1 hover:border-alert-30",
          "transition-all duration-300",
          className
        )}
        {...props}
      >
        {icon && (
          <div className="mb-4 text-alert">
            {icon}
          </div>
        )}
        <span className="font-mono text-xs uppercase text-concrete tracking-wider mb-2">
          {label}
        </span>
        <div className="flex items-end gap-3">
          <span className="font-display text-4xl font-semibold tracking-tight tabular-nums text-eng-blue group-hover:translate-x-1 transition-transform duration-300">
            {value}
          </span>
          {change && (
            <span
              className={cn(
                "font-mono text-xs tabular-nums mb-1",
                change.trend === "up" && "text-green-600",
                change.trend === "down" && "text-alert",
                change.trend === "neutral" && "text-concrete"
              )}
            >
              {change.trend === "up" && "↑"}
              {change.trend === "down" && "↓"}
              {change.value > 0 && "+"}
              {change.value}%
            </span>
          )}
        </div>
      </div>
    );
  }
);

Metric.displayName = "Metric";

export { Metric };
