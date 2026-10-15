export function startPolling(
  task: (signal: AbortSignal) => Promise<boolean>,
  onError: (error: unknown) => void,
  delay = 1000,
): () => void {
  let stopped = false;
  let timer: ReturnType<typeof setTimeout> | undefined;
  let controller: AbortController | undefined;
  const run = async () => {
    if (stopped) return;
    if (document.hidden) {
      timer = setTimeout(run, delay);
      return;
    }
    controller = new AbortController();
    let next = delay;
    try {
      const again = await task(controller.signal);
      if (!again || stopped) return;
    } catch (error) {
      if (stopped) return;
      onError(error);
      next = 5000;
    }
    if (!stopped) timer = setTimeout(run, next);
  };
  void run();
  return () => {
    stopped = true;
    clearTimeout(timer);
    controller?.abort();
  };
}
