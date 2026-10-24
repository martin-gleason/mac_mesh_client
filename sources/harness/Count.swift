// Created: 2026-10-24 10:45 -05:00 · Edited: 2026-10-24 10:45 -05:00
//
// `C4-T2` · `D27`. Count the checks that actually EXECUTED, and hold them to a floor.
//
// **Why this is separate from `run`.** An exit code cannot show a suite that stopped
// running: a test that returns early, or a loop that runs zero times, passes having
// checked nothing. Counting tests would not see either.
//
// Swift Testing reports tests, not checks, so the count comes from code coverage:
// every `#expect(` and `#require(` under `tests/` contributes the number of times its
// line ran. A check inside a loop of three counts three; a check after an early
// `return` counts zero.

import Foundation

enum Count {
    static func main(_ args: [String], root: URL) -> Int32 {
        let check = args.contains("--check")
        let floorPath = value(after: "--floor", in: args) ?? "tests/FLOOR"

        let codecov = Shell.run(["swift", "test", "--show-codecov-path"], in: root)
        guard codecov.status == 0, let jsonPath = codecov.output.split(separator: "\n").last.map(String.init) else {
            return fail("count: could not find the coverage path:\n\(codecov.output)")
        }
        // A coverage file left over from an earlier run would be counted as this one.
        try? FileManager.default.removeItem(at: URL(fileURLWithPath: jsonPath).deletingLastPathComponent())

        let run = Shell.run(["swift", "test", "--enable-code-coverage"], in: root)
        guard run.status == 0 else {
            FileHandle.standardError.write(Data(run.output.utf8))
            return fail("count: the suite failed (exit \(run.status)) — a count over a red suite means nothing.")
        }

        let count: Int
        do {
            count = try executedChecks(coverageJSON: URL(fileURLWithPath: jsonPath), testsDirectory: root.appending(path: "tests"))
        } catch {
            return fail("count: could not read coverage at \(jsonPath): \(error)")
        }

        guard check else {
            print(count)
            return 0
        }
        let floorURL = floorPath.hasPrefix("/") ? URL(fileURLWithPath: floorPath) : root.appending(path: floorPath)
        guard let text = try? String(contentsOf: floorURL, encoding: .utf8),
              let floor = Int(text.trimmingCharacters(in: .whitespacesAndNewlines)) else {
            return fail("count: no integer floor at \(floorPath)")
        }
        // Zero is not a very clean run. It is the signature of coverage being off.
        if count == 0 {
            return fail("count: 0 checks executed. Either the suite checks nothing, or coverage did not reach tests/.")
        }
        if count < floor {
            return fail("count: FAIL — \(count) check(s) executed, floor is \(floor). A shrinking suite is blind, not clean. "
                + "Deliberately removing a behaviour means lowering the floor in the same commit, on purpose.")
        }
        print("count: pass — \(count) check(s) executed, floor \(floor)")
        return 0
    }

    /// Sum, over every `#expect(`/`#require(` in a test file, the number of times its position ran.
    static func executedChecks(coverageJSON: URL, testsDirectory: URL) throws -> Int {
        let report = try JSONDecoder().decode(Report.self, from: Data(contentsOf: coverageJSON))
        let prefix = testsDirectory.standardizedFileURL.path + "/"
        var total = 0
        for file in report.data.flatMap(\.files) where file.filename.hasPrefix(prefix) {
            let source = try String(contentsOfFile: file.filename, encoding: .utf8)
            for (index, line) in source.components(separatedBy: "\n").enumerated() {
                let code = line.components(separatedBy: "//").first ?? ""
                for column in checkColumns(in: code) {
                    total += executions(at: (index + 1, column), in: file.segments)
                }
            }
        }
        return total
    }

    /// 1-based columns where a check macro starts.
    static func checkColumns(in line: String) -> [Int] {
        var columns: [Int] = []
        for macro in ["#expect(", "#require("] {
            var searchStart = line.startIndex
            while let range = line.range(of: macro, range: searchStart..<line.endIndex) {
                columns.append(line.utf8.distance(from: line.startIndex, to: range.lowerBound) + 1)
                searchStart = range.upperBound
            }
        }
        return columns
    }

    /// The count of the coverage segment in force at a position; zero if it is not instrumented.
    static func executions(at position: (Int, Int), in segments: [Segment]) -> Int {
        let active = segments.last { ($0.line, $0.column) <= position }
        guard let active, active.hasCount else { return 0 }
        return active.count
    }

    static func value(after flag: String, in args: [String]) -> String? {
        guard let i = args.firstIndex(of: flag), i + 1 < args.count else { return nil }
        return args[i + 1]
    }

    // llvm-cov's export format: segments are [line, column, count, hasCount, isRegionEntry, isGapRegion].
    struct Report: Decodable { let data: [Export] }
    struct Export: Decodable { let files: [File] }
    struct File: Decodable { let filename: String; let segments: [Segment] }
    struct Segment: Decodable {
        let line: Int, column: Int, count: Int, hasCount: Bool
        init(from decoder: Decoder) throws {
            var c = try decoder.unkeyedContainer()
            line = try c.decode(Int.self)
            column = try c.decode(Int.self)
            count = try c.decode(Int.self)
            hasCount = try c.decode(Bool.self)
        }
    }
}
