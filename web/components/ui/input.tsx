"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

type InputProps = React.InputHTMLAttributes<HTMLInputElement> & {
  error?: string;
};

export function Input({ className, error, ...props }: InputProps) {
  return (
    <div>
      <input
        className={cn(
          "h-10 w-full rounded-md border border-border bg-panel px-3 text-sm text-foreground outline-none transition placeholder:text-muted focus:border-brand focus:ring-2 focus:ring-brand/30",
          error && "border-danger focus:border-danger focus:ring-danger/30",
          className
        )}
        {...props}
      />
      {error ? (
        <p className="mt-1 text-xs text-dangerText" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
