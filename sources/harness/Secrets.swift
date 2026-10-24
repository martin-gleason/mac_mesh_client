// Created: 2026-10-24 09:44 -05:00 · Edited: 2026-10-24 10:09 -05:00
//
// `C4-T6`, ported from `scripts/check_secrets.py`. Refuse a commit that carries a credential.
// `NFR7` · `RR8`. Git remembers whatever lands here, so a later deletion does not undo it.
//
// **Scans the staged content, not the working tree** — they differ exactly when somebody
// staged a file and then edited it. **A net, not a proof:** credentials live in
// `~/.config` at mode 0600; this catches the slip.

import Foundation

enum Secrets {
    // A line carrying this marker is a pattern definition, not a leak. Excluded by line,
    // not by file, so a real credential parked in this file is still caught.
    static let marker = "secret-pattern-definition"

    static let patterns: [(label: String, regex: NSRegularExpression)] = [
        ("a PEM private key", #"-----BEGIN [A-Z ]*PRIVATE KEY-----"#),  // secret-pattern-definition
        ("a Google service-account key", #""type"\s*:\s*"service_account""#),  // secret-pattern-definition
        ("a Google private key id", #""private_key_id"\s*:\s*"[0-9a-f]{16,}""#),  // secret-pattern-definition
        ("an OAuth client secret", #""client_secret"\s*:\s*"[^"]{8,}""#),  // secret-pattern-definition
        // `_` is a word character, so `\bpsk` would miss MESH_PSK. The quote is optional:
        // a .env line and unquoted YAML are the likeliest places this appears.
        ("a Meshtastic channel PSK", #"(?i)[A-Za-z0-9_]*psk[A-Za-z0-9_]*\s*[:=]\s*['"]?[A-Za-z0-9+/]{16,}={0,2}"#),  // secret-pattern-definition
        // The channel-share URL *is* the key material.
        ("a Meshtastic channel-share URL, which carries the key", #"https?://meshtastic\.org/e/#[A-Za-z0-9_-]{10,}"#),  // secret-pattern-definition
        ("a Google API key", #"\bAIza[0-9A-Za-z_\-]{35}\b"#),  // secret-pattern-definition
        ("a GitHub token", #"\bgh[pousr]_[A-Za-z0-9]{36,}\b"#),  // secret-pattern-definition
        ("a Slack token", #"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"#),  // secret-pattern-definition
        ("an AWS access key id", #"\bAKIA[0-9A-Z]{16}\b"#),  // secret-pattern-definition
    ].map { ($0.0, try! NSRegularExpression(pattern: $0.1)) }

    static func main(root: URL) -> Int32 {
        // NUL-separated, so git does not quote a non-ASCII name into a path `git show`
        // cannot find. `C4` review, finding 4.
        let staged = Shell.run(["git", "diff", "--cached", "--name-only", "-z", "--diff-filter=ACM"], in: root)
        guard staged.status == 0 else { return fail("secrets: could not list staged files:\n\(staged.output)") }

        var findings: [String] = []
        for path in staged.output.split(separator: "\0").map(String.init) {
            // Lossy decoding, so a staged binary cannot abort the scan of everything after it.
            let shown = Shell.run(["git", "show", ":\(path)"], in: root)
            guard shown.status == 0 else { return fail("secrets: could not read staged \(path) — refusing rather than skipping it") }
            let content = shown.output
            for (index, line) in content.components(separatedBy: "\n").enumerated() where !line.contains(marker) {
                let range = NSRange(line.startIndex..., in: line)
                for (label, regex) in patterns where regex.firstMatch(in: line, range: range) != nil {
                    findings.append("  \(path):\(index + 1) — looks like \(label)")
                }
            }
        }
        guard !findings.isEmpty else {
            print("secrets: pass — nothing credential-shaped in the staged content")
            return 0
        }
        return fail("""

            secrets: REFUSED — the staged content carries something credential-shaped

            \(findings.joined(separator: "\n"))

              Credentials live at ~/.config, mode 0600, and never in the repository (NFR7).
              Git remembers whatever lands here, so a later deletion does not undo this.
              If this is a false positive, say so in the commit and use --no-verify deliberately.

            """)
    }
}
