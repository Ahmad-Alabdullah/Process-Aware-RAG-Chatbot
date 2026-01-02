"use client";

import { X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { ContextState } from "@/types";

interface ContextChipsProps {
  state: ContextState;
  onClearProcess: () => void;
  onClearTask: () => void;
}

export function ContextChips({
  state,
  onClearProcess,
  onClearTask,
}: ContextChipsProps) {
  if (!state.process) return null;

  return (
    <div className="flex flex-wrap gap-2">
      <Badge variant="secondary" className="gap-1 pr-1">
        <span className="text-xs opacity-70">Prozess:</span>
        <span>{state.process.name}</span>
        <button
          onClick={onClearProcess}
          className="ml-1 hover:bg-background/50 rounded p-0.5"
          aria-label="Prozess entfernen"
        >
          <X className="h-3 w-3" />
        </button>
      </Badge>

      {state.task && (
        <Badge variant="secondary" className="gap-1 pr-1">
          <span className="text-xs opacity-70">Schritt:</span>
          <span>{state.task.task_name}</span>
          <button
            onClick={onClearTask}
            className="ml-1 hover:bg-background/50 rounded p-0.5"
            aria-label="Schritt entfernen"
          >
            <X className="h-3 w-3" />
          </button>
        </Badge>
      )}

      <Badge
        variant="outline"
        className={
          state.scope === "step"
            ? "bg-purple-500/20 text-purple-400 border-purple-500/30"
            : "bg-blue-500/20 text-blue-400 border-blue-500/30"
        }
      >
        {state.scope === "step" ? "Schritt-Kontext" : "Prozess-Überblick"}
      </Badge>
    </div>
  );
}
