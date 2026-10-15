import json
import shutil
from pathlib import Path

from defect_lens.evaluation import EvaluationReport


def export_report(input: Path, output: Path) -> None:
    report = EvaluationReport.model_validate_json((input / "report.json").read_bytes())
    if output.exists():
        raise ValueError("Curated report destination already exists; create a reviewed revision")
    output.mkdir(parents=True)
    for name in ["report.json", "split-manifest.json", "environment.json"]:
        shutil.copyfile(input / name, output / name)
    lines = [
        "# Held-out procedural inspection report"
        if report.claim_level == "fixture"
        else "# Owned capture inspection report",
        "",
        f"Complete: {report.complete}. Data mode: {report.data_mode}. No industrial claim.",
        "",
        "| Method | Precision | Recall | False reject | Missed defect | Review burden | Warm p95 ms |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for method in report.methods:
        m = method.metrics
        latency = (
            f"{method.warm_latency_p95_ms:.2f}"
            if method.warm_latency_p95_ms is not None
            else "unavailable"
        )
        lines.append(
            f"| {method.model.method} | {m.precision} | {m.recall} | {m.false_reject_rate} | {m.missed_defect_rate} | {m.review_burden} | {latency} |"
        )
        gallery = input / method.model.method / "failure-gallery"
        if gallery.exists():
            shutil.copytree(gallery, output / "failure-gallery" / method.model.method)
    lines.extend(
        [
            "",
            "Binary fail threshold and operational pass/review/fail metrics are separate. Ambiguous frames are excluded from binary denominators and retained in review burden. Intervals resample procedural specimen groups, not independently photographed physical assemblies. Pixel AP is the mean per-image value over known defect masks.",
            "",
            "Timing includes PNG decode, ECC alignment, actual scorer and PNG artifact storage, with three unmeasured warmups. API timings use actual ASGI requests and a supervised worker, including queue/storage and excluding TCP. Cold timing includes model loading and first inference; peak RSS samples the entire benchmark process tree every 10 ms.",
            "",
            "The failure gallery includes uncertain blur examples even if all labelled defects are detected. These original procedural images support a software demonstration; no owned photographs have been validated.",
            "",
            "See report.json for sample/model/lock/config hashes, thresholds, slice counts, specimen bootstrap, per-stage timing and all prediction rows.",
        ]
    )
    (output / "report.md").write_text("\n".join(lines) + "\n")
    (output / "environment.json").write_text(json.dumps(report.environment, indent=2) + "\n")
