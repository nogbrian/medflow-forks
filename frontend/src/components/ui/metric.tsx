"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * Metric Industrial
 *
 * Exibição de métricas/KPIs no estilo dashboard técnico.
 * Números grandes com fonte sans, label mono.
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
          "flex flex-col justify-end p-6 bg-white border border-graphite",
          "group hover:bg-paper/50 transition-colors duration-100",
          className
        )}
        {...props}
      >
        {icon && (
          <div className="mb-4 text-accent-orange">
            {icon}
          </div>
        )}
        <span className="font-mono text-[10px] uppercase text-steel tracking-wider mb-2">
          {label}
        </span>
        <div className="flex items-end gap-3">
          <span className="font-sans text-4xl font-bold tracking-tighter tabular-nums group-hover:translate-x-1 transition-transform duration-100">
            {value}
          </span>
          {change && (
            <span
              className={cn(
                "font-mono text-xs tabular-nums mb-1",
                change.trend === "up" && "text-[#22C55E]",
                change.trend === "down" && "text-accent-orange",
                change.trend === "neutral" && "text-steel"
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
