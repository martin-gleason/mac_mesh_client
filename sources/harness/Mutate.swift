// Created: 2026-10-24 09:42 -05:00 · Edited: 2026-10-24 10:09 -05:00
//
// `C4-T5`. Break the shipped code on purpose and require the suite to notice.
//
// **A test that has never been shown to fail is not evidence** (`NFR8`). A behaviour is
// protected only once a mutation has been applied to the shipped code and the suite
// has been *seen* to fail.
//
// **A red suite is not a kill.** Each mutation names the test that must catch it, and
// that test must be among the failures. A mutant that does not compile is not a kill
// either — the compiler caught it, not the suite.
//
//     swift run harness mutate            # run every mutation
//     swift run harness mutate --list     # name them without touching anything
//     swift run harness mutate M14        # run one

import Foundation

struct Edit {
    let path: String
    let old: String
    let new: String
}

struct Mutation {
    let id: String
    let description: String
    let edits: [Edit]
    let caughtBy: String

    init(id: String, description: String, path: String, old: String, new: String, caughtBy: String) {
        self.init(id: id, description: description, edits: [Edit(path: path, old: old, new: new)], caughtBy: caughtBy)
    }

    /// More than one edit, for a failure that needs two things to go wrong at once.
    init(id: String, description: String, edits: [Edit], caughtBy: String) {
        self.id = id
        self.description = description
        self.edits = edits
        self.caughtBy = caughtBy
    }
}

// Every file this process has mutated and not yet put back. A signal handler cannot
// reach a local, and leaving mutated source on disk is the one outcome this must never produce.
nonisolated(unsafe) var pendingRestore: [String: String] = [:]

func restorePending() {
    for (path, original) in pendingRestore {
        try? original.write(toFile: path, atomically: true, encoding: .utf8)
    }
    pendingRestore = [:]
}

enum Mutate {
    static let budget = "sources/meshkitcore/PayloadBudget.swift"

    static let mutations: [Mutation] = [
        Mutation(
            id: "M14", description: "hardcode 190 for the protocol limit — the mistake this project actually made",
            path: budget,
            old: "public static var protocolLimit: Int { Constants.dataPayloadLen.rawValue }",
            new: "public static var protocolLimit: Int { 190 }",
            caughtBy: "theProtocolLimitIsNotTheUnsourced190"),
        Mutation(
            id: "M15", description: "count characters instead of bytes",
            path: budget,
            old: "        text.utf8.count",
            new: "        text.count",
            caughtBy: "encodedSizeCountsBytesNotCharacters"),
        Mutation(
            id: "M16", description: "cut on a raw byte boundary, splitting a character in half",
            path: budget,
            old: """
                    var used = 0
                    var end = text.startIndex
                    for index in text.indices {
                        let size = text[index].utf8.count
                        if used + size > cap { break }
                        used += size
                        end = text.index(after: index)
                    }
                    return String(text[..<end])
            """,
            new: "        return String(decoding: Array(text.utf8.prefix(cap)), as: UTF8.self)",
            caughtBy: "truncatedOutputIsAlwaysAWholeCharacterPrefixWithinBudget"),
        Mutation(
            id: "M17", description: "measure against a literal 233 instead of the budget's own limit",
            path: budget,
            old: "        limit - Self.encodedSize(text)",
            new: "        233 - Self.encodedSize(text)",
            caughtBy: "theBudgetUsesTheLimitItWasGivenNotALiteral"),
        Mutation(
            id: "M18", description: "cut between Unicode scalars instead of whole characters — half a flag goes out",
            path: budget,
            old: """
                    for index in text.indices {
                        let size = text[index].utf8.count
                        if used + size > cap { break }
                        used += size
                        end = text.index(after: index)
                    }
            """,
            new: """
                    for index in text.unicodeScalars.indices {
                        let size = text.unicodeScalars[index].utf8.count
                        if used + size > cap { break }
                        used += size
                        end = text.unicodeScalars.index(after: index)
                    }
            """,
            caughtBy: "truncateNeverSendsHalfAFlag"),
        Mutation(
            id: "M19", description: "hardcode 233, then a firmware bump moves the protocol to 240 — the literal stays behind",
            edits: [
                Edit(path: budget,
                     old: "public static var protocolLimit: Int { Constants.dataPayloadLen.rawValue }",
                     new: "public static var protocolLimit: Int { 233 }"),
                Edit(path: "protos/meshtastic/mesh.proto",
                     old: "  DATA_PAYLOAD_LEN = 233;",
                     new: "  DATA_PAYLOAD_LEN = 240;"),
            ],
            caughtBy: "theProtocolLimitMatchesTheVendoredProtoFile"),
    ]

    static func main(_ args: [String], root: URL) -> Int32 {
        if args.contains("--list") {
            for m in mutations { print("\(m.id)  \(m.description)\n      caught by \(m.caughtBy)") }
            return 0
        }
        let chosen = args.isEmpty ? mutations : mutations.filter { args.contains($0.id) }
        guard !chosen.isEmpty else { return fail("mutate: no mutation named \(args.joined(separator: " "))") }

        signal(SIGINT) { _ in restorePending(); exit(130) }
        signal(SIGTERM) { _ in restorePending(); exit(143) }

        var escaped: [String] = []
        for m in chosen {
            defer { restorePending() }
            for edit in m.edits {
                let path = root.appending(path: edit.path).path
                guard let original = try? String(contentsOfFile: path, encoding: .utf8) else {
                    return fail("mutate: cannot read \(edit.path)")
                }
                let occurrences = original.components(separatedBy: edit.old).count - 1
                guard occurrences == 1 else {
                    return fail("mutate: \(m.id) — expected the target text once in \(edit.path), found \(occurrences). "
                        + "The shipped code moved; update the mutation, do not skip it.")
                }
                pendingRestore[path] = original
                do {
                    try original.replacingOccurrences(of: edit.old, with: edit.new).write(toFile: path, atomically: true, encoding: .utf8)
                } catch {
                    return fail("mutate: could not write \(edit.path): \(error)")
                }
            }

            let run = Shell.run(["swift", "test"], in: root)
            let failed = failedTests(in: run.output)
            let total = totalTests(in: run.output)
            if run.output.contains("error: ") && failed.isEmpty {
                print("\(m.id)  NOT A KILL — the mutant did not compile, so no test was asked")
                escaped.append(m.id)
            } else if failed.contains(m.caughtBy) {
                print("\(m.id)  caught by \(m.caughtBy) — \(failed.count) of \(total) test(s) red")
            } else {
                print("\(m.id)  ESCAPED — \(m.caughtBy) stayed green (red: \(failed.sorted().joined(separator: ", ")))")
                escaped.append(m.id)
            }
        }
        // Read back what was restored, rather than trusting the write.
        for m in chosen {
            for edit in m.edits {
                let now = (try? String(contentsOfFile: root.appending(path: edit.path).path, encoding: .utf8)) ?? ""
                if now.contains(edit.new) && !now.contains(edit.old) {
                    return fail("mutate: \(edit.path) still carries \(m.id) — restore from git now")
                }
            }
        }
        if !escaped.isEmpty { return fail("mutate: FAIL — \(escaped.joined(separator: ", ")) not caught") }
        print("mutate: pass — \(chosen.count) of \(chosen.count) caught, code restored")
        return 0
    }

    /// Names of tests Swift Testing reported as failed: `✘ Test name() …`.
    static func failedTests(in output: String) -> Set<String> {
        var names: Set<String> = []
        for line in output.split(separator: "\n") where line.contains("✘ Test ") {
            guard let start = line.range(of: "✘ Test ")?.upperBound,
                  let paren = line[start...].firstIndex(of: "(") else { continue }
            let name = String(line[start..<paren])
            if name != "run with" && !name.hasPrefix("run ") { names.insert(name) }
        }
        return names
    }

    static func totalTests(in output: String) -> Int {
        guard let line = output.split(separator: "\n").last(where: { $0.contains("Test run with ") }),
              let r = line.range(of: "Test run with ") else { return 0 }
        return Int(line[r.upperBound...].prefix { $0.isNumber }) ?? 0
    }
}
