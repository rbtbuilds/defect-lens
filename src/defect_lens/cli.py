import argparse
import subprocess
import sys
from pathlib import Path

import uvicorn

from defect_lens.api import create_app
from defect_lens.config import Settings
from defect_lens.fixtures import generate_fixtures
from defect_lens.models import prepare_model


def _main() -> None:
    parser = argparse.ArgumentParser(description="Local visual inspection")
    parser.add_argument(
        "command", choices=["serve", "fixtures", "prepare", "batch", "benchmark", "export-report"]
    )
    parser.add_argument("--model", type=Path)
    parser.add_argument("--difference-model", type=Path)
    parser.add_argument("--patch-model", type=Path)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--api", default="http://127.0.0.1:8111")
    parser.add_argument("--dataset", type=Path)
    parser.add_argument("--method", choices=["difference", "resnet18_patch"], default="difference")
    parser.add_argument("--output", type=Path, default=Path(".runtime/data/fixtures"))
    parser.add_argument("--seed", type=int, default=20261015)
    parser.add_argument("--host", choices=["127.0.0.1"], default="127.0.0.1")
    parser.add_argument("--port", type=int, choices=[8111], default=8111)
    args = parser.parse_args()
    if args.command == "fixtures":
        manifest = generate_fixtures(args.output, args.seed)
        print(f"Generated {len(manifest.samples)} original procedural samples")
        return
    if args.command == "prepare":
        if args.dataset is None:
            parser.error("prepare requires --dataset")
        print(prepare_model(args.dataset, args.method, args.output).model_dump_json(indent=2))
        return
    if args.command == "batch":
        from defect_lens.batch import run_batch

        if args.manifest is None:
            parser.error("batch requires --manifest")
        summary = run_batch(args.manifest, args.api, args.output)
        print(summary)
        raise SystemExit(summary.exit_code)
    if args.command == "benchmark":
        from defect_lens.evaluation import evaluate
        from defect_lens.manifests import load_manifest
        from defect_lens.models import read_model_manifest

        if args.dataset is None or args.difference_model is None:
            parser.error("benchmark requires --dataset and --difference-model")
        directories = [args.difference_model] + ([args.patch_model] if args.patch_model else [])
        report = evaluate(
            load_manifest(args.dataset),
            [read_model_manifest(path) for path in directories],
            args.output,
            dataset_root=args.dataset.parent,
            model_directories=directories,
        )
        print(f"Complete: {report.complete}; {len(report.methods)} actual methods")
        raise SystemExit(0 if report.complete else 4)
    if args.command == "export-report":
        from defect_lens.reporting import export_report

        if args.input is None:
            parser.error("export-report requires --input")
        export_report(args.input, args.output)
        return
    uvicorn.run(create_app(Settings(Path.cwd(), args.model)), host=args.host, port=args.port)


def main() -> None:
    from defect_lens.errors import DomainError
    from defect_lens.lease import LeaseBusy

    try:
        _main()
    except LeaseBusy as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(3) from error
    except DomainError as error:
        print(f"{error.code}: {error.message}", file=sys.stderr)
        raise SystemExit(3 if error.status == 503 else 2) from error
    except (OSError, ValueError) as error:
        print(f"Invalid input or local resource: {error}", file=sys.stderr)
        raise SystemExit(2) from error
    except subprocess.CalledProcessError as error:
        print("Processing failed; inspect the local command log", file=sys.stderr)
        raise SystemExit(4) from error
