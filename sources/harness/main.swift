// Created: 2026-10-24 10:30 -05:00 · Edited: 2026-10-24 10:45 -05:00
//
// `C4`. The harness, in Swift (`D21`). One executable, one subcommand per capability:
//
//     swift run harness count            # print the number of checks that executed
//     swift run harness count --check    # and hold it to tests/FLOOR
//
// Tooling only — never linked into an app.

import Foundation

let root = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
var args = Array(CommandLine.arguments.dropFirst())
let command = args.isEmpty ? "" : args.removeFirst()

let status: Int32
switch command {
case "count":
    status = Count.main(args, root: root)
default:
    FileHandle.standardError.write(Data("harness: unknown command '\(command)'. Try: count\n".utf8))
    status = 2
}
exit(status)
