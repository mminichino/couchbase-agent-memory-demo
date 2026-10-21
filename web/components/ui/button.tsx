"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost" | "danger";
};

const styles: Record<NonNullable<ButtonProps["variant"]>, string> = {
  primary:
    "bg-brand text-brandFg hover:bg-brandHover focus-visible:outline-brand",
  secondary:
    "bg-panelMuted text-foreground border border-border hover:bg-panelHover focus-visible:outline-brand",
  ghost:
    "bg-transparent text-foreground hover:bg-panelMuted focus-visible:outline-brand",
  danger:
    "bg-danger text-dangerFg hover:bg-dangerHover focus-visible:outline-danger"
};

export function Button({
  className,
  variant = "primary",
  type = "button",
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      className={cn(
        "inline-flex h-10 items-center justify-center rounded-md px-4 text-sm font-medium transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 disabled:cursor-not-allowed disabled:opacity-60",
        styles[variant],
        className
      )}
      {...props}
    />
  );
}
