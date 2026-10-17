"""Acquire only the frozen VisA candle development subset from the official tar."""

import argparse
from pathlib import Path

from defect_lens.photographs import acquire


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(".runtime/data/visa-candle"))
    parser.add_argument("--evidence", type=Path, default=Path("reports/visa-candle-dev-v1"))
    args = parser.parse_args()
    manifest = acquire(args.output, args.evidence, Path("docs/PHOTO-PROTOCOL.md"))
    print(
        f"Acquired {len(manifest.samples)} public photographs; final specimen gate remains blocked"
    )


if __name__ == "__main__":
    main()
