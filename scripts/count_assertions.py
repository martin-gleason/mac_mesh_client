#!/usr/bin/env python3
"""`C1-T2` — count the assertions that actually EXECUTED, and hold them to a floor.

**Why this is separate from `run`.** An exit code cannot show a suite that stopped
running. A module-level `sys.exit(0)` exits clean having asserted nothing; tests
written below a `__main__` guard never run under one runner and do under another, and
both report green. Counting *tests collected* would not catch either — the number
that matters is how many assertions were reached and passed.

The count comes from pytest's own `pytest_assertion_pass` hook, which fires once per
`assert` statement that executed and held. It requires `enable_assertion_pass_hook`
in `pyproject.toml`; without it a cold run reports `0`, which is why `--check` treats
a zero count as a failure rather than as a very clean run.

**Every run is cold, deliberately.** Both CPython's `__pycache__` and pytest's
assertion-rewrite cache validate on *integer-second* mtime plus size, so a same-second
same-size edit is served stale and silently. That defeats the whole instrument: a
broken shipped file reports green, and with a warm cache the assertion-pass hook can
be switched off entirely while this script keeps printing the old number. Pointing
`sys.pycache_prefix` at a fresh directory per run makes both caches miss.

    python scripts/count_assertions.py            # print one integer
    python scripts/count_assertions.py --check    # compare against tests/FLOOR
"""

from __future__ import annotations

import argparse
import importlib
import io
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FLOOR = ROOT / "tests" / "FLOOR"


class AssertionCounter:
    """One tick per assert statement that executed and passed."""

    def __init__(self) -> None:
        self.count = 0

    def pytest_assertion_pass(self, item, lineno, orig, expl) -> None:  # noqa: ARG002
        self.count += 1


def run_suite() -> tuple[int, int, str]:
    """(exit code, assertions executed, captured pytest output)."""
    counter = AssertionCounter()
    captured = io.StringIO()

    # A fresh bytecode directory per run, so neither CPython's cache nor pytest's
    # assertion-rewrite cache can serve a stale module. Both key on mtime-to-the-
    # second plus size, and an edit that keeps the size and lands in the same second
    # is invisible to them — which is how a gate reports a state the working tree
    # does not have. TemporaryDirectory cleans it up; the recompile costs milliseconds.
    with tempfile.TemporaryDirectory(prefix="mesh-pycache-") as cache:
        sys.pycache_prefix = cache
        importlib.invalidate_caches()
        # pytest writes its report to stdout; this command's contract is one integer,
        # so the report is captured and only surfaced when something went wrong.
        with redirect_stdout(captured):
            code = pytest.main(
                ["-q", "--no-header", "-p", "no:cacheprovider", str(ROOT / "tests")],
                plugins=[counter],
            )
    return int(code), counter.count, captured.getvalue()


def read_floor() -> int:
    if not FLOOR.is_file():
        raise SystemExit(f"count: no floor at {FLOOR.relative_to(ROOT)} — `C1-T4` builds it")
    text = FLOOR.read_text(encoding="utf-8").strip()
    try:
        return int(text)
    except ValueError:
        raise SystemExit(f"count: {FLOOR.relative_to(ROOT)} is not an integer: {text!r}") from None


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true",
                    help="fail if the count is below tests/FLOOR")
    args = ap.parse_args(argv[1:])

    code, count, output = run_suite()

    if code != 0:
        print(output, file=sys.stderr)
        print(f"count: the suite failed (pytest exit {code}) — the count below it is "
              f"not meaningful, because a failing assert never fires the pass hook.",
              file=sys.stderr)
        return 1

    if not args.check:
        print(count)
        return 0

    floor = read_floor()
    # Zero is not a very clean run. It is the signature of the assertion-pass hook
    # being switched off, which is exactly the blindness this script exists to stop.
    if count == 0:
        print("count: 0 assertions executed. Either the suite asserts nothing, or "
              "`enable_assertion_pass_hook` is missing from pyproject.toml.",
              file=sys.stderr)
        return 1
    if count < floor:
        print(f"count: FAIL — {count} assertion(s) executed, floor is {floor}. "
              f"A shrinking suite is blind, not clean. Deliberately removing a "
              f"behaviour means lowering the floor in the same commit, on purpose.",
              file=sys.stderr)
        return 1

    print(f"count: pass — {count} assertion(s) executed, floor {floor}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
