"use client";

import { useState, useCallback } from "react";
import type { ContextState, ProcessOption, TaskOption, LaneOption, ScopeType } from "@/types";

const initialState: ContextState = {
  process: null,
  task: null,
  role: null,
  scope: "docs",  // Default to docs scope
};

export function useContextState() {
  const [state, setState] = useState<ContextState>(initialState);

  const setProcess = useCallback((process: ProcessOption | null) => {
    setState((prev) => ({
      ...prev,
      process,
      // Clear role and task when process changes
      role: null,
      task: null,
      // Default to docs scope (works for all process types)
      scope: "docs",
    }));
  }, []);

  const setRole = useCallback((role: LaneOption | null) => {
    setState((prev) => ({
      ...prev,
      role,
      // Clear task if it's not in the new role's lane
      task: prev.task && prev.task.lane_id !== role?.id ? null : prev.task,
    }));
  }, []);

  const setTask = useCallback((task: TaskOption | null) => {
    setState((prev) => ({
      ...prev,
      task,
      // Auto-switch to step context when selecting a task
      scope: task ? "step" : "docs",
    }));
  }, []);

  const setScope = useCallback((scope: ScopeType) => {
    setState((prev) => ({
      ...prev,
      scope,
      // Clear task AND role when switching to docs or overview (only keep them in step mode)
      task: scope === "step" ? prev.task : null,
      role: scope === "step" ? prev.role : null,
    }));
  }, []);

  const clearProcess = useCallback(() => {
    setState(initialState);
  }, []);

  const clearTask = useCallback(() => {
    setState((prev) => ({
      ...prev,
      task: null,
      // Auto-switch to docs when clearing task in step mode
      scope: prev.scope === "step" ? "docs" : prev.scope,
    }));
  }, []);

  const reset = useCallback(() => {
    setState(initialState);
  }, []);

  return {
    state,
    setProcess,
    setRole,
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
