"use client";

import { cn } from "@/lib/utils";
import type { ScopeType } from "@/types";

interface ScopeControlProps {
  value: ScopeType;
  onChange: (scope: ScopeType) => void;
  disabled?: boolean;
  stepDisabled?: boolean;
}

export function ScopeControl({
  value,
  onChange,
  disabled = false,
  stepDisabled = false,
}: ScopeControlProps) {
  const options: { value: ScopeType; label: string }[] = [
    { value: "docs", label: "Dokumente" },
    { value: "overview", label: "Prozess" },
    { value: "step", label: "Schritt" },
  ];

  return (
    <div
      className={cn(
        "inline-flex h-10 items-center rounded-lg border border-input p-1 bg-muted/50",
        disabled && "opacity-50 pointer-events-none"
      )}
      role="radiogroup"
      aria-label="Kontext-Scope"
    >
      {options.map((option) => {
        const isDisabled = disabled || (option.value === "step" && stepDisabled);
        const isSelected = value === option.value;

        return (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={isSelected}
            disabled={isDisabled}
            onClick={() => !isDisabled && onChange(option.value)}
            className={cn(
              "px-3 py-1.5 text-sm font-medium rounded-md transition-colors",
              isSelected
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground",
              isDisabled && "opacity-50 cursor-not-allowed"
            )}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
