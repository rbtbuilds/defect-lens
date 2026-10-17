import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile, access } from "node:fs/promises";
import path from "node:path";
import type { ModelMetadata } from "../src/types.ts";

const root = path.resolve(import.meta.dirname, "../..");
const source = path.resolve(
  root,
  process.argv[2] ?? ".runtime/demo/latest.json",
);
const output = path.resolve(
  root,
  process.argv[3] ?? ".runtime/demo/walkthrough.mp4",
);
if (
  !output.startsWith(root + path.sep) ||
  !source.startsWith(root + path.sep)
) {
  throw new Error("Demo files must remain in this checkout");
}
try {
  await access(output);
  throw new Error(
    "Refusing to overwrite an existing demo; choose a new output path",
  );
} catch (error) {
  if (!(error instanceof Error && "code" in error && error.code === "ENOENT"))
    throw error;
}
const recording = JSON.parse(await readFile(source, "utf8")) as {
  model: ModelMetadata;
  input_mode: string;
  inference: string;
  correction: string;
  inputs: Array<{ image_path: string; image_sha256: string }>;
  timeline: Array<{ seconds: number; title: string; detail: string }>;
  video: string;
};
if (
  recording.model.method !== "difference" ||
  recording.input_mode !== "procedural"
) {
  throw new Error(
    "This walkthrough packages procedural difference inference only",
  );
}
const videoPath = path.resolve(recording.video);
if (!videoPath.startsWith(path.join(root, ".runtime") + path.sep)) {
  throw new Error("Source recording must be under this checkout's .runtime");
}
await mkdir(path.dirname(output), { recursive: true });
const converted = spawnSync(
  "ffmpeg",
  [
    "-hide_banner",
    "-n",
    "-i",
    videoPath,
    "-c:v",
    "libx264",
    "-preset",
    "slow",
    "-crf",
    "24",
    "-pix_fmt",
    "yuv420p",
    "-movflags",
    "+faststart",
    output,
  ],
  { encoding: "utf8" },
);
if (converted.status !== 0)
  throw new Error(converted.stderr || "FFmpeg failed");
const probe = spawnSync(
  "ffprobe",
  [
    "-v",
    "error",
    "-show_entries",
    "format=duration,size",
    "-show_entries",
    "stream=codec_name,width,height",
    "-of",
    "json",
    output,
  ],
  { encoding: "utf8" },
);
if (probe.status !== 0) throw new Error(probe.stderr || "FFprobe failed");
const hash = async (file: string) =>
  createHash("sha256")
    .update(await readFile(file))
    .digest("hex");
const { video: _localVideoPath, ...portable } = recording;
const provenance = {
  ...portable,
  video: path.basename(output),
  sha256: await hash(output),
  original_webm_sha256: await hash(videoPath),
  recorder_sha256: await hash(path.join(root, "web/demo/record.mts")),
  packager_sha256: await hash(path.join(root, "web/demo/package.mts")),
  ffprobe: JSON.parse(probe.stdout) as unknown,
  annotation_note:
    "Caption bar injected by the recorder; app interactions and inference are real. No audio. Timeline uses approximate recording wall time.",
};
await writeFile(
  output.replace(/\.mp4$/, "") + ".json",
  JSON.stringify(provenance, null, 2) + "\n",
);
console.log(
  JSON.stringify({
    output: path.relative(root, output),
    sha256: provenance.sha256,
  }),
);
