import { useState } from "react";
import type { ModelMetadata } from "../types";
export function UploadPanel({
  model,
  busy,
  onSubmit,
}: {
  model: ModelMetadata | null;
  busy: boolean;
  onSubmit: (file: File) => Promise<void>;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState("");
  return (
    <section className="upload panel" aria-labelledby="upload-title">
      <div>
        <span className="eyebrow">01 / Input</span>
        <h2 id="upload-title">Inspect an assembly</h2>
        <p className="muted">
          Overhead plate, four fasteners. PNG or JPEG, up to 8 MiB.
        </p>
      </div>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          if (file) {
            setError("");
            void onSubmit(file).catch((e: unknown) =>
              setError(e instanceof Error ? e.message : "Upload failed"),
            );
          }
        }}
      >
        <label htmlFor="inspection-image">Inspection image</label>
        <input
          id="inspection-image"
          type="file"
          accept="image/png,image/jpeg"
          onChange={(event) => {
            const selected = event.currentTarget.files?.[0] ?? null;
            setFile(selected);
            setError(
              selected && selected.size > 8 * 1024 * 1024
                ? "Image exceeds 8 MiB. Choose a smaller file."
                : "",
            );
          }}
        />
        <button
          className="primary"
          disabled={
            busy || !file || Boolean(error) || model?.status !== "ready"
          }
        >
          {busy ? "Submitting image" : "Inspect image"}
        </button>
        {error && <p role="alert">{error}</p>}
      </form>
      {model?.status !== "ready" && (
        <p className="notice">
          Model {model?.status ?? "loading"}. Prepare a model and start the
          local API to inspect images.
        </p>
      )}
    </section>
  );
}
