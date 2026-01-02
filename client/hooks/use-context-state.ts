"use client";

import { useState, useCallback } from "react";
import type { ContextState, ProcessOption, TaskOption, ScopeType } from "@/types";

const initialState: ContextState = {
  process: null,
  task: null,
  scope: "overview",
};

export function useContextState() {
  const [state, setState] = useState<ContextState>(initialState);

  const setProcess = useCallback((process: ProcessOption | null) => {
    setState((prev) => ({
      ...prev,
      process,
      // Clear task when process changes
      task: null,
      // Reset scope to overview when selecting a non-modeled process
      scope: process?.has_model ? prev.scope : "overview",
    }));
  }, []);

  const setTask = useCallback((task: TaskOption | null) => {
    setState((prev) => ({
      ...prev,
      task,
      // Auto-switch to step context when selecting a task
      scope: task ? "step" : "overview",
    }));
  }, []);

  const setScope = useCallback((scope: ScopeType) => {
    setState((prev) => ({
      ...prev,
      scope,
      // Clear task when switching to overview
      task: scope === "overview" ? null : prev.task,
    }));
  }, []);

  const clearProcess = useCallback(() => {
    setState(initialState);
  }, []);

  const clearTask = useCallback(() => {
    setState((prev) => ({
      ...prev,
      task: null,
      // Auto-switch to overview when clearing task in step mode
      scope: prev.scope === "step" ? "overview" : prev.scope,
    }));
  }, []);

  const reset = useCallback(() => {
    setState(initialState);
  }, []);

  return {
    state,
    setProcess,
    setTask,
    setScope,
    clearProcess,
    clearTask,
    reset,
    // Computed properties
    hasProcess: !!state.process,
    hasTask: !!state.task,
    isModeled: state.process?.has_model ?? false,
    needsTask: state.process?.has_model && state.scope === "step" && !state.task,
  };
}
