"""`F1-T1` · `D13` — the radio seam and the fake that plugs into it.

**The checkpoint this file exists to demonstrate:** a test drives a full sample cycle and
can produce all five degradation shapes, with no hardware and no network.

The second half of that sentence is not decoration, so it is asserted rather than asserted
*about* — see `test_a_full_cycle_runs_with_the_network_torn_out`, which removes the ability
to open a socket at all and then drives the cycle. Every other test here would pass just as
happily against a fake that quietly phoned home.
"""

import dataclasses
import socket

import pytest

from mesh_client.radio import V4_NODE_ID, FakeRadio, Radio, Snapshot

# `D10` — the soak's real cadence. Written once here so a test asserting "one cadence" and
# the fake's default cannot drift apart silently.
CADENCE_S = 30

# `D3` — "unrecovered" means not restored within five minutes. At a 30-second cadence that
# is ten samples, and that is the number pass criterion 2 is evaluated against.
UNRECOVERED_SAMPLES = 10


def test_a_full_sample_cycle_reports_every_field_FR4_requires():
    """`FR4`: node count, node identity, uptime counter, free heap, connection state.

    Asserted field by field rather than against a whole constructed `Snapshot`. An
    assertion that hand-builds its expected object re-derives what it is checking, and the
    failure message then names the whole record instead of the one field that moved.
    """
    radio = FakeRadio(node_count=215, uptime_s=3600, free_heap_bytes=180_000)

    sample = radio.snapshot()

    assert sample.connected is True
    assert sample.node_id == V4_NODE_ID
    assert sample.node_count == 215
    assert sample.uptime_s == 3600 + CADENCE_S
    assert sample.free_heap_bytes == 180_000
    assert sample.position_packets == 0
    assert radio.samples_taken == 1


def test_a_full_cycle_runs_with_the_network_torn_out():
    """**No test touches the V4**, and this is the one that proves it for this module.

    `socket.socket` is replaced with something that raises, so any attempt to open a
    connection — by this module or by anything it imports at call time — fails loudly
    inside the test rather than succeeding quietly against a radio that happens to be on
    the desk of whoever ran the suite.

    The other tests in this file are all satisfied by a fake that opens a socket and
    ignores it. This one is not, which is why the rule gets its own assertion instead of
    living in a docstring.
    """

    def refuse(*args, **kwargs):
        raise AssertionError(
            "a test opened a socket. The fake is the seam (`D13`) and no test may "
            "touch the V4 — `uv run pytest -q` must pass with the radio powered off."
        )

    original = socket.socket
    socket.socket = refuse
    try:
        radio = FakeRadio()
        radio.set_position_rate(2)
        radio.set_heap_drift(-500)
        radio.disconnect(recover_after=2)
        samples = [radio.snapshot() for _ in range(6)]
    finally:
        socket.socket = original

    assert len(samples) == 6
    assert [s.connected for s in samples] == [False, False, True, True, True, True]


def test_uptime_advances_by_exactly_one_cadence_per_sample():
    """The counter pass criterion 1 watches. If it does not move, nothing else means much."""
    radio = FakeRadio(uptime_s=0)

    uptimes = [radio.snapshot().uptime_s for _ in range(4)]

    assert uptimes == [CADENCE_S, 2 * CADENCE_S, 3 * CADENCE_S, 4 * CADENCE_S]


# -- the five degradation shapes ------------------------------------------------------


def test_shape_one_a_reboot_steps_the_uptime_counter_backwards():
    """Shape 1. Pass criterion 1 is *this*, and it holds regardless of what the socket did.

    That independence is the whole of `D3`'s argument: a reconnect cannot paper over a
    radio reboot, because the reboot is visible in a counter the socket has no say in.
    """
    radio = FakeRadio(uptime_s=90_000)
    before = radio.snapshot()

    radio.reboot()
    after = radio.snapshot()

    assert before.uptime_s == 90_000 + CADENCE_S
    assert after.uptime_s == CADENCE_S
    assert after.uptime_s < before.uptime_s


def test_a_reboot_returns_free_heap_to_its_starting_value():
    """The reason an unattended reboot can *hide* a leak, made reproducible.

    Heap drift survives the reboot deliberately: a radio that leaks starts leaking again,
    and a fake that quietly cured it would let a test claim a leak was fixed.
    """
    radio = FakeRadio(free_heap_bytes=180_000)
    radio.set_heap_drift(-10_000)
    radio.snapshot()
    leaked = radio.snapshot()

    radio.reboot()
    recovered = radio.snapshot()
    leaking_again = radio.snapshot()

    assert leaked.free_heap_bytes == 160_000
    assert recovered.free_heap_bytes == 170_000  # reset to 180_000, then one sample's drift
    assert leaking_again.free_heap_bytes == 160_000


def test_shape_two_free_heap_trends_down_and_stops_at_zero():
    """Shape 2 — `RR1`'s signature. Upstream `firmware#9632` is a heap leak.

    Clamped at zero rather than allowed negative: a radio cannot report less free memory
    than none, and a fake that produced `-20_000` would let a test pass against an
    implementation that never handled exhaustion.
    """
    radio = FakeRadio(free_heap_bytes=180_000)
    radio.set_heap_drift(-100_000)

    heaps = [radio.snapshot().free_heap_bytes for _ in range(4)]

    assert heaps == [80_000, 0, 0, 0]


def test_shape_three_the_node_db_collapses_toward_zero():
    """Shape 3. ~215 nodes in range is this mesh's real number, so the collapse starts there."""
    radio = FakeRadio(node_count=215)
    radio.set_node_drift(-100)

    counts = [radio.snapshot().node_count for _ in range(4)]

    assert counts == [115, 15, 0, 0]


def test_shape_four_a_disconnect_recovers_after_exactly_the_samples_asked_for():
    """Shape 4 — the recovered disconnect, which `D3` calls **data, not failure**.

    The count is asserted exactly. "Recovers eventually" is satisfied by an off-by-one,
    and `F1-T4` computes an outage duration from precisely this number.
    """
    radio = FakeRadio()
    radio.disconnect(recover_after=3)

    states = [radio.snapshot().connected for _ in range(5)]

    assert states == [False, False, False, True, True]


def test_shape_five_a_disconnect_that_never_recovers_stays_down():
    """Shape 5 — the one that fails pass criterion 2 (`D3`, five minutes).

    `recover_after=None` is the default, and it is the *dangerous* default on purpose: a
    test that forgets the argument gets the shape that fails, not the one that passes.
    """
    radio = FakeRadio()
    radio.disconnect()

    states = [radio.snapshot().connected for _ in range(UNRECOVERED_SAMPLES + 2)]

    assert states == [False] * (UNRECOVERED_SAMPLES + 2)
    assert radio.samples_taken == UNRECOVERED_SAMPLES + 2


def test_a_negative_recovery_count_is_refused_with_a_readable_message():
    """`disconnect(recover_after=-1)` is a typo, not a shape. Say so where it happens."""
    radio = FakeRadio()

    with pytest.raises(ValueError) as caught:
        radio.disconnect(recover_after=-1)

    assert "-1" in str(caught.value)
    assert "None" in str(caught.value)


# -- what a disconnect does and does not hide -----------------------------------------


def test_a_disconnect_produces_a_row_rather_than_a_gap():
    """`RR2`: a gap in the data must be **attributable**.

    A disconnected sample is a `Snapshot` like any other, with its telemetry `None`. That
    is distinguishable from no row at all — which is what a logger that could not write
    leaves behind (`FR9`) — and the two must never look the same at hour 40.
    """
    radio = FakeRadio()
    radio.disconnect()

    sample = radio.snapshot()

    assert sample.connected is False
    assert sample.node_id is None
    assert sample.node_count is None
    assert sample.uptime_s is None
    assert sample.free_heap_bytes is None


def test_uptime_keeps_climbing_through_a_disconnect_so_a_drop_is_not_a_reboot():
    """The distinction `F1-T4` is built on, and the reason the fake advances while blind.

    A socket that dropped and came back shows uptime **jumped by the elapsed time**. A
    radio that rebooted shows it back near zero. If the fake froze uptime while
    disconnected, both would look alike and the reconnect logic could not be tested at all.
    """
    radio = FakeRadio(uptime_s=90_000)
    before = radio.snapshot()

    radio.disconnect(recover_after=3)
    for _ in range(3):
        radio.snapshot()
    after = radio.snapshot()

    assert before.uptime_s == 90_000 + CADENCE_S
    assert after.uptime_s == before.uptime_s + 4 * CADENCE_S
    assert after.connected is True


def test_a_rebooted_radio_that_was_disconnected_still_shows_the_step_backwards():
    """The two events together — the case a real soak will actually produce.

    A radio that reboots drops the socket. What comes back must still be legible as a
    reboot, or criterion 1 is evaluated against a reconnect that hid it.
    """
    radio = FakeRadio(uptime_s=90_000)
    before = radio.snapshot()

    radio.disconnect(recover_after=2)
    radio.reboot()
    for _ in range(2):
        radio.snapshot()
    after = radio.snapshot()

    assert before.uptime_s == 90_000 + CADENCE_S
    assert after.uptime_s == 3 * CADENCE_S
    assert after.uptime_s < before.uptime_s


# -- `FR5` — counted, never located ----------------------------------------------------


def test_position_packets_are_counted():
    """`FR5`, the half of it that is a feature."""
    radio = FakeRadio()
    radio.set_position_rate(3)

    counts = [radio.snapshot().position_packets for _ in range(3)]

    assert counts == [3, 6, 9]


def test_a_snapshot_has_nowhere_to_put_a_coordinate():
    """`FR5`, the half that is a guarantee — and the stronger half.

    Aggregating 48 hours of positions for ~215 nodes creates a dataset that did not
    previously exist, and no pass criterion needs it. **A record with no field to put a
    coordinate in is a stronger guarantee than a rule about not filling one in**, so this
    asserts on the shape of the type rather than on the contents of one instance.

    Pinned as an exact set, not a substring scan. A scan for "lat" passes the day somebody
    adds `gps_fix`; this fails on any new field at all and makes the author say why.
    """
    fields = {f.name for f in dataclasses.fields(Snapshot)}

    assert fields == {
        "connected",
        "node_id",
        "node_count",
        "uptime_s",
        "free_heap_bytes",
        "position_packets",
    }


def test_position_packets_do_not_accrue_while_disconnected():
    """A dead socket delivers nothing, and the tally must not invent traffic.

    It also must not reset — the count so far is still true, and zeroing it would fake a
    drop that never happened.
    """
    radio = FakeRadio()
    radio.set_position_rate(5)
    radio.snapshot()

    radio.disconnect(recover_after=2)
    during = [radio.snapshot().position_packets for _ in range(2)]
    after = radio.snapshot()

    assert during == [5, 5]
    assert after.position_packets == 10


# -- the seam itself -------------------------------------------------------------------


def test_a_sample_cannot_be_edited_after_it_is_taken():
    """A record that can be rewritten is not evidence, and a 48-hour run is where nobody
    would notice."""
    radio = FakeRadio()
    sample = radio.snapshot()

    with pytest.raises(dataclasses.FrozenInstanceError):
        sample.free_heap_bytes = 1

    assert sample.free_heap_bytes == 180_000


def test_the_fake_satisfies_the_radio_protocol_the_sampler_depends_on():
    """`D13`: the sampler takes its radio as a dependency, so the fake must *be* one.

    Without this the seam is a convention rather than a type, and the real `TCPInterface`
    adapter in `F1-T7` could diverge from the fake with nothing to notice.

    **Weaker than it reads, and stated so rather than left to be discovered.** A
    `runtime_checkable` Protocol checks that the *method exists*, not that its signature
    or return type match. It catches a rename and nothing subtler. It has no mutation for
    that reason: breaking it means breaking every other test in the file, which would
    score as a kill while proving nothing about this assertion.
    """
    radio = FakeRadio()

    assert isinstance(radio, Radio)


def test_the_endpoint_can_answer_as_a_different_radio():
    """`RR5` · `FR12` — the failure this project is named for, made reproducible.

    It has already happened once: a desktop client froze, recovered onto a repeater on
    this LAN, and said nothing. Detecting it is `F1-T7`'s; **being able to stage it at all
    is this task's**, and it cannot be staged on hardware without a second radio and a
    DHCP lease nobody controls.
    """
    radio = FakeRadio()
    ours = radio.snapshot()

    radio.answer_as(11111111)
    theirs = radio.snapshot()

    assert ours.node_id == V4_NODE_ID
    assert theirs.node_id == 11111111
    assert theirs.node_id != ours.node_id
