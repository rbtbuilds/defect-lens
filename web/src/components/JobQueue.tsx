import type { Job } from "../types";
import { StatusBadge } from "./StatusBadge";
export function JobQueue({
  jobs,
  selected,
  onSelect,
  onMore,
  hasMore,
}: {
  jobs: Job[];
  selected: string | null;
  onSelect: (job: Job) => void;
  onMore: () => void;
  hasMore: boolean;
}) {
  return (
    <aside className="queue panel" aria-labelledby="queue-title">
      <div className="section-heading">
        <h2 id="queue-title">Inspection queue</h2>
        <span className="muted">{jobs.length}</span>
      </div>
      {jobs.length === 0 ? (
        <p className="muted">
          Your inspections will appear here. Generate the sample using the
          README quickstart, then choose an image.
        </p>
      ) : (
        <ol className="job-list">
          {jobs.map((job) => (
            <li key={job.id}>
              <button
                type="button"
                aria-pressed={job.id === selected}
                onClick={() => onSelect(job)}
              >
                <span className="job-id">{job.id.slice(0, 8)}</span>
                <StatusBadge status={job.status} />
                <span className="job-time">
                  {new Date(job.created_at).toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}{" "}
                  /{" "}
                  {job.data_mode === "procedural"
                    ? "procedural"
                    : "owned capture"}
                </span>
              </button>
            </li>
          ))}
        </ol>
      )}
      {hasMore && (
        <button type="button" onClick={onMore}>
          Load earlier jobs
        </button>
      )}
    </aside>
  );
}
