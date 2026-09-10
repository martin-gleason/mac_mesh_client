"""`FR17` · `D5` — the byte budget.

Every fixture below that touches encoding is **multi-byte on purpose**. A pure-ASCII
string satisfies both a correct byte budget and an incorrect character count, so it
distinguishes nothing and a suite built on one is a tautology with a green tick.
"""

from meshtastic import mesh_pb2

from mesh_client import budget

# 1 character, 2 bytes. 1 character, 4 bytes. Chosen so byte length and character
# length disagree by a different amount in each case.
E_ACUTE = "é"
EMOJI = "🛰"


class _FakeConstants:
    DATA_PAYLOAD_LEN = 99


class _FakeProto:
    """Stands in for `meshtastic.mesh_pb2` with a limit no real radio would report."""

    Constants = _FakeConstants


def test_limit_is_read_at_call_time_not_baked_in(monkeypatch):
    """The actual requirement: `FR17`/`D5` say *read at runtime, never hardcoded*.

    Swapping the library out from under the module must change the answer. **Any**
    literal fails this — `190`, and equally the `233` the library happens to return
    today, which is the far likelier way to get this wrong. The test below asserts
    equality with the constant and cannot see that case at all, because it re-derives
    its expected value from the same expression under test.
    """
    monkeypatch.setattr(budget, "mesh_pb2", _FakeProto)
    assert budget.payload_limit() == 99
    assert budget.remaining("") == 99
    assert budget.fits("a" * 99)
    assert not budget.fits("a" * 100)


def test_limit_agrees_with_the_library_in_the_real_configuration():
    """Weaker than it looks, and kept for the one thing it does prove.

    This re-derives its expected value, so it cannot distinguish a runtime read from
    a literal that happens to match. It stays because it is the check that the wiring
    reaches the *right* constant rather than some other integer on the module.
    """
    assert budget.payload_limit() == mesh_pb2.Constants.DATA_PAYLOAD_LEN


def test_limit_is_not_the_unsourced_190():
    """The regression test for the mistake this project actually made.

    `190` sat in an approved intent as a stated constraint until the constant was
    read out of the library. This asserts the specific wrong answer stays wrong —
    the equality test above would also catch it, and two independent assertions on
    one historical defect is the cheapest insurance in the file.
    """
    assert budget.payload_limit() != 190


def test_encoded_size_counts_bytes_not_characters():
    assert len(E_ACUTE) == 1
    assert budget.encoded_size(E_ACUTE) == 2
    assert len(EMOJI) == 1
    assert budget.encoded_size(EMOJI) == 4


def test_remaining_is_measured_in_bytes():
    limit = budget.payload_limit()
    assert budget.remaining("") == limit
    assert budget.remaining(EMOJI) == limit - 4


def test_remaining_goes_negative_rather_than_clamping():
    """How far over matters. Clamping to zero throws that away."""
    over = EMOJI * (budget.payload_limit() // 4 + 2)
    assert budget.remaining(over) < 0


def test_fits_at_the_boundary_and_one_byte_past_it():
    """Multi-byte at the boundary, per this file's own rule.

    `fits()` is encoding-sensitive and was previously tested with `"a" * limit` —
    a pure-ASCII fixture that satisfies a byte budget and a character count equally,
    in the one test where the difference is the whole point.
    """
    limit = budget.payload_limit()
    pad = "a" * (limit - 4)
    assert budget.encoded_size(pad + EMOJI) == limit
    assert budget.fits(pad + EMOJI)
    assert not budget.fits(pad + "a" + EMOJI)


def test_truncate_returns_the_input_unchanged_when_it_fits():
    text = f"hello {EMOJI}"
    assert budget.truncate(text) == text


def test_truncate_never_splits_a_character():
    """Cut at 3 bytes through a 4-byte character: the whole character must go."""
    assert budget.truncate(EMOJI, limit=3) == ""
    assert budget.truncate("ab" + EMOJI, limit=4) == "ab"
    assert budget.truncate("ab" + EMOJI, limit=6) == "ab" + EMOJI


def test_truncated_output_is_always_a_decodable_prefix_within_budget():
    """The property, asserted on the output rather than on the model of it.

    Every cut across a multi-byte string must come back as real text, be a prefix of
    the original, and fit. Checked at every byte boundary so no single lucky cap can
    make this pass.
    """
    text = f"{E_ACUTE}{EMOJI}ok{E_ACUTE}"
    raw = text.encode("utf-8")
    for cap in range(len(raw) + 1):
        cut = budget.truncate(text, limit=cap)
        assert text.startswith(cut)
        assert budget.encoded_size(cut) <= cap


def test_truncate_refuses_a_negative_budget():
    try:
        budget.truncate("anything", limit=-1)
    except ValueError as exc:
        assert "negative" in str(exc)
    else:
        raise AssertionError("a negative budget should not be accepted")
