import { buildEvaluationFormData, evaluateWithFallback, syncEvaluation } from "./api";

describe("buildEvaluationFormData", () => {
  it("serializes text fields and uploaded files using the shared API contract", () => {
    const file = new File(["image"], "oracle.png", { type: "image/png" });
    const formData = buildEvaluationFormData({
      user_question: "森和林的甲骨文长什么样",
      model_answer: "这里是回答",
      images: [file],
      text_model: "google/gemma-4-31b-it:free",
      vision_model: "",
    });

    expect(formData.get("user_question")).toBe("森和林的甲骨文长什么样");
    expect(formData.get("model_answer")).toBe("这里是回答");
    expect(formData.get("text_model")).toBe("google/gemma-4-31b-it:free");
    expect(formData.get("vision_model")).toBeNull();
    expect((formData.getAll("images")[0] as File).name).toBe("oracle.png");
  });
});

describe("evaluateWithFallback", () => {
  it("falls back to the sync endpoint when the stream transport fails", async () => {
    const streamTransport = vi.fn().mockRejectedValue(new Error("stream failed"));
    const syncTransport = vi.fn().mockResolvedValue({
      ok: true,
      run_id: "run_sync",
      workflow: { status: "completed", nodes: [] },
    });

    const result = await evaluateWithFallback(
      {
        user_question: "30万以内商务车推荐",
        model_answer: "推荐 GL8。",
        images: [],
        text_model: "",
        vision_model: "",
      },
      {
        stream: streamTransport,
        sync: syncTransport,
      },
      vi.fn(),
    );

    expect(streamTransport).toHaveBeenCalledTimes(1);
    expect(syncTransport).toHaveBeenCalledTimes(1);
    expect(result.mode).toBe("sync");
    expect(result.payload.run_id).toBe("run_sync");
  });
});

describe("syncEvaluation", () => {
  it("uses same-origin API paths by default for packaged deployments", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ ok: true, run_id: "run_packaged" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );

    await syncEvaluation({
      user_question: "30万以内商务车推荐",
      model_answer: "推荐 GL8。",
      images: [],
      text_model: "",
      vision_model: "",
    });

    expect(globalThis.fetch).toHaveBeenCalledWith("/api/evaluate", expect.any(Object));
  });
});
