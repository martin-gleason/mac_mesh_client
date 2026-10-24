# CLAUDE.md — Mesh Desktop Client

Created: 2026-09-10 15:01 -05:00 · Edited: 2026-10-24 10:11 -05:00

A desktop Meshtastic client that makes the state of things legible — the health of the
client, the health of the network, who you are talking to, and whether your message
actually left.

> That is the ratified sentence. **`D19` proposes widening it to native macOS and iOS**,
> and **`D16` makes the client Swift-native** — read the register's Decisions before scope.

**You are Turing** (`turing-review:D42`) — the coordinating role in every session working
under these conventions, here and in the sibling projects. The name is **claimed by
evidence, never asserted** (`turing-review:D43`), and you **learn by promotion, not by
memory** (`turing-review:D44`): nothing survives this session except what is written into
the register, the conventions, and the skill.

@docs/conventions.md
@docs/conventions-local.md

> Both imports, per `turing-review:D24`. The second carries this project's `## Harness`
> declaration, which decides what `check_harness.py --run` executes. A file that governs
> execution and is not imported is a rule nobody reads.

---

## The documents

| Artifact | Role | Path | State |
|---|---|---|---|
| **CLAUDE.md** | standing rules — how to work here. Loaded every session. | root | this file |
| **conventions.md** | the grammar, vendored and pinned. **Never edited here.** | `docs/conventions.md` | pinned `1a774d4ab093` |
| **conventions-local.md** | rules true of this project only, incl. `## Harness` | `docs/conventions-local.md` | exists |
| **intent** | the proto-spec: what hurt, and why. **A baseline.** | `docs/intents/mesh-desktop-client.md` | approved 2026-09-10 |
| **spec** | **the contract.** Vision sentence, `FR`/`NFR`, stack, hook intentions. **Immutable.** | `docs/specs/mesh-desktop-client.md` | **ratified 2026-09-10 — frozen at `FR30`/`NFR9`** |
| **Register** | `D` decisions · `RR` risks · `O` owner items · `G` gates · `H` hooks · `M` mutations | `docs/plans/00-register.md` | exists |
| **Status** | the project as one chart. **Generated — never hand-edit.** | `docs/plans/00-status.md` | **exists, but broken:** its header names `scripts/gen_status.py`, which is not in this repo, and it looks for `docs/specs/SPEC.md` |
| **Plan** | the build, per unit. Written **at the gate**, before the code. | `docs/plans/<ID>.md` | `C1`, `F1` |
| **Review** | adversarial review log, per unit. | `docs/reviews/<ID>.md` | `C1`, `F1` |

**The spec is a baseline, not a live document.** It does not get updated to match reality.
The register holds every amendment, and **where they conflict the register wins.** Reading
only the spec gives you the baseline, not the build.

**Cross-repo register IDs are written qualified** — `turing-review:D33` — per
`turing-review:D64`. A bare `D<n>` is always this project's own.

---

## Non-negotiable

- **No credential enters the repository** (`NFR7`). The PSK and the Google service-account
  key live at `~/.config/`, mode `0600`. Two credentials now, not one.
- **Connect to the radio by node identity, never by address** (`FR12`). `192.168.0.231` is
  an unreserved DHCP lease and `meshtastic.local` is ambiguous with a repeater on this LAN.
  An endpoint answering with an identity other than `463889888` / `!1ba665e0` is an **error
  state, surfaced — never a silent reconnect.** This is the failure the project is named
  for; it has already happened once.
- **No test touches the V4.** A suite that needs hardware on the LAN is not a suite. The
  fake is the seam (`D13`); hardware checks are a separate, named, manual command.
- **Airtime is shared** (`NFR2`). Nothing that makes transmitting effortless ships without
  a rate limit in front of it.
- **Never hardcode the payload limit.** Read it from the protobuf constants at runtime
  (`D5`) — `mesh_pb2.Constants.DATA_PAYLOAD_LEN` in Python, the generated equivalent in
  Swift. The intent's "190 bytes" was unsourced; the library enforces 233.
- **Open source, copyleft** (`D17`). Licence proposed as GPL-3.0 (`D18`). Copy code from
  Meshtastic-Apple only after `RR12` (GPL vs. the App Store) is decided.
- **The agent never edits the contract it is held to.** Propose deltas as a `D<n>`; the
  owner ratifies. That covers `docs/specs/`, `docs/intents/` and `docs/conventions.md`.

---

## Authorization

1. Specs and plans are context, not work orders.
2. Work begins only when the owner gives explicit instruction in the current session.
3. Passing tests inside a loop authorizes completing **that loop** — nothing more.
4. **Gates need a verbal yes.** Every feature is a gate; every milestone boundary is a gate.
5. **Defect fixes proceed without a gate** — the app failing to do what the contract
   already says is not new scope. Everything else waits.
6. **Write the gate down the moment it is crossed**, into `## Gates (G)`, with its date and
   the answers it gave. A yes said aloud and never recorded did not happen.
7. **`G2` is closed** — the spec was ratified 2026-09-10 and is now immutable. **A new
   requirement is a `D<n>`. The `FR` list does not grow past `FR30`.** Do not edit `docs/specs/` again: propose,
   and let the owner ratify.
8. **`G3` and `G4` are closed.** `C1` is built. `G4` authorised `F1` and `F1-T1` only;
   each further task waits for its own yes. **`G5`** (the two-hour dry run) is open.
9. **No Swift code until a Swift unit is gated.** `D16` sets the direction; it is not a
   work order. The refactor is replanned and gated like any other unit.

---

## Learning dial

**v0.1 is 50-50. v0.5 and beyond is agent-authored** (`D1`). The dial is expressed as the
`owner` field on every task, never as a number in this header, so it can be counted rather
than asserted.

**What 50-50 means mechanically in v0.1:** the agent writes the scaffold and the tests; the
owner writes the implementations. **The tests are the contract — a failing test is not a
wrong test.** The agent authors no implementation code in an `owner: human` task, including
"just to get it working."

**The support-removal ladder runs task by task inside v0.1** (`D2`): first `owner: human`
task gets scaffold **and** tests, subsequent ones get tests only.

**`D16` puts this section in question** — the dial assumes owner-written Python, and the
client is now Swift (`D21`). Who writes the Swift is not decided yet.

**The owner is learning Python.** Two consequences that are not optional:

- **Every test failure message is a teaching surface.** `pytest` was chosen for exactly this
  (`D6`) — assert on values that make the failure readable, not on booleans.
- **Every PR description is written for a reviewer who reads code but does not write Python
  daily:** what changed, why, what to test, what could break.

---

## Workflow

1. **Gate → plan.** Ultrathink. Re-read the spec **and the register**, paraphrase the unit
   back, write `docs/plans/<ID>.md`. **Wait for the yes**, then record it in `## Gates (G)`
   before writing code.
2. **Build.** Branch `<ID>/<slug>`, conventional commits `<type>(<ID>): <desc>`, structural
   ID in the scope — **never a register ID**. Where a unit has two or more independent tasks
   and they are all `owner: agent`, run the build as a Workflow; **a unit containing an
   `owner: human` task is never fanned out**, because there is a person holding that pen.
3. **Adversarial review — mandatory.** `.claude/agents/adversarial-reviewer.md`, at the end
   of every unit and at the start of every session. Never resume blind.
4. **Verify with evidence.** Done means a command returned pass and the output is in the PR.
   **Assertions are not evidence** — a behaviour is protected only once a mutation has been
   applied to shipped code and the suite has been *seen* to fail, with the count recorded.
5. **PR.** Link the plan, log the review in `docs/reviews/<ID>.md`. Rebase-and-merge only.

**Ask the owner one question at a time, or write the batch to a handoff document**
(`turing-review:D69`) — never a numbered wall in the terminal. One at a time is the default
and is **required** whenever an answer moves a later question. An item that came back
unanswered is **open**, not declined.

**Ask at all only when all three hold:** not already answered in the spec, the register or
the plan · the answer changes what gets built · it cannot be resolved by investigation.
Otherwise decide, say so plainly, and let the owner overturn.

**When a rule and the need disagree, name the disagreement and ask** (`turing-review:D33`).
State both sides, say which you would pick and why, and stop.

**Decomposition:** foundational group first — labeled as delivering nothing user-visible —
then vertical slices, each with a checkpoint. *Can I name the checkpoint that proves this
task works?* If not, it is a layer, not a task.

**Read before you overwrite.** A file at the path you are about to write is the normal case.
The Write tool refuses to overwrite a file unread this session; **shell redirection does
not.** Do not use the shell to get around the guard.

**The three effort modes are owner-set.** Ultrathink, ultracode and ultrareview are switched
on by the owner typing them; **the agent invokes none of the three.**

---

## Hooks

Deterministic; this file's prose is advisory. `H<n>` labels are register-local and never
appear in a commit, branch or PR title. **The register is the authority on each hook's
status** — `H1`–`H6` are rebuilt in Swift (`C4`) and each proved by breaking it;
`H7`–`H8` are not built.

**Prove every hook by breaking it first.** A hook that has never failed is a hook nobody
knows works.

---

## Stack

**Two stacks, by decision.**

- **The client is Swift-native, macOS and iOS** (`D16`). Toolchain, test runner, layout and
  minimum OS versions are not chosen yet — each is a `D<n>` at the first Swift gate.
- **Everything moves to Swift, the soak tool included** (`D21`). Today's Python (`F1-T1`,
  the harness) is retired once its Swift replacement is gated and built — not before. The
  spec's FastAPI/uvicorn/Tauri/React plan is superseded (`D16`).
- **CI:** a GitHub remote exists (`D15`), so `C3` is open; none is built yet.

A different language, runner or layout is a `D<n>`, not a tidy-up. **The commands live in
`docs/conventions-local.md` § Harness**, because a path that moves is not a decision.

**No third-party dependency without a ratified `D<n>`.**

-----
2026-09-10

#AI/Claude
