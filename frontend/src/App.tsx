import { useEffect, useMemo, useState } from "react";

import { InputPanel } from "./components/InputPanel";
import { ResultPanel } from "./components/ResultPanel";
import { WorkflowPanel } from "./components/WorkflowPanel";
import { evaluateWithFallback } from "./lib/api";
import { loadSampleImages, sampleCases, type SampleCase } from "./lib/samples";
import { formSchema, validateImageFiles } from "./lib/validation";
import { applyStreamEvent, createInitialRunState } from "./lib/workflow";
import type { EvaluationFormValues, RunState } from "./types/evaluation";

const defaultModel = "google/gemma-4-31b-it:free";

const emptyValues: EvaluationFormValues = {
  user_question: "",
  model_answer: "",
  images: [],
  text_model: defaultModel,
  vision_model: defaultModel,
};

export default function App() {
  const [values, setValues] = useState<EvaluationFormValues>(emptyValues);
  const [runState, setRunState] = useState<RunState>(() => createInitialRunState());
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previews, setPreviews] = useState<string[]>([]);

  useEffect(() => {
    const nextPreviews = values.images.map((file) => URL.createObjectURL(file));
    setPreviews(nextPreviews);
    return () => {
      nextPreviews.forEach((url) => URL.revokeObjectURL(url));
    };
  }, [values.images]);

  const runningLabel = useMemo(
    () => runState.workflow.nodes.find((node) => node.status === "running")?.node_name ?? "待启动",
    [runState.workflow.nodes],
  );

  async function submitEvaluation() {
    const parsed = formSchema.safeParse(values);
    if (!parsed.success) {
      setError(parsed.error.issues[0]?.message ?? "输入校验失败");
      return;
    }
    const imageError = validateImageFiles(values.images);
    if (imageError) {
      setError(imageError);
      return;
    }

    setError(null);
    setIsRunning(true);
    setRunState(createInitialRunState());
    try {
      const result = await evaluateWithFallback(
        values,
        undefined,
        (streamEvent) => setRunState((current) => applyStreamEvent(current, streamEvent)),
      );
      setRunState((current) => ({
        ...current,
        ...result.payload,
        logs: result.warning
          ? [
              ...(result.payload.logs ?? current.logs),
              { time: new Date().toISOString(), level: "warning", message: `流式通道切换：${result.warning}` },
            ]
          : result.payload.logs ?? current.logs,
      }));
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "评估请求失败");
      setRunState((current) => ({
        ...current,
        workflow: { ...current.workflow, status: "failed" },
        error: submitError instanceof Error ? submitError.message : "评估请求失败",
      }));
    } finally {
      setIsRunning(false);
    }
  }

  async function loadSample(sample: SampleCase) {
    setError(null);
    try {
      const images = await loadSampleImages(sample);
      setValues({
        user_question: sample.user_question,
        model_answer: sample.model_answer,
        images,
        text_model: defaultModel,
        vision_model: defaultModel,
      });
    } catch (sampleError) {
      setError(sampleError instanceof Error ? sampleError.message : "样例加载失败");
    }
  }

  function clearInput() {
    setValues(emptyValues);
    setRunState(createInitialRunState());
    setError(null);
  }

  return (
    <main className="min-h-screen px-4 py-4 text-slate-100 lg:px-6">
      <header className="mb-4 flex flex-col justify-between gap-3 rounded-lg border border-slate-800 bg-slate-950/72 px-5 py-4 shadow-2xl shadow-black/25 lg:flex-row lg:items-end">
        <div>
          <p className="text-xs uppercase tracking-[0.32em] text-cyan-300/70">Multimodal Evaluation</p>
          <h1 className="mt-1 text-3xl font-black tracking-tight text-slate-50">图文回复评估平台</h1>
        </div>
        <div className="grid grid-cols-2 gap-3 text-sm text-slate-300 sm:grid-cols-4">
          <Metric label="运行节点" value={runningLabel} />
          <Metric label="图片数量" value={`${values.images.length}`} />
          <Metric label="流程状态" value={runState.workflow.status} />
          <Metric label="最终标签" value={String(runState.final_eval?.final_label ?? "--")} />
        </div>
      </header>

      <div className="grid min-h-[calc(100vh-126px)] grid-cols-1 gap-4 xl:grid-cols-[390px_minmax(520px,1fr)_410px]">
        <InputPanel
          values={values}
          disabled={isRunning}
          error={error}
          previews={previews}
          sampleCases={sampleCases}
          onChange={setValues}
          onSubmit={submitEvaluation}
          onClear={clearInput}
          onLoadSample={loadSample}
        />
        <WorkflowPanel runState={runState} />
        <ResultPanel runState={runState} />
      </div>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 rounded-md border border-slate-800 bg-slate-900/55 px-3 py-2">
      <p className="text-[11px] text-slate-500">{label}</p>
      <p className="truncate text-sm font-semibold text-slate-100">{value}</p>
    </div>
  );
}
