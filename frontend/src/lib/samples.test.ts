import { sampleCases } from "./samples";

describe("sampleCases", () => {
  it("exposes the two interview scenarios with stable asset paths", () => {
    expect(sampleCases).toHaveLength(2);
    expect(sampleCases[0].id).toBe("case-1");
    expect(sampleCases[0].images).toEqual([
      "/sample-assets/1-1.PNG",
      "/sample-assets/1-2.PNG",
      "/sample-assets/1-3.PNG",
    ]);
    expect(sampleCases[1].images).toHaveLength(6);
    expect(sampleCases[1].user_question).toContain("甲骨文");
  });
});
