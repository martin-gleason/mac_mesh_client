// Created: 2026-10-24 11:15 -05:00 · Edited: 2026-10-24 11:15 -05:00
//
// `FR17` · `D5` — the byte budget, ported from `tests/test_budget.py` (`C4-T4`).
//
// Every fixture that touches encoding is **multi-byte on purpose**. A pure-ASCII string
// satisfies both a byte budget and a character count, so it distinguishes nothing.

import Testing
@testable import MeshKitCore

// 1 character, 2 bytes · 1 character, 4 bytes · 1 character, 2 scalars, 8 bytes.
// Chosen so bytes, scalars and characters disagree by a different amount in each.
let eAcute = "é"
let satellite = "🛰"
let flag = "🇺🇸"

@Test func theBudgetUsesTheLimitItWasGivenNotALiteral() {
    // Any literal fails this — 190, and equally 233, the value the protocol returns
    // today and so the likelier way to get it wrong.
    let budget = PayloadBudget(limit: 99)
    #expect(budget.remaining("") == 99)
    #expect(budget.fits(String(repeating: "a", count: 99)))
    #expect(!budget.fits(String(repeating: "a", count: 100)))
}

@Test func theProtocolLimitIsTheGeneratedConstant() {
    // Re-derives its expected value, so it proves the wiring reaches the right
    // constant — not that the constant is right. `harness protos` does that.
    #expect(PayloadBudget.protocolLimit == Constants.dataPayloadLen.rawValue)
    #expect(PayloadBudget().limit == PayloadBudget.protocolLimit)
}

@Test func theProtocolLimitIsNotTheUnsourced190() {
    // The regression test for the mistake this project actually made.
    #expect(PayloadBudget.protocolLimit != 190)
}

@Test func encodedSizeCountsBytesNotCharacters() {
    #expect(eAcute.count == 1)
    #expect(PayloadBudget.encodedSize(eAcute) == 2)
    #expect(satellite.count == 1)
    #expect(PayloadBudget.encodedSize(satellite) == 4)
}

@Test func remainingIsMeasuredInBytes() {
    let budget = PayloadBudget()
    #expect(budget.remaining("") == budget.limit)
    #expect(budget.remaining(satellite) == budget.limit - 4)
}

@Test func remainingGoesNegativeRatherThanClamping() {
    let budget = PayloadBudget()
    let over = String(repeating: satellite, count: budget.limit / 4 + 2)
    #expect(budget.remaining(over) < 0)
}

@Test func fitsAtTheBoundaryAndOneBytePastIt() {
    let budget = PayloadBudget()
    let pad = String(repeating: "a", count: budget.limit - 4)
    #expect(PayloadBudget.encodedSize(pad + satellite) == budget.limit)
    #expect(budget.fits(pad + satellite))
    #expect(!budget.fits(pad + "a" + satellite))
}

@Test func truncateReturnsTheInputUnchangedWhenItFits() throws {
    let text = "hello \(satellite)"
    #expect(try PayloadBudget().truncate(text) == text)
}

@Test func truncateNeverSplitsACharacter() throws {
    let budget = PayloadBudget()
    #expect(try budget.truncate(satellite, to: 3) == "")
    #expect(try budget.truncate("ab" + satellite, to: 4) == "ab")
    #expect(try budget.truncate("ab" + satellite, to: 6) == "ab" + satellite)
}

@Test func truncateNeverSendsHalfAFlag() throws {
    // A flag is two scalars of four bytes each. A cut at 4 bytes lands between them:
    // a scalar-boundary cut returns one regional-indicator letter; a character cut
    // returns nothing.
    #expect(try PayloadBudget().truncate(flag, to: 4) == "")
    #expect(try PayloadBudget().truncate(flag, to: 8) == flag)
}

@Test func truncatedOutputIsAlwaysAWholeCharacterPrefixWithinBudget() throws {
    // Checked at every byte boundary so no single lucky cap can make this pass.
    let text = "\(eAcute)\(satellite)ok\(flag)\(eAcute)"
    let budget = PayloadBudget()
    for cap in 0...PayloadBudget.encodedSize(text) {
        let cut = try budget.truncate(text, to: cap)
        #expect(text.hasPrefix(cut))
        #expect(PayloadBudget.encodedSize(cut) <= cap)
    }
}

@Test func truncateRefusesANegativeBudget() {
    #expect(throws: BudgetError.negativeBudget(-1)) {
        try PayloadBudget().truncate("anything", to: -1)
    }
}
