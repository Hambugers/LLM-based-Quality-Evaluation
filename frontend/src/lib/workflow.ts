import type { RunLog, RunState, StreamEvent, WorkflowNode } from "../types/evaluation";

export const workflowNodes: WorkflowNode[] = [
  { node_key: "input", node_name: "输入接收", status: "waiting" },
  { node_key: "preprocess", node_name: "预处理", status: "waiting" },
  { node_key: "text_eval", node_name: "文本评估", status: "waiting" },
  { node_key: "image_eval", node_name: "图片基础质检", status: "waiting" },
  { node_key: "cross_modal_eval", node_name: "图文一致性评估", status: "waiting" },
  { node_key: "aggregate", node_name: "结果聚合", status: "waiting" },
  { node_key: "final_decision", node_name: "最终裁决", status: "waiting" },
];

export function createInitialRunState(): RunState {
  return {
    workflow: {
      status: "idle",
      nodes: workflowNodes.map((node) => ({ ...node })),
    },
    logs: [],
    error: null,
  };
}

export function applyStreamEvent(state: RunState, streamEvent: StreamEvent): RunState {
  const { event, data } = streamEvent;
  if (event === "run_started") {
    return {
      ...state,
      run_id: typeof data.run_id === "string" ? data.run_id : state.run_id,
      workflow: { ...state.workflow, status: "running" },
      error: null,
    };
  }

  if (event === "node_update") {
    const nodeKey = String(data.node_key ?? "");
    return {
      ...state,
      workflow: {
        ...state.workflow,
        nodes: state.workflow.nodes.map((node) =>
          node.node_key === nodeKey ? { ...node, ...data } : node,
        ) as WorkflowNode[],
      },
    };
  }

  if (event === "log") {
    return {
      ...state,
      logs: [...state.logs, data as unknown as RunLog],
    };
  }

  if (event === "run_completed") {
    const payload = data as unknown as RunState;
    return {
      ...state,
      ...payload,
      workflow: payload.workflow ?? state.workflow,
      logs: payload.logs ?? state.logs,
      error: null,
    };
  }

  if (event === "run_failed") {
    return {
      ...state,
      workflow: { ...state.workflow, status: "failed" },
      error: typeof data.error === "string" ? data.error : "评估执行失败",
    };
  }

  return state;
}

export function activeNode(state: RunState): WorkflowNode | undefined {
  return (
    state.workflow.nodes.find((node) => node.status === "running") ??
    [...state.workflow.nodes].reverse().find((node) => node.status === "completed")
  );
}
