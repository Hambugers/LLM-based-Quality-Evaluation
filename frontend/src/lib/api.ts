import type { EvaluationFormValues, EvaluationResponse, StreamEvent } from "../types/evaluation";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8001";

export type StreamTransport = (
  values: EvaluationFormValues,
  onEvent: (event: StreamEvent) => void,
) => Promise<EvaluationResponse>;

export type SyncTransport = (values: EvaluationFormValues) => Promise<EvaluationResponse>;

export interface EvaluationTransports {
  stream: StreamTransport;
  sync: SyncTransport;
}

export function buildEvaluationFormData(values: EvaluationFormValues): FormData {
  const formData = new FormData();
  formData.set("user_question", values.user_question);
  formData.set("model_answer", values.model_answer);
  if (values.text_model.trim()) {
    formData.set("text_model", values.text_model.trim());
  }
  if (values.vision_model.trim()) {
    formData.set("vision_model", values.vision_model.trim());
  }
  values.images.forEach((file) => formData.append("images", file));
  return formData;
}

export async function streamEvaluation(
  values: EvaluationFormValues,
  onEvent: (event: StreamEvent) => void,
): Promise<EvaluationResponse> {
  const response = await fetch(`${API_BASE}/api/evaluate/stream`, {
    method: "POST",
    body: buildEvaluationFormData(values),
  });
  if (!response.ok || !response.body) {
    throw new Error(await responseTextOrStatus(response));
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";
  let completed: EvaluationResponse | null = null;

  while (true) {
    const { value, done } = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() ?? "";
    for (const chunk of chunks) {
      const parsed = parseSseChunk(chunk);
      if (!parsed) {
        continue;
      }
      onEvent(parsed);
      if (parsed.event === "run_completed") {
        completed = parsed.data as unknown as EvaluationResponse;
      }
      if (parsed.event === "run_failed") {
        throw new Error(String(parsed.data.error ?? "评估执行失败"));
      }
    }
  }

  if (!completed) {
    throw new Error("未收到完整评估结果");
  }
  return completed;
}

export async function syncEvaluation(values: EvaluationFormValues): Promise<EvaluationResponse> {
  const response = await fetch(`${API_BASE}/api/evaluate`, {
    method: "POST",
    body: buildEvaluationFormData(values),
  });
  if (!response.ok) {
    throw new Error(await responseTextOrStatus(response));
  }
  return (await response.json()) as EvaluationResponse;
}

export async function evaluateWithFallback(
  values: EvaluationFormValues,
  transports: EvaluationTransports = {
    stream: streamEvaluation,
    sync: syncEvaluation,
  },
  onEvent: (event: StreamEvent) => void,
): Promise<{ mode: "stream" | "sync"; payload: EvaluationResponse; warning?: string }> {
  try {
    const payload = await transports.stream(values, onEvent);
    return { mode: "stream", payload };
  } catch (error) {
    const payload = await transports.sync(values);
    return {
      mode: "sync",
      payload,
      warning: error instanceof Error ? error.message : "流式评估不可用，已切换为完整结果返回。",
    };
  }
}

function parseSseChunk(chunk: string): StreamEvent | null {
  const eventLine = chunk.split("\n").find((line) => line.startsWith("event:"));
  const dataLine = chunk.split("\n").find((line) => line.startsWith("data:"));
  if (!eventLine || !dataLine) {
    return null;
  }
  return {
    event: eventLine.replace("event:", "").trim(),
    data: JSON.parse(dataLine.replace("data:", "").trim()) as Record<string, unknown>,
  };
}

async function responseTextOrStatus(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: string };
    if (payload.detail) {
      return payload.detail;
    }
  } catch {
    // Fall back to status text below.
  }
  return response.statusText || `HTTP ${response.status}`;
}
