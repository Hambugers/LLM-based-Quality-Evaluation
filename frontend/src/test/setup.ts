import "@testing-library/jest-dom/vitest";

class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}

Object.defineProperty(globalThis, "ResizeObserver", {
  writable: true,
  configurable: true,
  value: ResizeObserverStub,
});

Object.defineProperty(URL, "createObjectURL", {
  writable: true,
  configurable: true,
  value: () => "blob:test-preview",
});

Object.defineProperty(URL, "revokeObjectURL", {
  writable: true,
  configurable: true,
  value: () => undefined,
});
