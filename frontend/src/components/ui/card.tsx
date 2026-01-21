"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * Card Industrial
 *
 * Ficha técnica com borda preta e fundo branco.
 * Opção de "dobra" decorativa no canto.
 */

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  folded?: boolean;
}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, folded = false, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "bg-white border border-graphite p-6 relative",
          folded && "card-industrial-folded",
          className
        )}
        {...props}
      >
        {children}
        {folded && (
          <div
            className="absolute top-0 right-0 w-0 h-0"
            style={{
              borderWidth: "0 16px 16px 0",
              borderStyle: "solid",
              borderColor: "#F2F0E9 #F2F0E9 transparent transparent",
            }}
          />
        )}
      </div>
    );
  }
);

Card.displayName = "Card";

const CardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex flex-col space-y-1.5 pb-4 border-b border-graphite mb-4", className)}
    {...props}
  />
));
CardHeader.displayName = "CardHeader";

const CardTitle = React.forwardRef<
  HTMLHeadingElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn("font-bold text-lg tracking-tight uppercase", className)}
    {...props}
  />
));
CardTitle.displayName = "CardTitle";

const CardDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn("text-sm text-steel", className)}
    {...props}
  />
));
CardDescription.displayName = "CardDescription";

const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("", className)} {...props} />
));
CardContent.displayName = "CardContent";

const CardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex items-center pt-4 border-t border-graphite mt-4", className)}
    {...props}
  />
));
CardFooter.displayName = "CardFooter";

export { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter };
