"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * Input - Intelligent Flow Design
 *
 * Campo de entrada com bordas arredondadas e estados modernos.
 * Focus com ring sutil e transições suaves.
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
            className="block font-sans text-sm font-medium text-eng-blue mb-2"
          >
            {label}
          </label>
        )}
        <input
          type={type}
          id={inputId}
          className={cn(
            "flex h-12 w-full px-5 py-3",
            "bg-white/80 backdrop-blur-sm",
            "border-2 border-eng-blue-10",
            "rounded-md",
            "font-sans text-eng-blue text-sm",
            "placeholder:text-concrete/50",
            "transition-all duration-300",
            "hover:border-eng-blue-30",
            "focus:border-alert focus:ring-4 focus:ring-alert-10 focus:outline-none",
            "disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-eng-blue-05",
            error && "border-alert focus:ring-alert-10",
            className
          )}
          ref={ref}
          {...props}
        />
        {error && (
          <p className="mt-2 font-sans text-sm text-alert">
            {error}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";

export { Input };
