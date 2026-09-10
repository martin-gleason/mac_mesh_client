"""`F1-T1` · `D13` — the radio seam, and the fake that plugs into it.

**No test touches the V4** (`docs/conventions-local.md`). A suite that needs hardware on
the LAN cannot run on a train, cannot run twice in a row reliably, and its failures are
ambiguous between *the code is wrong* and *the radio is asleep*. So the sampler takes its
radio as a **dependency** rather than constructing a `TCPInterface`, and everything under
`tests/` reaches a radio only through `FakeRadio`.

The check on that rule is cheap and anybody can perform it: **`uv run pytest -q` must pass
with the V4 powered off.** Unplug it.

## What lives here, and what deliberately does not

`Snapshot` is *what the radio reports*. It carries no timestamp, because the clock belongs
to the sampling loop (`F1-T3`) and is injected there — a test that takes 48 hours is not a
test. It carries no coordinates, because `FR5` says position packets are counted and never
located, and **a record with no field to put a coordinate in is a stronger guarantee than a
rule about not filling one in.**

Turning a `Snapshot` into the row that reaches the spreadsheet is `F1-T2`, and is not here.

## The five degradation shapes

`RR1` is the reason this feature exists: a persistently held TCP connection may degrade the
V4. The shapes that would show it are all but impossible to provoke on real hardware to
order — you cannot ask a radio to leak heap for ninety minutes on cue. Each is one method:

| Shape | Method |
|---|---|
| a reboot — the uptime counter steps backwards | `reboot()` |
| free heap trending down | `set_heap_drift(-n)` |
| the node DB collapsing toward zero | `set_node_drift(-n)` |
| a disconnect that recovers | `disconnect(recover_after=n)` |
| a disconnect that never recovers | `disconnect(recover_after=None)` |

A sixth is here because `FR4` records node **identity** and `RR5` is the failure this
project is named for — an endpoint answering as a different radio: `answer_as()`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

# `FR4` · `FR12`. The V4 this project is built against, in both renderings. `FR13` says
# store one and render the other, so these are here as the fixture's default rather than
# as a pair anything is expected to keep in step.
V4_NODE_ID = 463889888
V4_NODE_ID_HEX = "!1ba665e0"


@dataclass(frozen=True, slots=True)
class Snapshot:
    """One observation of the radio's state. `FR4`, `FR5`.

    **Frozen.** A sample that can be edited after the fact is not evidence, and a 48-hour
    run is exactly the situation where a mutated record would never be noticed.

    **The telemetry fields are `None` while disconnected, and that is the point.** A
    disconnect produces a `Snapshot` like any other rather than a missing row, so a gap in
    the data is *attributable* — `RR2` is the risk that it is not, and a row saying
    `connected=False` is distinguishable from no row at all, which is what a logger that
    could not write leaves behind.
    """

    connected: bool
    node_id: int | None
    node_count: int | None
    uptime_s: int | None
    free_heap_bytes: int | None

    # `FR5`: **a count, never a location.** Client-side and cumulative for the run, so it
    # is not `None` while disconnected — the tally so far is still true, and zeroing it
    # would invent a drop that did not happen.
    position_packets: int


@runtime_checkable
class Radio(Protocol):
    """What the sampler needs from a radio, and nothing more.

    Deliberately one method. The real `TCPInterface` adapter arrives with `F1-T7`; its
    whole job is to translate a dead socket into `connected=False` rather than letting an
    exception escape, because the loop above it must keep sampling across a disconnect.
    """

    def snapshot(self) -> Snapshot:
        """The radio's current state, as observed now."""
        ...


class FakeRadio:
    """A radio that degrades on command. `D13`.

    Every mutator takes effect from the **next** `snapshot()` call, so a test reads like
    the timeline it is describing:

        radio = FakeRadio()
        before = radio.snapshot()
        radio.reboot()
        after = radio.snapshot()
        assert after.uptime_s < before.uptime_s

    **The radio's own state advances whether or not anyone is connected to it.** Uptime
    keeps climbing through a disconnect, so a reconnect that shows uptime jumped by the
    elapsed time is distinguishable from one that shows it back near zero — the first is a
    socket that dropped, the second is a radio that rebooted, and `F1-T4` has to tell them
    apart. Position packets are the exception: they accrue only while connected, because a
    dead socket delivers nothing.
    """

    def __init__(
        self,
        *,
        node_id: int = V4_NODE_ID,
        node_count: int = 215,
        uptime_s: int = 3600,
        free_heap_bytes: int = 180_000,
        cadence_s: int = 30,
        position_packets: int = 0,
    ) -> None:
        # ~215 nodes in range and a cadence of 30s (`D10`) are this mesh's real numbers.
        # Defaults that match the field mean a test that passes here is describing the
        # radio the soak will actually run against.
        self._node_id = node_id
        self._node_count = node_count
        self._uptime_s = uptime_s
        self._free_heap_bytes = free_heap_bytes
        self._cadence_s = cadence_s
        self._position_packets = position_packets

        self._initial_free_heap_bytes = free_heap_bytes
        self._connected = True
        self._recover_in: int | None = None
        self._heap_drift = 0
        self._node_drift = 0
        self._position_rate = 0

        #: How many times `snapshot()` has been called. A test asserting a 48-hour run
        #: produced 5,760 samples needs this, and counting from outside is one more thing
        #: to get wrong.
        self.samples_taken = 0

    # -- observation ------------------------------------------------------------------

    def snapshot(self) -> Snapshot:
        """Advance the radio one cadence and report what is visible from here."""
        self.samples_taken += 1
        self._maybe_recover()
        self._advance()

        if not self._connected:
            return Snapshot(
                connected=False,
                node_id=None,
                node_count=None,
                uptime_s=None,
                free_heap_bytes=None,
                position_packets=self._position_packets,
            )

        return Snapshot(
            connected=True,
            node_id=self._node_id,
            node_count=self._node_count,
            uptime_s=self._uptime_s,
            free_heap_bytes=self._free_heap_bytes,
            position_packets=self._position_packets,
        )

    def _maybe_recover(self) -> None:
        if self._connected or self._recover_in is None:
            return
        if self._recover_in <= 0:
            self._connected = True
            self._recover_in = None
        else:
            self._recover_in -= 1

    def _advance(self) -> None:
        self._uptime_s += self._cadence_s

        # Clamped at zero on both: a radio cannot report negative free heap and a node DB
        # cannot hold fewer than no nodes. Clamping here rather than in the assertion
        # means a drift steep enough to overshoot still produces the *shape* being asked
        # for — a collapse toward zero, not through it.
        self._free_heap_bytes = max(0, self._free_heap_bytes + self._heap_drift)
        self._node_count = max(0, self._node_count + self._node_drift)

        if self._connected:
            self._position_packets += self._position_rate

    # -- the degradation shapes -------------------------------------------------------

    def reboot(self) -> None:
        """The uptime counter steps backwards. Pass criterion 1 watches for exactly this.

        Free heap returns to its starting value too, because a reboot is the one event
        that genuinely recovers a leak — which is what makes an unattended reboot able to
        *hide* one. Heap drift is left in place: a radio that leaks will start leaking
        again, and a fake that quietly cured it would let a test claim a leak was fixed.
        """
        self._uptime_s = 0
        self._free_heap_bytes = self._initial_free_heap_bytes

    def set_heap_drift(self, bytes_per_sample: int) -> None:
        """Free heap moves by this much each sample. **Negative leaks.**

        Signed and one method rather than a `leak_heap()` and a `recover_heap()`, so a
        test cannot set both and leave the reader to work out which won.
        """
        self._heap_drift = bytes_per_sample

    def set_node_drift(self, nodes_per_sample: int) -> None:
        """The node DB grows or shrinks by this much each sample. **Negative collapses.**"""
        self._node_drift = nodes_per_sample

    def set_position_rate(self, packets_per_sample: int) -> None:
        """How many position packets arrive per sample, while connected. `FR5`."""
        self._position_rate = packets_per_sample

    def disconnect(self, *, recover_after: int | None = None) -> None:
        """Drop the connection.

        `recover_after` is a count of **samples spent disconnected** before the link
        returns. `None` — the default — never recovers, which is the shape that fails
        pass criterion 2 (`D3`: not restored within five minutes).

        Requiring the keyword is deliberate. `disconnect(3)` and `disconnect(None)` are
        opposite outcomes separated by one bare argument, and this is the fixture behind
        every reconnect test in `F1-T4`.
        """
        if recover_after is not None and recover_after < 0:
            raise ValueError(
                f"recover_after counts samples and cannot be negative: {recover_after}. "
                f"Pass None for a disconnect that never recovers."
            )
        self._connected = False
        self._recover_in = recover_after

    def reconnect(self) -> None:
        """Restore the link now, whatever `disconnect()` scheduled."""
        self._connected = True
        self._recover_in = None

    def answer_as(self, node_id: int) -> None:
        """The endpoint starts answering as a different radio. `FR4` · `RR5`.

        The failure this project is named for: `192.168.0.231` is an unreserved DHCP lease
        and `meshtastic.local` is ambiguous with a repeater on this LAN. It has already
        happened once — a desktop client froze, recovered onto the repeater, and said
        nothing. **A mismatched identity is an error state, surfaced; never a silent
        reconnect** (`FR12`).
        """
        self._node_id = node_id
