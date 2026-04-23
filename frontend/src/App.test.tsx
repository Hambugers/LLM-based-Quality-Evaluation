import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import App from "./App";

describe("App", () => {
  it("renders the evaluation workspace regions", () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: "图文回复评估平台" })).toBeInTheDocument();
    expect(screen.getByText("评估输入")).toBeInTheDocument();
    expect(screen.getByText("执行流程")).toBeInTheDocument();
    expect(screen.getByText("评估结果")).toBeInTheDocument();
  });

  it("loads preset sample text and image files through the shared upload contract", async () => {
    const user = userEvent.setup();
    vi.spyOn(globalThis, "fetch").mockImplementation(() =>
      Promise.resolve(new Response(new Blob(["image"], { type: "image/png" }), { status: 200 })),
    );

    render(<App />);
    await user.click(screen.getByRole("button", { name: "使用商务车推荐样例" }));

    await waitFor(() => {
      expect(screen.getByDisplayValue("30万以内商务车推荐")).toBeInTheDocument();
    });
    expect(globalThis.fetch).toHaveBeenCalledWith("/sample-assets/1-1.PNG");
  });
});
