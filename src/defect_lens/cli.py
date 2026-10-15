import argparse
from pathlib import Path

import uvicorn

from defect_lens.api import create_app
from defect_lens.config import Settings
from defect_lens.fixtures import generate_fixtures
from defect_lens.models import prepare_model


def main() -> None:
    parser = argparse.ArgumentParser(description="Local visual inspection")
    parser.add_argument("command", choices=["serve", "fixtures", "prepare"])
    parser.add_argument("--model", type=Path)
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
    uvicorn.run(create_app(Settings(Path.cwd(), args.model)), host=args.host, port=args.port)
