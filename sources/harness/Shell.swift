// Created: 2026-10-24 10:45 -05:00 · Edited: 2026-10-24 10:45 -05:00
import Foundation

/// Run a command to completion and capture what it printed.
struct Shell {
    let status: Int32
    let output: String

    static func run(_ arguments: [String], in directory: URL) -> Shell {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/env")
        process.arguments = arguments
        process.currentDirectoryURL = directory
        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = pipe
        do {
            try process.run()
        } catch {
            return Shell(status: 127, output: "could not start \(arguments.joined(separator: " ")): \(error)")
        }
        // Read before waiting: a full pipe blocks the child, and the child never exits.
        let data = pipe.fileHandleForReading.readDataToEndOfFile()
        process.waitUntilExit()
        return Shell(status: process.terminationStatus, output: String(decoding: data, as: UTF8.self))
    }
}

func fail(_ message: String) -> Int32 {
    FileHandle.standardError.write(Data((message + "\n").utf8))
    return 1
}
