// swift-tools-version: 6.0
// Created: 2026-10-24 09:36 -05:00 · Edited: 2026-10-24 10:09 -05:00
//
// `C4` · `D25`. One package. Directories are lowercase (`docs/conventions.md`), so every
// target names its path rather than relying on SwiftPM's capitalised defaults.

import PackageDescription

let package = Package(
    name: "MeshClient",
    platforms: [.macOS(.v14), .iOS(.v17)],
    products: [
        .library(name: "MeshKitCore", targets: ["MeshKitCore"]),
        .library(name: "MeshKit", targets: ["MeshKit"]),
    ],
    dependencies: [
        // `D28`. Exact, because the runtime must match the generator that wrote the
        // committed `.pb.swift` files (`protoc-gen-swift --version` → 1.39.0).
        .package(url: "https://github.com/apple/swift-protobuf.git", exact: "1.39.0"),
    ],
    targets: [
        .target(
            name: "MeshKitCore",
            dependencies: [.product(name: "SwiftProtobuf", package: "swift-protobuf")],
            path: "sources/meshkitcore"
        ),
        .target(name: "MeshKit", dependencies: ["MeshKitCore"], path: "sources/meshkit"),
        // Tooling, never linked into an app.
        .executableTarget(name: "harness", path: "sources/harness"),
        .testTarget(
            name: "MeshKitCoreTests",
            dependencies: ["MeshKitCore"],
            path: "tests/meshkitcoretests"
        ),
    ]
)
