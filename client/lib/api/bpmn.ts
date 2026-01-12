import { apiClient } from "./client";
import type {
  BpmnDefinition,
  ProcessCombo,
  ProcessOption,
  TaskOption,
  LaneOption,
} from "@/types";

interface DefinitionsResponse {
  ok: boolean;
  definitions: BpmnDefinition[];
}

interface ProcessNamesResponse {
  ok: boolean;
  process_names: Array<{ name: string; doc_count: number; has_model: boolean }>;
}

interface ComboResponse {
  ok: boolean;
  id: string;
  name: string;
  lanes: Array<{ id: string; name: string }>;
  nodes: Array<{ id: string; name: string; type: string; laneId?: string }>;
}

interface LanesResponse {
  ok: boolean;
  lanes: Array<{ id: string; name: string; task_count?: number }>;
}

/**
 * Fetch all BPMN definitions (modeled processes from Neo4j)
 */
export async function fetchDefinitions(): Promise<BpmnDefinition[]> {
  const response = await apiClient.get<DefinitionsResponse>(
    "/api/bpmn/definitions"
  );
  return response.definitions || [];
}

/**
 * Fetch process names from document index (OpenSearch aggregation)
 */
export async function fetchDocumentProcessNames(): Promise<ProcessOption[]> {
  try {
    const response = await apiClient.get<ProcessNamesResponse>(
      "/api/search/process-names"
    );
    if (response.ok) {
      return response.process_names.map((p) => ({
        id: `doc_${p.name}`,
        name: p.name,
        source: "docs" as const,
        has_model: false,
        doc_count: p.doc_count,
      }));
    }
    return [];
  } catch {
    return [];
  }
}

/**
 * Fetch merged process list from Neo4j + Document index
 * Combines BPMN-modeled processes with document-derived process names
 */
export async function fetchProcesses(): Promise<ProcessOption[]> {
  const [definitions, docProcesses] = await Promise.all([
    fetchDefinitions(),
    fetchDocumentProcessNames(),
  ]);

  // Create a map of doc processes by name for quick lookup
  const docProcessMap = new Map<string, ProcessOption>();
  for (const dp of docProcesses) {
    docProcessMap.set(dp.name.toLowerCase(), dp);
  }

  // Flatten all processes from BPMN definitions, merging with doc info if exists
  const bpmnProcesses: ProcessOption[] = [];
  const seenNames = new Set<string>();

  for (const def of definitions) {
    for (const proc of def.processes) {
      if (proc.id && proc.name) {
        const docInfo = docProcessMap.get(proc.name.toLowerCase());
        bpmnProcesses.push({
          id: proc.id,
          name: proc.name,
          source: "neo4j",
          has_model: true,
          // Merge doc_count if this process also has documents
          doc_count: docInfo?.doc_count,
        });
        seenNames.add(proc.name.toLowerCase());
      }
    }
  }

  // Add document-only processes (ones without BPMN models)
  const uniqueDocProcesses = docProcesses.filter(
    (dp) => !seenNames.has(dp.name.toLowerCase())
  );

  return [...bpmnProcesses, ...uniqueDocProcesses];
}

/**
 * Fetch nodes and lanes for a process (for task selection)
 */
export async function fetchProcessCombo(
  processId: string
): Promise<ProcessCombo | null> {
  try {
    const response = await apiClient.get<ComboResponse>(
      `/api/bpmn/processes/${processId}/combo`
    );
    if (response.ok) {
      return {
        id: response.id,
        name: response.name,
        lanes: response.lanes || [],
        nodes: response.nodes || [],
      };
    }
    return null;
  } catch {
    return null;
  }
}

/**
 * Get selectable tasks (user-facing nodes only) for a process.
 * - Filters to userTask and task types only (no callActivity, events, gateways)
 * - Deduplicates by task name to avoid showing same task multiple times
 */
export async function fetchTasks(processId: string): Promise<TaskOption[]> {
  const combo = await fetchProcessCombo(processId);
  if (!combo) return [];

  // Only include userTask (manual user tasks, not automated system tasks)
  const userFacingTypes = ["userTask"];

  // Filter and deduplicate by name
  const seenNames = new Set<string>();
  const tasks: TaskOption[] = [];

  for (const node of combo.nodes) {
    if (!userFacingTypes.includes(node.type)) continue;
    if (!node.name) continue; // Skip nameless nodes

    // Deduplicate by name
    const normalizedName = node.name.toLowerCase();
    if (seenNames.has(normalizedName)) continue;
    seenNames.add(normalizedName);

    tasks.push({
      task_id: node.id,
      task_name: node.name,
      task_type: node.type,
      lane_id: node.laneId,
    });
  }

  return tasks;
}

/**
 * Fetch lanes/roles for a process (for role selection combobox)
 */
export async function fetchRoles(processId: string): Promise<LaneOption[]> {
  try {
    const response = await apiClient.get<LanesResponse>(
      `/api/bpmn/processes/${processId}/lanes`
    );
    if (response.ok) {
      return response.lanes || [];
    }
    return [];
  } catch {
    return [];
  }
}
