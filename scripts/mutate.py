#!/usr/bin/env python3
"""`C1-T5` — break the shipped code on purpose and require the suite to notice.

**A test that has never been shown to fail is not evidence** (`NFR8`). A suite with
no mutations is a false-assurance instrument, and that is not theoretical: fifteen
checks once passed for a register parser that was returning the same title for every
row. They passed because every assertion hand-built its own object.

So a behaviour is not protected until a mutation has been applied to the **shipped**
code — not to a copy, not to a model of it — and the suite has been *seen* to fail.
`caught at n/m` is evidence. *Prevented by construction* is an argument.

**A red suite is not a kill.** Each mutation names the test that must catch it, and
this checks that *that named test* is among the failures. Accepting any failure is
how a harness scores a crash as a kill: rename the named test and a mutation is
"caught" by a test that no longer exists.

    python scripts/mutate.py             # run every mutation
    python scripts/mutate.py --list      # name them without touching anything
    python scripts/mutate.py M1          # run one
"""

from __future__ import annotations

import argparse
import os
import re
import signal
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Every file this process has mutated and not yet put back. A signal handler cannot
# reach a local variable, and leaving mutated source on disk is the one outcome this
# tool must never produce.
_PENDING: dict[Path, str] = {}


@dataclass(frozen=True)
class Mutation:
    id: str
    description: str
    path: Path
    old: str
    new: str
    caught_by: str


MUTATIONS: tuple[Mutation, ...] = (
    Mutation(
        id="M1",
        description=("replace the runtime read of DATA_PAYLOAD_LEN with the literal "
                     "190 — the mistake this project actually made"),
        path=ROOT / "src/mesh_client/budget.py",
        old="    return int(mesh_pb2.Constants.DATA_PAYLOAD_LEN)",
        new="    return 190",
        caught_by="tests/test_budget.py::test_limit_is_read_at_call_time_not_baked_in",
    ),
    Mutation(
        id="M4",
        description=("hardcode 233 — the value the library returns TODAY, so every "
                     "equality assertion still agrees and only a runtime read fails"),
        path=ROOT / "src/mesh_client/budget.py",
        old="    return int(mesh_pb2.Constants.DATA_PAYLOAD_LEN)",
        new="    return 233",
        caught_by="tests/test_budget.py::test_limit_is_read_at_call_time_not_baked_in",
    ),
    Mutation(
        id="M2",
        description="count characters instead of bytes",
        path=ROOT / "src/mesh_client/budget.py",
        old='    return len(text.encode("utf-8"))',
        new="    return len(text)",
        caught_by="tests/test_budget.py::test_encoded_size_counts_bytes_not_characters",
    ),
    Mutation(
        id="M3",
        description="cut on a raw byte boundary, splitting a character in half",
        path=ROOT / "src/mesh_client/budget.py",
        old="""    cut = raw[:cap]
    while cut:
        try:
            return cut.decode("utf-8")
        except UnicodeDecodeError:
            cut = cut[:-1]
    return \"\"""",
        new='    return raw[:cap].decode("utf-8", errors="replace")',
        caught_by=("tests/test_budget.py::"
                   "test_truncated_output_is_always_a_decodable_prefix_within_budget"),
    ),
)

FAILED_LINE = re.compile(r"^FAILED (\S+)", re.M)


def restore_all(*_args) -> None:
    for path, original in list(_PENDING.items()):
        path.write_text(original, encoding="utf-8")
        _PENDING.pop(path, None)


def _on_signal(signum, _frame):
    # SIGTERM and SIGHUP run the default handler and exit WITHOUT unwinding, so
    # `finally` never fires: a closed terminal, an IDE stop button or a CI timeout
    # would otherwise leave mutated source in the tree.
    restore_all()
    print(f"\nmutate: signal {signum} — shipped files restored", file=sys.stderr)
    sys.exit(128 + signum)


def run_suite() -> tuple[bool, str, set[str]]:
    """(did the suite pass, output, the set of failed test node ids)."""
    env = dict(os.environ)
    with tempfile.TemporaryDirectory(prefix="mesh-pycache-") as cache:
        # Same reason as in count_assertions.py: both bytecode caches key on
        # mtime-to-the-second plus size, and a mutation is exactly a same-second edit.
        # A warm cache would run the ORIGINAL code and score the mutation uncaught.
        env["PYTHONPYCACHEPREFIX"] = cache
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "--no-header", "--tb=no", "-rf",
             "-p", "no:cacheprovider"],
            cwd=ROOT, capture_output=True, text=True, env=env,
        )
    output = (proc.stdout + proc.stderr).strip()
    failed = {m.group(1) for m in FAILED_LINE.finditer(output)}
    return proc.returncode == 0, output, failed


def summary(output: str) -> str:
    for line in reversed(output.splitlines()):
        if "passed" in line or "failed" in line or "error" in line:
            return line.strip()
    return output.splitlines()[-1] if output else "(no output)"


def apply(m: Mutation) -> bool:
    """Apply one mutation, run the suite, restore. True when the NAMED test caught it."""
    original = m.path.read_text(encoding="utf-8")
    if m.old not in original:
        print(f"  {m.id} SKIP — the code it mutates has moved. A mutation pointing at "
              f"a line that no longer exists proves nothing; update it or retire it.")
        return False
    try:
        _PENDING[m.path] = original
        m.path.write_text(original.replace(m.old, m.new, 1), encoding="utf-8")
        passed, output, failed = run_suite()
    finally:
        restore_all()

    if passed:
        print(f"  {m.id} NOT CAUGHT — {m.description}")
        print(f"       the suite stayed green: {summary(output)}")
        print(f"       {m.caught_by} did not fail. That behaviour is unguarded.")
        return False

    if m.caught_by not in failed:
        # The suite went red, but not for the stated reason. Scoring this as a kill
        # is how a harness credits a crash as evidence.
        print(f"  {m.id} MISATTRIBUTED — {m.description}")
        print(f"       the suite failed, but {m.caught_by} is not among the failures.")
        print(f"       failed instead: {', '.join(sorted(failed)) or '(none parsed)'}")
        print(f"       Either the named test was renamed, or something else is broken.")
        return False

    print(f"  {m.id} caught — {m.description}")
    print(f"       {summary(output)}  (tests, not assertions)")
    print(f"       by {m.caught_by}")
    return True


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("ids", nargs="*", help="mutation ids to run (default: all)")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args(argv[1:])

    if args.list:
        for m in MUTATIONS:
            print(f"{m.id}  {m.description}\n      caught by {m.caught_by}")
        return 0

    chosen = [m for m in MUTATIONS if not args.ids or m.id in args.ids]
    if not chosen:
        raise SystemExit(f"mutate: no such mutation: {', '.join(args.ids)}")

    for sig in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
        signal.signal(sig, _on_signal)

    # A green suite before mutating, or every "caught" below is meaningless.
    passed, output, _ = run_suite()
    if not passed:
        print(f"mutate: the suite is already failing — {summary(output)}", file=sys.stderr)
        print("mutate: fix that first. A mutation is only evidence against a green suite.",
              file=sys.stderr)
        return 1

    print(f"\nmutate — {len(chosen)} mutation(s) against a green suite\n")
    caught = [m for m in chosen if apply(m)]
    print(f"\n  {len(caught)} of {len(chosen)} caught\n")
    return 0 if len(caught) == len(chosen) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
