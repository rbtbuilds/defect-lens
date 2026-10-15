import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ReviewForm } from "./ReviewForm";
import { UploadPanel } from "./UploadPanel";
import { InspectionView } from "./InspectionView";
import { api, ApiError } from "../api";
import type { Inspection, ModelMetadata } from "../types";
vi.mock("../api", async (original) => ({
  ...(await original<typeof import("../api")>()),
  api: {
    review: vi.fn(),
    reviews: vi.fn().mockResolvedValue({ items: [] }),
    inspection: vi.fn(),
  },
}));
const inspection: Inspection = {
  id: "id",
  job_id: "job",
  model_revision: "a".repeat(64),
  data_mode: "procedural",
  original_decision: "review",
  score: null,
  reasons: ["blur"],
  aligned_image_url: "/image",
  heatmap_url: null,
  normalized_image_url: "/image",
  regions: [],
  latest_review: null,
};
const model: ModelMetadata = {
  status: "unprepared",
  model_revision: null,
  data_mode: null,
  method: null,
  low: null,
  high: null,
  heatmap_display_max: null,
};
describe("operator workflow", () => {
  it("disables submit while model is unready", () => {
    render(<UploadPanel model={model} busy={false} onSubmit={vi.fn()} />);
    expect(
      screen.getByRole("button", { name: "Inspect image" }),
    ).toBeDisabled();
  });
  it("preserves correction note on conflict", async () => {
    vi.mocked(api.review).mockRejectedValue(
      new ApiError(
        "REVIEW_CONFLICT",
        "Refresh latest review",
        false,
        "request",
      ),
    );
    const user = userEvent.setup();
    render(<ReviewForm inspection={inspection} onSaved={vi.fn()} />);
    await user.type(screen.getByLabelText("Operator alias"), "Matthew");
    await user.type(
      screen.getByLabelText("Review note"),
      "Fastener is present",
    );
    await user.click(screen.getByRole("button", { name: "Save correction" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Refresh");
    expect(screen.getByLabelText("Review note")).toHaveValue(
      "Fastener is present",
    );
  });
  it("shows quality reason without a misleading heatmap", () => {
    render(<InspectionView inspection={inspection} model={model} />);
    expect(screen.getByText(/blur: /)).toBeInTheDocument();
    expect(screen.queryByLabelText("Heatmap opacity")).not.toBeInTheDocument();
  });
});
