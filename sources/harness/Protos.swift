// Created: 2026-10-24 11:05 -05:00 · Edited: 2026-10-24 11:05 -05:00
//
// `C4-T3` · `D28`. The committed Swift must be exactly what the generator makes from the
// vendored `.proto` files — otherwise a hand edit, or a stale regeneration, ships silently.
//
//     swift run harness protos           # fail if the committed Swift has drifted
//     swift run harness protos --write   # regenerate it
//
// Building never needs `protoc`; only these two commands do.

import Foundation

enum Protos {
    static let generatorVersion = "protoc-gen-swift 1.39.0"   // must match Package.swift's exact pin
    static let generated = "sources/meshkitcore/generated"

    static func main(_ args: [String], root: URL) -> Int32 {
        let version = Shell.run(["protoc-gen-swift", "--version"], in: root)
        guard version.status == 0 else {
            return fail("protos: protoc-gen-swift not found — `brew install protobuf swift-protobuf`")
        }
        guard version.output.trimmingCharacters(in: .whitespacesAndNewlines) == generatorVersion else {
            return fail("protos: expected \(generatorVersion), found \(version.output.trimmingCharacters(in: .whitespacesAndNewlines)). "
                + "The runtime pinned in Package.swift and the generator must move together.")
        }

        let write = args.contains("--write")
        let fm = FileManager.default
        let target = write ? root.appending(path: generated)
                           : fm.temporaryDirectory.appending(path: "mesh-protos-\(UUID().uuidString)")
        defer { if !write { try? fm.removeItem(at: target) } }
        try? fm.removeItem(at: target)
        try? fm.createDirectory(at: target, withIntermediateDirectories: true)

        let protoFiles = ((try? fm.contentsOfDirectory(atPath: root.appending(path: "protos/meshtastic").path)) ?? [])
            .filter { $0.hasSuffix(".proto") }.sorted().map { "protos/meshtastic/\($0)" }
        guard !protoFiles.isEmpty else { return fail("protos: no .proto files under protos/meshtastic") }

        let gen = Shell.run(["protoc", "--proto_path=protos", "--proto_path=/opt/homebrew/include",
                             "--swift_out=\(target.path)", "--swift_opt=Visibility=Public"] + protoFiles, in: root)
        guard gen.status == 0 else { return fail("protos: protoc failed:\n\(gen.output)") }

        if write {
            print("protos: wrote \(protoFiles.count) file(s) to \(generated)")
            return 0
        }
        let diff = Shell.run(["diff", "-r", "-q", root.appending(path: generated).path, target.path], in: root)
        guard diff.status == 0 else {
            return fail("protos: FAIL — committed Swift differs from a fresh generation:\n\(diff.output)"
                + "Run `swift run harness protos --write` if the change is intended.")
        }
        print("protos: pass — \(protoFiles.count) file(s) match a fresh generation")
        return 0
    }
}
