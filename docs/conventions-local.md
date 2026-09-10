# Conventions — Mesh Desktop Client, local

Rules true of **this project only**. The inherited baseline is the pinned copy in
`docs/conventions.md`, which is never edited (`turing-review:D24`). A rule here that turns
out to be true of every project gets **promoted upstream** — a visible move, on the record,
rather than the same paragraph appearing in fourteen files.

---

## Harness

Declared per `turing-review:F8`. The process ships the **contract**, never a harness — a
shipped harness would be one language's and worth nothing to the others. These commands are
`C1`'s deliverable and **do not exist yet**; `check_harness.py --run` will fail until they
do, which is the intended behaviour and not a defect to route around.

- run: `uv run pytest -q`
- count: `uv run python scripts/count_assertions.py`
- floor: `tests/FLOOR`
- mutate: `uv run python scripts/mutate.py`
- precommit: `.githooks/pre-commit`

**Why `count` is separate from `run`.** An exit code cannot show a suite that stopped
running. A module-level `sys.exit(0)` exits clean having asserted nothing. The count is what
catches that, and it counts assertions that **executed**, not tests collected.

**`precommit` runs after the last edit.** Gates satisfied in advance and then edited past
are not gates. Installed per-clone with `git config core.hooksPath .githooks`; no commit can
carry that setting, so a fresh clone is unprotected until somebody runs it.

---

## No test touches the radio

A suite that needs a V4 at `192.168.0.231` is not a suite — it cannot run on a train, it
cannot run twice in a row reliably, and its failures are ambiguous between "the code is
wrong" and "the radio is asleep". **The fake is the seam** (`D13`).

Hardware verification is real and stays real; it is simply not the suite. It runs under its
own named command, its output goes in the PR, and it is never a gate that a hosted runner or
a disconnected laptop could be asked to satisfy.

**`run` must pass with the radio powered off.** That is the check on this rule, and it is
cheap to perform: unplug it.

---

## Bytes are not characters, and neither is the limit a constant

The payload limit is read from `mesh_pb2.Constants.DATA_PAYLOAD_LEN` at runtime (`D5`,
`FR17`). Two failure modes this project must never ship:

- **A hardcoded limit.** The intent carried `190` unsourced; the library enforces `233`.
  A firmware or library bump must not be able to silently invalidate the calculator.
- **A naive slice.** UTF-8 means a byte budget and a character count differ, and slicing at
  a byte boundary can split a character. Any test of the budget uses a multi-byte string —
  a fixture that is pure ASCII satisfies both the right and the wrong implementation and so
  distinguishes nothing.

---

## The soak states its power condition

Every soak run records the TX power setting and whether a battery was attached (`FR10`).
Two hypotheses exist for the observed instability — brownout at high TX power, and the
desktop client — and **neither has evidence** (`RR9`). The soak can distinguish them only
if the power condition is held constant and stated. This is variable control, not a claim
about cause.

---

## Two retry rules, and they are not the same rule

Stated because they look like a contradiction and are not (`NFR9`):

- **Retrying a spreadsheet write is correct.** The sample should land somewhere; `FR7`'s
  local fallback exists for when it cannot.
- **Reconnecting to the radio is governed by `FR6`** — capped backoff, and every disconnect
  *and reconnect* logged as its own event. Never silent. A silent reconnect would paper over
  the exact failure the soak exists to hunt.

-----
2026-09-10

#AI/Claude
