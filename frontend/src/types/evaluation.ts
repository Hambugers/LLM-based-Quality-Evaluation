export type NodeStatus = "waiting" | "running" | "completed" | "failed";

export interface WorkflowNode {
  node_key: string;
  node_name: string;
  status: NodeStatus;
  started_at?: string | null;
  ended_at?: string | null;
  duration_ms?: number | null;
  summary?: string | null;
  error?: string | null;
  output?: Record<string, unknown>;
}

export interface WorkflowState {
  status: string;
  started_at?: string | null;
  ended_at?: string | null;
  duration_ms?: number | null;
  nodes: WorkflowNode[];
}

export interface RunLog {
  time: string;
  level: "info" | "warning" | "error" | string;
  message: string;
}

export interface EvaluationResponse {
  ok: boolean;
  run_id: string;
  workflow: WorkflowState;
  preprocess: Record<string, unknown>;
  text_eval: Record<string, unknown>;
  image_eval: Record<string, unknown>;
  cross_modal_eval: Record<string, unknown>;
  final_eval: Record<string, unknown>;
  uploaded_images: Array<Record<string, unknown>>;
  logs: RunLog[];
}

export interface EvaluationFormValues {
  user_question: string;
  model_answer: string;
  images: File[];
  text_model: string;
  vision_model: string;
}

export interface StreamEvent {
  event: string;
  data: Record<string, unknown>;
}

export interface RunState {
  run_id?: string;
  workflow: WorkflowState;
  preprocess?: Record<string, unknown>;
  text_eval?: Record<string, unknown>;
  image_eval?: Record<string, unknown>;
  cross_modal_eval?: Record<string, unknown>;
  final_eval?: Record<string, unknown>;
  uploaded_images?: Array<Record<string, unknown>>;
  logs: RunLog[];
  error?: string | null;
}
