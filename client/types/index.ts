// API Types for Process-Aware RAG Chatbot

// === QA/Chat Types ===

export interface AskRequest {
  query: string;
  top_k?: number;
  use_rerank?: boolean;
  rerank_top_n?: number;
  use_hyde?: boolean;
  model?: string;
  process_name?: string;
  process_id?: string;
  definition_id?: string;
  current_node_id?: string;
  roles?: string[];
  force_process_context?: boolean;
  prompt_style?: string;
  tags?: string[];
}

export interface EvidenceChunk {
  chunk_id: string;
  text: string;
  score?: number; // cosine similarity
  rerank_score?: number; // cross-encoder score
  metadata?: Record<string, unknown>;
}

export interface GatingMetadata {
  context_type: "none" | "overview" | "gating";
  num_allowed_lanes?: number;
  num_allowed_nodes?: number;
  num_successors?: number;
  num_gateways?: number;
  current_node?: string;
  current_lane?: string;
}

export interface PositionInfo {
  current_node: string;
  current_node_id: string;
  current_lane?: string;
  allowed_successors?: Array<{
    name: string;
    is_gateway: boolean;
    branches?: Array<{ describe: string }>;
  }>;
}

export interface ProcessOverview {
  all_lanes: string[];
  all_steps: string[];
  key_decisions: string[];
}

export interface AskResponse {
  answer: string;
  context: EvidenceChunk[];
  gating_mode: "none" | "process" | "gating";
  gating_hint: string;
  gating_metadata: GatingMetadata;
  whitelist: boolean;
  used_model: string;
  used_hyde: boolean;
  used_rerank: boolean;
  used_retrieval_mode: string;
  used_temperature: number;
  used_llm_backend: string;
  top_k: number;
  embedding_config: {
    backend: string;
    model: string;
  };
  position?: PositionInfo;
  process_overview?: ProcessOverview;
}

// === Process/BPMN Types ===

export interface ProcessOption {
  id: string;
  name: string;
  source: "neo4j" | "docs";
  has_model: boolean;
  doc_count?: number; // Number of documents for this process
}

export interface TaskOption {
  task_id: string;
  task_name: string;
  task_type?: string;
  lane_id?: string;
}

export interface BpmnDefinition {
  id: string;
  name: string;
  filename?: string;
  processCount: number;
  processes: Array<{ id: string; name: string }>;
}

export interface ProcessCombo {
  id: string;
  name: string;
  lanes: Array<{ id: string; name: string }>;
  nodes: Array<{
    id: string;
    name: string;
    type: string;
    laneId?: string;
  }>;
}

// === Chat History Types ===

export interface Chat {
  id: string;
  title: string;
  preview: string;
  created_at: string;
  updated_at: string;
  message_count?: number;
}

export interface Message {
  id: string;
  chat_id: string;
  role: "user" | "assistant";
  content: string;
  evidence?: EvidenceChunk[];
  confidence?: ConfidenceInfo;
  gating_mode?: string;
  isError?: boolean; // Indicates if this message is an error message
  created_at: string;
}

export interface ConfidenceInfo {
  score: number;
  level: "high" | "medium" | "low";
  label: string;
  color: string;
}

// === Context State Types ===

export type GatingMode =
  | "NONE"
  | "PROCESS_CONTEXT"
  | "GATING_ENABLED"
  | "DOCS_ONLY";

export type ScopeType = "overview" | "step";

export interface ContextState {
  process: ProcessOption | null;
  task: TaskOption | null;
  scope: ScopeType;
}

// === Admin Types ===

export interface AdminChat extends Chat {
  session_id: string;
}

// === API Response Wrappers ===

export interface ApiResponse<T> {
  ok: boolean;
  data?: T;
  error?: string;
}
