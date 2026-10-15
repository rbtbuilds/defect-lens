import { useEffect, useState } from "react";
import { api, ApiError, errorText } from "../api";
import type { Inspection, Review, ReviewCreate } from "../types";
import { StatusBadge } from "./StatusBadge";
export function ReviewForm({
  inspection,
  onSaved,
}: {
  inspection: Inspection;
  onSaved: () => void;
}) {
  const [note, setNote] = useState("");
  const [alias, setAlias] = useState("");
  const [decision, setDecision] = useState<ReviewCreate["decision"]>(
    inspection.latest_review?.decision ?? inspection.original_decision,
  );
  const [version, setVersion] = useState(
    inspection.latest_review?.version ?? 0,
  );
  const [error, setError] = useState("");
  const [conflict, setConflict] = useState(false);
  const [saving, setSaving] = useState(false);
  const [history, setHistory] = useState<Review[]>([]);
  const [attempt, setAttempt] = useState<{
    key: string;
    payload: string;
  } | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    void api
      .reviews(inspection.id, controller.signal)
      .then((data) => setHistory(data.items))
      .catch((e: unknown) => {
        if (!controller.signal.aborted) setError(errorText(e));
      });
    return () => controller.abort();
  }, [inspection.id, inspection.latest_review?.version]);
  return (
    <section className="review panel" aria-labelledby="review-title">
      <span className="eyebrow">03 / Human review</span>
      <h2 id="review-title">Record a correction</h2>
      <p className="muted">
        Feedback is stored separately. It does not retrain the model.
      </p>
      <p>
        Original: <StatusBadge status={inspection.original_decision} />
      </p>
      {inspection.latest_review && (
        <p>
          Latest correction:{" "}
          <StatusBadge status={inspection.latest_review.decision} /> / v
          {inspection.latest_review.version}
        </p>
      )}
      <form
        onSubmit={(event) => {
          event.preventDefault();
          setSaving(true);
          setError("");
          const input: ReviewCreate = {
            decision,
            note,
            operator_alias: alias,
            expected_version: version,
          };
          const payload = JSON.stringify(input);
          const key =
            attempt?.payload === payload ? attempt.key : crypto.randomUUID();
          setAttempt({ key, payload });
          void api
            .review(inspection.id, input, key)
            .then((saved) => {
              setVersion(saved.version);
              setNote("");
              setAttempt(null);
              setConflict(false);
              onSaved();
            })
            .catch((e: unknown) => {
              setError(errorText(e));
              setConflict(
                e instanceof ApiError && e.code === "REVIEW_CONFLICT",
              );
            })
            .finally(() => setSaving(false));
        }}
      >
        <label htmlFor="review-decision">Corrected decision</label>
        <select
          id="review-decision"
          value={decision}
          onChange={(event) =>
            setDecision(event.currentTarget.value as ReviewCreate["decision"])
          }
        >
          <option value="pass">Pass</option>
          <option value="review">Review</option>
          <option value="fail">Fail</option>
        </select>
        <label htmlFor="operator-alias">Operator alias</label>
        <input
          id="operator-alias"
          autoComplete="nickname"
          value={alias}
          maxLength={80}
          required
          onChange={(event) => setAlias(event.currentTarget.value)}
        />
        <small>Unverified local label</small>
        <label htmlFor="review-note">Review note</label>
        <textarea
          id="review-note"
          rows={4}
          value={note}
          maxLength={1000}
          onChange={(event) => setNote(event.currentTarget.value)}
        />
        <small>{note.length}/1000 characters</small>
        {error && <p role="alert">{error}</p>}
        {conflict && (
          <button
            type="button"
            onClick={() => {
              void api
                .inspection(inspection.id)
                .then((latest) => {
                  setVersion(latest.latest_review?.version ?? 0);
                  setConflict(false);
                  setAttempt(null);
                  setError(
                    "Latest version refreshed. Your note is retained; submit again to save.",
                  );
                  onSaved();
                })
                .catch((e: unknown) => setError(errorText(e)));
            }}
          >
            Refresh latest review
          </button>
        )}
        <button className="primary" disabled={saving || conflict}>
          {saving ? "Saving correction" : "Save correction"}
        </button>
      </form>
      <details>
        <summary>Correction history ({history.length})</summary>
        {history.length === 0 ? (
          <p>No corrections recorded.</p>
        ) : (
          <ol className="history">
            {history.map((review) => (
              <li key={review.id}>
                <strong>
                  v{review.version} / {review.decision}
                </strong>
                <p>{review.note || "No note"}</p>
                <small>
                  {review.operator_alias} /{" "}
                  {new Date(review.created_at).toLocaleString()}
                </small>
              </li>
            ))}
          </ol>
        )}
      </details>
    </section>
  );
}
