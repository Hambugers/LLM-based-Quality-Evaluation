import { applyStreamEvent, createInitialRunState } from "./workflow";

describe("workflow state mapping", () => {
  it("updates a node status from streaming events", () => {
    const initial = createInitialRunState();

    const running = applyStreamEvent(initial, {
      event: "node_update",
      data: {
        node_key: "preprocess",
        status: "running",
        summary: null,
      },
    });

    expect(running.workflow.nodes.find((node) => node.node_key === "preprocess")?.status).toBe("running");

    const completed = applyStreamEvent(running, {
      event: "node_update",
      data: {
        node_key: "preprocess",
        status: "completed",
        summary: "预处理完成",
      },
    });

    expect(completed.workflow.nodes.find((node) => node.node_key === "preprocess")?.status).toBe("completed");
    expect(completed.workflow.nodes.find((node) => node.node_key === "preprocess")?.summary).toBe("预处理完成");
  });
});
