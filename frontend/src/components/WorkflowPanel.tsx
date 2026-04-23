import { useMemo, useState } from "react";
import { Background, Controls, MarkerType, Position, ReactFlow, type Edge, type Node } from "@xyflow/react";
import { Activity, Clock, Crosshair } from "lucide-react";

import type { RunState, WorkflowNode } from "../types/evaluation";
import { activeNode } from "../lib/workflow";

interface WorkflowPanelProps {
  runState: RunState;
}

const statusClass: Record<string, string> = {
  waiting: "border-slate-700 bg-slate-900 text-slate-400",
  running: "border-cyan-300 bg-cyan-300/12 text-cyan-100",
  completed: "border-emerald-300/60 bg-emerald-300/10 text-emerald-100",
  failed: "border-red-300/60 bg-red-300/10 text-red-100",
};

export function WorkflowPanel({ runState }: WorkflowPanelProps) {
  const [selectedKey, setSelectedKey] = useState("input");
  const selectedNode = runState.workflow.nodes.find((node) => node.node_key === selectedKey) ?? runState.workflow.nodes[0];
  const currentNode = activeNode(runState);

  const flowNodes = useMemo<Node[]>(
    () =>
      runState.workflow.nodes.map((node, index) => ({
        id: node.node_key,
        data: { label: `${node.node_name}\n${statusText(node.status)}` },
        position: { x: (index % 2) * 260, y: Math.floor(index / 2) * 108 },
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
        className: node.status === "running" ? "!border-cyan-300 !bg-cyan-300/15" : undefined,
      })),
    [runState.workflow.nodes],
  );

  const flowEdges = useMemo<Edge[]>(
    () =>
      runState.workflow.nodes.slice(0, -1).map((node, index) => ({
        id: `${node.node_key}-${runState.workflow.nodes[index + 1].node_key}`,
        source: node.node_key,
        target: runState.workflow.nodes[index + 1].node_key,
        animated: runState.workflow.nodes[index + 1].status === "running",
        markerEnd: { type: MarkerType.ArrowClosed },
        style: { stroke: "#47716f" },
      })),
    [runState.workflow.nodes],
  );

  return (
    <section className="min-h-0 rounded-lg border border-slate-700/70 bg-slate-950/72 shadow-2xl shadow-black/30">
      <div className="border-b border-slate-800 px-5 py-4">
        <p className="text-xs uppercase tracking-[0.24em] text-cyan-300/70">Workflow</p>
        <div className="mt-1 flex items-center justify-between gap-3">
          <h2 className="text-xl font-semibold text-slate-50">执行流程</h2>
          <span className="rounded-md border border-slate-700 px-2 py-1 text-xs text-slate-300">
            {runState.workflow.status}
          </span>
        </div>
      </div>

      <div className="grid min-h-[680px] grid-rows-[360px_1fr] gap-4 p-5">
        <div className="overflow-hidden rounded-lg border border-slate-800 bg-slate-950/80">
          <ReactFlow
            nodes={flowNodes}
            edges={flowEdges}
            fitView
            minZoom={0.55}
            onNodeClick={(_, node) => setSelectedKey(node.id)}
          >
            <Background gap={22} color="#1d3536" />
            <Controls showInteractive={false} />
          </ReactFlow>
        </div>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_260px]">
          <div className="space-y-2">
            {runState.workflow.nodes.map((node) => (
              <button
                key={node.node_key}
                type="button"
                onClick={() => setSelectedKey(node.node_key)}
                className={`w-full rounded-md border px-3 py-3 text-left transition ${statusClass[node.status] ?? statusClass.waiting}`}
              >
                <div className="flex items-center justify-between gap-3">
                  <span className="font-medium">{node.node_name}</span>
                  <span className="text-xs">{statusText(node.status)}</span>
                </div>
                <p className="mt-1 line-clamp-2 text-xs opacity-75">{node.summary ?? "等待执行"}</p>
              </button>
            ))}
          </div>

          <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-4">
            <div className="flex items-center gap-2 text-sm text-cyan-100">
              <Crosshair className="h-4 w-4" />
              节点状态
            </div>
            <h3 className="mt-3 text-lg font-semibold text-slate-50">{selectedNode?.node_name}</h3>
            <p className="mt-2 text-sm leading-6 text-slate-400">{selectedNode?.summary ?? "暂无节点输出。"}</p>
            {selectedNode?.error ? <p className="mt-3 text-sm text-red-200">{selectedNode.error}</p> : null}
            <div className="mt-4 space-y-2 text-xs text-slate-500">
              <p className="flex items-center gap-2">
                <Activity className="h-3.5 w-3.5" />
                当前执行：{currentNode?.node_name ?? "待启动"}
              </p>
              <p className="flex items-center gap-2">
                <Clock className="h-3.5 w-3.5" />
                耗时：{selectedNode?.duration_ms ? `${selectedNode.duration_ms} ms` : "未记录"}
              </p>
            </div>
            <pre className="mt-4 max-h-44 overflow-auto rounded-md bg-slate-950/80 p-3 text-xs leading-5 text-slate-300">
              {JSON.stringify(selectedNode?.output ?? {}, null, 2)}
            </pre>
          </div>
        </div>
      </div>
    </section>
  );
}

function statusText(status: WorkflowNode["status"]) {
  if (status === "running") return "运行中";
  if (status === "completed") return "已完成";
  if (status === "failed") return "失败";
  return "等待中";
}
