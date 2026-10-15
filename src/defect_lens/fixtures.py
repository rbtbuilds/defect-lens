from pathlib import Path
from typing import Literal

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from defect_lens.contracts import DatasetManifest, SampleRecord
from defect_lens.manifests import ManifestError, file_hash, load_manifest

Kind = Literal["good", "missing", "mark", "blur"]


def render_frame(
    kind: Kind, seed: int = 0, dx: int = 0, brightness: int = 0
) -> tuple[Image.Image, Image.Image]:
    image = Image.new("RGB", (256, 256), (48 + brightness,) * 3)
    draw = ImageDraw.Draw(image)
    draw.rectangle((34, 34, 222, 222), fill=(168 + brightness,) * 3)
    mask = Image.new("L", (256, 256), 0)
    marked = ImageDraw.Draw(mask)
    rng = np.random.default_rng(seed)
    for index, (x, y) in enumerate([(68, 68), (188, 68), (68, 188), (188, 188)]):
        radius = 10
        box = (x - radius, y - radius, x + radius, y + radius)
        if kind == "missing" and index == 0:
            marked.ellipse(box, fill=255)
        else:
            draw.ellipse(box, fill=(36 + brightness,) * 3)
    if kind == "mark":
        draw.line((108, 107, 150, 145), fill=(48, 48, 48), width=5)
        marked.line((108, 107, 150, 145), fill=255, width=5)
    array = np.asarray(image, dtype=np.float32)
    noise = rng.normal(0, 0.7, array.shape).astype(np.float32)
    image = Image.fromarray(np.clip(array + noise, 0, 255).astype(np.uint8))
    if dx:
        image = image.transform(
            image.size, Image.Transform.AFFINE, (1, 0, -dx, 0, 1, 0), fillcolor=(48, 48, 48)
        )
        mask = mask.transform(mask.size, Image.Transform.AFFINE, (1, 0, -dx, 0, 1, 0))
    if kind == "blur":
        image = image.filter(ImageFilter.GaussianBlur(4))
    return image, mask


def generate_fixtures(output: Path, seed: int, specimens_per_split: int = 6) -> DatasetManifest:
    if not 1 <= specimens_per_split <= 100:
        raise ValueError("specimen count must be 1..100")
    destination = output / "manifest.json"
    if destination.exists():
        previous = load_manifest(destination)
        if (
            previous.seed == seed
            and len({s.specimen_id for s in previous.samples}) == specimens_per_split * 3
        ):
            return previous
        raise ManifestError("existing recipe differs; choose a new output directory")
    output.mkdir(parents=True, exist_ok=True)
    samples: list[SampleRecord] = []
    splits: list[Literal["train", "validation", "test"]] = ["train", "validation", "test"]
    for split_index, split in enumerate(splits):
        for specimen in range(specimens_per_split):
            for session in range(3):
                kinds: list[Kind] = (
                    ["good", "good"]
                    if split == "train"
                    else ["good", "good", "missing", "mark", "blur"]
                )
                for view, kind in enumerate(kinds):
                    identifier = f"{split}-{specimen:02}-{session}-{view}"
                    frame_seed = seed + split_index * 10000 + specimen * 100 + session * 10 + view
                    image, mask = render_frame(
                        kind, frame_seed, dx=session - 1, brightness=(session - 1) * 6
                    )
                    path = output / f"{identifier}.png"
                    image.save(path)
                    mask_path = None
                    mask_sha = None
                    if kind in {"missing", "mark"}:
                        mask_path = f"{identifier}-mask.png"
                        mask.save(output / mask_path)
                        mask_sha = file_hash(output / mask_path)
                    label: Literal["good", "defect", "ambiguous"] = (
                        "good" if kind == "good" else "ambiguous" if kind == "blur" else "defect"
                    )
                    defects: dict[
                        Kind, Literal["none", "missing_fastener", "surface_mark", "quality"]
                    ] = {
                        "good": "none",
                        "missing": "missing_fastener",
                        "mark": "surface_mark",
                        "blur": "quality",
                    }
                    defect = defects[kind]
                    lighting: list[Literal["dim", "normal", "bright"]] = ["dim", "normal", "bright"]
                    samples.append(
                        SampleRecord(
                            id=identifier,
                            image_path=path.name,
                            image_sha256=file_hash(path),
                            specimen_id=f"{split}-specimen-{specimen}",
                            session_id=f"{split}-session-{session}",
                            split=split,
                            label=label,
                            defect_kind=defect,
                            mask_path=mask_path,
                            mask_sha256=mask_sha,
                            lighting=lighting[session],
                            blur="strong" if kind == "blur" else "none",
                        )
                    )
    manifest = DatasetManifest(seed=seed, samples=samples)
    temporary = output / "manifest.json.tmp"
    temporary.write_text(manifest.model_dump_json(indent=2) + "\n")
    temporary.replace(destination)
    return manifest
