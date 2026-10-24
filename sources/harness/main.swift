// Created: 2026-10-24 09:36 -05:00 · Edited: 2026-10-24 10:09 -05:00
//
// `C4`. The harness, in Swift (`D21`). One executable, one subcommand per capability:
//
//     swift run harness count            # print the number of checks that executed
//     swift run harness count --check    # and hold it to tests/FLOOR
//     swift run harness protos           # generated protobufs match the vendored .proto files
//     swift run harness mutate           # break the code on purpose; the named test must go red
//     swift run harness secrets          # nothing credential-shaped in the staged content
//     swift run harness commit-msg FILE  # no register ID in a commit subject
//     swift run harness stamp FILE...    # write the Created/Edited line from git and the clock
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
case "protos":
    status = Protos.main(args, root: root)
case "mutate":
    status = Mutate.main(args, root: root)
case "secrets":
    status = Secrets.main(root: root)
case "commit-msg":
    status = CommitMessage.main(args)
case "stamp":
    status = Stamp.main(args, root: root)
default:
    FileHandle.standardError.write(Data("harness: unknown command '\(command)'. Try: count, protos, mutate, secrets, commit-msg, stamp\n".utf8))
    status = 2
}
exit(status)
