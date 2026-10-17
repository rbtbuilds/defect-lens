import { chromium, expect } from "@playwright/test";
import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import type { ModelMetadata } from "../src/types.ts";

const root = path.resolve(import.meta.dirname, "../..");
const destination = path.join(root, ".runtime/demo", Date.now().toString());
await mkdir(destination, { recursive: true });
const manifest = JSON.parse(
  await readFile(
    path.join(root, ".runtime/data/fixtures/manifest.json"),
    "utf8",
  ),
) as {
  samples: Array<{
    image_path: string;
    image_sha256: string;
    split: string;
    defect_kind: string;
  }>;
};
const browser = await chromium.launch();
const context = await browser.newContext({
  viewport: { width: 1280, height: 1400 },
  colorScheme: "light",
  reducedMotion: "reduce",
  recordVideo: { dir: destination, size: { width: 1280, height: 1400 } },
});
const page = await context.newPage();
const timeline: Array<{ seconds: number; title: string; detail: string }> = [];
const inputs: Array<{ image_path: string; image_sha256: string }> = [];
const started = Date.now();
let model: ModelMetadata | undefined;
const video = page.video();
if (!video) throw new Error("Recording unavailable");

async function caption(title: string, detail: string, hold = 3000) {
  timeline.push({ seconds: (Date.now() - started) / 1000, title, detail });
  await page.evaluate(
    ({ title, detail }) => {
      let bar = document.getElementById("demo-caption");
      if (!bar) {
        bar = document.createElement("aside");
        bar.id = "demo-caption";
        bar.style.cssText =
          "position:fixed;bottom:0;left:0;right:0;z-index:9999;background:#122b35;color:#fff;padding:18px 30px;font:16px/1.5 system-ui;border-top:3px solid #55d4ba;pointer-events:none";
        document.body.style.paddingBottom = "130px";
        document.body.append(bar);
      }
      bar.replaceChildren();
      const label = document.createElement("div");
      label.style.cssText =
        "font:11px/1.5 ui-monospace,monospace;letter-spacing:1.3px;color:#9edbce";
      label.textContent =
        "DEFECT LENS / PROCEDURAL INPUTS / ACTUAL CPU INFERENCE / AUTOMATED WALKTHROUGH";
      const heading = document.createElement("strong");
      heading.style.cssText = "display:block;font-size:22px";
      heading.textContent = title;
      const text = document.createElement("div");
      text.textContent = detail;
      bar.append(label, heading, text);
    },
    { title, detail },
  );
  // Deliberate viewing time for the recording, never a synchronization condition.
  await page.waitForTimeout(hold);
}

async function inspect(kind: string) {
  const job = page.getByTestId("result-job");
  const previous = (await job.count()) ? await job.textContent() : null;
  const sample = manifest.samples.find(
    (s) => s.split === "test" && s.defect_kind === kind,
  );
  if (!sample) throw new Error(`Missing ${kind} fixture`);
  const file = path.join(root, ".runtime/data/fixtures", sample.image_path);
  const hash = createHash("sha256")
    .update(await readFile(file))
    .digest("hex");
  if (hash !== sample.image_sha256) throw new Error("Fixture hash mismatch");
  inputs.push({ image_path: sample.image_path, image_sha256: hash });
  await page.getByLabel("Inspection image").setInputFiles(file);
  await page
    .getByRole("button", { name: "Inspect image", exact: true })
    .click();
  if (previous) await expect(job).not.toHaveText(previous);
  await expect(job).toHaveText(/succeeded/);
}

try {
  const response = await page.request.get("http://127.0.0.1:5111/api/models");
  expect(response.ok()).toBe(true);
  model = (await response.json()) as ModelMetadata;
  expect(model.method).toBe("difference");
  expect(model.data_mode).toBe("procedural");
  expect(model.status).toBe("ready");
  await page.goto("http://127.0.0.1:5111");
  await expect(
    page.getByText("Procedural demonstration", { exact: true }).first(),
  ).toBeVisible();
  await caption(
    "An inspection you can trace",
    "Compare appearance, inspect the evidence, keep the original decision.",
  );
  await inspect("none");
  await expect(page.getByLabel("Heatmap opacity")).toBeVisible();
  await caption(
    "Start with a good reference view",
    "This result comes from the running local API and its difference model.",
  );
  await inspect("missing_fastener");
  const opacity = page.getByLabel("Heatmap opacity");
  await expect(opacity).toBeVisible();
  await caption(
    "A missing fastener changes the image",
    "The overlay locates unusual appearance; it does not diagnose a damage cause.",
  );
  await opacity.fill("0");
  await caption(
    "Compare the original and the overlay",
    "The slider exposes the input beneath the anomaly map.",
    2000,
  );
  await opacity.fill("80");
  await caption(
    "Inspect spatial evidence",
    "The numeric score and model revision stay with the saved result.",
  );
  await inspect("quality");
  await expect(page.getByText(/blur: /)).toBeVisible();
  await expect(opacity).toHaveCount(0);
  await caption(
    "Uncertainty is visible",
    "Blur forces review and suppresses localization instead of implying a precise defect.",
    4000,
  );
  await page.getByLabel("Corrected decision").selectOption("review");
  await page.getByLabel("Operator alias").fill("Automated demo");
  await page
    .getByLabel("Review note")
    .fill("Scripted correction on a generated blur fixture; not human review.");
  await caption(
    "Keep feedback separate from model output",
    "This scripted correction demonstrates persistence. It is not a human annotation.",
  );
  await page.getByRole("button", { name: "Save correction" }).click();
  await page.getByText(/Correction history \(/).click();
  await expect(
    page.getByText(
      "Scripted correction on a generated blur fixture; not human review.",
      { exact: true },
    ),
  ).toBeVisible();
  await caption(
    "An append-only correction history",
    "The saved version leaves the original inference unchanged.",
  );
  await page.reload();
  await page.getByText(/Correction history \(/).click();
  await expect(
    page.getByText(
      "Scripted correction on a generated blur fixture; not human review.",
      { exact: true },
    ),
  ).toBeVisible();
  await caption(
    "Saved after reload",
    "Model output and correction remain linked. No automatic retraining takes place.",
  );
  await caption(
    "Know what the evidence supports",
    "Procedural demo. Separate public-photo development study. No industrial validation.",
    4000,
  );
} finally {
  await context.close();
  await browser.close();
}
const evidence = {
  model,
  input_mode: "procedural",
  inference: "actual difference API",
  correction: "automated script, not human review",
  inputs,
  timeline,
  video: await video.path(),
};
await writeFile(
  path.join(destination, "recording.json"),
  JSON.stringify(evidence, null, 2) + "\n",
);
await writeFile(
  path.join(root, ".runtime/demo/latest.json"),
  JSON.stringify(evidence, null, 2) + "\n",
);
console.log(
  JSON.stringify({ directory: destination, video: await video.path() }),
);
