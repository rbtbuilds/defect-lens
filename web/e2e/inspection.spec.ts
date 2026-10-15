import { test, expect } from "@playwright/test";
import { readFile } from "node:fs/promises";
import path from "node:path";
const root = path.resolve(import.meta.dirname, "../..");
const manifest = JSON.parse(
  await readFile(
    path.join(root, ".runtime/data/fixtures/manifest.json"),
    "utf8",
  ),
) as {
  samples: Array<{
    image_path: string;
    split: string;
    label: string;
    defect_kind: string;
  }>;
};
test("actual good, defect, blur, correction and reload", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByText("Procedural demonstration", { exact: true }).first(),
  ).toBeVisible();
  for (const kind of ["none", "missing_fastener", "quality"]) {
    const sample = manifest.samples.find(
      (s) => s.split === "test" && s.defect_kind === kind,
    );
    if (!sample) throw new Error("Missing fixture");
    await page
      .getByLabel("Inspection image")
      .setInputFiles(
        path.join(root, ".runtime/data/fixtures", sample.image_path),
      );
    await page
      .getByRole("button", { name: "Inspect image", exact: true })
      .click();
    await expect(
      page.getByRole("heading", { name: "Inspection result" }),
    ).toBeVisible();
    await expect(page.getByTestId("result-job")).toHaveText(/succeeded/);
    if (kind === "quality") {
      await expect(page.getByText(/blur: /)).toBeVisible();
      await expect(page.getByLabel("Heatmap opacity")).toHaveCount(0);
    } else {
      await expect(page.getByLabel("Heatmap opacity")).toBeVisible();
      await page.getByLabel("Heatmap opacity").focus();
      await page.keyboard.press("ArrowLeft");
    }
  }
  await page.getByLabel("Corrected decision").focus();
  await page.keyboard.press("Tab");
  await expect(page.getByLabel("Operator alias")).toBeFocused();
  await page.keyboard.type("Matthew");
  await page.keyboard.press("Tab");
  await page.keyboard.type("Reviewed staged blur example");
  await page.keyboard.press("Tab");
  await page.keyboard.press("Enter");
  await page.getByText(/Correction history \(/).click();
  await expect(
    page.getByText("Reviewed staged blur example", { exact: true }),
  ).toBeVisible();
  await page.reload();
  await page.getByText(/Correction history \(/).click();
  await expect(
    page.getByText("Reviewed staged blur example", { exact: true }),
  ).toBeVisible();
  const selected = page.getByRole("button", { pressed: true });
  await selected.click();
  await expect(
    page.getByRole("heading", { name: "Inspection result" }),
  ).toBeVisible();
});
for (const theme of ["light", "dark"] as const)
  for (const width of [390, 1280]) {
    test(`${theme} ${width}px keyboard and reduced motion`, async ({
      page,
    }) => {
      await page.setViewportSize({ width, height: 1000 });
      await page.emulateMedia({ colorScheme: theme, reducedMotion: "reduce" });
      await page.goto("/");
      await page.getByRole("button", { name: "Toggle theme" }).focus();
      await page.keyboard.press("Enter");
      await page.keyboard.press("Enter");
      await expect(page.locator("html")).toHaveAttribute("data-theme", theme);
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
      ).toBe(true);
      const contrast = await page.evaluate(() => {
        const luminance = (value: string) => {
          const channels = (value.match(/\d+/g) ?? [])
            .slice(0, 3)
            .map(Number)
            .map((v) => {
              const n = v / 255;
              return n <= 0.04045 ? n / 12.92 : ((n + 0.055) / 1.055) ** 2.4;
            });
          return (
            0.2126 * (channels[0] ?? 0) +
            0.7152 * (channels[1] ?? 0) +
            0.0722 * (channels[2] ?? 0)
          );
        };
        const root = getComputedStyle(document.documentElement);
        const text = root.getPropertyValue("--muted").trim();
        const surface = root.getPropertyValue("--surface").trim();
        const color = (v: string) => {
          const probe = document.createElement("span");
          probe.style.color = v;
          document.body.append(probe);
          const result = getComputedStyle(probe).color;
          probe.remove();
          return result;
        };
        const a = luminance(color(text));
        const b = luminance(color(surface));
        return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
      });
      expect(contrast).toBeGreaterThanOrEqual(4.5);
      expect(
        await page
          .locator("button")
          .first()
          .evaluate((el) => getComputedStyle(el).transitionDuration),
      ).toBe("0s");
      await page.screenshot({
        path: path.join(root, `.runtime/screenshots/${theme}-${width}.png`),
        fullPage: true,
      });
    });
  }

test("restores a linked inspection beyond the first page and rejects a missing link", async ({
  page,
}) => {
  const metadata = (await (await page.request.get("/api/models")).json()) as {
    model_revision: string;
    data_mode: string;
  };
  const sample = manifest.samples.find(
    (s) => s.split === "test" && s.defect_kind === "missing_fastener",
  );
  if (!sample) throw new Error("Missing defect fixture");
  const buffer = await readFile(
    path.join(root, ".runtime/data/fixtures", sample.image_path),
  );
  const submit = async () => {
    const response = await page.request.post("/api/jobs", {
      headers: { "Idempotency-Key": crypto.randomUUID() },
      multipart: {
        image: { name: "fixture.png", mimeType: "image/png", buffer },
        model_revision: metadata.model_revision,
        data_mode: metadata.data_mode,
      },
    });
    expect(response.status()).toBe(202);
    return (await response.json()) as { id: string };
  };
  const linked = await submit();
  await expect
    .poll(async () => {
      const response = await page.request.get(`/api/jobs/${linked.id}`);
      return ((await response.json()) as { status: string }).status;
    })
    .toBe("succeeded");
  for (let count = 0; count < 31; count++) await submit();
  const latest = (await (
    await page.request.get("/api/jobs?limit=30")
  ).json()) as {
    items: Array<{ id: string }>;
  };
  expect(latest.items.some((job) => job.id === linked.id)).toBe(false);
  await page.goto(`/#${linked.id}`);
  await expect(page.getByTestId("result-job")).toHaveText(
    new RegExp(linked.id.slice(0, 8)),
  );
  await expect(
    page.getByRole("heading", { name: "Inspection result" }),
  ).toBeVisible();
  await expect(page.getByRole("button", { pressed: true })).toContainText(
    linked.id.slice(0, 8),
  );
  await page.reload();
  await expect(page.getByTestId("result-job")).toHaveText(
    new RegExp(linked.id.slice(0, 8)),
  );
  await page.goto(`/#${crypto.randomUUID()}`);
  await page.reload();
  await expect(page.getByRole("alert")).toContainText("NOT_FOUND");
  await expect(page.getByTestId("result-job")).toHaveCount(0);
});
