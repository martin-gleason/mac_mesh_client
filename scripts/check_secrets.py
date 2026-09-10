#!/usr/bin/env python3
"""`C1-T6` — refuse a commit that carries a credential.

`NFR7` · `RR8`. Two credentials exist for this project — the radio PSK and the Google
service-account key — and both behave the same way: recoverable from git history
forever, whatever the next commit deletes.

**Scans the staged content, not the working tree.** What is about to be committed is
the only thing that matters here, and the two differ precisely when somebody has
staged a file and then edited it.

`.gitignore` is the first line of defence and this is the second, because a rule that
depends on a file nobody re-reads is a rule that lapses.

**This is a net, not a proof.** It catches shapes. A credential in a shape nobody
anticipated gets through, so the rule that credentials live in `~/.config` at mode
`0600` is the actual protection and this is what catches the slip.

    python scripts/check_secrets.py
"""

from __future__ import annotations

import re
import subprocess
import sys

# A line carrying this marker is a pattern definition, not a leak. Excluding by LINE
# rather than by file is deliberate: excluding whole files left a hole where a real
# credential parked in an excluded file — a hook script is a plausible place for
# somebody to put an export — passed the scan.
MARKER = "secret-pattern-definition"

# Each pattern names the thing it catches, so a refusal explains itself rather than
# printing a regex at somebody who is trying to commit.
PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("a PEM private key",
     re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),  # secret-pattern-definition
    ("a Google service-account key",
     re.compile(r'"type"\s*:\s*"service_account"')),  # secret-pattern-definition
    ("a Google private key id",
     re.compile(r'"private_key_id"\s*:\s*"[0-9a-f]{16,}"')),  # secret-pattern-definition
    ("an OAuth client secret",
     re.compile(r'"client_secret"\s*:\s*"[^"]{8,}"')),  # secret-pattern-definition
    # `\bpsk` missed MESH_PSK and CHANNEL_PSK entirely, because `_` is a word
    # character. The quote is optional now too: a .env line and unquoted YAML are the
    # two most likely places this actually appears.
    ("a Meshtastic channel PSK",
     re.compile(r"[A-Za-z0-9_]*psk[A-Za-z0-9_]*\s*[:=]\s*['\"]?[A-Za-z0-9+/]{16,}={0,2}",
                re.IGNORECASE)),  # secret-pattern-definition
    # The channel-share URL *is* the key material, and it is how Meshtastic channels
    # are actually exchanged between people — the likeliest shape of all for this repo.
    ("a Meshtastic channel-share URL, which carries the key",
     re.compile(r"https?://meshtastic\.org/e/#[A-Za-z0-9_-]{10,}")),  # secret-pattern-definition
    ("a Google API key",
     re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),  # secret-pattern-definition
    ("a GitHub token",
     re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),  # secret-pattern-definition
    ("a Slack token",
     re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),  # secret-pattern-definition
    ("an AWS access key id",
     re.compile(r"\bAKIA[0-9A-Z]{16}\b")),  # secret-pattern-definition
)


def staged_files() -> list[str]:
    out = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                         capture_output=True, text=True, check=True).stdout
    return [f for f in out.splitlines() if f]


def staged_content(path: str) -> str:
    # `errors="replace"` rather than strict: a staged PNG used to raise
    # UnicodeDecodeError out of this function, which aborted the whole scan at the
    # first binary file and left everything after it unexamined.
    proc = subprocess.run(["git", "show", f":{path}"],
                          capture_output=True, check=False)
    if proc.returncode != 0:
        return ""
    return proc.stdout.decode("utf-8", errors="replace")


def main() -> int:
    findings: list[str] = []
    for path in staged_files():
        for lineno, line in enumerate(staged_content(path).splitlines(), start=1):
            if MARKER in line:
                continue
            for label, pattern in PATTERNS:
                if pattern.search(line):
                    findings.append(f"  {path}:{lineno} — looks like {label}")

    if not findings:
        print("secrets: pass — nothing credential-shaped in the staged content")
        return 0

    print("\nsecrets: REFUSED — the staged content carries something credential-shaped\n",
          file=sys.stderr)
    for f in findings:
        print(f, file=sys.stderr)
    print("\n  Credentials live at ~/.config, mode 0600, and never in the repository "
          "(NFR7).\n  Git remembers whatever lands here, so a later deletion does not "
          "undo this.\n  If this is a false positive, say so in the commit and use "
          "--no-verify deliberately.\n", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
