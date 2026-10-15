import argparse
from pathlib import Path

import uvicorn

from defect_lens.api import create_app
from defect_lens.config import Settings


def main() -> None:
    parser = argparse.ArgumentParser(description="Local visual inspection")
    parser.add_argument("command", choices=["serve"])
    parser.add_argument("--model", type=Path)
    parser.add_argument("--host", choices=["127.0.0.1"], default="127.0.0.1")
    parser.add_argument("--port", type=int, choices=[8111], default=8111)
    args = parser.parse_args()
    uvicorn.run(create_app(Settings(Path.cwd(), args.model)), host=args.host, port=args.port)
