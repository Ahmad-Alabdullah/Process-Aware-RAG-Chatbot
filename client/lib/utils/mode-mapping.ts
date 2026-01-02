import type { GatingMode, ContextState } from "@/types";
import type { AskRequest } from "@/types";

/**
 * Determine backend gating mode from context state
 */
export function determineGatingMode(context: ContextState): GatingMode {
  const { process, task, scope } = context;

  if (!process) return "NONE";

  if (!process.has_model) return "DOCS_ONLY";

  if (scope === "overview") return "PROCESS_CONTEXT";

  if (scope === "step" && task) return "GATING_ENABLED";

  // Fallback: scope=step but no task → auto-fallback to overview
  return "PROCESS_CONTEXT";
}

/**
 * Build request payload from context state
 */
export function buildAskRequest(
  query: string,
  context: ContextState,
  options: Partial<AskRequest> = {}
): AskRequest {
  const mode = determineGatingMode(context);

  const request: AskRequest = {
    query,
    ...options,
  };

  if (context.process) {
    request.process_name = context.process.name;

    if (context.process.has_model) {
      request.process_id = context.process.id;

      if (mode === "PROCESS_CONTEXT") {
        request.force_process_context = true;
      }

      if (mode === "GATING_ENABLED" && context.task) {
        request.current_node_id = context.task.task_id;
      }
    }
  }

  return request;
}

/**
 * Check if context state requires task selection
 * Returns true if scope is "step" but no task is selected
 */
export function needsTaskSelection(context: ContextState): boolean {
  return (
    context.process?.has_model === true &&
    context.scope === "step" &&
    !context.task
  );
}
