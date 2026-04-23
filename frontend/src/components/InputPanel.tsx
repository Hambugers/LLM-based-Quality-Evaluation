import { FileImage, Play, RotateCcw, Sparkles, Upload } from "lucide-react";

import type { EvaluationFormValues } from "../types/evaluation";
import type { SampleCase } from "../lib/samples";

interface InputPanelProps {
  values: EvaluationFormValues;
  disabled: boolean;
  error: string | null;
  previews: string[];
  sampleCases: SampleCase[];
  onChange: (values: EvaluationFormValues) => void;
  onSubmit: () => void;
  onClear: () => void;
  onLoadSample: (sample: SampleCase) => void;
}

export function InputPanel({
  values,
  disabled,
  error,
  previews,
  sampleCases,
  onChange,
  onSubmit,
  onClear,
  onLoadSample,
}: InputPanelProps) {
  const update = <K extends keyof EvaluationFormValues>(key: K, value: EvaluationFormValues[K]) => {
    onChange({ ...values, [key]: value });
  };

  return (
    <section className="min-h-0 rounded-lg border border-slate-700/70 bg-slate-950/72 shadow-2xl shadow-black/30">
      <div className="border-b border-slate-800 px-5 py-4">
        <p className="text-xs uppercase tracking-[0.24em] text-cyan-300/70">Input</p>
        <h2 className="mt-1 text-xl font-semibold text-slate-50">评估输入</h2>
      </div>

      <div className="space-y-4 p-5">
        <div className="grid grid-cols-2 gap-2">
          {sampleCases.map((sample) => (
            <button
              key={sample.id}
              type="button"
              disabled={disabled}
              onClick={() => onLoadSample(sample)}
              className="flex items-center justify-center gap-2 rounded-md border border-cyan-400/25 bg-cyan-300/8 px-3 py-2 text-sm text-cyan-100 transition hover:border-cyan-300/70 hover:bg-cyan-300/14 disabled:cursor-not-allowed disabled:opacity-45"
            >
              <Sparkles className="h-4 w-4" />
              {sample.id === "case-1" ? "使用商务车推荐样例" : "使用甲骨文字形样例"}
            </button>
          ))}
        </div>

        <label className="block">
          <span className="text-sm text-slate-300">用户问题</span>
          <input
            value={values.user_question}
            disabled={disabled}
            onChange={(event) => update("user_question", event.target.value)}
            className="mt-2 w-full rounded-md border border-slate-700 bg-slate-900/80 px-3 py-2 text-slate-100 outline-none transition focus:border-cyan-300"
            placeholder="输入待评估的用户问题"
          />
        </label>

        <label className="block">
          <span className="text-sm text-slate-300">模型文本回复</span>
          <textarea
            value={values.model_answer}
            disabled={disabled}
            onChange={(event) => update("model_answer", event.target.value)}
            className="mt-2 h-52 w-full resize-none rounded-md border border-slate-700 bg-slate-900/80 px-3 py-3 text-sm leading-6 text-slate-100 outline-none transition focus:border-cyan-300"
            placeholder="输入需要评估的模型回复"
          />
        </label>

        <div>
          <label className="flex cursor-pointer items-center justify-center gap-2 rounded-md border border-dashed border-slate-600 bg-slate-900/55 px-3 py-4 text-sm text-slate-200 transition hover:border-cyan-300/70 hover:bg-cyan-300/8">
            <Upload className="h-4 w-4 text-cyan-300" />
            上传评估图片
            <input
              type="file"
              accept="image/png,image/jpeg,image/webp"
              multiple
              disabled={disabled}
              onChange={(event) => update("images", Array.from(event.currentTarget.files ?? []))}
              className="hidden"
            />
          </label>
          <p className="mt-2 text-xs text-slate-500">最多 8 张，单张不超过 10MB。</p>
        </div>

        {previews.length > 0 ? (
          <div className="grid grid-cols-3 gap-2">
            {previews.map((preview, index) => (
              <div
                key={`${values.images[index]?.name ?? "image"}-${index}`}
                className="aspect-[4/3] overflow-hidden rounded-md border border-slate-700 bg-slate-900"
              >
                <img src={preview} alt={`上传图片 ${index + 1}`} className="h-full w-full object-cover" />
              </div>
            ))}
          </div>
        ) : (
          <div className="flex items-center gap-2 rounded-md border border-slate-800 bg-slate-900/45 px-3 py-3 text-sm text-slate-500">
            <FileImage className="h-4 w-4" />
            图片预览将在上传后显示
          </div>
        )}

        <div className="grid grid-cols-1 gap-3">
          <label className="block">
            <span className="text-sm text-slate-300">文本裁判模型</span>
            <input
              value={values.text_model}
              disabled={disabled}
              onChange={(event) => update("text_model", event.target.value)}
              className="mt-2 w-full rounded-md border border-slate-700 bg-slate-900/80 px-3 py-2 text-sm text-slate-100 outline-none focus:border-cyan-300"
              placeholder="google/gemma-4-31b-it:free"
            />
          </label>
          <label className="block">
            <span className="text-sm text-slate-300">视觉裁判模型</span>
            <input
              value={values.vision_model}
              disabled={disabled}
              onChange={(event) => update("vision_model", event.target.value)}
              className="mt-2 w-full rounded-md border border-slate-700 bg-slate-900/80 px-3 py-2 text-sm text-slate-100 outline-none focus:border-cyan-300"
              placeholder="未填写时沿用文本裁判模型"
            />
          </label>
        </div>

        {error ? (
          <div className="rounded-md border border-red-400/40 bg-red-500/10 px-3 py-2 text-sm text-red-100">
            {error}
          </div>
        ) : null}

        <div className="grid grid-cols-[1fr_auto] gap-2">
          <button
            type="button"
            disabled={disabled}
            onClick={onSubmit}
            className="flex items-center justify-center gap-2 rounded-md bg-cyan-300 px-4 py-3 font-semibold text-slate-950 transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-45"
          >
            <Play className="h-4 w-4" />
            发起评估
          </button>
          <button
            type="button"
            disabled={disabled}
            onClick={onClear}
            className="flex h-full items-center justify-center rounded-md border border-slate-700 px-4 text-slate-200 transition hover:border-amber-300/70 hover:text-amber-100 disabled:cursor-not-allowed disabled:opacity-45"
            aria-label="清空输入"
          >
            <RotateCcw className="h-4 w-4" />
          </button>
        </div>
      </div>
    </section>
  );
}
