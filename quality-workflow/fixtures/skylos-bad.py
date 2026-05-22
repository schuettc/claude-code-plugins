"""Known-bad fixture for skylos hook verification.

This file deliberately contains a high-complexity function so skylos
will fire when it sees the file staged. quality-verify-hook stages this
file in a temp location, runs the hook, and asserts exit 1.
"""


def deeply_nested(a, b, c, d, e, f, g, h, i, j, k, l):
    """Cyclomatic complexity > 10 — should trigger SKY-Q301."""
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0:
                    if e > 0:
                        if f > 0:
                            if g > 0:
                                if h > 0:
                                    if i > 0:
                                        if j > 0:
                                            if k > 0:
                                                if l > 0:
                                                    return a + b + c + d + e + f + g + h + i + j + k + l
    return 0
