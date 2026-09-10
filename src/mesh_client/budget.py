"""The byte budget for a Meshtastic message.

`FR17` · `D5`. **The limit is read from the library at runtime and never hardcoded.**
The approved intent carried `190` as a stated constraint; the library enforces `233`
and raises `"Data payload too big"` above it. A literal here would be wrong today and
could go wrong again on a firmware or library bump, silently, in a daemon that runs
for days (`NFR1`).

**Bytes, not characters.** UTF-8 makes those differ, and cutting at a byte boundary
can split a character in half.
"""

from __future__ import annotations

from meshtastic import mesh_pb2


def payload_limit() -> int:
    """The maximum data payload the radio accepts, in bytes.

    Read at call time rather than import time, so a library upgraded underneath a
    long-running daemon cannot leave a stale value baked in.
    """
    return int(mesh_pb2.Constants.DATA_PAYLOAD_LEN)


def encoded_size(text: str) -> int:
    """The number of bytes `text` occupies on the wire."""
    return len(text.encode("utf-8"))


def remaining(text: str) -> int:
    """Bytes left in the budget. Negative once `text` is over it.

    Negative rather than clamped to zero: *how far over* is the thing a user needs
    to know, and clamping throws it away.
    """
    return payload_limit() - encoded_size(text)


def fits(text: str) -> bool:
    """Whether `text` can be sent without truncation."""
    return remaining(text) >= 0


def truncate(text: str, limit: int | None = None) -> str:
    """The longest prefix of `text` fitting in `limit` bytes, whole characters only.

    `limit` defaults to `payload_limit()`. Passing one explicitly is what lets this
    be tested at a boundary that lands mid-character without depending on the length
    of the radio's own limit.
    """
    cap = payload_limit() if limit is None else limit
    if cap < 0:
        raise ValueError(f"byte budget cannot be negative: {cap}")

    raw = text.encode("utf-8")
    if len(raw) <= cap:
        return text

    # Walk back a byte at a time until the prefix is valid UTF-8 again. At most
    # three steps, because no encoded character is longer than four bytes.
    # Written as a decode attempt rather than continuation-byte arithmetic because
    # the decoder is the authority on what a whole character is, and this file's
    # entire reason for existing is not restating a rule someone else owns.
    cut = raw[:cap]
    while cut:
        try:
            return cut.decode("utf-8")
        except UnicodeDecodeError:
            cut = cut[:-1]
    return ""
