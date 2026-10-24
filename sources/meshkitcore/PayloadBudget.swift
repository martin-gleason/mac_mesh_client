// Created: 2026-10-24 09:41 -05:00 · Edited: 2026-10-24 10:09 -05:00
//
// The byte budget for one Meshtastic message. `FR17` · `D5`.
//
// **The limit comes from the protocol definitions, never a literal.** The approved intent
// carried `190`; the protocol says `233`. In Swift the value is compiled in from the
// generated protobufs, so what keeps it honest is `harness protos` — the generated code
// is pinned to the radio's firmware and fails the check if it drifts.
//
// **Bytes, not characters.** UTF-8 makes those differ, and a cut at a byte boundary can
// split a character in half.

/// What it costs to send a piece of text, measured against a byte limit.
public struct PayloadBudget: Sendable {
    /// The limit the Meshtastic protocol declares, in bytes.
    public static var protocolLimit: Int { Constants.dataPayloadLen.rawValue }

    /// The limit this budget measures against. Defaults to the protocol's; passing one
    /// is what lets a test prove the budget uses the limit it was given.
    public let limit: Int

    public init(limit: Int = PayloadBudget.protocolLimit) {
        self.limit = limit
    }

    /// The number of bytes `text` occupies on the wire.
    public static func encodedSize(_ text: String) -> Int {
        text.utf8.count
    }

    /// Bytes left. Negative once `text` is over — *how far over* is what a user needs
    /// to know, and clamping to zero throws it away.
    public func remaining(_ text: String) -> Int {
        limit - Self.encodedSize(text)
    }

    /// Whether `text` can be sent without truncation.
    public func fits(_ text: String) -> Bool {
        remaining(text) >= 0
    }

    /// The longest prefix of `text` that fits in `cap` bytes, whole characters only.
    ///
    /// A character here is what a person sees — a flag emoji is two Unicode scalars and
    /// eight bytes, and cutting between the scalars would send half a flag.
    public func truncate(_ text: String, to cap: Int? = nil) throws(BudgetError) -> String {
        let cap = cap ?? limit
        guard cap >= 0 else { throw .negativeBudget(cap) }
        var used = 0
        var end = text.startIndex
        for index in text.indices {
            let size = text[index].utf8.count
            if used + size > cap { break }
            used += size
            end = text.index(after: index)
        }
        return String(text[..<end])
    }
}

public enum BudgetError: Error, Equatable {
    case negativeBudget(Int)
}
