"""Known-good fixture for skylos hook verification.

Plain function, low complexity, no security issues, no dead code.
quality-verify-hook stages this, runs the hook, asserts exit 0.
"""


def greet(name: str) -> str:
    """Return a greeting for `name`."""
    return f"hello, {name}"
