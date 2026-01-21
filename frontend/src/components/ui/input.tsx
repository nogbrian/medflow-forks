"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * Input Industrial
 *
 * Campo de entrada com estética de formulário técnico.
 * Bordas pretas, sem border-radius.
 */

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, label, error, id, ...props }, ref) => {
    const inputId = id || React.useId();

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={inputId}
            className="block font-mono text-[10px] uppercase text-steel mb-2 tracking-wider"
          >
            {label}
          </label>
        )}
        <input
          type={type}
          id={inputId}
          className={cn(
            "flex h-12 w-full bg-white border border-graphite px-4 py-3",
            "text-ink text-sm placeholder:text-steel",
            "transition-colors duration-100",
            "focus:outline-none focus:border-accent-orange focus:ring-0",
            "disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-paper",
            "rounded-none",
            error && "border-accent-orange",
            className
          )}
          ref={ref}
          {...props}
        />
        {error && (
          <p className="mt-1.5 font-mono text-[10px] uppercase text-accent-orange tracking-wider">
            {error}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";

export { Input };
