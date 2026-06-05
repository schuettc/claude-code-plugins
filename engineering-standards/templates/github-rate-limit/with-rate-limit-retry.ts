export interface BackoffOpts {
  /** Max retries on rate-limit responses (not counting the initial attempt). */
  maxRetries: number;
  /** Injected sleep (ms). Lets tests run instantly. */
  sleep: (ms: number) => Promise<void>;
  /** Hard ceiling on a single sleep, in ms. Default 60_000 (1 min). */
  maxSleepMs?: number;
}

/** True if the response represents a GitHub primary/secondary rate-limit hit. */
export async function isRateLimited(res: Response): Promise<boolean> {
  if (res.status === 429) return true;
  if (res.status !== 403) return false;
  try {
    const text = await res.clone().text();
    return /rate limit|secondary rate/i.test(text);
  } catch {
    return false;
  }
}

/**
 * Run fetchFn; if its response is a rate-limit hit, sleep based on
 * retry-after / x-ratelimit-reset headers and retry up to opts.maxRetries.
 * Returns the final response (success OR final rate-limited response).
 */
export async function withRateLimitRetry(
  fetchFn: () => Promise<Response>,
  opts: BackoffOpts,
): Promise<Response> {
  const maxSleep = opts.maxSleepMs ?? 60_000;
  let lastResponse: Response | null = null;
  for (let attempt = 0; attempt <= opts.maxRetries; attempt += 1) {
    const res = await fetchFn();
    if (!(await isRateLimited(res))) return res;
    lastResponse = res;
    if (attempt === opts.maxRetries) break;
    const waitMs = Math.min(maxSleep, computeWaitMs(res));
    await opts.sleep(waitMs);
  }
  return lastResponse!;
}

function computeWaitMs(res: Response): number {
  const retryAfter = res.headers.get("retry-after");
  if (retryAfter) {
    const sec = Number(retryAfter);
    if (Number.isFinite(sec) && sec >= 0) return Math.ceil(sec * 1000);
  }
  const reset = res.headers.get("x-ratelimit-reset");
  if (reset) {
    const epochSec = Number(reset);
    if (Number.isFinite(epochSec)) {
      const delta = epochSec * 1000 - Date.now();
      if (delta > 0) return delta;
    }
  }
  return 5_000;
}
