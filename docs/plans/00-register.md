# Register — Mesh Desktop Client

Every register for this project, in one file, one `##` per register. This is the
"where are we" read. Detail lives in the entry; nothing here summarises a document you
also have to open.

**One intake path.** Anything that changes scope enters as a `D<n>`. There is no second
way for work to appear. An item with no number has not been decided, however clearly it
was said aloud.

> **Cross-repo citations are qualified** — `turing-review:D33` — per `turing-review:D64`.
> A bare `D<n>` is always this project's own.

---

## Decisions (D)

ADR-style: numbered, dated, **immutable once ratified.** A ratified decision is never
edited — it is superseded by a later entry that links back.

**Status:** `proposed` · `ratified` · `rejected` · `superseded`
**Milestone:** where a ratified decision lands. Not the current milestone = *parked*.

| ID | Status | Milestone | Decision |
|---|---|---|---|
| D1 | ratified | v0.1 | **The learning dial is 50-50 for v0.1 and agent-authored from v0.5 on, with the byte-budget calculator as the single `owner: human` carve-out.** Ratified 2026-09-10 by the owner, choosing *"intent.md stands"* against the agent's recommendation to bias v0.5 upward. The disagreement was raised under `turing-review:D33`, and it was a real one: `turing-review:D32` says a project whose purpose IS learning the language biases **up**, and this project's README says it exists *"to learn additional features of Mesh and Python."* The owner's ruling is that 50-50 at v0.1 **is** the increase over previous projects, and that v0.5's size makes it the wrong place to pay for learning — Tauri work is gated behind v0.5's ratification. Consequence recorded rather than argued: the largest rung on the ladder is the one the owner does not write. |
| D2 | ratified | v0.1 | **The support-removal ladder runs inside v0.1, task by task.** Ratified 2026-09-10. The intent named a ladder — *scaffold + tests → tests only → owner writes the tests → nothing* — and gave it no trigger for advancing a rung. `D1` then left v0.1 as the only milestone containing owner-written Python, so a per-milestone ladder would have had one rung and stopped. It indexes on tasks instead: the first `owner: human` task in v0.1 gets scaffold **and** tests; subsequent ones get tests only. By the `FR17` byte-budget calculator at v0.5 the owner is on *tests only*. |
| D3 | ratified | v0.1 | **The soak logger reconnects to the radio with capped backoff, and every disconnect and reconnect is a logged event. "Unrecovered" means not restored within 5 minutes.** Ratified 2026-09-10, **superseding the intent's clarification** that *"must not reconnect on failure applies to the radio only."* That sentence contradicted pass criterion 2 (*"zero **unrecovered** disconnects… recovered ones are data, not failures"*), which presumes recovery happens: as written, one transient blip at hour 3 ended the run and discarded 45 hours of sample. The fear behind the original sentence — a reconnect papering over a radio reboot — is answered by criterion 1, which watches the uptime counter step backwards regardless of what the socket did. Realised as `FR6`, `NFR9`, and criterion 2's five-minute threshold. |
| D4 | ratified | v0.1 | **The soak is 48 hours — 36h passive, then 12h active.** Ratified 2026-09-10, resolving a contradiction inside the approved intent: its version-ladder row said *"72h elapsed"* while its soak specification said *"48 hours total"* in ~36h + ~12h windows. The specification wins as the reasoned section. Sized against the actual threat: upstream `meshtastic/firmware#9632` reports a persistent TCP client crashing a V4 roughly every 90 minutes, so 36 hours passive is ~24 opportunities for that failure to appear, and the third day buys diminishing evidence for two more calendar days of delay. Realised as `FR2`. |
| D5 | ratified | v0.5 | **The byte limit is read from `mesh_pb2.Constants.DATA_PAYLOAD_LEN` at runtime and never hardcoded.** Ratified 2026-09-10. The intent stated **190 bytes** as a constraint; the library enforces **233**. Verified in this repo's venv before ratification, per `turing-review:D30`: `$ .venv/bin/python -c "from meshtastic import mesh_pb2; print(mesh_pb2.Constants.DATA_PAYLOAD_LEN)"` → `233`, and `mesh_interface.py:560` raises `"Data payload too big"` above it. 190 is not sourced anywhere and was carried forward unexamined. Reading the constant at runtime means a firmware or library bump cannot silently invalidate the one `owner: human` task in v0.5. Realised as `FR17`. |
| D6 | ratified | `C1` | **`pytest` is the test runner.** Ratified 2026-09-10 by the owner. The deciding argument is `D1`-shaped: at 50-50 the agent writes the tests and the owner writes the implementations, so **the tests are what the owner reads to find out what is wrong.** pytest rewrites assertions and prints actual and expected inline; `unittest` prints `AssertionError` and leaves the reader to go looking. When the failing test is the teacher, that is the lesson, not a convenience. Costs one dev dependency. |
| D7 | ratified | `C1` | **Python 3.14.7 and `uv`.** Decided by the agent from evidence rather than asked, per `turing-review`'s three-part test: `.python-version` reads `3.14.7`, `pyvenv.cfg` records `uv = 0.9.18`, and `meshtastic` 2.7.11 installs and imports. Investigation settled it, so it is recorded rather than raised. **Owner may overturn.** Known cost: 3.14 is new enough that some tutorial answers will not match the interpreter, which is a real tax on a learning project (`RR6`). |
| D8 | ratified | `C1` | **Layout is `src/mesh_client/` with tests in `tests/`.** Agent-decided; overturnable. src-layout keeps the installed package and the working tree from shadowing each other, which is the failure that teaches the least per hour lost. |
| D9 | ratified | `C1` | **`C1` is local-first: the harness gates run in a pre-commit hook, not in CI.** Agent-decided. This repository has no remote, and every test that touches the radio needs `192.168.0.231` on the LAN, which no hosted runner has. CI becomes `C3` — running only the fake-backed suite — if and when a remote exists (`O5`). Recorded because *"there is no CI"* must be a decision with a reason, not an omission: `RR4` holds it open. |
| D10 | ratified | v0.1 | **The soak sample cadence is 30 seconds.** Agent-decided, promoted from prose. The number appears exactly once in the intent, as an aside inside the decision record about API volume (*"roughly two writes per minute"*). Every pass criterion is evaluated against it, so it is stated as a requirement rather than inferred from a parenthesis. Realised as `FR1`. |
| D11 | ratified | v0.1 | **The Sheets route is `google-api-python-client`, the official client.** Ratified 2026-09-10 by the owner, **against the agent's recommendation of `gspread`.** The intent reserved this choice for the spec explicitly — *"the available libraries differ substantially in difficulty for a learner"* — and the owner owns the learning curve under `D1`. The agent's case for gspread was a smaller surface: three-line service-account auth, `append_rows` as one call. The owner's case for the official client is that what is learned maps onto Google's own documentation and onto every other Google service later. **Stated cost:** discovery documents, `spreadsheets().values().append(...).execute()` chains, and a `valueInputOption` the learner has to know exists — more Google-specific yak-shaving than transferable Python, which is the trade the intent's revised ownership split set out to avoid. Realised as `FR7`. |
| D12 | ratified | v0.1 | **`docs/intents/mesh-desktop-client.md` is a baseline and is not updated to match reality.** Moved there from `docs/intent.md` on 2026-09-10 — its own header already named that path, and `turing-review:D49` plus the plural-directory rule require it. A change in what is wanted is a `D<n>`; the register holds it, not the intent. |
| D13 | proposed | v0.1 | **A single `Fake` radio interface is the test seam, written by the agent as scaffold.** No test may touch the V4 — a suite that needs hardware on the LAN is not a suite. Under `D2` this is rung one, so the fake is scaffold and therefore the agent's; the agent's own view, recorded because it lost, is that writing it is where dependency injection stops being a phrase and is the most instructive object in v0.1. **Proposed, not ratified:** it is a direct consequence of `D2` but the owner has not been asked. |

| D14 | ratified | v0.5 | **The daemon is an asyncio service exposing FastAPI + uvicorn, with WebSocket for daemon→client push and plain HTTP for client→daemon commands.** Ratified 2026-09-10 by the owner. **Three decisions in one row, deliberately** (`turing-review:D65` — a row naming the winner without naming what it won is half a decision): *framework* is FastAPI + uvicorn; *transport* is WebSocket for push and HTTP for commands; *concurrency model* is asyncio. Recording only the framework would have left `O7` looking closed while the protocol was still unnamed. **The deciding argument is legibility, not ergonomics:** FastAPI generates a browsable OpenAPI page, and that page is the daemon's own legibility surface — the vision sentence requires the health of the client to be knowable, `FR20` requires backend-reachable and radio-reachable to be separately visible, and a URL a human can open at 11pm to read what the daemon believes is that, at no extra cost. Pydantic also makes the wire contract readable *as a contract*, which matters under `D1` where the owner reviews Python he did not write. **Rejected, with reasons:** Flask — synchronous, no native WebSocket, the wrong shape for a push-driven mesh where packets arrive unsolicited via pubsub; bare `websockets` — hand-rolled routing, auth and serialization for no gain; Starlette alone — FastAPI minus the generated API page, which is the thing being bought. **Verified before ratification** per `turing-review:D30`, because pydantic-core is a Rust extension and a missing 3.14 wheel would have put a compiler in the loop and made `RR6` materially worse: `$ uv pip install --dry-run fastapi uvicorn` → `Resolved 13 packages` · `fastapi==0.141.1` · `pydantic==2.13.5` · `pydantic-core==2.46.5` · `starlette==1.6.0` · `uvicorn==0.52.4`, all as downloads. **Known cost, recorded rather than discovered:** `RR10`. **Not installed until the v0.5 gate** — nothing in `C1` or `F1` imports a web framework, and a dependency nothing exercises is one nothing checks. Closes `O7`. **Does not close `O8`:** FastAPI's dependency injection is a good mechanism for guarding the API, but whether an unauthenticated localhost daemon holding the PSK is acceptable is a policy question and the owner's. Realised as `FR29`, `FR30`. |

| D15 | ratified | `C1` | **`D9`'s premise was false: this repository has a GitHub remote, and `C3` is unblocked.** The remote is `upstream` → `https://github.com/martin-gleason/mac_mesh_client.git`, carrying `main` at `8de5664`. **`D9` asserted "this repository has no remote" and the agent never ran `git remote -v` before writing it** — `git status` and `git ls-files` were run, neither of which shows remotes, and the absence of an `origin` was taken for the absence of any remote. That is `turing-review:D30` exactly: a decision asserting what an external system can do, ratified without running the command that would confirm it, and it is *most* needed where it feels least needed. Evidence, run 2026-09-10: `$ git remote -v` → `upstream https://github.com/martin-gleason/mac_mesh_client.git (fetch/push)`; `$ git ls-remote --heads upstream` → `8de5664... refs/heads/main`. **What survives from `D9`:** the pre-commit gates stay, and they are still the primary surface. **What does not:** CI is not blocked, because nothing under `tests/` touches the radio — the suite is fake-backed by rule, so a hosted runner can run all of it. Closes `O5`; `RR4` gains a route to closure; `C3` moves from blocked to open. **The ratified spec's `## Stack` still reads "no remote exists on this repository" and is not edited** — it is immutable, the register outranks it where they conflict, and this row is that conflict. |

---

## Risks (RR)

| ID | Risk | Likelihood | Impact | Mitigation | Owner | Status |
|---|---|---|---|---|---|---|
| RR1 | **A persistently held TCP connection degrades the V4.** Upstream `meshtastic/firmware#9632` reports a heap leak crashing a V4 roughly every 90 minutes on 2.7.15/2.7.19. Closed upstream, and this radio runs 2.7.26 — but a long-lived client is exactly the shape that provoked it. | unknown | blocks v0.5 | the soak (`FR1`–`FR10`) is the instrument built to answer this | agent | open |
| RR2 | **The soak logger's own network and auth dependency makes a data gap ambiguous** between radio failure and logger failure — and it fails silently, which is the flavour of failure this project exists to eliminate. | medium | corrupts the result | `FR7` local fallback · `FR9` log the logger's own write failures · `NFR9` separates the two retry rules | owner (accepted) | open |
| RR3 | **Google auth may not survive 48 unattended hours.** Named by the owner as a binding risk when he accepted the Sheets decision against recommendation. `D11` chose the client with the larger auth surface. | medium | loses the run | the two-hour dry run is the instrument; auth failure surfaces in the first ten minutes or not at all | owner | open |
| RR4 | **No CI.** Every check runs only where somebody remembers to run it. Detected by upstream `detect_risks.py`: `$ ls .github/workflows` → *(no workflows)*. | certain | silent drift | `D9` puts the gates in pre-commit. `D15` found the remote already exists, so `C3` is open rather than blocked — the suite is fake-backed by rule and runs anywhere | agent | open |
| RR5 | **Either endpoint can silently resolve to the wrong radio.** `192.168.0.231` is an unreserved DHCP lease and `meshtastic.local` is ambiguous with a repeater on the LAN. This already happened once: a desktop client froze, recovered onto the repeater, and said nothing. | high | the failure the project is named for | `FR12` binds to node identity; a mismatched identity is an error state, never a silent reconnect | agent | open |
| RR6 | **Python 3.14 is new enough that tutorial answers will not match the interpreter** — a real tax on a project whose purpose is learning the language. | medium | slows the owner | `D7` records it as a known cost; overturnable to 3.13 at any time | owner | open |
| RR7 | **Concurrent clients are unproven beyond seconds.** The daemon, `tools/mesh.py` and possibly the soak logger are 2–3 simultaneous TCP clients against the V4. What was tested is *two clients for seconds* — it says nothing about long-lived reconnect, radio reboot under a held connection, or ESP32-S3 memory pressure. The intent's "this app does not become a gatekeeper" is a non-goal with an untested cost. | medium | v0.5 | none yet; the soak measures one client, not three | owner | open |
| RR8 | **Credentials could enter the tree.** Two now: the PSK and the Google service-account key. | low | severe, irreversible | `NFR7` · `.gitignore` covers `service-account*.json`, `credentials.json`, `token.json`, `*.pem`, `*.key` · secret-scan hook under `C1` | agent | open |
| RR9 | **Two hypotheses for the observed instability and no evidence for either.** Earlier notes attribute intermittent V4 disconnects to brownout at high TX power with no battery attached; the owner's current view is that the problem was the desktop client. Carried in from outside the intent's session and unverified there. | — | misdiagnosis | `FR10` — each soak run states its power condition, holding the variable constant. This is variable control, not a claim about cause. | owner | open |

| RR10 | **The sync→async bridge at the `meshtastic` pubsub boundary.** The library's callbacks are synchronous and fire on its own thread; `D14` makes the daemon asyncio. Every packet must cross that boundary via a thread-safe queue or `run_coroutine_threadsafe`, and that bridge is the classic place this architecture drops or reorders messages — silently, which is the flavour of failure this project exists to eliminate. | medium | silent message loss in v0.5 | named here before it is written rather than found in review. **A mutation candidate:** drop a packet at the thread boundary and see whether anything notices. Not yet an `M<n>` — the rule is name it, then **run** it, then write the row. | agent | open |

| RR11 | **The assertion floor is gameable by lengthening a fixture.** 22 of 43 assertions come from one loop over a string's byte boundaries, so adding four bytes to that fixture buys 8 counts and pays for deleting four distinct assertions elsewhere with the gate green. *Assertions executed* is the right metric for a suite that stopped running and a weak one for a suite that shrank. | low | a shrinking suite passes the floor | named by the `C1` review (finding 10) and left open deliberately: a second metric is more machinery than the risk currently justifies. Revisit when the suite has more than one module. | agent | open |

---

## Owner items (O)

Outstanding items only the owner can close.

| ID | Item | Milestone | P | Status |
|---|---|---|---|---|
| O1 | **How much history, and pruned how?** Unbounded growth on a service that will run for years, versus a retention rule that discards the thing the app exists to preserve. Carried from the intent's open questions. | v0.5 | P1 | open |
| O2 | **What does the client show when the daemon is down** — an error surface, or a read-only view of the last known store? Carried from the intent's open questions. | v1.0 | P1 | open |
| O3 | **Adopt the process proposal that the intent is written when the conversation settles, not during it?** *"A document amended more than once is being used as a workspace, and a workspace is not a proto-spec."* Proposed in the intent's session, not adopted. If yes, it belongs **upstream** in `turing-review/conventions.md`, not local here. | — | P2 | open |
| O4 | **The repo is named `mac_mesh_client` but the ladder ships Windows at v1.1.** The platform is baked into a name that outgrows it. Rename is cheap now, annoying later. | v1.1 | P2 | open |
| ~~O5~~ | ~~**Is a GitHub remote intended for this repository?**~~ | `C1` | P1 | **closed 2026-09-10 — `D15`.** One exists and always did: `upstream`, `martin-gleason/mac_mesh_client`. The question was asked because the agent had not looked. |
| O6 | **What does a sent broadcast display, given broadcasts are never ACKed?** *"Whether your message actually left"* is in the vision sentence and has no `FR` behind it. Meshtastic distinguishes at least queued-to-radio, transmitted, ACKed and NAKed — and **the set differs by tab type**: a DM can be ACKed, a channel-0 broadcast cannot, ever. So the vision's own word means something structurally different on the two tab types `FR23` is otherwise careful to separate. | v1.0 | P0 | open |
| ~~O7~~ | ~~**What is the daemon↔client protocol?** WebSocket, SSE, HTTP polling, Unix socket.~~ | v0.5 | P1 | **closed 2026-09-10 — `D14`.** WebSocket for daemon→client push, HTTP for client→daemon commands, FastAPI + uvicorn on asyncio. |
| O8 | **What guards the daemon's own API?** `NFR5`'s three mechanisms defend against shoulder-surfers, strangers on channel 0, and the owner at 11pm. **None defends the interface.** A daemon on localhost holding the PSK is reachable by any process on the Mac and by any web page the owner has open. Token in `~/.config` beside the PSK, or accepted risk with a reason. **`D14` supplies the mechanism (FastAPI dependency injection) and deliberately does not supply the policy.** | v0.5 | P1 | open |
| O9 | **What shape is the message store, and which clock is authoritative?** SQLite (stdlib, and a good thing to learn) or JSONL. And: the radio's `rxTime` — which can be unset or drifted — or local receive time? Get the clock wrong and history sorts wrong in a way nobody notices for months. | v0.5 | P1 | open |
| O10 | **Does the daemon tolerate `tools/mesh.py` operating concurrently, or become the sole writer?** The intent says it does not become a gatekeeper; `RR7` is the cost of that. | v0.5 | P1 | open |
| O11 | **Google Cloud console work needs the owner at the keyboard.** The intent assigns credential plumbing to the agent — service-account creation, API enablement, key placement, sheet permissions — but project creation and billing consent cannot be delegated. | v0.1 | P0 | open |
| ~~O12~~ | ~~**Ratify `docs/specs/mesh-desktop-client.md`.**~~ | `C1` | P0 | **closed 2026-09-10 — gate `G2`.** The owner ratified it as written. The spec is now immutable; amendments are `D<n>` rows. |
| O13 | **Acknowledge the upstream instruction changes.** `turing-review`'s `H12` reports 4 unacknowledged files after `turing-review:D69` — `conventions.md`, `CLAUDE.md`, `SKILL.md`, `conventions.starter.md`. Acknowledging is the owner's act; an agent that acknowledges its own instruction changes has built a loop with no human in it. | — | P1 | open |

---

## Gates (G)

A gate is an **event**, not a place — but the event has to be recorded somewhere or it
did not happen. `turing-review:D22`: a yes said aloud and never written down is the
signature failure this discipline exists to stop.

| ID | Gate | Date | Status |
|---|---|---|---|
| G1 | **Intent approved.** `docs/intents/mesh-desktop-client.md` carries status `approved`, which is where this gate is recorded. | 2026-09-10 | closed |
| G2 | **Spec ratified.** Crossed aloud by the owner — *"spec is approved"* — and written down the same turn. **The requirement baseline froze here at `FR1`–`FR30` and `NFR1`–`NFR9`** (counted from the spec, not asserted: `grep -c '^| \*\*FR' docs/specs/mesh-desktop-client.md` → 30, `NFR` → 9). Every requirement after this is a `D<n>`. | 2026-09-10 | closed |
| G3 | **`C1` gate — build the harness.** Crossed aloud by the owner — *"begin c1"* — and written down before the first line of code. `docs/plans/C1.md` was written and waiting beforehand, which is the point of the gate: it gave the owner a moment to say *don't build that* while saying so was still cheap. No question was left open at the crossing. | 2026-09-10 | closed |

---

## Hooks (H)

Built under `C1` and `C2`. **Prove every hook by breaking it first** — a hook that has
never failed is a hook nobody knows works. Nothing below has been observed to fail yet,
and that is stated rather than assumed.

| ID | Hook | Surface | Protects | Status |
|---|---|---|---|---|
| H1 | suite runs; count of **executed** assertions reported | `C1` run + count | an exit code cannot show a suite that stopped running | **built, proved.** `count: pass — 43 assertion(s) executed`. Proved by removing `enable_assertion_pass_hook` → `0`, rc 1. |
| H2 | count may not fall below a floor | `C1` floor | a shrinking suite is blind, not clean | **built, proved.** Proved twice: floor raised to 999 → rc 1; a test deleted, 34 vs 38 → rc 1. |
| H3 | at least one named mutation per protected behaviour | `C1` mutate | `NFR8` | **built, proved.** 4 of 4 caught. Proved by renaming a named test → `MISATTRIBUTED`, rc 1. |
| H4 | gates run **after** the last edit | `C1` pre-commit | gates satisfied in advance and then edited past are not gates | **built, proved.** Fires on a real `git commit`; refused a staged credential and created no commit. |
| H5 | no secret in the diff | pre-commit | `NFR7`, `RR8` | **built, proved.** Refused a staged service-account key and six PSK shapes the first version missed. |
| H6 | no register ID in a commit subject | commit-msg | the two-tier ID grammar | **built, proved.** Refused `feat(C1): D5 harness` on a real `git commit`; 10 accept/reject cases verified. |
| H7 | status page regenerates clean | `C2` | it cannot go stale | not built |
| H8 | every `FR` has a test; every test cites an `FR` or `D` | `C2` | drift, in both directions | not built |

---

## Mutations (M)

Named ways to break the code, each paired with the test that must catch it. **Named, then
run, before the row is written** — `caught at n/m` is evidence; *prevented by construction*
is an argument.

**Allocation-order slip, recorded rather than tidied away:** `M2`, `M3` and `M4` were
written into `scripts/mutate.py` before they had rows here — the code minted the ID, which
is the one-intake-path rule inverted. Caught by the `C1` adversarial review (finding 6).
The rows below are written after each mutation was applied to shipped code and the suite
was **seen** to fail — which is what `closed` means on these rows.

| ID | Status | Mutation | Caught by | Evidence |
|---|---|---|---|---|
| M1 | closed | Replace the runtime read of `DATA_PAYLOAD_LEN` with the literal `190` — the mistake this project actually made, carried in an approved intent until the constant was read out of the library. | `tests/test_budget.py::test_limit_is_read_at_call_time_not_baked_in` | caught, `3 failed, 8 passed` |
| M2 | closed | Count characters instead of bytes in `encoded_size`. | `tests/test_budget.py::test_encoded_size_counts_bytes_not_characters` | caught, `4 failed, 7 passed` |
| M3 | closed | Cut on a raw byte boundary in `truncate`, splitting a character in half. | `tests/test_budget.py::test_truncated_output_is_always_a_decodable_prefix_within_budget` | caught, `2 failed, 9 passed` |
| M4 | closed | **Hardcode `233`** — the value the library returns *today*, so every equality assertion still agrees and only a genuine runtime read fails. | `tests/test_budget.py::test_limit_is_read_at_call_time_not_baked_in` | caught, `1 failed, 10 passed`. **Added by the `C1` review**, which showed this mutation passed every gate before the runtime-read test existed. |

**The counts above are tests, not assertions** — stated because the convention's `caught at
446/447` form implies assertion counts and these are not that. `scripts/mutate.py` prints
the same caveat inline rather than letting the number imply more than it carries.

---

## Units

| ID | Unit | Kind | Milestone | Owner | Status |
|---|---|---|---|---|---|
| `C1` | Build the harness | chore | `C1` | agent | **built and reviewed 2026-09-10.** Six tasks done, `M1`–`M4` run, every gate proved by breaking it. Adversarial review logged at `docs/reviews/C1.md`: 10 findings, 6 major, all addressed. **Uncommitted** — awaiting the owner. |
| `C2` | Status page generator | chore | v0.1 | agent | not opened. Upstream `gen_status.py` writes only `turing-review`'s own page; `turing-review:D13` requires this one be generated, so this project needs its own. Plan written at its gate. |
| `C3` | CI | chore | v0.1 | agent | **open** — unblocked by `D15`. Runs the whole suite plus `count --check`; no hardware needed, because nothing under `tests/` touches the radio. Plan written at its gate. |
| `F1` | The soak test tool | feature | v0.1 | mixed — see `D1`, `D2` | not opened |

-----
2026-09-10

#AI/Claude
