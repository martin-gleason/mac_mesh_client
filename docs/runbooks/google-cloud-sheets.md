# Runbook — Google Cloud and the soak spreadsheet

**Closes:** `O11` · **Unblocks:** `F1-T5`, `F1-T6`, `F1-T7` · **Owner: human, entirely.**
**Written:** 2026-09-10, against console documentation last updated 2026-07-22.

> **Why this is a runbook and not a task.** Project creation and billing consent cannot be
> delegated to an agent, and neither can the click that downloads a private key. Everything
> below is the owner at the keyboard. The agent's part starts at **§9 Verification**, which
> is the only part that produces evidence.

**Assumed:** you have used the Google Cloud console before. This does not explain what a
service account is. It explains the four places this particular setup goes wrong.

---

## The four traps, stated first

Read these before clicking anything. Each one produces a working-looking setup that fails
later, which is the failure mode this whole project is named for.

1. **The official Python quickstart is the wrong document.** It walks you through an **OAuth
   client ID** and a consent screen, because it assumes a human clicking "allow" in a
   browser. A 48-hour unattended soak has nobody to click. You want a **service account**,
   and the consent screen is **not required** for one. Skip §2–3 of the quickstart entirely.
2. **Project-level IAM roles do nothing for Sheets.** Granting the service account `Editor`
   on the GCP project does not give it access to a single spreadsheet. Sheets authorises per
   **file**, through Drive sharing. The share in §7 is the authorisation; the project role is
   not. Grant **no project roles at all**.
3. **Never let the service account create the spreadsheet.** A file created by a service
   account is *owned* by it, lives in a Drive no human can open, and does not appear in your
   Drive at all. Diagnosing that at hour 20 of a soak is `RR2` exactly. You create the sheet;
   you lend it to the robot.
4. **Application Default Credentials will silently stand in for a missing key.**
   `~/.config/gcloud/application_default_credentials.json` already exists on this machine. If
   the code ever calls `google.auth.default()` instead of loading the service-account file by
   path, it will find *your personal* credentials and work — on your laptop, as you, until it
   doesn't. `F1-T5` loads the key by explicit path. See §9.

---

## 1 · Create the project

Console → project picker → **New Project**. Name it something that reads as an instrument,
not a product: `mesh-soak` is fine.

**Leave Location as "No organization".** A consumer Google account has no organization, and
that is what you want here: the `iam.disableServiceAccountKeyCreation` constraint — enforced
**by default** on any organization created on or after 3 May 2024 — is an organization-level
policy and has nothing to attach to. If you ever move this project under an organization,
§5 stops working; that is the first thing to check if it does.

**Billing:** the Sheets API has no billing requirement at this volume. Do not attach a
billing account. If the console pushes one, you are on the wrong API.

---

## 2 · Enable the Sheets API — and only that one

**APIs & Services → Library →** search `Google Sheets API` → **Enable**.

**Do not enable the Drive API.** It is only needed to *create, list or delete* spreadsheet
files, and per trap 3 we never do. Enabling it widens what a leaked key can reach for no
capability we use. If a future task needs to create sheets, that is a `D<n>`.

---

## 3 · Skip the OAuth consent screen

There is nothing to do here. Left in as a numbered step because the quickstart puts it at
step 2 and its absence otherwise reads as an omission.

---

## 4 · Create the service account

**IAM & Admin → Service Accounts → Create service account.**

- **Name:** `mesh-soak-logger`. The generated address is what you paste in §7, so make it
  recognisable in a Drive share dialog eighteen months from now.
- **"Grant this service account access to the project"** — **skip it.** No roles. See trap 2.
- **"Grant users access to this service account"** — skip it.

Copy the full address (`mesh-soak-logger@<project-id>.iam.gserviceaccount.com`). You need it
twice: in §7, and to confirm §9 is talking to the right identity.

---

## 5 · Create the JSON key

Click the service account → **Keys** tab → **Add key → Create new key → JSON → Create**.

The file downloads immediately and **cannot be retrieved again**. If you lose it, delete the
key and make another; there is no re-download.

**If the button is greyed out or you get "Service account key creation is disabled":** an
organization policy is enforcing one of two constraints, and disabling only one is the
common wasted afternoon — the legacy `iam.disableServiceAccountKeyCreation` and the newer
managed `iam.managed.disableServiceAccountKeyCreation` are separate, and either one alone
still blocks you. On a no-organization project this should not arise. If it does, stop and
raise it rather than working around it — a workaround here is a credential decision.

By default these keys **never expire**. That is a standing liability, not a convenience:
`RR8`. It is acceptable for an instrument that runs for 48 hours; delete the key when the
soak programme ends.

---

## 6 · Place the key, and lock it

```sh
mkdir -p ~/.config/mesh-client
mv ~/Downloads/<project-id>-<hash>.json ~/.config/mesh-client/service-account.json
chmod 0600 ~/.config/mesh-client/service-account.json
ls -l ~/.config/mesh-client/service-account.json    # expect -rw-------
```

**`NFR7`: no credential enters the repository.** `.gitignore` already covers
`service-account*.json`, and the pre-commit secret scan (`H5`) refuses a staged key — both
are backstops, not the plan. The plan is that the file is never inside the tree.

Empty your Downloads folder of the original. A world-readable copy of this key in
`~/Downloads` is the same exposure as one in the repo, minus the hook that would have caught
it.

---

## 7 · Create the spreadsheet yourself, then share it

**You create it, in your own Drive.** Name it `mesh-soak-<yyyy-mm>` or similar.

Then **Share** → paste the service-account address from §4 → role **Editor** → **turn off
"Notify people"** (there is no inbox behind that address) → **Share**.

Two things to know about this share:

- The service account will now appear in the file's share list as a robot address with no
  photo. That is correct and is the only authorisation in the system.
- **`Viewer` is not enough** and fails at the first write with a 403 that names permission
  rather than sharing, which is a confusing place to start debugging.

**Do not create the tab layout by hand.** `F1-T5` owns the column contract; a
hand-made header row that disagrees with it is a silent column-shift for 48 hours. Leave the
sheet empty.

Copy the **spreadsheet id** — the segment between `/d/` and `/edit` in the URL, not the whole
URL, not the sheet name.

---

## 8 · Record the sheet id outside the repository

```sh
cat > ~/.config/mesh-client/soak.toml <<'EOF'
# Not in the repository, and not a credential — but it names one.
spreadsheet_id = "PASTE_THE_ID_HERE"
credentials_path = "~/.config/mesh-client/service-account.json"
EOF
chmod 0600 ~/.config/mesh-client/soak.toml
```

**The filename and key names above are a proposal, not a contract.** `F1-T7` owns the config
shape and may land somewhere else; if it does, this section gets corrected rather than the
config being duplicated. What is *not* negotiable is that neither value lives in the tree.

---

## 9 · Verification — the part that produces evidence

**`turing-review:D30`: a decision about what another system can do is not ratifiable until
something has run.** Everything above is a claim that a setup exists. This is the command
that turns it into a fact, and its output goes in the `O11` closure row.

It needs `google-api-python-client`, which per `D11` enters `pyproject.toml` when `F1-T5`
starts and is deliberately not installed yet. Run it with `uv` without touching the project's
dependency tree:

```sh
uv run --with google-api-python-client --with google-auth python - <<'EOF'
import tomllib, pathlib
from google.oauth2 import service_account
from googleapiclient.discovery import build

cfg = tomllib.loads(pathlib.Path("~/.config/mesh-client/soak.toml").expanduser().read_text())
key = pathlib.Path(cfg["credentials_path"]).expanduser()

# Load the key BY PATH. `google.auth.default()` would fall back to your personal
# Application Default Credentials and pass while proving nothing (trap 4).
creds = service_account.Credentials.from_service_account_file(
    str(key), scopes=["https://www.googleapis.com/auth/spreadsheets"])
print("acting as:", creds.service_account_email)

svc = build("sheets", "v4", credentials=creds)
meta = svc.spreadsheets().get(spreadsheetId=cfg["spreadsheet_id"]).execute()
print("sheet:", meta["properties"]["title"])

svc.spreadsheets().values().append(
    spreadsheetId=cfg["spreadsheet_id"], range="A1",
    valueInputOption="RAW",
    body={"values": [["runbook verification", "delete this row"]]}).execute()
print("write: ok")
EOF
```

**A pass looks like three lines**: the robot address from §4, the sheet title from §7, and
`write: ok`. Paste all three into the `O11` row. Then delete the test row from the sheet.

**`acting as:` is the assertion that matters.** If it prints your own gmail address, trap 4
has you and the setup is not proven — the code found ADC, not the key.

`valueInputOption` is `RAW` deliberately: `USER_ENTERED` makes Sheets parse each cell the way
the UI would, which turns a heap figure into a number, a timestamp into a date serial, and a
node id beginning `!` into whatever Sheets thinks that is. The soak logs values, not
spreadsheet content.

---

## 10 · What the volume actually looks like

At `FR1`'s 30-second cadence: **5,760 samples over 48 hours, ~2 writes a minute.** The Sheets
API allows 300 write requests per minute per project and 60 per user per minute, so an
unbatched implementation would sit at roughly 3% of quota.

**So batching in `F1-T5` is not about quota** — it is about not being fragile across 5,760
independent opportunities for a transient failure, and the plan says so. Do not let a quota
argument creep into that task; the number is here so nobody has to guess it.

---

## 11 · Failure modes, and what each one actually means

| What you see | What it is |
|---|---|
| `403` naming **permission** on a write | shared as Viewer, not Editor (§7) |
| `404` on the spreadsheet id | wrong id — you copied the URL or the tab name, not the `/d/…/` segment |
| `403 Google Sheets API has not been used in project …` | §2 not done, or done in a different project than the key belongs to |
| `acting as:` prints your gmail address | trap 4 — ADC, not the key |
| key creation greyed out | organization policy, both constraints (§5) |
| works today, `invalid_grant` later | the key was deleted or the service account disabled; keys themselves do not expire |

---

## 12 · Hand back

Three things close `O11`, and all three are the owner's:

1. The service-account address.
2. The three verification lines from §9.
3. Confirmation that `ls -l` showed `-rw-------` on the key.

The spreadsheet id is **not** on that list and does not go in the register — it goes in
`~/.config` and nowhere else.

-----
2026-09-10

#AI/Claude
