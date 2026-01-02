"use client";

import { AlertCircle } from "lucide-react";
import { ProcessCombobox } from "./process-combobox";
import { TaskCombobox } from "./task-combobox";
import { ScopeControl } from "./scope-control";
import { ContextChips } from "./context-chips";
import type { ContextState, ProcessOption, TaskOption, ScopeType } from "@/types";

interface ContextBarProps {
  state: ContextState;
  onProcessChange: (process: ProcessOption | null) => void;
  onTaskChange: (task: TaskOption | null) => void;
  onScopeChange: (scope: ScopeType) => void;
  onClearProcess: () => void;
  onClearTask: () => void;
}

export function ContextBar({
  state,
  onProcessChange,
  onTaskChange,
  onScopeChange,
  onClearProcess,
  onClearTask,
}: ContextBarProps) {
  const hasProcess = !!state.process;
  const isModeled = state.process?.has_model ?? false;
  const needsTask = isModeled && state.scope === "step" && !state.task;

  return (
    <div className="space-y-3 p-3 border border-border rounded-lg bg-muted/30">
      {/* Controls Row */}
      <div className="flex flex-wrap items-start gap-3">
        <ProcessCombobox value={state.process} onSelect={onProcessChange} />

        {hasProcess && (
          <>
            <TaskCombobox
              processId={isModeled ? state.process!.id : null}
              value={state.task}
              onSelect={onTaskChange}
              disabled={!isModeled}
            />

            <ScopeControl
              value={state.scope}
              onChange={onScopeChange}
              disabled={!hasProcess}
              stepDisabled={!isModeled}
            />
          </>
        )}
      </div>

      {/* Context Chips */}
      {hasProcess && (
        <ContextChips
          state={state}
          onClearProcess={onClearProcess}
          onClearTask={onClearTask}
        />
      )}

      {/* Validation Warning */}
      {needsTask && (
        <div className="flex items-center gap-2 text-sm text-amber-400">
          <AlertCircle className="h-4 w-4" />
          <span>
            Wähle einen Schritt für lokalen Kontext, oder wechsle zu
            &quot;Überblick&quot;.
          </span>
        </div>
      )}

      {/* Docs-only Helper */}
      {hasProcess && !isModeled && (
        <div className="text-xs text-muted-foreground">
          Für diesen Prozess liegt kein BPMN-Modell vor. Es wird nur
          Dokumentkontext verwendet.
        </div>
      )}
    </div>
  );
}
