import { expect, it, vi } from "vitest";
import { render, screen, waitFor, act } from "@testing-library/react";
import App from "./App";
import userEvent from "@testing-library/user-event";
import { api } from "./api";
import type { Job, Inspection, Review } from "./types";
vi.mock("./api", async (original) => ({
  ...(await original<typeof import("./api")>()),
  api: {
    inspection: vi.fn(),
    reviews: vi.fn().mockResolvedValue({ items: [] }),
    review: vi.fn(),
    models: vi.fn().mockResolvedValue({
      status: "ready",
      model_revision: "a".repeat(64),
      method: "difference",
      data_mode: "procedural",
      low: 0.1,
      high: 0.2,
      heatmap_display_max: 1,
    }),
    jobs: vi.fn().mockResolvedValue({
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
    job: vi.fn().mockResolvedValue({
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
  await waitFor(() =>
    expect(status).toHaveTextContent("Inspection job: failed"),
  );
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

it("ignores an old correction refresh after selecting another inspection", async () => {
  location.hash = "";
  const revision = "a".repeat(64);
  const job = (id: string): Job => ({
    id,
    status: "succeeded",
    model_revision: revision,
    data_mode: "procedural",
    created_at: "2026-10-15T10:00:00Z",
    started_at: null,
    finished_at: null,
    inspection_id: `inspection-${id}`,
    error: null,
  });
  const inspection = (id: string): Inspection => ({
    id: `inspection-${id}`,
    job_id: id,
    model_revision: revision,
    data_mode: "procedural",
    original_decision: "pass",
    score: 0.01,
    reasons: [],
    normalized_image_url: `/${id}.png`,
    aligned_image_url: `/${id}.png`,
    heatmap_url: null,
    regions: [],
    latest_review: null,
  });
  const a = inspection("job-a"),
    b = inspection("job-b");
  const saved: Review = {
    id: "review",
    inspection_id: a.id,
    version: 1,
    decision: "pass",
    note: "review A",
    operator_alias: "tester",
    created_at: "2026-10-15T10:00:00Z",
    model_revision: revision,
  };
  let finish: ((value: Inspection) => void) | undefined;
  const late = new Promise<Inspection>((resolve) => {
    finish = resolve;
  });
  let aCalls = 0;
  vi.mocked(api.jobs).mockResolvedValue({
    items: [job("job-a"), job("job-b")],
    next_cursor: null,
  });
  vi.mocked(api.job).mockImplementation((id) => Promise.resolve(job(id)));
  vi.mocked(api.inspection).mockImplementation((id) =>
    id === a.id
      ? ++aCalls === 1
        ? Promise.resolve(a)
        : late
      : Promise.resolve(b),
  );
  vi.mocked(api.review).mockResolvedValue(saved);
  render(<App />);
  await waitFor(() =>
    expect(
      screen.getByAltText(
        "Aligned overhead assembly in 256 by 256 coordinates",
      ),
    ).toHaveAttribute("src", "/job-a.png"),
  );
  const user = userEvent.setup();
  await user.type(screen.getByLabelText("Operator alias"), "tester");
  await user.click(screen.getByRole("button", { name: "Save correction" }));
  await waitFor(() => expect(aCalls).toBe(2));
  await user.click(screen.getByRole("button", { name: /job-b/ }));
  await waitFor(() =>
    expect(
      screen.getByAltText(
        "Aligned overhead assembly in 256 by 256 coordinates",
      ),
    ).toHaveAttribute("src", "/job-b.png"),
  );
  await act(async () => {
    finish?.({ ...a, latest_review: saved });
    await late;
  });
  expect(
    screen.getByAltText("Aligned overhead assembly in 256 by 256 coordinates"),
  ).toHaveAttribute("src", "/job-b.png");
  expect(screen.getByTestId("result-job")).toHaveTextContent("job-b");
});
