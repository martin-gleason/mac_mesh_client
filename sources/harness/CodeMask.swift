// Created: 2026-10-24 10:09 -05:00 · Edited: 2026-10-24 10:09 -05:00
//
import Foundation

// `C4` review, finding 2. Text the compiler never sees must not be counted as a check.
// Blanks comments, string literals and `#if false` blocks to spaces, keeping every byte
// in place so line and column numbers still match llvm-cov's.
//
// Known limit, stated rather than hidden: only `#if false` is recognised. A check under
// any other inactive condition (`#if os(Linux)` on a Mac) is still counted.

enum CodeMask {
    static func mask(_ source: String) -> [UInt8] {
        let b = Array(source.utf8)
        var out = b
        var i = 0
        func blank(_ range: Range<Int>) {
            for k in range where out[k] != UInt8(ascii: "\n") { out[k] = UInt8(ascii: " ") }
        }
        func at(_ k: Int, _ s: String) -> Bool {
            let u = Array(s.utf8)
            return k + u.count <= b.count && Array(b[k..<k + u.count]) == u
        }
        while i < b.count {
            if at(i, "//") {
                let end = b[i...].firstIndex(of: UInt8(ascii: "\n")) ?? b.count
                blank(i..<end); i = end
            } else if at(i, "/*") {
                // Swift block comments nest.
                var depth = 0, k = i
                repeat {
                    if at(k, "/*") { depth += 1; k += 2 } else if at(k, "*/") { depth -= 1; k += 2 } else { k += 1 }
                } while depth > 0 && k < b.count
                blank(i..<k); i = k
            } else if b[i] == UInt8(ascii: "#") || b[i] == UInt8(ascii: "\"") {
                // A raw string opens with one or more `#` then `"`; a macro is `#` then a letter.
                var hashes = 0
                while i + hashes < b.count && b[i + hashes] == UInt8(ascii: "#") { hashes += 1 }
                guard i + hashes < b.count, b[i + hashes] == UInt8(ascii: "\"") else {
                    if hashes > 0 && at(i, "#if false") {
                        let end = endOfInactiveBlock(b, from: i)
                        blank(i..<end); i = end
                    } else { i += max(hashes, 1) }
                    continue
                }
                let multi = at(i + hashes, "\"\"\"")
                let close = (multi ? "\"\"\"" : "\"") + String(repeating: "#", count: hashes)
                var k = i + hashes + (multi ? 3 : 1)
                while k < b.count && !at(k, close) {
                    // In a non-raw string a backslash escapes the next byte.
                    if hashes == 0 && b[k] == UInt8(ascii: "\\") { k += 2 } else { k += 1 }
                }
                k = min(b.count, k + close.utf8.count)
                blank(i..<k); i = k
            } else {
                i += 1
            }
        }
        return out
    }

    /// The byte after the `#endif` matching a `#if false` at `start`, counting nested `#if`s.
    static func endOfInactiveBlock(_ b: [UInt8], from start: Int) -> Int {
        let text = String(decoding: b[start...], as: UTF8.self)
        var depth = 0, offset = start
        for line in text.split(separator: "\n", omittingEmptySubsequences: false) {
            let t = line.trimmingCharacters(in: .whitespaces)
            if t.hasPrefix("#if") { depth += 1 }
            if t.hasPrefix("#endif") { depth -= 1 }
            offset += line.utf8.count + 1
            if depth == 0 { return min(offset, b.count) }
        }
        return b.count
    }
}
