import { useState } from "react";
import type { Inspection, ModelMetadata } from "../types";
import { StatusBadge } from "./StatusBadge";
const explanations: Record<string, string> = {
  blur: "Image detail is too soft. Retake with a steady camera and clear focus.",
  alignment:
    "Plate alignment could not be verified. Retake using the overhead placement guide.",
  framing: "The image is outside the supported square framing.",
  clipping:
    "Too much of the inspection area is very dark or bright. Adjust lighting.",
};
export function InspectionView({
  inspection,
  model,
}: {
  inspection: Inspection;
  model: ModelMetadata | null;
}) {
  const [opacity, setOpacity] = useState(60);
  const [aligned, setAligned] = useState(true);
  return (
    <section className="workbench panel" aria-labelledby="inspection-title">
      <div className="section-heading">
        <div>
          <span className="eyebrow">02 / Evidence</span>
          <h2 id="inspection-title">Inspection result</h2>
        </div>
        <StatusBadge status={inspection.original_decision} />
      </div>
      <div className="evidence-label">
        {inspection.data_mode === "procedural"
          ? "Procedural demonstration"
          : "Owned capture"}{" "}
        / revision {inspection.model_revision.slice(0, 12)}
      </div>
      {inspection.reasons.length > 0 && (
        <div className="notice">
          {inspection.reasons.map((reason) => (
            <p key={reason}>
              {reason}: {explanations[reason] ?? "Human review required."}
            </p>
          ))}
        </div>
      )}
      <figure>
        <div className="image-stage">
          <img
            src={
              (aligned ? inspection.aligned_image_url : null) ??
              inspection.normalized_image_url
            }
            alt={
              aligned
                ? "Aligned overhead assembly in 256 by 256 coordinates"
                : "Normalized uploaded assembly"
            }
            width="256"
            height="256"
          />
          {aligned && inspection.heatmap_url && (
            <img
              className="heatmap"
              src={inspection.heatmap_url}
              alt="Appearance difference overlay; corresponding regions listed below"
              style={{ opacity: opacity / 100 }}
              width="256"
              height="256"
            />
          )}
        </div>
        <figcaption>
          {aligned ? "Aligned" : "Normalized input"} frame / 256 x 256 pixels
        </figcaption>
      </figure>
      <label className="check">
        <input
          type="checkbox"
          checked={aligned}
          onChange={(event) => setAligned(event.currentTarget.checked)}
        />
        Show aligned frame
      </label>
      {inspection.heatmap_url && (
        <div className="overlay-controls">
          <label htmlFor="opacity">
            Heatmap opacity <output>{opacity}%</output>
          </label>
          <input
            id="opacity"
            type="range"
            min="0"
            max="100"
            value={opacity}
            onChange={(event) => setOpacity(Number(event.currentTarget.value))}
          />
          <div
            className="legend"
            role="img"
            aria-label={`Heatmap scale: zero to ${model?.heatmap_display_max ?? "unavailable"}`}
          />
          <div className="legend-label">
            <span>0 / less difference</span>
            <span>
              {model?.model_revision === inspection.model_revision
                ? model.heatmap_display_max?.toFixed(4)
                : "Scale unavailable"}{" "}
              / more
            </span>
          </div>
        </div>
      )}
      <div className="score-line">
        <span>Appearance score</span>
        <strong>
          {inspection.score === null
            ? "Unavailable for quality review"
            : inspection.score.toFixed(5)}
        </strong>
      </div>
      <details>
        <summary>Localized regions ({inspection.regions.length})</summary>
        {inspection.regions.length === 0 ? (
          <p>No localized region is asserted.</p>
        ) : (
          <ol>
            {inspection.regions.map((region, index) => (
              <li key={index}>
                x {region.x}, y {region.y}; {region.width} x {region.height}{" "}
                pixels; peak {region.peak_score.toFixed(4)}
              </li>
            ))}
          </ol>
        )}
      </details>
    </section>
  );
}
