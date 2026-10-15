import { useEffect, useState } from "react";
import { api, errorText } from "./api";
import { startPolling } from "./polling";
import type { Inspection, Job, ModelMetadata } from "./types";
import { UploadPanel } from "./components/UploadPanel";
import { JobQueue } from "./components/JobQueue";
import { InspectionView } from "./components/InspectionView";
import { ReviewForm } from "./components/ReviewForm";
import { ThemeToggle } from "./components/ThemeToggle";
import { StatusBadge } from "./components/StatusBadge";
import "./styles.css";
export default function App() {
  const [model, setModel] = useState<ModelMetadata | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selected, setSelected] = useState<Job | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(
    () => location.hash.slice(1) || null,
  );
  const [inspection, setInspection] = useState<Inspection | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [modelError, setModelError] = useState("");
  const [jobError, setJobError] = useState("");
  const displayedError = error || jobError || modelError;
  const [epoch, setEpoch] = useState(0);
  const [cursor, setCursor] = useState<string | null>(null);
  const [announcement, setAnnouncement] = useState("Loading local workbench");
  useEffect(
    () =>
      startPolling(
        async (signal) => {
          const [metadata, list] = await Promise.all([
            api.models(signal),
            api.jobs(signal),
          ]);
          if (signal.aborted) return false;
          setModel(metadata);
          setJobs((current) => {
            const retained = current.find(
              (job) => job.id === location.hash.slice(1),
            );
            return retained && !list.items.some((job) => job.id === retained.id)
              ? [retained, ...list.items]
              : list.items;
          });
          setCursor(list.next_cursor);
          setModelError("");
          setSelectedId((current) => current ?? list.items[0]?.id ?? null);
          return (
            metadata.status === "loading" ||
            list.items.some(
              (job) => job.status === "queued" || job.status === "running",
            )
          );
        },
        (e) => setModelError(errorText(e)),
      ),
    [epoch],
  );
  useEffect(() => {
    if (!selectedId) return;
    return startPolling(
      async (signal) => {
        const job = await api.job(selectedId, signal);
        if (signal.aborted) return false;
        setSelected(job);
        setAnnouncement(`Inspection ${job.id.slice(0, 8)}: ${job.status}`);
        setJobs((current) =>
          current.some((item) => item.id === job.id)
            ? current.map((item) => (item.id === job.id ? job : item))
            : [job, ...current],
        );
        if (job.inspection_id) {
          const result = await api.inspection(job.inspection_id, signal);
          if (!signal.aborted) setInspection(result);
        }
        setJobError("");
        return job.status === "queued" || job.status === "running";
      },
      (e) => setJobError(errorText(e)),
    );
  }, [selectedId, epoch]);
  function choose(job: Job) {
    if (selectedId === job.id) return;
    setInspection(null);
    setSelected(job);
    setSelectedId(job.id);
    setError("");
    setJobError("");
    location.hash = job.id;
  }
  async function submit(file: File) {
    if (!model?.model_revision || !model.data_mode) return;
    setBusy(true);
    setError("");
    try {
      const job = await api.submit(
        file,
        model.model_revision,
        model.data_mode,
        crypto.randomUUID(),
      );
      setJobs((current) => [
        job,
        ...current.filter((item) => item.id !== job.id),
      ]);
      choose(job);
      setEpoch((value) => value + 1);
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  }
  function reloadInspection() {
    if (inspection)
      void api
        .inspection(inspection.id)
        .then((fresh) =>
          setInspection((current) =>
            current?.id === fresh.id ? fresh : current,
          ),
        )
        .catch((e) => setError(errorText(e)));
  }
  return (
    <main>
      <a href="#inspection-image" className="skip-link">
        Skip to image input
      </a>
      <header>
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">
            DL
          </span>
          <div>
            <h1>Defect Lens</h1>
            <p>Tabletop visual inspection</p>
          </div>
        </div>
        <ThemeToggle />
      </header>
      <section className="model-strip" aria-label="Active model">
        <span className="badge">
          {model?.data_mode === "owned_capture"
            ? "Owned capture"
            : "Procedural demonstration"}
        </span>
        <span>
          Active method:{" "}
          <strong>
            {model?.method === "resnet18_patch"
              ? "ResNet18 patch"
              : "Aligned difference"}
          </strong>
        </span>
        <StatusBadge status={model?.status ?? "loading"} />
        {model?.model_revision && (
          <button
            type="button"
            className="revision"
            title={model.model_revision}
            onClick={() => {
              void navigator.clipboard
                .writeText(model.model_revision ?? "")
                .then(() => setAnnouncement("Full model revision copied"))
                .catch((e) => setError(errorText(e)));
            }}
          >
            Revision {model.model_revision.slice(0, 12)} / Copy
          </button>
        )}
      </section>
      <p className="sr-only" role="status" aria-live="polite">
        {announcement}
      </p>
      {displayedError && (
        <div className="notice error" role="alert">
          {displayedError}
          <button type="button" onClick={() => setEpoch((value) => value + 1)}>
            Retry connection
          </button>
        </div>
      )}
      <UploadPanel model={model} busy={busy} onSubmit={submit} />
      <div className="workspace">
        <JobQueue
          jobs={jobs}
          selected={selectedId ?? null}
          onSelect={choose}
          hasMore={Boolean(cursor)}
          onMore={() => {
            if (cursor)
              void api
                .jobs(undefined, cursor)
                .then((list) => {
                  setJobs((current) => [
                    ...current,
                    ...list.items.filter(
                      (item) => !current.some((job) => job.id === item.id),
                    ),
                  ]);
                  setCursor(list.next_cursor);
                })
                .catch((e) => setError(errorText(e)));
          }}
        />
        <div className="result-column">
          {selected && (
            <p className="job-progress" data-testid="result-job">
              Inspection {selected.id.slice(0, 8)} / {selected.status}
            </p>
          )}
          {selected?.status === "failed" && (
            <div className="notice error">
              <h2>Processing failed</h2>
              <p>
                {selected.error?.code}: {selected.error?.message}
              </p>
              <button
                type="button"
                onClick={() =>
                  document.getElementById("inspection-image")?.focus()
                }
              >
                Choose image to resubmit
              </button>
              <p>A new submission uses a new request key.</p>
            </div>
          )}
          {inspection ? (
            <InspectionView
              key={inspection.id}
              inspection={inspection}
              model={model}
            />
          ) : (
            <section className="panel empty">
              <span className="eyebrow">02 / Evidence</span>
              <h2>
                {selected?.status === "running"
                  ? "Inspecting the assembly"
                  : selected?.status === "queued"
                    ? "Waiting for the worker"
                    : "A clear view of every decision"}
              </h2>
              <div className="assembly-diagram" aria-hidden="true">
                <i />
                <i />
                <i />
                <i />
              </div>
              <p className="muted">
                {selected && ["running", "queued"].includes(selected.status)
                  ? "Processing status updates automatically."
                  : "Upload an image to compare its appearance with the frozen good reference. Results include uncertainty and a traceable model revision."}
              </p>
            </section>
          )}
        </div>
        {inspection ? (
          <ReviewForm
            key={inspection.id}
            inspection={inspection}
            onSaved={reloadInspection}
          />
        ) : (
          <aside className="panel review empty">
            <span className="eyebrow">03 / Human review</span>
            <h2>Keep the evidence</h2>
            <p className="muted">
              Completed inspections retain their original decision. Corrections
              add a versioned record.
            </p>
            <p className="muted">
              No owned-photo validation has been performed.
            </p>
          </aside>
        )}
      </div>
      <footer>
        <span>Bento Labs / local inspection workbench</span>
        <span>
          Controlled tabletop demonstration. Human review required outside this
          setup.
        </span>
      </footer>
    </main>
  );
}
