# Intent · Mesh Desktop Client

**Author:** Marty Gleason
**Status:** **approved** — 2026-09-10. Downstream work may advance on it.
**Lands at:** `docs/intents/mesh-desktop-client.md`
**Session:** 2026-09-10, chat. No code was written in this session. Where a finding was
tested, the sentence says how far the test went; where a fact came from outside this
session, the sentence says so.

---

## Vision sentence

> **A desktop Meshtastic client that makes the state of things legible — the health of the
> client, the health of the network, who you are talking to, and whether your message
> actually left.**

The word doing the work is **legible**. It is a filter, not a description: every proposed
feature must answer *does this make state knowable?* Tabs pass. Node aliases pass. A theme
picker does not — it is permitted, not justified.

### Framings considered and rejected

Kept deliberately, so the repository does not re-run this argument with less information
than the argument had.

- **A — "A desktop Meshtastic client with tabs and a real keyboard."**
  Rejected: describes the furniture. Nothing in it can adjudicate whether a feature belongs.

- **B — "A comfortable desktop client for the mesh."**
  Rejected, and the dangerous one. *Comfortable* has no failure condition, so every
  prettiness argument wins against it and the scope fence rots.

- **C′ — "…customizable, makes things clear and legible…"** (owner's first draft)
  *Customizable* was cut from the sentence and kept as a feature. It has B's defect — no
  failure condition — and it points opposite to *legible*: customization is what lets two
  channels be made to look alike. It survives as a capability, bounded by the constraint on
  channel identity below.

---

## Problem

The mesh is reachable from the phone and, in principle, from the Mac. In practice the
desktop path is opaque in three specific ways, each observed rather than hypothesised:

1. **The client's state is not knowable.** A Meshtastic desktop client froze hard enough to
   nearly require a reboot. On recovery it connected to a *different radio* — the repeater —
   and said nothing. The owner discovered it by noticing, not by being told.

2. **Node identity is unusable.** Nodes are addressed as `!1ba665e0`. Assigning readable
   names is enough of a chore that it does not get done, so the roster stays unreadable.

3. **There is no history and no navigation.** The radio is not a message store. Nothing
   survives a reboot, and there is no way to keep several conversations open and move
   between them.

A fourth followed from the first and is the same problem pointed elsewhere: **the mesh is
hard to diagnose.** Which node am I attached to, is it healthy, did that message leave, did
it arrive. This is not a separate role; it is legibility aimed at the network.

### A mechanism that makes (1) worse, not incidental

`meshtastic.local` is now ambiguous on this LAN. Upstream states mDNS is reliable only with
a *single* Meshtastic device present; there is now a repeater alongside the V4. The prior
handoff's recommendation — prefer `meshtastic.local` over the DHCP address — is therefore
**unsafe in this topology**, and either endpoint can silently resolve to the wrong radio.

---

## Proposed outcome

A Python backend running as a service, owning the radio connection, the message store, the
node aliases, the airtime budget and the rate limiting. A React frontend in a Tauri shell
attaches to it as a thin client. Python does the heavy lifting; the shell is a window.

### Version ladder

Set by the owner. Each rung is separately shippable and separately provable, which is the
property that makes it better than a single v1.0.

| Rung | Contents | Done when |
|---|---|---|
| `C1` | Python-only harness: run · count · floor · one mutation · pre-commit | A check is proven by breaking it |
| **v0.1** | The soak test tool | It runs unattended and produces a log worth trusting |
| *(gate)* | The soak **result** | 72h elapsed against pass criteria declared beforehand |
| **v0.5** | The Python backend, complete | Owner ratifies |
| **v1.0** | Tauri shell + React frontend, macOS | — |
| **v1.1** | Windows | — |

The soak **build** and the soak **result** are deliberately separate: the tool can ship
while the answer is still three days away. **Tauri work does not begin until v0.5 is
complete and ratified.**

### In scope for v1.0

- Tabs — channels and direct messages in one flat strip, IRC underneath, AIM in feel
- Node aliasing: rename any node, persisted locally
- Unmistakable channel identity, and unmistakable tab type
- Persistent message history surviving app restart and radio reboot
- Honest connection status bound to **node identity**, not to an address
- 190-byte budget display and rate limiting
- Runs unattended
- One transport — TCP/WiFi — implemented behind a transport interface
- Themes, last and bounded (see constraints)
- The three privacy mechanisms named below

### Deliberately out of v1.0

Recorded with reasons, because an unreasoned cut gets re-litigated.

| Deferred | Why | Where |
|---|---|---|
| Firmware update scanning | A second product: board→firmware mapping, release fetching, and a flashing path that can brick hardware. `esptool` already exists. | v2 or never |
| "A variety of boards and firmwares" | Not a feature, a compatibility matrix. Untestable without the hardware in hand. | Named-hardware only |
| Serial transport | The v1 deliverable is the *interface*; one implementation proves it. The second is cheap once the seam is right. | v1.1 |
| Bluetooth transport | Same reasoning, one step further out. | v1.2 |
| Weather / location share buttons | Makes transmitting effortless on shared airtime — the central risk — and location on channel 0 is ~215 strangers. | v1.5, gated by exposure controls |
| Windows support | v1.0 ships macOS. Shipping one platform is what proves the process; a second target doubles packaging and CI before anything has been delivered. | v1.1 |
| Off-grid resilience | v1 depends on router, host machine and the V4's WiFi. Accepted knowingly. | v1.5 |
| MQTT transport | Blocked upstream; becomes an implementation behind the interface, not a rewrite. | Post-v1 |

---

## Affected users and systems

**Users.** One, initially: the author. Brad now owns the V3 and is the intended second party
on a shared channel; the private channel currently has no other humans on it, so the only
channel with traffic is the public one. Any future user of the app is a third class of
affected user and is the reason safe defaults exist.

**Systems.**

- **Heltec V4** — base station, TCP/WiFi at `192.168.0.231` (DHCP lease, **not reserved**),
  firmware `2.7.26.54e0d8d`, region US, `LONG_FAST`, `hop_limit 3`, `CLIENT_BASE`,
  `ok_to_mqtt False`, MQTT disabled. This project **depends on** the V4 and names this
  firmware as the version it is built against.
- **A repeater** on the same LAN. Newly relevant: it is the second mDNS responder and the
  node the stalled client attached to.
- **SenseCAP T1000-E** — portable node; configuration state not confirmed in this session.
- **`tools/mesh.py`** (Pennyworth) — the existing CLI. Continues to work; this app does not
  become a gatekeeper for it.
- **Home Assistant / MQTT** — future consumer of the same radio. Unaffected by v1.
- **Pennyworth** — source of the prior handoff only. This is a **separate repository**: its
  `CLAUDE.md` governs a live house and none of its constraints apply here. Additionally, a
  separate repo is what puts `C1: build the harness` under test, which is the point of the
  exercise.

---

## Constraints

**Inherited from the radio and the medium**

- **Airtime is shared.** A UI makes transmitting effortless; that is the risk. Rate limiting
  is a feature requirement, not a nicety.
- **190 bytes.** The UI shows the budget rather than letting the user discover it. Bytes,
  not characters — UTF-8 makes these differ, and a naive slice can split a character.
- **Channel 0 is public**, roughly 215 nodes in range. **And the private channel currently
  has nobody on it**, so the owner will legitimately live on channel 0 for months. The
  constraint is therefore *not* "hide the public channel" — it is that **channel identity
  must remain unmistakable at a glance after habituation.**
- **The radio is not a message store.** Persistence is the app's, entirely.
- **`192.168.0.231` is a lease** and `meshtastic.local` is ambiguous. Neither is an
  identity. Connect to a node identity; a changed identity behind a known endpoint is an
  **error state, not a silent reconnect**.
- **The PSK never enters the repository.** Credentials at `~/.config/`, mode `0600`.

**Adopted in this session**

- **Architecture: daemon plus thin client.** The Python backend runs as a service,
  independent of the window. The Tauri client attaches to it and may be closed without
  interrupting the mesh. The stated unattended requirement wins over the simpler sidecar
  shape. Consequence: *is the backend reachable* becomes a first-class status the client
  must display, distinct from *is the radio reachable*.
- **Channel identity is not customizable.** Themes may change anything except the signals
  that tell the user where their words are about to go.
- **Shape and colour are persistent identity, not decoration.** A channel tab and a DM tab,
  and a public tab and a private tab, are distinguishable by shape and persistent colour
  before the label is read. These signals do not vary by theme, by state, or by user
  configuration.
- **The connection target is the V4, by node identity:** node number `463889888`, node id
  `!1ba665e0`. These are one value — `0x1BA665E0` = 463,889,888 — so **one representation is
  stored and the other rendered**; storing both invites them to disagree. An endpoint that
  answers with any other identity is an error state, surfaced, never a silent reconnect.
- **Display-name resolution order:** owner-assigned alias → node `longName` → node
  `shortName` → node id. First non-empty wins; the node id is the floor and always exists,
  so no tab is ever nameless.
- **A DM tab does not exist until a direct message arrives.** The node roster and the tab
  strip are therefore separate structures. A DM tab carries a resolved display name per the
  order above.
- **Privacy is three mechanisms, not one mode**, because they fail separately:
  - **Discreet mode** — defends the user locally. Hides content and node names from
    shoulder-surfers, screenshots and demos. Display only; transmits nothing, changes
    nothing on the network.
  - **Exposure controls** — defend against strangers on channel 0. Govern what leaves the
    machine: location, real names, presence. **Per-channel policy**, not a global mode.
  - **Safe defaults** — defend against new users, including the owner at 11pm.
    Confirmation on public sends, private channel as default, destructive actions gated.

**Process and ownership**

- **`C1` is a Python-only harness.** The first two rungs contain no Rust and nothing to
  package, so the Rust toolchain and macOS packaging join the harness as their own chore at
  v1.0. **Rust competence does not gate `C1`.** This closes the session's open question on
  the point without either side of it losing.
- **Learning dial — v0.1 (soak test): 50-50.** Mechanically: the agent authors the scaffold
  and the tests; the owner writes the implementations. The tests are the contract — a
  failing test is not a wrong test.
  - *Known property of this mechanic, recorded so it is chosen rather than discovered:* when
    the agent writes the scaffold, the design is already decided. The owner learns the
    language, not the arrangement. Acceptable for a first task; the next step up is a bare
    scaffold, not a higher percentage.
  - *Support-removal ladder, in this order:* scaffold + tests → tests only → owner writes
    the tests → nothing. Scaffold goes first because removing the tests instead would leave
    the owner filling blanks with no external signal of correctness.
- **Learning dial — v0.5 and beyond: agent-authored, owner reviews traditionally.** The one
  `owner: human` task inside v0.5 is the **byte-budget calculator**: pure, no I/O, no clock,
  no globals — testable without hardware, which is the lesson. Revisitable upward at the
  owner's discretion.
- **React is 100% agent-authored.**
- **No external definition of done.** This project is not anchored to a book, against the
  standing preference for one. Accepted knowingly: the scope fence above is what replaces
  the missing final chapter, and it is the only thing that does.

---

## What was tested, and how far

- **Concurrent TCP clients work.** Two `TCPInterface` clients held connections to the V4
  simultaneously. **This proves two clients for seconds, not five clients for days.** It says
  nothing about long-lived reconnect, radio reboot under a held connection, or ESP32-S3
  memory pressure. Upstream `meshtastic/firmware#9632` reports a heap leak with a persistent
  TCP client crashing a V4 roughly every 90 minutes on 2.7.15/2.7.19; it is closed and this
  radio runs 2.7.26, but a long-lived client is exactly the shape that provoked it.
  **Unverified until soaked.** The design consequence is already absorbed: supervised
  reconnect and honest health reporting are v1 requirements regardless of the outcome.
- **Sending works** on the configured channel from this radio, verified end to end.
- **The desktop client freeze and silent reattachment to the repeater** was observed by the
  owner. Cause not established.
- **Intermittent V4 disconnects, attributed in an earlier session to brownout at high TX
  power with no battery attached, are carried in from notes outside this session and are
  unverified here.** The owner's current view is that the observed problem was the desktop
  client rather than the radio. **These are two hypotheses and neither has evidence.** The
  soak test is the instrument that can distinguish them, and can only do so if the power
  condition is held constant — so each soak run **states its power condition** (TX power
  setting, battery attached or not) as part of the result. That is variable control, not a
  claim about cause.
- **Everything else in this document is a stated requirement or an inference, not a result.**

---

## Soak test specification (v0.1)

Declared before the run, not after. The soak asks one question: **does a persistently held
TCP connection to the V4 degrade the radio over time?** Everything below serves that.

### Run shape

- **48 hours total**, in two ordered windows:
  - **Passive window (~36h, first): receive-only.** No transmission from the logger. Any
    degradation observed here has one cause, uncontaminated by the instrument's own traffic.
  - **Active window (~12h, second): heartbeats added.** Send-path coverage on a known
    baseline. Proposed cadence in tens of minutes, `hop_limit` reduced so the mesh does not
    rebroadcast test traffic. Every send timestamped so failures can be correlated against it.
- **Ordering is load-bearing.** Passive first, or a failure in the active window cannot be
  attributed between elapsed time and self-inflicted load.
- **The power condition is stated as part of the result** — TX power setting, battery
  attached or not. This is variable control, not a claim about cause.
- **A two-hour dry run precedes the real run.** Auth, permissions, batching and column
  layout fail in the first ten minutes or not at all; discovering them at hour 20 costs two
  days.

### Pass criteria — event-based, not a percentage

A ratio was considered and rejected: 99% uptime could be one 29-minute outage or 200
three-second blips, which are different diagnoses. The percentage destroys the information
the soak exists to collect. (An earlier proposal of 99.99999% over 48h would have allowed
17 milliseconds of downtime across two days; a single five-second reconnect misses it by
roughly 300×.)

1. **Zero radio reboots.** Detected by watching the radio's reported uptime counter for a
   *backwards* step. This is the primary criterion and maps directly to the upstream
   heap-leak report.
2. **Zero unrecovered disconnects.** Every disconnect logged with timestamp and duration;
   recovered ones are data, not failures.
3. **Node DB still populated at end.** A count collapsing toward zero is degradation even
   with the socket nominally alive.
4. **Reported free heap not trending monotonically down** across the run.

### What is logged

- Nodes found (count, and node identity)
- Messages sent — active window only
- **Position packets: count only. No coordinates are stored.** Reconsidered during this
  session: aggregating 48 hours of positions for ~215 nodes into a durable file creates a
  dataset that did not previously exist, and none of the four checks need it.
- Radio uptime counter, reported free heap, connection state transitions
- **Write failures of the logger itself**, so a gap in the data is attributable — "logger
  could not write" must be distinguishable from "radio was down," or the four checks cannot
  be evaluated.

### Logging destination

**Direct to a Google spreadsheet.** Owner's ruling, taken against recommendation; see the
decision record below.

Required handling:

- A **local file as fallback** when a remote write fails, so the sample lands somewhere.
- **Service account credentials in `~/.config`, mode `0600`, never in the repository** — the
  existing PSK constraint applied to a file that behaves like a PSK. Sheet not link-shared.
- Batched writes rather than one call per sample.

**Clarification, because two rules could appear to collide:** *must not reconnect on
failure* applies to **the radio only**. Retrying a spreadsheet write is fine; reconnecting
to the radio would paper over the exact failure being hunted.

### Ownership within v0.1

Dial is 50-50; the split is by kind, revised at the owner's request during this session.

**Agent:** the scaffold, the tests, and the credential plumbing — service account creation,
API enablement, key placement, sheet permissions. This is console work with no Python in it
and nothing transferable.

**Owner:** all Python. The sampling loop, record construction, the Sheets client usage,
batching (including the flush-on-shutdown case, without which the tail of the run is lost),
and the failure/fallback path.

Rationale for the revision: API-client usage, batching and exception handling are general
Python skills that transfer to every future API; only the console setup is Google-specific
yak-shaving. **Noted as a consequence, not an objection:** v0.1 grew while the dial stayed
fixed, so this is a larger share of owner hours than the original estimate.

**Spec item:** the Python route to Sheets is a deliberate choice — the available libraries
differ substantially in difficulty for a learner — and belongs in `docs/specs/`, not in
whatever the agent reaches for first.

---

## Open questions

1. **How much history, and pruned how?** Unbounded growth on a service that will run for
   years, versus a retention rule that discards the thing the app exists to preserve.
2. **What does the client show when the daemon is down** — an error surface, or a read-only
   view of the last known store?
3. **Unratified process proposal:** *the intent is written when the conversation settles,
   not during it; a document amended more than once is being used as a workspace, and a
   workspace is not a proto-spec.* Proposed in this session, not yet adopted.

---

## Decisions taken against recommendation

Recorded so that a failure is diagnosed rather than re-argued from scratch.

- **Soak logging writes directly to a Google spreadsheet.** Recommended instead: local
  append-only CSV as source of truth, imported to Sheets afterward at no code cost, with a
  separate uploader only if live visibility was needed. **The stated risk:** the instrument
  acquires a network dependency, an API and an auth token, so a gap in the data becomes
  ambiguous between radio failure and logger failure — and it fails silently, which is the
  flavour of failure this project exists to eliminate. The binding risks are **auth
  surviving 48 unattended hours** and **transient network gaps eating samples**; an earlier
  claim in this session that API quota was a leading risk was **overstated and is withdrawn**
  — at a 30-second cadence the run is roughly two writes per minute. Owner accepted the risk
  with the four mitigations recorded in the soak specification.

---

## Findings from this session, for promotion

Carried because nothing survives a conversation except what is written down.

- **A fact was imported from outside the session and recorded as project context without
  saying so** (the 28 dBm brownout attribution). The causation was hedged; the underlying
  fact was not sourced. Corrected above. The general rule: hedge the provenance, not just
  the inference.
- **The draft was amended live across two turns**, which turned the conversation into
  document maintenance and let the artefact steer the discussion. This is the same failure
  as a register that grows while nothing ships. Open question 4 is the proposed remedy.
- **A constraint was written as settled ("not optional") rather than proposed.** The owner
  does not ratify what he was not offered.
- **Scope accreted after the fence was ratified** — two constraints and one open question
  were added by the author, not the owner. Individually defensible, collectively drift.

---

## Next

1. `docs/specs/` — stack, layout, runner, CI named; `D<n>` records for the transport
   interface, the daemon/thin-client architecture, and the display-name resolution order.
2. `C1` — Python-only harness. Also the point at which the editor's toolchain must be shown
   to agree with the harness's, which is why the interpreter check precedes it.
3. **v0.1** — soak test, 50-50, per the specification above. Two-hour dry run first; power
   condition fixed and stated before the real run.
4. **v0.5** — Python backend. Ratified before any Tauri work begins.
5. `docs/plans/00-register.md`, `CLAUDE.md` importing a vendored `docs/conventions.md`, and
   the adversarial reviewer in `.claude/agents/`.

UI design work belongs after the spec's data model is settled and before v1.0. "Make channel
identity unmistakable" is a visual problem worth solving on a canvas — but only once the
structure behind the tab strip exists.

-----
2026-09-10

#AI/Claude
