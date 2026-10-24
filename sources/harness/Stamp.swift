// Created: 2026-10-24 10:09 -05:00 · Edited: 2026-10-24 10:09 -05:00
//
// `D76`. Writes the `Created … · Edited …` line from a command, never by hand (`D68`):
// Created from git's first commit of the file (now, if it has none), Edited as now.
// `C4` review, finding 7 — hand-typed stamps were set ahead of the clock.
//
//     swift run harness stamp FILE...
//
// Replaces an existing stamp line in the first ten lines; refuses a file without one,
// because where the line goes depends on the file's comment syntax.

import Foundation

enum Stamp {
    static func main(_ files: [String], root: URL) -> Int32 {
        guard !files.isEmpty else { return fail("usage: harness stamp FILE...") }
        let now = format(Date())
        for file in files {
            let path = root.appending(path: file).path
            guard let text = try? String(contentsOfFile: path, encoding: .utf8) else { return fail("stamp: cannot read \(file)") }
            var lines = text.components(separatedBy: "\n")
            guard let i = lines.prefix(10).firstIndex(where: { $0.contains("Created:") && $0.contains("Edited:") }) else {
                return fail("stamp: \(file) has no stamp line in its first ten lines — add one by hand once, then use this")
            }
            let log = Shell.run(["git", "log", "--diff-filter=A", "--follow", "--format=%aI", "--", file], in: root)
            let firstCommit = log.output.split(separator: "\n").last.map(String.init)
            let created = firstCommit.flatMap { ISO8601DateFormatter().date(from: $0) }.map(format) ?? now
            let prefix = String(lines[i][..<lines[i].range(of: "Created:")!.lowerBound])
            lines[i] = "\(prefix)Created: \(created) · Edited: \(now)"
            do { try lines.joined(separator: "\n").write(toFile: path, atomically: true, encoding: .utf8) }
            catch { return fail("stamp: cannot write \(file): \(error)") }
            print("stamp: \(file) — Created \(created) · Edited \(now)")
        }
        return 0
    }

    static func format(_ date: Date) -> String {
        let f = DateFormatter()
        f.locale = Locale(identifier: "en_US_POSIX")
        f.dateFormat = "yyyy-MM-dd HH:mm xxx"
        return f.string(from: date)
    }
}
