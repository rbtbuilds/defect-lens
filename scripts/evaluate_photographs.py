"""Run development diagnostics in a model child protected by the shared lease."""

import argparse
import sys
from pathlib import Path

from defect_lens.lease import DEFAULT_LEASE, MachineLease, run_model_process, token_matches
from defect_lens.photo_evaluation import compare


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path(".runtime/data/visa-candle"))
    parser.add_argument("--output", type=Path, default=Path(".runtime/visa-candle-dev-v1"))
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--lease-token")
    parser.add_argument("--final", action="store_true")
    args = parser.parse_args()
    if args.final:
        parser.error("Final evaluation blocked: no verified physical specimen/session grouping")
    if args.lease_token:
        if not token_matches(DEFAULT_LEASE, args.lease_token):
            parser.error("Missing matching machine lease")
        compare(args.dataset, args.output, args.weights, Path("docs/PHOTO-PROTOCOL.md"))
    else:
        with MachineLease().acquire("VisA candle full development comparison") as lease:
            run_model_process(
                [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    *sys.argv[1:],
                    "--lease-token",
                    lease.token,
                ]
            )


if __name__ == "__main__":
    main()
