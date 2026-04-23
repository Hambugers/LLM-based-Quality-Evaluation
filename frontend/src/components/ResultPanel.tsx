import { AlertTriangle, BadgeCheck, Braces, ShieldCheck } from "lucide-react";
import type { ReactNode } from "react";

import type { RunState } from "../types/evaluation";
import { LogPanel } from "./LogPanel";

interface ResultPanelProps {
  runState: RunState;
}

export function ResultPanel({ runState }: ResultPanelProps) {
  const finalLabel = String(runState.final_eval?.final_label ?? "待评估");
  const finalScore = numberText(runState.final_eval?.final_score);

  return (
    <section className="min-h-0 rounded-lg border border-slate-700/70 bg-slate-950/72 shadow-2xl shadow-black/30">
      <div className="border-b border-slate-800 px-5 py-4">
        <p className="text-xs uppercase tracking-[0.24em] text-cyan-300/70">Result</p>
        <h2 className="mt-1 text-xl font-semibold text-slate-50">评估结果</h2>
      </div>

      <div className="space-y-4 p-5">
        <div className="rounded-lg border border-cyan-300/30 bg-cyan-300/10 p-4">
          <div className="flex items-center gap-2 text-sm text-cyan-100">
            <ShieldCheck className="h-4 w-4" />
            最终结论
          </div>
          <div className="mt-3 flex items-end justify-between gap-3">
            <span className="text-4xl font-black tracking-tight text-slate-50">{finalLabel}</span>
            <span className="text-lg text-cyan-100">{finalScore}</span>
          </div>
          <p className="mt-3 text-sm leading-6 text-slate-300">
            {String(runState.final_eval?.summary ?? runState.final_eval?.final_reason ?? "评估完成后展示综合结论。")}
          </p>
        </div>

        <ResultSection title="预处理结果" icon={<BadgeCheck className="h-4 w-4" />} data={runState.preprocess} />
        <ResultSection title="文本评估结果" icon={<Braces className="h-4 w-4" />} data={runState.text_eval} />
        <ResultSection title="图片基础质检" icon={<BadgeCheck className="h-4 w-4" />} data={runState.image_eval} />
        <ResultSection title="图文一致性评估" icon={<AlertTriangle className="h-4 w-4" />} data={runState.cross_modal_eval} />
        <ResultSection title="结构化输出" icon={<Braces className="h-4 w-4" />} data={runState.final_eval} />

        <LogPanel logs={runState.logs} />
      </div>
    </section>
  );
}

function ResultSection({
  title,
  icon,
  data,
}: {
  title: string;
  icon: ReactNode;
  data?: Record<string, unknown>;
}) {
  return (
    <details className="rounded-lg border border-slate-800 bg-slate-900/50 p-4" open={title === "预处理结果"}>
      <summary className="flex cursor-pointer list-none items-center gap-2 text-sm font-medium text-slate-100">
        <span className="text-cyan-200">{icon}</span>
        {title}
      </summary>
      <pre className="mt-3 max-h-56 overflow-auto rounded-md bg-slate-950/80 p-3 text-xs leading-5 text-slate-300">
        {JSON.stringify(data ?? {}, null, 2)}
      </pre>
    </details>
  );
}

function numberText(value: unknown) {
  if (typeof value === "number") {
    return value.toFixed(2);
  }
  return "--";
}
