// Known-bad fixture for fallow hook verification.
// Deliberate high-complexity export so fallow will flag the diff.

export function deeplyNested(a: number, b: number, c: number, d: number,
                              e: number, f: number, g: number, h: number,
                              i: number, j: number, k: number, l: number,
                              m: number, n: number, o: number, p: number): number {
  if (a > 0) if (b > 0) if (c > 0) if (d > 0) if (e > 0) if (f > 0) if (g > 0)
  if (h > 0) if (i > 0) if (j > 0) if (k > 0) if (l > 0) if (m > 0) if (n > 0)
  if (o > 0) if (p > 0) { return a+b+c+d+e+f+g+h+i+j+k+l+m+n+o+p; }
  return 0;
}
