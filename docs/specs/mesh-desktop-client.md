# Spec — Mesh Desktop Client

**Status:** **ratified 2026-09-10 by the owner.** Gate `G2`, recorded in
`docs/plans/00-register.md` § Gates. Written by the agent from
`docs/intents/mesh-desktop-client.md` (approved) and the owner's answers in that session;
the vision sentence is the owner's own words. **The agent never ratifies the contract it is
held to** — this line records the owner's yes, and nothing below it was changed to add it.

**This is a baseline, and it is now frozen. It is not updated to match reality.** The
requirement list closed at ratification: **`FR1`–`FR30` and `NFR1`–`NFR9`. The list does not
grow past those.** A new requirement after this point is a `D<n>` in
`docs/plans/00-register.md` — behaviour traces to *a spec requirement **or** a numbered
ratified decision*, and **where the two conflict the register wins.** If this file could
keep absorbing requirements there would be nothing fixed for drift to be measured from,
which is the whole of `Drift = built − (spec + ratified deltas)`.

Reading only this file gives you the baseline, not the build.

> Register IDs from the upstream process repository are written qualified —
> `turing-review:D33` — per `turing-review:D64`. A bare `D<n>` always means this project's.

---

## Vision sentence

> **A desktop Meshtastic client that makes the state of things legible — the health of the
> client, the health of the network, who you are talking to, and whether your message
> actually left.**

The owner's words, carried verbatim from the intent. The load-bearing word is **legible**,
and it is a filter rather than a description: every proposed feature answers *does this make
state knowable?* Tabs pass. Node aliases pass. A theme picker does not — it is permitted,
not justified.

**This sentence is the only thing here a script cannot check.** It is what a reader holds
the built thing against at a gate, which is why it stays one sentence.

---

## Stack

Baseline. A different language, runner or layout is a `D<n>`, not a tidy-up.

- language: Python 3.14.7, pinned in `.python-version`, managed with `uv` 0.9.18 (`D7`)
- framework: none for v0.1 — the soak tool is standard library plus `meshtastic` 2.7.11 and
  `google-api-python-client` (`D11`). **v0.5 adds FastAPI + uvicorn on asyncio** (`D14`),
  installed at the v0.5 gate and not before. React in a Tauri shell arrives at v1.0 and is
  not begun until v0.5 is ratified.
- runner: `pytest` (`D6`)
- layout: `src/mesh_client/`, tests in `tests/` (`D8`)
- ci: none today — local pre-commit only (`D9`). No remote exists on this repository, and
  no hosted runner can reach `192.168.0.231`. `C3` opens if `O5` says yes.

**Third-party dependencies need a ratified `D<n>`.** Six are ratified above — `meshtastic`,
`google-api-python-client`, `pytest`, `fastapi`, `uvicorn`, and `pydantic` as FastAPI's own
— and the rest of the tree is standard library.

---

## Version ladder

Set by the owner in the intent. Each rung is separately shippable and separately provable,
which is the property that makes it better than one v1.0.

| Rung | Contents | Done when |
|---|---|---|
| `C1` | Python-only harness: run · count · floor · one mutation · pre-commit | a check is proven by breaking it |
| **v0.1** | the soak test tool | it runs unattended and produces a log worth trusting |
| *(gate)* | the soak **result** | 48h elapsed against the criteria below, declared beforehand |
| **v0.5** | the Python backend, complete | owner ratifies |
| **v1.0** | Tauri shell + React frontend, macOS | — |
| **v1.1** | Windows | — |

The soak **build** and the soak **result** are deliberately separate: the tool can ship
while the answer is still two days away. **Tauri work does not begin until v0.5 is complete
and ratified.**

---

## Functional requirements

Every `FR` traces forward to a test and backward to this document or a ratified `D<n>`.
Anything tracing to neither is drift **by definition, not by judgement**.

**`FR` numbers are allocated in the order they were decided, not in section order.** `FR29`
and `FR30` sit in the v0.5 block because that is where they belong, and they carry the
numbers that were free when `D14` was ratified. **They are identifiers, not an index: gaps
and out-of-order numbers are legal and permanent, and renumbering to tidy the sequence would
break every citation pointing at them.**

### v0.1 — the soak test tool

| ID | Requirement |
|---|---|
| **FR1** | Hold one TCP connection to the V4 and sample its state on a fixed cadence of **30 seconds** (`D10`). |
| **FR2** | Run in two ordered windows: **36h passive (receive-only), then 12h active (heartbeats added)** (`D4`). Ordering is load-bearing — passive first, or a failure in the active window cannot be attributed between elapsed time and self-inflicted load. |
| **FR3** | In the active window, send heartbeats on a cadence in tens of minutes with `hop_limit` reduced so the mesh does not rebroadcast test traffic. Every send is timestamped. |
| **FR4** | Record per sample: node count, node identity, radio uptime counter, reported free heap, connection state. |
| **FR5** | Record **position packets as a count only. No coordinates are stored** — aggregating 48h of positions for ~215 nodes creates a dataset that did not previously exist, and no pass criterion needs it. |
| **FR6** | **Reconnect to the radio with capped backoff** after a disconnect. Every disconnect **and every reconnect** is logged as its own timestamped event (`D3`). |
| **FR7** | Write batched samples to a Google spreadsheet via `google-api-python-client` (`D11`), with a **local file fallback** when a remote write fails, so the sample lands somewhere. |
| **FR8** | Flush pending batches on shutdown. Without this the tail of the run is lost. |
| **FR9** | Log the logger's **own write failures**, so a gap in the data is attributable. *"Logger could not write"* must be distinguishable from *"radio was down"*, or the criteria below cannot be evaluated. |
| **FR10** | State the **power condition** — TX power setting, battery attached or not — as part of the result. Variable control, not a claim about cause. |

### v0.5 — the Python backend

| ID | Requirement |
|---|---|
| **FR11** | Own the radio connection as a **daemon**, running independently of any window. |
| **FR12** | Connect to the V4 **by node identity** — node number `463889888` (`!1ba665e0`). An endpoint answering with any other identity is an **error state, surfaced; never a silent reconnect**. |
| **FR13** | Store one representation of that identity and render the other. `0x1BA665E0` = 463,889,888 are one value; storing both invites them to disagree. |
| **FR14** | Persist message history so it survives app restart **and radio reboot**. The radio is not a message store. |
| **FR15** | Resolve a display name in this order: **owner-assigned alias → node `longName` → node `shortName` → node id.** First non-empty wins. The node id is the floor and always exists, so nothing is ever nameless. |
| **FR16** | Rename any node, persisted locally. |
| **FR17** | Compute the remaining byte budget for a message, reading the limit from **`mesh_pb2.Constants.DATA_PAYLOAD_LEN` at runtime** — never a hardcoded constant (`D5`). Bytes, not characters: UTF-8 makes these differ and a naive slice can split a character. |
| **FR18** | Rate-limit transmission. Airtime is shared and a UI makes transmitting effortless; this is a requirement, not a nicety. |
| **FR19** | Implement **one transport — TCP/WiFi — behind a transport interface.** The v1 deliverable is the interface; one implementation proves it. |
| **FR20** | Report **backend reachable** and **radio reachable** as two distinct statuses. The daemon architecture makes the first a first-class state the client must display. |
| **FR29** | Expose the daemon over **WebSocket for daemon→client push and plain HTTP for client→daemon commands** (`D14`). The mesh is push-driven — packets arrive unsolicited via pubsub — so polling is structurally the wrong shape. |
| **FR30** | Serve a **browsable API description** at a known local URL (`D14`). This is not developer convenience: it is the daemon's own legibility surface, and it is how a human answers *what does the backend currently believe* without a debugger. |

### v1.0 — the client

| ID | Requirement |
|---|---|
| **FR21** | Tabs — channels and direct messages in one flat strip. |
| **FR22** | **A DM tab does not exist until a direct message arrives.** The node roster and the tab strip are therefore separate structures. |
| **FR23** | Channel identity and tab type are distinguishable by **shape and persistent colour before the label is read** — channel vs. DM, public vs. private. |
| **FR24** | Display the byte budget from `FR17`. |
| **FR25** | **Discreet mode** — hides content and node names from shoulder-surfers, screenshots and demos. Display only: transmits nothing, changes nothing on the network. |
| **FR26** | **Exposure controls** — **per-channel policy**, not a global mode, governing what leaves the machine: location, real names, presence. |
| **FR27** | **Safe defaults** — confirmation on public sends, private channel as default, destructive actions gated. |
| **FR28** | Themes, bounded by `NFR3`. |

---

## Non-functional requirements

| ID | Requirement |
|---|---|
| **NFR1** | **Runs unattended.** The daemon survives the window being closed and does not require a human at the keyboard. |
| **NFR2** | **Airtime is shared.** No feature may make transmitting effortless without a rate limit in front of it. |
| **NFR3** | **Channel identity is not customizable.** Themes may change anything except the signals that tell the user where their words are about to go. Shape and colour are persistent identity, not decoration: they do not vary by theme, by state, or by user configuration. |
| **NFR4** | **Neither `192.168.0.231` nor `meshtastic.local` is an identity.** The address is an unreserved DHCP lease; mDNS is reliable only with a single Meshtastic device present and this LAN has a repeater. Both can silently resolve to the wrong radio. |
| **NFR5** | **The three privacy mechanisms are separate because they fail separately.** Discreet mode defends the user locally; exposure controls defend against strangers on channel 0; safe defaults defend against a new user, including the owner at 11pm. None substitutes for another. |
| **NFR6** | **Channel 0 is public**, roughly 215 nodes in range, and the private channel currently has nobody on it — so the owner will legitimately live on channel 0 for months. The requirement is not *hide the public channel*; it is that **channel identity stays unmistakable at a glance after habituation**. |
| **NFR7** | **No credential enters the repository.** The PSK and the Google service-account key live at `~/.config/`, mode `0600`. The sheet is not link-shared. |
| **NFR8** | **A test that has never been shown to fail is not evidence.** At least one mutation per behaviour the tests protect, recorded as `M<n>` with the test that catches it. |
| **NFR9** | **The soak's retry rules differ by target.** Retrying a *spreadsheet* write is correct. Reconnecting to the *radio* is governed by `FR6` and every reconnect is a logged event, never silent — a silent reconnect would paper over the failure the soak exists to hunt. |

---

## Soak pass criteria

**Declared before the run, not after.** The soak asks one question: *does a persistently
held TCP connection to the V4 degrade the radio over time?*

Event-based, not a percentage. A ratio was considered and rejected: 99% uptime could be one
29-minute outage or 200 three-second blips, which are different diagnoses, and the
percentage destroys the information the soak exists to collect.

| # | Criterion |
|---|---|
| 1 | **Zero radio reboots**, detected by the radio's reported uptime counter stepping *backwards*. Primary criterion; maps directly to the upstream heap-leak report. |
| 2 | **Zero unrecovered disconnects.** A disconnect not restored within **5 minutes** is unrecovered and fails the run. Recovered ones are data, not failures (`D3`). |
| 3 | **Node DB still populated at end.** A count collapsing toward zero is degradation even with the socket nominally alive. |
| 4 | **Reported free heap not trending monotonically down** across the run. |

**A two-hour dry run precedes the real run.** Auth, permissions, batching and column layout
fail in the first ten minutes or not at all; discovering them at hour 20 costs two days.

---

## Deliberately out of scope

Recorded with reasons, because an unreasoned cut gets re-litigated in code.

| Deferred | Why | Where |
|---|---|---|
| Firmware update scanning | A second product: board→firmware mapping, release fetching, and a flashing path that can brick hardware. `esptool` already exists. | v2 or never |
| "A variety of boards and firmwares" | Not a feature, a compatibility matrix. Untestable without the hardware in hand. | named hardware only |
| Serial transport | The v1 deliverable is the *interface*; one implementation proves it. | v1.1 |
| Bluetooth transport | Same reasoning, one step further out. | v1.2 |
| Weather / location share buttons | Makes transmitting effortless on shared airtime — the central risk — and location on channel 0 is ~215 strangers. | v1.5, gated by exposure controls |
| Windows support | Shipping one platform is what proves the process. A second target doubles packaging and CI before anything has been delivered. | v1.1 |
| Off-grid resilience | v1 depends on router, host machine and the V4's WiFi. Accepted knowingly. | v1.5 |
| MQTT transport | Blocked upstream; becomes an implementation behind the interface, not a rewrite. | post-v1 |

---

## Affected systems

- **Heltec V4** — base station, TCP/WiFi at `192.168.0.231` (DHCP lease, **not reserved**), firmware `2.7.26.54e0d8d`, region US, `LONG_FAST`, `hop_limit 3`, `CLIENT_BASE`, `ok_to_mqtt False`, MQTT disabled. This project **depends on** the V4 and names this firmware as the version it is built against.
- **A repeater** on the same LAN — the second mDNS responder, and the node the stalled desktop client silently attached to.
- **SenseCAP T1000-E** — portable node; configuration state not confirmed.
- **`tools/mesh.py`** (Pennyworth) — the existing CLI. Continues to work; this app does not become a gatekeeper for it. The cost of that non-goal is `RR7`.
- **Home Assistant / MQTT** — future consumer of the same radio. Unaffected by v1.

---

## Hook intentions

What the project intends to enforce mechanically. The mechanisms are built under `C1` and
`C2` and each is proved by being broken first.

| Intent | Protects |
|---|---|
| The suite runs and reports a **count of assertions that executed** | an exit code cannot show a suite that stopped running |
| A **floor** the count may not fall below | a shrinking suite is blind, not clean |
| At least one named **mutation** per protected behaviour | `NFR8` |
| A **pre-commit** that runs the gates after the last edit | gates satisfied in advance and then edited past are not gates |
| No register ID in a commit subject | the two-tier ID grammar |
| No secret in the diff | `NFR7` |
| The status page regenerates clean | it cannot go stale |
| Every `FR` has a test; every test cites an `FR` or a `D` | drift, in both directions |

-----
2026-09-10

#AI/Claude
