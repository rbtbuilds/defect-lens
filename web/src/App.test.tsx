import { expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import App from "./App";
vi.mock("./api", async (original) => ({
  ...(await original<typeof import("./api")>()),
  api: {
    models: vi
      .fn()
      .mockResolvedValue({
        status: "ready",
        model_revision: "a".repeat(64),
        method: "difference",
        data_mode: "procedural",
        low: 0.1,
        high: 0.2,
        heatmap_display_max: 1,
      }),
    jobs: vi
      .fn()
      .mockResolvedValue({
        items: [
          {
            id: "job",
            status: "failed",
            model_revision: "a".repeat(64),
            data_mode: "procedural",
            created_at: "2026-10-15T10:00:00Z",
            error: { code: "TIMEOUT", message: "Processing deadline exceeded" },
          },
        ],
        next_cursor: null,
      }),
    job: vi
      .fn()
      .mockResolvedValue({
        id: "job",
        status: "failed",
        error: { code: "TIMEOUT", message: "Processing deadline exceeded" },
      }),
  },
}));
it("announces a processing failure once with a resubmit path", async () => {
  render(<App />);
  expect(
    await screen.findByText("TIMEOUT: Processing deadline exceeded"),
  ).toBeInTheDocument();
  expect(
    screen.getByRole("button", { name: "Choose image to resubmit" }),
  ).toBeInTheDocument();
  const status = screen.getByRole("status");
  const observer = vi.fn();
  const mutations = new MutationObserver(observer);
  mutations.observe(status, {
    childList: true,
    subtree: true,
    characterData: true,
  });
  await new Promise((resolve) => setTimeout(resolve, 20));
  expect(observer).not.toHaveBeenCalled();
  mutations.disconnect();
});
