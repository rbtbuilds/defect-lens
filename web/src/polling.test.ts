import { afterEach, expect, it, vi } from "vitest";
import { startPolling } from "./polling";
afterEach(() => vi.useRealTimers());
it("aborts active requests when unmounted", () => {
  let captured: AbortSignal | undefined;
  const stop = startPolling((signal) => {
    captured = signal;
    return new Promise<boolean>(() => {});
  }, vi.fn());
  stop();
  expect(captured?.aborted).toBe(true);
});
it("stops after terminal result and pauses hidden tabs", async () => {
  vi.useFakeTimers();
  const task = vi.fn().mockResolvedValue(false);
  const stop = startPolling(task, vi.fn());
  await vi.runAllTimersAsync();
  expect(task).toHaveBeenCalledTimes(1);
  stop();
  vi.spyOn(document, "hidden", "get").mockReturnValue(true);
  const hiddenTask = vi.fn().mockResolvedValue(true);
  const stopHidden = startPolling(hiddenTask, vi.fn());
  await vi.advanceTimersByTimeAsync(2000);
  expect(hiddenTask).not.toHaveBeenCalled();
  stopHidden();
  vi.restoreAllMocks();
});
it("backs off on a network error", async () => {
  vi.useFakeTimers();
  const task = vi
    .fn()
    .mockRejectedValueOnce(new Error("network"))
    .mockResolvedValue(false);
  const errors = vi.fn();
  const stop = startPolling(task, errors);
  await vi.advanceTimersByTimeAsync(4999);
  expect(task).toHaveBeenCalledTimes(1);
  await vi.advanceTimersByTimeAsync(1);
  expect(task).toHaveBeenCalledTimes(2);
  expect(errors).toHaveBeenCalledTimes(1);
  stop();
});
