# Headless Code-Signing and Serena MCP Harness — Findings Audit

**Project**: Juniper — Cascade Correlation Neural Network Research Platform
**Scope**: Ecosystem-wide agentic harness. Area 1 — the headless-merge code-signing key regression (git/gpg config, keyring, YubiKey card binding, fleet signature census). Area 2 — Serena MCP disuse (wiring, registry, the symbol-overlay masking layer, guardrail coverage).
**Author**: Paul Calnon (audit executed by a Claude Code `auditor` subagent)
**Date**: 2026-08-09
**Status**: FINDINGS ONLY — no remediation performed, no configuration or git state modified
**Grounding**: juniper-ml session worktree `.claude/worktrees/cryptic-dancing-badger`, HEAD `b64eaaf`; `origin/main` tip observed at audit time = `be9f131` (advanced past the `e835e2b` grounding tip named in the task). All sibling-repo facts read from absolute paths under `/home/pcalnon/Development/python/Juniper/`; all GitHub facts from `gh api` / `gh api graphql` at 2026-08-09.
**Host**: `yamaguchi` (`hostname` / `uname -n`)

---

## 1. Executive summary

**Area 1 — the stale-RSA regression is NOT live on this host, and has not been for ~26 days.** An exhaustive hunt across this worktree's `scripts/` `util/` `conf/` `.github/` `notes/templates/` `scripts/backups/`, all eight sibling repos' full trees, all nine `.git/config` files, `~/.gitconfig`, `~/.gnupg/gpg.conf`, `~/.gnupg/gpg-agent.conf`, the system git config, and the four active git hooks found **zero** references to the
legacy RSA key `B5AFCD0686585249` outside one historical notes document. Every live signing knob points at the correct ed25519 signing subkey. A 3,208-commit signature census across the nine repos dates the **last** old-RSA-signed main commit to **2026-07-14** (juniper-ml `112dc0d7`) and **2026-07-12** (five siblings) — immediately before the 2026-07-16 repoint. The interim ed448 key signed **zero** main commits, ever.

What the audit *did* find is a plausible origin for the "still referencing an old RSA key" impression, plus three real headless-fragility classes:

- The repo's only signing-validation utility, `util/test_gpg_signing.bash`, still pins the **superseded ed448 key** (`93E8591643C507FF`) in three places — a tool that "validates" a key git no longer uses.
- The only `notes/` document about signing, `JUNIPER_2026-07-16_JUNIPER-ECOSYSTEM_CODE-SIGNING-KEY-MIGRATION-STATUS.md`, is **stale**: it states the current signing key is the ed448 key and carries Status `PARTIALLY MIGRATED — remaining steps DEFERRED`. Several of its deferred items are in fact now done, and its stated current key is wrong. Any human or agent grounding on it would conclude the key is misconfigured.
- The keyring's card stubs bind card `0006 24955323` while the **connected card is `24955114`** (a backup YubiKey carrying the same subkey). Signing empirically works today, but the mismatch is the classic `Please insert the card with serial number …` pinentry class, and the unattended-signing preconditions (card present, PIN cached, `UIF Sign=off`) are undocumented and unenforced — `~/.gnupg/gpg-agent.conf` contains exactly one line and sets no cache TTLs, so GnuPG's 600 s / 7200 s defaults apply.

Crucially, the failure mode for any *future* stale-RSA use is now **loud, not silent**: the GitHub account's public GPG list contains exactly one key (the ed25519), so an RSA-signed commit would land Unverified and be rejected by any `required_signatures` ruleset.

**Area 2 — Serena has been non-functional for 123 days, and nothing in the harness can notice.** Three independent, individually-sufficient root causes stack: the live `.mcp.json` starts Serena with **no `--project`**; **juniper-ml is absent from Serena's project registry**; and **no instruction anywhere tells an agent to call `activate_project`** — while `.claude/skills/template-agent/SKILL.md:47` explicitly authorises "Skip
silently if Serena is unavailable". Log evidence quantifies the outcome far beyond the reported figure: the last productive Serena tool application was **2026-04-08**; in the **123 days** since, across **73 distinct days** and **248 MCP server sessions**, there were **zero** tool applications. The single call in the window is this audit's own smoke test, which errored `No active project`.

Two masking layers guarantee the silence. `util/prompt_discovery/symbol_overlay.py:50` stamps `overlay = "serena"` **unconditionally** — an empty Serena contribution still claims Serena provenance, and `tests/test_symbol_overlay.py:90-93` pins that behaviour as correct. And `util/agent_suite_doctor.py:219-224` — the suite's dogfood health gate — has **no MCP or Serena check at all**, so it reports the suite fully OK while its symbol-enrichment layer is dead.

A fourth, structural contributor cuts across both areas' tooling: `.mcp.json` is gitignored, so **every git worktree checkout lacks it entirely** — verified in this session's worktree and in two centralized worktrees. Under the ecosystem's mandatory-worktree convention, the majority of task sessions therefore start with no project-scope MCP configuration and no local permission allowlist.

**Counts**: 0 CRITICAL-to-production, 2 CRITICAL-to-area, 10 MAJOR, 6 MINOR, 9 OBSERVATION. 5 items could not be verified (§8).

---

## 2. Scope, method, and checklist

### 2.1 Method

Every finding below carries either a `file:line`, a command with its output, or a URL with a fetched excerpt. Read-only throughout: no file in any repository was modified, no git state changed, no configuration edited. The only live probes were read-only (`gpg2 --list-secret-keys`, `gpg2 --card-status`, `gh api`). Per the session sandbox, sibling-repo facts were read via absolute-path file reads rather than `git` invocations outside the worktree.

Three verdict classes are used and kept distinct: **verified pass**, **verified fail**, and **could not verify** (§8).

### 2.2 Checklist applied

| # | Item | Pass means | Verdict |
|---|---|---|---|
| C1 | No stale RSA key reference in juniper-ml tooling | No `B5AFCD0686585249` / `9F5D0FDE` / stale `signingkey` in `scripts/` `util/` `conf/` `.github/` `notes/templates/` `scripts/backups/` | **PASS** (§3.1) |
| C2 | No stale reference in sibling repos | Same tokens absent from all 8 sibling trees | **PASS** (§3.1) |
| C3 | No repo-local signing override | No `[user]`/`[gpg]`/`[commit]` signing keys in any of 9 `.git/config` | **PASS** (§3.1) |
| C4 | No user/system-level stale default key | No `default-key`/`local-user` in `gpg.conf`; no system git signing config | **PASS** (§3.1) |
| C5 | Live git signing config is correct | `user.signingkey` = ed25519 `[S]` subkey, exact-pinned | **PASS** (§3.1) |
| C6 | Launcher/cleanup scripts carry no signing wiring | No gpg/signing logic in the 4 named scripts | **PASS** (§3.1) |
| C7 | Git hooks carry no signing wiring | Active hooks do not sign or set keys | **PASS** (§3.1) |
| C8 | Repo signing utilities target the current key | Any in-repo signing helper names the ed25519 key | **FAIL** — A1-F1 |
| C9 | Signing documentation matches reality | The `notes/` signing record states the current key | **FAIL** — A1-F2 |
| C10 | Fleet signature census clean of the old key | No old-RSA signature in the recent main window | **PASS** (§3.2, Appendix A) |
| C11 | Card binding coherent with the inserted card | Stub card-no equals connected card serial | **FAIL** — A1-F3 |
| C12 | Unattended-signing preconditions stated + enforced | Documented TTL/card/UIF posture | **FAIL** — A1-F4 |
| C13 | Harness flows' signing path characterised | Local-sign vs GitHub-sign per flow, with evidence | **PASS** (§3.5) |
| C14 | Serena MCP wired to an activatable project | Live Serena entry binds a project that resolves | **FAIL** — A2-F1, A2-F2 |
| C15 | Serena failure is observable | Some artifact records Serena unavailability | **FAIL** — A2-F5, A2-F6 |
| C16 | Suite health check covers MCP dependencies | `agent_suite_doctor` has an MCP/Serena check | **FAIL** — A2-F6 |
| C17 | Overlay provenance is honest | `overlay` marker set only on real Serena contribution | **FAIL** — A2-F5 |
| C18 | MCP config survives the worktree convention | Worktree sessions retain project MCP config | **FAIL** — A2-F4 |

---

## 3. Area 1 — headless code-signing

### 3.1 The stale-RSA hunt (C1-C7): verified clean

**Verified live configuration.**

```
$ git config --global --list | grep -e sign -e gpg
user.signingkey=B5619F58FDA4D94E2D73D8BABA18D1A733B1831A!
gpg.program=gpg2
commit.gpgsign=true
tag.gpgsign=true

$ git config --global --show-origin --get user.signingkey
file:/home/pcalnon/.gitconfig   B5619F58FDA4D94E2D73D8BABA18D1A733B1831A!
```

`~/.gitconfig:4` is the sole origin. `B5619F58FDA4D94E2D73D8BABA18D1A733B1831A` is the fingerprint of the ed25519 `[S]` subkey `BA18D1A733B1831A`, exact-pinned with the trailing `!`. **This is correct.**

**Verified absence of the old key.** Searching this worktree for the legacy RSA key ID and its fingerprint prefix:

```
$ grep -rniI -e 'B5AFCD0686585249' -e '9F5D0FDE' . --exclude-dir=.git
notes/JUNIPER_2026-07-16_JUNIPER-ECOSYSTEM_CODE-SIGNING-KEY-MIGRATION-STATUS.md:24
notes/JUNIPER_2026-07-16_JUNIPER-ECOSYSTEM_CODE-SIGNING-KEY-MIGRATION-STATUS.md:29
notes/JUNIPER_2026-07-16_JUNIPER-ECOSYSTEM_CODE-SIGNING-KEY-MIGRATION-STATUS.md:32
```

Three hits, all inside one historical narrative document — **no live reference**. The same search across all eight sibling repos' full trees (excluding `.git`) returned **no matches at all** (`grep … -l ; EXIT-FULL:1`).

Searching the broader signing vocabulary in this worktree's `scripts/ util/ conf/ .github/ notes/templates/` produced 12 hits, all of which are **deliberate signing-disablement for headless automation**, plus one stale-key utility (A1-F1):

| Location | Content class |
|---|---|
| `util/test_gpg_signing.bash:4,6,7` | **Stale ed448 key reference — see A1-F1** |
| `util/fleet_triage/predict_merge.py:57,84,89,90` | `-c commit.gpgsign=false` / `tag.gpgsign=false` for throwaway merges |
| `util/release_train/propose.py:985,1441,1444` | `-c commit.gpgsign=false` on proposal commits |
| `.github/workflows/release-train.yml:476,478,685,687` | `git config --global commit.gpgsign false` in both write jobs |

`scripts/` (including `scripts/backups/`) returned **no** signing hits (`SCRIPTS-EXIT:1`). The four scripts named in the audit brief — `scripts/wake_the_claude.bash`, `scripts/claude_interactive.bash`, `scripts/default_interactive_session_claude_code.bash`, `util/worktree_cleanup.bash` — matched only the substring `sign` inside the words *assign / assigned / Assigning* (`wake_the_claude.bash:403,416,421,511,548,567`). **No signing wiring exists in the launcher or worktree-cleanup path.**

**Verified absence of repo-local and system overrides.**

```
$ grep -niI -e sign -e gpg -e user  <9 sibling .git/config files>
EXIT:1              # no matches in any of the nine

$ git config --system --get-regexp "sign|gpg"
system-exit:1       # no system-level signing configuration
```

`~/.gnupg/gpg.conf` (39 lines, read in full) contains **no `default-key` and no `local-user`** — only algorithm/trust/display preferences. The four active git hooks (`post-checkout`, `post-commit`, `post-merge`, `pre-push` under `core.hooksPath=/…/juniper-ml/.git/hooks`) are pure Git LFS shims and matched no signing tokens (`HOOKGREP-EXIT:1`).

**Conclusion for C1-C7: there is no stale RSA reference anywhere on this host's Juniper surface.** The owner's report is not reproducible against the current local state. §3.2 dates the behaviour it describes to on-or-before 2026-07-14; §8 records what could not be ruled out.

---

#### A1-F1 — MAJOR — repo's only signing-validation utility pins the superseded ed448 key

**Location**: `util/test_gpg_signing.bash:4,6,7`

**Problem**: The repository's sole signing-validation helper validates `93E8591643C507FF` — the **ed448 interim key**, superseded on 2026-08-07 by the ed25519 subkey. Running it "validates" a key that git does not use and that GitHub does not recognise, producing false assurance. Line 4 also omits the exact-key `!` suffix, re-entering the ambiguity class of A1-F5.

**Evidence**:

```
$ cat -n util/test_gpg_signing.bash
     3  echo "Validating code-signing:"
     4  echo test | gpg --clearsign -u 93E8591643C507FF
     5
     6  # git config --global user.signingkey '93E8591643C507FF!'
     7  # gpg --armor --export 93E8591643C507FF

$ git log --format='%h %ad %an | %s' --date=short -- util/test_gpg_signing.bash
49d8a25 2026-07-21 Paul Calnon | adding util script to validate code signing.  added a thread handoff prompt
```

Authored 2026-07-21 — five days after the ed448 repoint, seventeen days before it was itself superseded. Corroboration that the key it names is no longer in use: the live `user.signingkey` is the ed25519 fingerprint (§3.1), and the 3,208-commit census (§3.2) shows the ed448 key has signed **zero** main commits in any repo.

**Recommended fix**: Repoint the utility at the live key by reading `git config --get user.signingkey` rather than hard-coding an ID, so it can never drift again; keep the `!` exact-pin semantics.

---

#### A1-F2 — MAJOR — the canonical signing note is stale and states the wrong current key

**Location**: `notes/JUNIPER_2026-07-16_JUNIPER-ECOSYSTEM_CODE-SIGNING-KEY-MIGRATION-STATUS.md:7,25,46,55-78`

**Problem**: This is the **only** document in `notes/` covering code signing (`ls notes/ | grep -i sign` returns exactly one signing document). It asserts a current state that has been false since 2026-08-07, and its Status line still reads `PARTIALLY MIGRATED — remaining steps DEFERRED`. A human or agent grounding on it would conclude the signing key is misconfigured — which is a strong candidate explanation for the report that motivated this audit.

**Evidence** — document says:

- `:7` — `**Status**: PARTIALLY MIGRATED — remaining steps DEFERRED (see §5)`
- `:25` — the ed448 key `93E8591643C507FF` is `intended replacement; **now** git user.signingkey`
- `:46` — `git config --global user.signingkey '93E8591643C507FF!'` — repointed to the ed448 yubikey-3 key`

Reality, verified above and in §3.3: `user.signingkey` is the **ed25519** subkey fingerprint; the ed448 key is neither used nor registered on GitHub.

Two of the document's deferred §5 items are demonstrably **already satisfied**, and nothing records it:

- §5.1 (UID/email alignment) — the ed25519 primary's only UID is `Paul Calnon (PaulCalnon_overtoad.research@gmail.com_Yubikey-3c_2026-08-06) <paul.calnon@gmail.com>`, matching `user.email=paul.calnon@gmail.com`.
- §5.2 (upload the public key to GitHub) — `gh api /users/pcalnon/gpg_keys` returns the ed25519 key with all three subkeys.
- §5.3 (empirical verification probe) — satisfied for ed25519: `gh api /repos/pcalnon/juniper-ml/commits/be9f131` → `{"verified": true, "reason": "valid"}`.

No 2026-08-07 completion record exists in `notes/`.

**Recommended fix**: Supersede the document with a current-state record (key inventory, the ed25519 pin, the card-binding posture of A1-F3, the preconditions of A1-F4) and mark the 2026-07-16 file historical. Because it is the only signing doc, its staleness is load-bearing for every future diagnosis.

---

### 3.2 Signature census (C10)

Two passes were run against `refs/heads/main` for each of the nine repos via `gh api graphql`, classifying every commit's `signature { … on GpgSignature { keyId } }`.

**Key-ID legend, verified rather than assumed.** The audit brief anticipated GitHub web-flow key `4AEE18F83AFDEB23`; the observed key is `B5690EEEBB952194`. Both are genuine GitHub web-flow keys — the former expired and the latter replaced it:

```
$ gh api /users/web-flow/gpg_keys
{"key_id":"4AEE18F83AFDEB23","created_at":"2017-09-27...","expires_at":"2024-01-16T14:00:00.000-06:00","can_sign":true}
{"key_id":"B5690EEEBB952194","created_at":"2024-01-16T12:13:57.000-06:00","expires_at":null,"can_sign":true}
```

So `B5690EEEBB952194` = **GitHub web-flow (current)** and is the expected signature on every `gh pr merge` commit. Full per-repo tables are in Appendix A (15-commit window) and Appendix B (deep window).

**Pass 1 — last 15 main commits per repo (135 commits total).**

| Classification | Count |
|---|---|
| ed25519 correct (`BA18D1A733B1831A`) | 10 |
| GitHub web-flow current (`B5690EEEBB952194`) | 120 |
| **OLD RSA (`B5AFCD0686585249`)** | **0** |
| ed448 interim (`93E8591643C507FF`) | 0 |
| Unsigned | 5 |

**Pass 2 — deep scan, 3,208 commits across the nine repos.** This locates the last wrong-key use:

| Repo | Commits scanned | Window oldest | OLD-RSA count | Last OLD-RSA commit |
|---|---|---|---|---|
| juniper-ml | 1600 | 2026-05-04 | 228 | `112dc0d7` (**2026-07-14**) |
| juniper-cascor | 500 | 2026-04-05 | 85 | `990697c0` (2026-07-12) |
| juniper-data | 500 | 2026-02-13 | 164 | `3d2c15d0` (2026-05-18) |
| juniper-data-client | 273 | 2026-02-19 | 95 | `b24dfe53` (2026-05-21) |
| juniper-cascor-client | 197 | 2026-02-21 | 75 | `7fbb4969` (2026-07-12) |
| juniper-cascor-worker | 246 | 2026-02-21 | 80 | `86421921` (2026-05-21) |
| juniper-canopy | 500 | 2026-04-29 | 150 | `1bff2b5d` (2026-07-12) |
| juniper-deploy | 274 | 2026-02-25 | 82 | `29501b66` (2026-07-12) |
| juniper-recurrence | 218 | 2026-06-14 | 80 | `d7df91f5` (2026-07-12) |
| **Total** | **3208** | — | **1039** | **2026-07-14** |

#### A1-F3a — MAJOR (historical, now closed) — the old RSA key was the fleet signing key through 2026-07-14

**Problem / finding**: 1,039 main-branch commits in the scanned windows are signed with `B5AFCD0686585249`. The **most recent** is `112dc0d7` in juniper-ml, `2026-07-14T23:12:47Z` — which matches exactly the incident narrative in the migration note (`…MIGRATION-STATUS.md:13-17`: failures during the "release-train wave-2 fan-out (2026-07-14)"). Five siblings' last RSA use is 2026-07-12. **No repo has an old-RSA signature after
2026-07-14** — i.e. none in the last 26 days, and none at all in the 15-commit window.

The interim ed448 key `93E8591643C507FF` produced **0** signatures across all 3,208 commits — it was configured on 2026-07-16 and superseded on 2026-08-07 without ever signing a main-branch commit. This corroborates that the §5.3 "empirical verification probe" of the migration note was genuinely never performed for ed448.

**Verified pass, but recorded as a finding** because it establishes the timeline: the regression the owner describes is **real and historical**, terminating with the 2026-07-16 repoint. It is not currently reproducible on this host.

#### A1-F3b — MINOR — five unsigned bot-lane main commits in the recent window

**Locations**: `juniper-canopy` 3, `juniper-cascor-client` 1, `juniper-recurrence` 1 (Appendix A detail).

**Problem**: Automation lanes (dependabot lockfile regeneration, the AGENTS.md touch-up bot, one direct feature commit) land **unsigned** on `main`. On any repo enforcing a `required_signatures` ruleset these are bypass-warning or rejection candidates — the exact class flagged as deferred decision §5.4 of the migration note.

**Evidence**: `juniper-cascor-client 94a21a55 2026-07-30 UNSIGNED "serena config file"`; `juniper-canopy 91edcbeb 2026-08-03 UNSIGNED "…Update requirements.lock"`; `juniper-canopy 375634c9 2026-07-28 UNSIGNED "chore(deps): auto-regenerate requirements.lock…"`; `juniper-canopy 37645b78 2026-07-28 UNSIGNED "chore(agents-md): bump Last Updated to 2026-07-28…"`; `juniper-recurrence 1c604b31 2026-08-08 UNSIGNED "feat(settings): Wave 3.3 — experiment YAML config layer…"`.

**Recommended fix**: Resolve the deferred §5.4 bot-commit policy explicitly — either route bot commits through the GitHub API signing path already used by `ceremony.py` (§3.5), or scope the rulesets. Not urgent; recorded so the decision is not lost again.

---

### 3.3 Key inventory and the card-binding gotcha (C11)

**Verified keyring state** (`gpg2 --list-secret-keys --keyid-format long --with-colons`, decoded):

| Key | Algo / created | Expiry | Secret location | Role |
|---|---|---|---|---|
| `EDA873F7371DA4C7` | rsa4096, 2019-01-10 | expired 2021-01-09 | offline stub (`#`) | 2019 certify master |
| ├ `740C17517A34845D` `[a]` | rsa4096 | expired | card `0006 09258397` | 2019 auth subkey |
| ├ `B5AFCD0686585249` `[s]` | rsa4096 | expired | card `0006 09258397` | 2019 **signing subkey (legacy)** |
| └ `7630416AE8D411FB` `[e]` | rsa4096 | expired | card `0006 09258397` | 2019 encrypt subkey |
| `B5AFCD0686585249` (standalone `[SC]`) | rsa4096, 2019-01-10 | **never** | card `0006 09258397` | second resolution path — see A1-F5 |
| `93E8591643C507FF` `[SCA]` | ed448, 2025-08-29 | never | **on disk (`+`)** | interim key — see A1-F6 |
| `084FA27B796DABC4` `[cESCA]` | ed25519, 2026-08-07 | never | offline (`sec#`) | **current certify master** |
| ├ `BA18D1A733B1831A` `[s]` | ed25519 | 2028-08-06 | card `0006 24955323` | **current signing subkey** (fpr `B5619F58…33B1831A`) |
| ├ `57E275E9F67430CE` `[e]` | cv25519 | 2028-08-06 | card `0006 24955323` | encrypt |
| └ `F6D949CF7D344E31` `[a]` | ed25519 | 2028-08-06 | card `0006 24955323` | auth |

#### A1-F4 — MAJOR — keyring card stubs bind card 24955323 while the connected card is 24955114

**Locations**: keyring shadow key `~/.gnupg/private-keys-v1.d/47E8366618D8AF8D2291601D7A9250747B92BA19.key` (the `[S]` subkey's keygrip); live card via `gpg2 --card-status`.

**Problem**: Every ed25519 subkey stub records `card-no: 0006 24955323`, but the card physically present is serial **24955114** — a backup YubiKey provisioned with a copy of the same subkeys. When GnuPG needs a card-resident key whose stub names a serial that is not present, the documented behaviour is an interactive `Please insert the card with serial number: …` pinentry prompt. In a headless or non-interactive context that prompt is a **stall or silent failure**, not an error the caller can handle.

**Evidence** — the stub:

```
$ python3 …  # scan private-keys-v1.d for card serials
47E8366618D8AF8D2291601D7A9250747B92BA19 shadowed ['D2760001240100000006249553230000', …]
5B4640F6D7623B9316DC4389660D441A45F4186E shadowed ['D2760001240100000006249553230000', …]
46ABC828E078EC50BDC026AEF06DFFC10E1B8377 shadowed ['D2760001240100000006249553230000', …]
```

`D276000124010000 0006249553230000` decodes to card-no `0006 24955323`.

The connected card:

```
$ gpg2 --card-status
Application ID ...: D2760001240100000006249551140000
Serial number ....: 24955114
Signature PIN ....: not forced
PIN retry counter : 3 0 3
Signature counter : 2
UIF setting ......: Sign=off Decrypt=on Auth=on
Signature key ....: B561 9F58 FDA4 D94E 2D73  D8BA BA18 D1A7 33B1 831A
General key info..: sub  ed25519/0xBA18D1A733B1831A …
ssb>  ed25519/0xBA18D1A733B1831A  created: 2026-08-07  expires: 2028-08-06
                                  card-no: 0006 24955323
```

Note the internal contradiction inside a single `--card-status` output: `Serial number ....: 24955114` (the card) versus `card-no: 0006 24955323` (the stub). The signature key fingerprint on the connected card is identical to the git `user.signingkey`.

**Mitigating empirical evidence** — signing currently works despite the mismatch. Five commits authored today verify Good against the correct key:

```
$ git log --format='%h %G? %GK | %s' --date=short -6 origin/main
be9f131 G BA18D1A733B1831A | test yubi 2
29b9ff7 G BA18D1A733B1831A | test 1
6ea44ee G BA18D1A733B1831A | moving prompt into correct dir
10c22895 G BA18D1A733B1831A | formatting markdown
2b4ac759 G BA18D1A733B1831A | formatting updates notes files
```

and `Signature counter: 2` on card 24955114 proves that card produced signatures itself. So GnuPG did resolve past the serial mismatch in an interactive-capable session. The residual risk is the **non-interactive** case, which was deliberately not reproduced (doing so would require mutating agent/card state — see §8).

**Recommended fix**: Make the stub agree with the card actually in use — either standardise on one card, or re-learn the stubs when swapping (so the recorded serial matches). Whichever is chosen, record the decision in the replacement signing document (A1-F2), because the mismatch is invisible unless someone reads `--card-status` closely enough to notice the two conflicting serials.

---

#### A1-F5 — MAJOR — unattended-signing preconditions are neither documented nor enforced

**Location**: `~/.gnupg/gpg-agent.conf` (entire file), `~/.gnupg/scdaemon.conf:4-5,14`

**Problem**: Unattended local signing on this host depends on a conjunction of four conditions, none of which is stated anywhere in the repo or in `notes/`, and none of which is checked before a headless flow attempts to sign:

1. **The card is present** — and, per A1-F4, resolvable despite the stub serial mismatch.
2. **The PIN is cached in gpg-agent** — `gpg-agent.conf` contains exactly one line, `enable-ssh-support`, and therefore sets **no** cache TTLs. GnuPG's documented defaults apply: *"`--default-cache-ttl n` — Set the time a cache entry is valid to n seconds. **The default is 600 seconds.** Each time a cache entry is accessed, the entry's timer is reset."* and *"`--max-cache-ttl n` … **The default is 2 hours (7200 seconds).**"*
   ([GnuPG Agent Options](https://www.gnupg.org/documentation/manuals/gnupg/Agent-Options.html)). So an idle window over 10 minutes, or any session longer than 2 hours, re-arms an interactive PIN prompt.
3. **`UIF Sign=off`** — currently satisfied (`UIF setting ......: Sign=off Decrypt=on Auth=on`), so signing needs no physical touch. Note `Decrypt=on` and `Auth=on` **do** require a touch; any flow that decrypts or authenticates via the card will block on hardware.
4. **`Signature PIN: not forced`** — currently satisfied; if flipped to `forced`, the card demands PIN entry per signature and no cache can help.

Anything that breaks the chain — reboot, `gpgconf --kill gpg-agent`, card removal/reinsertion, PIN cache expiry, a display-less session where pinentry cannot render — converts a headless signature into a hang or an opaque failure. This is precisely the class the migration note observed on 2026-07-16 (`…MIGRATION-STATUS.md:48-53`) and mitigated only by the convention "always commit with `-c commit.gpgsign=false`" in automation.

**Evidence**:

```
$ cat -n /home/pcalnon/.gnupg/gpg-agent.conf
     1  enable-ssh-support
```

**Recommended fix**: State the four preconditions in the replacement signing document, and — if unattended local signing is ever to be relied upon rather than bypassed — set explicit `default-cache-ttl` / `max-cache-ttl` values so the window is a decision rather than a default. Note that the existing automation convention (disable signing headlessly, §3.5) already sidesteps this; the finding is that the preconditions are undocumented, so a future flow may adopt local signing without knowing them.

---

#### A1-F6 — MINOR — the ambiguous key-ID resolution class is still present in the keyring

**Location**: keyring (`gpg2 --list-secret-keys --with-colons`), rows for `EDA873F7371DA4C7` and the standalone `B5AFCD0686585249`

**Problem**: `…MIGRATION-STATUS.md:32-35` diagnosed that the ID `B5AFCD0686585249` resolves along **two** paths — as an expired subkey of the 2019 master, and as a never-expiring standalone `[SC]` primary — producing nondeterministic `KEYEXPIRED`. **Both paths still exist.** Git is insulated by the `!` exact-pin, but any tool that resolves a key by bare ID re-enters the class — including `util/test_gpg_signing.bash:4`, which passes `-u 93E8591643C507FF` with no `!`.

**Evidence** — the two rows, from the same colon listing:

```
ssb:e:4096:1:B5AFCD0686585249:1547079588:1610150486:::::s:::D2760001240102010006092583970000:::23:   # expired subkey path
sec:f:4096:1:B5AFCD0686585249:1547079588:::-:::scSC:::D2760001240102010006092583970000:::23::0:       # never-expiring standalone path
```

Field 6 (`1610150486` = 2021-01-09) vs. field 6 empty (never) on the second row is the ambiguity.

**Recommended fix**: Retire the 2019 chain locally, or ensure every signing invocation uses the `!` exact-key suffix. Low urgency — nothing live resolves that ID today.

---

#### A1-F7 — MINOR — the ed448 key holds signing-capable secret material on disk

**Location**: keyring row for `93E8591643C507FF`

**Problem**: The interim key is `[SCA]`-capable, never expires, has **secret material on disk** (colon field 15 is `+`, not `#` and not a card serial), is no longer referenced by git, and is **not registered on the GitHub account** (`gh api /users/pcalnon/gpg_keys` returns only the ed25519). An unused, non-expiring, on-disk signing key is standing key-hygiene debt: it can sign, and nothing would recognise the result.

**Evidence**:

```
sec:u:448:22:93E8591643C507FF:1756445546:::u:::scaSCA:::+::ed448:8::0:
```

Field 15 = `+` (secret available on disk); field 12 = `scaSCA`; field 7 (expiry) empty.

**Recommended fix**: Decide its disposition — move to a card, move offline, or revoke — and record the decision. Do not silently leave it live.

---

#### A1-F8 — OBSERVATION — key backup material staged inside the live keyring directory

**Location**: `~/.gnupg/`

**Problem**: The active GnuPG home contains a key-backup archive and two scratch directories:

```
-rw-rw-r--  1 pcalnon pcalnon  5137 Aug  8 23:19 Yubikey-3c_24955323-and-24955114_key-backups_2026-08-08.tgz
drwxrwxr-x  3 pcalnon pcalnon  4096 Aug  8 23:20 backups-DELETE_ME
drwxrwxr-x  2 pcalnon pcalnon  4096 Aug  8 23:20 working-DELETE_ME
drwxrwxr-x  2 pcalnon pcalnon  4096 Jul 23 18:29 recovery_keys
-rw-------  1 pcalnon pcalnon   969 Aug  3 13:38 sk_9D55EB5F6FB0CE56.gpg
```

The archive and the two `*-DELETE_ME` directories are mode 664/775 (group- and world-readable). The parent `~/.gnupg` is `drwx------`, so other local users cannot traverse to them — the exposure is limited to anything running as this user, plus any backup or sync process that copies `~/.gnupg` wholesale. No key material was opened or quoted by this audit. The two `DELETE_ME` names indicate intended cleanup that has not happened.

**Recommended fix**: Move backup artifacts out of the live keyring directory to encrypted offline storage; complete the `DELETE_ME` cleanup.

---

#### A1-F9 — OBSERVATION — `sshcontrol` contains a fingerprint where a keygrip is required, plus a stale card keygrip

**Location**: `~/.gnupg/sshcontrol`

**Problem**: gpg-agent's `sshcontrol` is a list of **keygrips**. The file's three entries are:

```
800E00F15B50DCD53DFEB9DF3A4473B3585E230D      # keygrip of the 2019 RSA [a] subkey, on the absent card 0006 09258397
E7D6DCB076D687255853480E7C8C81EFD16A31C9 0
06DBAC384131E0380D89923F084FA27B796DABC4      # this is the ed25519 PRIMARY key FINGERPRINT, not a keygrip
```

The third entry is the fingerprint of `084FA27B796DABC4`; that key's actual keygrip is `27921680C72C28ED18EC6186EF2BCBDD30B6299B`. It will therefore never match, and the current card auth subkey is not exposed over gpg-agent's SSH socket. The first entry names a key on a card that is not present — if gpg-agent were ever the active `SSH_AUTH_SOCK`, offering it would trigger the same insert-card prompt class as A1-F4, on the git push path.

**Mitigating factor (verified)**: `~/.ssh/config` pins per-host **file-based** identities for all nine `github.com-juniper-*` hosts (`IdentityFile /home/pcalnon/.ssh/id_ed25519_gh_juniper*`), so git pushes today do not depend on the card at all. `enable-ssh-support` is nevertheless on in `gpg-agent.conf`, so the path is latent rather than absent.

**Recommended fix**: Correct or remove the entries. Low urgency given the file-based SSH identities.

---

#### A1-F10 — OBSERVATION — `scdaemon.conf` sets a deprecated no-op

**Location**: `~/.gnupg/scdaemon.conf:6`

**Problem**: `card-timeout 1` reads like an aggressive card power-down that would defeat PIN caching. It does nothing. GnuPG documents: *"`--card-timeout n`: This option is deprecated. In GnuPG 2.0, it used to be used for DISCONNECT command to control timing issue. Since DISCONNECT command works synchronously, it has no effect."* ([GnuPG Scdaemon
Options](https://www.gnupg.org/documentation/manuals/gnupg/Scdaemon-Options.html)). Recorded specifically so a future headless-signing investigation does not mis-attribute a stall to it. `disable-ccid` + `pcsc-driver` (lines 4-5) mean the card is reached through `pcscd`; if that daemon is down the card is simply invisible — a genuine, and separate, precondition for A1-F5.

---

#### A1-F11 — OBSERVATION — no reset code configured on the connected card

**Location**: `gpg2 --card-status` → `PIN retry counter : 3 0 3`

**Problem**: The middle counter (the reset code / PW2) is `0`, i.e. unset. Three wrong user-PIN entries would block PW1 with no reset-code recovery path, leaving only the Admin PIN. Relevant to headless operation because an automated flow that repeatedly retries a wrong PIN can exhaust the counter unattended.

---

### 3.4 GitHub-side key state

#### A1-F12 — OBSERVATION — the account carries exactly one GPG key; a future stale-key signature would fail loudly

**Evidence**:

```
$ gh api /users/pcalnon/gpg_keys --jq 'length'
1
$ gh api /users/pcalnon/gpg_keys --jq '.[] | .key_id, (.subkeys[]?.key_id)'
084FA27B796DABC4
BA18D1A733B1831A
57E275E9F67430CE
F6D949CF7D344E31
$ gh api /users/pcalnon/ssh_signing_keys --jq 'length'
0
```

Neither `B5AFCD0686585249` nor `93E8591643C507FF` appears in the public list. Historical RSA-signed commits nonetheless still read as verified:

```
$ gh api /repos/pcalnon/juniper-ml/commits/112dc0d7 --jq '{date,verified,reason}'
{"date":"2026-07-14T23:12:47Z","verified":true,"reason":"valid"}
$ gh api /repos/pcalnon/juniper-cascor/commits/990697c0 → {"verified":true,"reason":"valid"}
$ gh api /repos/pcalnon/juniper-canopy/commits/1bff2b5d → {"verified":true,"reason":"valid"}
```

This is consistent with GitHub's documented persistence model: *"When a commit signature is verified upon being pushed to GitHub, a verification record is stored alongside the commit"* and *"previously verified commits retain their verified status based on the record created during the initial verification"* ([About commit signature verification](https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification)).

**Consequence — the important one**: because the old key is not currently on the account, any *new* commit signed with it would land **Unverified**, and on repos enforcing `required_signatures` the push would be **rejected**. A stale-RSA regression is therefore a loud failure today, not a silent one. This materially bounds the risk of the reported issue. See §8 for the one thing that could not be settled: whether the key is removed outright or merely hidden from the public endpoint.

---

### 3.5 Which harness flows local-sign vs GitHub-sign (C13) — verified

#### A1-F13 — OBSERVATION (characterisation) — the harness's PR flows are GitHub-signed; no local key is involved

| Flow | Signing path | Evidence |
|---|---|---|
| PR merge (`gh pr merge`, squash/merge commits) | **GitHub web-flow key** `B5690EEEBB952194` — server-side, no local key | 120 of the 135 census commits; key identity confirmed via `gh api /users/web-flow/gpg_keys` |
| Release-train **ceremony** archive commit | **GitHub-signed** — commit created by GraphQL `createCommitOnBranch`, never a local commit | `util/release_train/ceremony.py:36,250,257`; `AGENTS.md:665` |
| Release-train **propose** commits | **Unsigned local** — signing explicitly disabled | `util/release_train/propose.py:985,1441,1444`; `AGENTS.md:665` |
| Release-train workflow jobs | **Unsigned** — global disable in both write jobs | `.github/workflows/release-train.yml:478,687` |
| Fleet-triage predicted merges | **Unsigned** — throwaway detached clone | `util/fleet_triage/predict_merge.py:84,89,90` |
| Owner's direct commits/pushes from this host | **Locally signed** with the ed25519 card subkey | The 10 `BA18D1A733B1831A` census commits, all 2026-08-09 |

`AGENTS.md:665` states the design intent verbatim: *"`propose.py`'s proposal commits are unsigned local git commits … so the headless run never trips the owner's YubiKey signing config. `ceremony.py`'s exempt-archive commit is instead created via the GitHub API (`createCommitOnBranch`, no local commit), so it is **GitHub-signed / Verified**"*.

**Implication for the reported regression**: the agentic PR flows exercised in this session's class of work **never touch the local signing key**. The local key is exercised only by the owner's own direct commits. That narrows the surface on which a stale-key regression could manifest to exactly one path — and §3.1/§3.2 show that path is currently correct.

---

## 4. Area 2 — Serena MCP disuse

### 4.1 Root causes, ranked

#### A2-F1 — CRITICAL (to the area) — ROOT CAUSE 1: the live Serena MCP entry never binds a project

**Location**: `/home/pcalnon/Development/python/Juniper/juniper-ml/.mcp.json:14-26`

**Problem**: The project-scope Serena server is launched **without `--project`**. Serena consequently starts with no active project, and the first symbol-resolution call fails. The three legacy entries in `~/.claude.json` — the only other Serena configurations on the machine — **do** pass `--project`, which is why Serena worked in the pre-polyrepo era and stopped working after the migration to per-repo checkouts.

**Evidence** — the live entry:

```json
"serena": {
  "type": "stdio",
  "command": "uvx",
  "args": ["--from","git+https://github.com/oraios/serena","serena","start-mcp-server","--context","claude-code"],
  "env": {}
}
```

versus a legacy entry from `~/.claude.json`:

```json
"…/JuniperCascor/juniper_cascor" -> {"command":"uvx","args":["--from","git+https://github.com/oraios/serena","serena","start-mcp-server","--context","claude-code","--project","/home/pcalnon/Development/python/Juniper/JuniperCascor/juniper_cascor"]}
```

The runtime consequence, from Serena's own log for this session:

```
ERROR 2026-08-09 17:15:46,986 [Task-1:GetCurrentConfigTool] serena.task_executor:run_task:68 -
  Error during execution of Task-1:GetCurrentConfigTool: No active project. Ask the user to provide the
  project path or to select a project from this list of known projects:
  ['Juniper', 'juniper-canopy', 'juniper-cascor-client', 'juniper-cascor-worker', 'juniper_cascor']
serena.tools.tools_base.ToolCallError: No active project. …
```

(`~/.serena/logs/2026-08-09/mcp_20260809-032336_3803193.txt`)

**Recommended fix**: out of scope for this audit — a separate plan document owns the design. The attachment point is recorded in §6.

---

#### A2-F2 — CRITICAL (to the area) — ROOT CAUSE 2: juniper-ml is absent from Serena's project registry

**Location**: `~/.serena/serena_config.yml`, key `projects`

**Problem**: Even a manual `activate_project` cannot rescue A2-F1 by name, because juniper-ml is not registered. The registry holds five paths, four of which are current-era repos plus the parent directory:

```
projects:
  - /home/pcalnon/Development/python/Juniper
  - /home/pcalnon/Development/python/Juniper/juniper-canopy
  - /home/pcalnon/Development/python/Juniper/juniper-cascor
  - /home/pcalnon/Development/python/Juniper/juniper-cascor-client
  - /home/pcalnon/Development/python/Juniper/juniper-cascor-worker
```

**Absent**: juniper-ml, juniper-data, juniper-data-client, juniper-deploy, juniper-recurrence — five of the nine repos, including the one whose agent suite depends on the overlay. Serena's startup banner confirms the effective set:

```
INFO  2026-08-09 17:17:32,629 serena.agent:__init__:640 -
  Available projects: Juniper, juniper-canopy, juniper-cascor-client, juniper-cascor-worker, juniper_cascor
```

(`~/.serena/logs/2026-08-09/mcp_20260809-171732_1671024.txt:7`)

Note that juniper-ml **does** ship a valid `.serena/project.yml` (`project_name: "juniper_ml"`, `languages: [python]`) and it **is** git-tracked (`git ls-files .serena/` → `.serena/.gitignore`, `.serena/project.yml`), so the repo-side artifact is fine — only the machine-level registry is missing it.

---

#### A2-F3 — MAJOR — ROOT CAUSE 3: no instruction tells an agent to activate a project, and silence is explicitly sanctioned

**Location**: `.claude/skills/template-agent/SKILL.md:42-47`

**Problem**: The capability to recover from A2-F1/A2-F2 exists and is pre-approved — `activate_project` is in Serena's exposed 23-tool surface (log line 13) and is the **first** entry in the permission allowlist (`.claude/settings.local.json:7`). No document anywhere instructs an agent to call it. Instead the Skill instructs a bare `find_symbol` / `find_declaration` call and then authorises abandonment:

```
42  **Serena symbol overlay (optional enrichment, OQ-8).** The bundle's `symbol_probe` is grep-based — the
43  path-invoked helper cannot reach Serena. Because you run in the main conversation you DO have MCP
44  access: for the task's named symbols, call Serena `find_symbol` / `find_declaration`, write the results
45  to a JSON file, and merge them with `python util/prompt_discovery/symbol_overlay.py --bundle <bundle>
46  --serena <serena>` (Serena-resolved wins; grep is the fallback; an unresolvable symbol stays
47  `UNRESOLVED`). Skip silently if Serena is unavailable — the grep bundle stays valid.
```

Line 47 is the design-level authorisation for the silence. Contrast the *hard* handling one paragraph earlier for the discovery CLI (`SKILL.md:39`): *"If it exits non-zero (a `discovery_failed` envelope) **stop and report** — never proceed on an empty bundle."* The two dependencies of the same step have opposite failure doctrines, and the softer one has been failing for four months undetected.

---

#### A2-F4 — MAJOR — worktree sessions lose project-scope MCP configuration entirely

**Locations**: `.gitignore:170` (juniper-ml), `juniper-canopy/.gitignore:207`

**Problem**: `.mcp.json` is gitignored in both repos that have one, and is untracked:

```
$ git ls-files --error-unmatch .mcp.json
error: pathspec '.mcp.json' did not match any file(s) known to git
$ git check-ignore -v .mcp.json
.gitignore:170:.mcp.json    .mcp.json
```

Therefore **no worktree checkout contains it**. Verified in three places:

```
$ ls .mcp.json .claude/settings.local.json          # this session's worktree
ls: cannot access '.mcp.json': No such file or directory
ls: cannot access '.claude/settings.local.json': No such file or directory

$ ls …/worktrees/juniper-canopy--fix--relay-supervisor-…/.mcp.json
$ ls …/worktrees/juniper-cascor--feat--w6-snapshots-dir-…/.mcp.json
ls: cannot access …: No such file or directory   (both)
```

The ecosystem convention mandates worktrees for all feature, bugfix, and task work (`CLAUDE.md`, Worktree Procedures). So the *majority* of task sessions start with **neither** the project MCP servers **nor** the local permission allowlist. This session has Serena only because MCP resolution happened at launch from the primary checkout; the worktree itself contributes nothing. An upward search found no `.mcp.json` at any ancestor (`.claude/worktrees/`, `juniper-ml/.claude/`, `…/Juniper/`, `$HOME`).

Additional detail: the worktree's `.claude/` holds only stale backups — `settings.local-ORIG_1.json` … `settings.local-ORIG_5.json` and `settings.local-WORKING.json` — with **no active `settings.local.json`**, so its 44-entry permission allowlist is also absent from worktree sessions.

---

#### A2-F5 — MAJOR — the overlay stamps Serena provenance unconditionally, and a test pins the lie

**Location**: `util/prompt_discovery/symbol_overlay.py:35,48,50`; `tests/test_symbol_overlay.py:90-93`

**Problem**: `merge_symbol_probe` marks the bundle slice as Serena-overlaid **regardless of whether Serena contributed anything**. Line 35 tolerates an empty/`None` Serena mapping (`for name, fact in (serena or {}).items()`), so the loop body never runs and `symbols` remains 100% grep output — yet line 50 unconditionally sets the marker:

```python
35      for name, fact in (serena or {}).items():
…
48              symbols[name] = {"status": "unresolved", "definition": None, "signature": None, "source": "serena"}
49      slice_["symbols"] = symbols
50      slice_["overlay"] = "serena"
```

A downstream consumer — notably the prompt-validator's R3.4b rule, which reads *"symbols/signatures — resolve from the bundle's symbol facts (produced by discovery's Serena…"* (`.claude/agents/prompt-validator.md:96`) — cannot distinguish a Serena-enriched bundle from a pure-grep one. Per-symbol provenance is honest (line 46 preserves `source: "grep"`), but the slice-level marker is not, and the slice-level marker is what signals "enrichment happened".

Line 48 is a second, smaller inaccuracy: a symbol Serena **failed** to resolve is recorded `source: "serena"`, attributing an unresolved result to a tool that did not resolve it.

**The behaviour is locked in by test**:

```python
90      def test_empty_serena_preserves_grep(self):
91          out = self.mod.merge_symbol_probe(_bundle({"foo": {"status": "resolved", "definition": "a.py:1", "signature": "def foo()"}}), {})
92          self.assertEqual(out["symbol_probe"]["symbols"]["foo"]["definition"], "a.py:1")
93          self.assertEqual(out["symbol_probe"]["overlay"], "serena")
```

Line 93 asserts that an **empty** Serena input still yields `overlay == "serena"`. Any future fix must change this test — which is exactly why it is worth naming here.

The module also has **no failure channel at all**: no exception, no status field, no non-zero exit path for "Serena unavailable". Silent degradation is structural, not incidental.

---

#### A2-F6 — MAJOR — the suite health check has no MCP or Serena coverage

**Location**: `util/agent_suite_doctor.py:219-224`

**Problem**: The doctor is the custom-agent suite's dogfood health gate, and its check registry is a closed list of seven:

```python
219  def run_checks(root: Path, no_discovery: bool = False):
220      checks = [check_agents, check_skill, check_templates, check_rubric, check_data_layer]
221      if not no_discovery:
222          checks.append(check_discovery)
223      checks.append(check_mirror)
224      return [fn(root) for fn in checks]
```

None of the seven is MCP-aware; a repository-wide grep for `serena|Serena|mcp|MCP` in the file returns nothing. So the doctor reports the suite **fully OK** while the symbol-enrichment layer described in `AGENTS.md:230,510` has been dead for 123 days. This is the single most consequential guardrail gap in Area 2: the mechanism designed to catch suite rot is structurally blind to this class of rot.

Notably, the adjacent `check_discovery` (`:167-186`) is a correct model of the opposite doctrine — it shells the CLI, and returns `FAIL` on a missing binary, a non-zero exit, non-JSON stdout, or a bundle missing `schema_version` / `provenance.head_sha`. The pattern to follow already exists in the same file.

---

#### A2-F7 — MAJOR — quantified disuse is 123 days / 248 sessions, ~4x and ~11x the reported figure

**Location**: `~/.serena/logs/` (152 date directories, 2025-11-18 → 2026-08-09)

**Problem**: Counting real tool applications (log lines emitted by `serena.tools.tools_base:_log_tool_application`) rather than server starts:

```
WINDOW 2026-04-09 .. 2026-08-08 (exclusive of today)
  calendar days since last productive use: 123
  distinct days with a serena server start: 73
  serena MCP server sessions started: 248
  productive tool applications: 0
```

The last date directory containing any tool application is **2026-04-08** (6 calls: `activate_project`, `get_symbols_overview`). Every subsequent server start did nothing. The only call in the entire window is today's `get_current_config`, from this audit's own smoke probe, which errored.

For contrast, the pre-regression cadence was substantial: 2026-04-03 recorded 81 tool applications across 10 sessions; 2026-04-04 recorded 46 across 7 — using `find_symbol`, `get_symbols_overview`, `find_file`, `search_for_pattern`, `read_memory`.

The reported figures (">=29 days, 22 sessions") **understate** the outage by roughly 4x in days and 11x in sessions. Recorded because remediation sizing and any "did it ever work here" question depend on the true window: Serena's last productive day predates the entire custom-agent suite's OQ-8 overlay work.

---

#### A2-F8 — MINOR — the Serena permission allowlist has drifted from the tool surface

**Location**: `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/settings.local.json:7-20`

**Problem**: 14 Serena tools are allowlisted; Serena 1.7.1's `claude-code` context exposes 23; only **8** overlap.

**Dead allowlist entries (6)** — tools that no longer exist or are excluded by the context: `check_onboarding_performed`, `list_dir`, `search_for_pattern`, `think_about_collected_information`, `think_about_task_adherence`, `think_about_whether_you_are_done`.

**Exposed but not allowlisted (15)** — would raise a permission prompt: `find_referencing_symbols`, `find_declaration`, `find_implementations`, `get_diagnostics_for_file`, `get_current_config`, `rename_symbol`, `safe_delete_symbol`, `replace_content`, `replace_in_files`, `replace_symbol_body`, `insert_after_symbol`, `insert_before_symbol`, `delete_memory`, `rename_memory`, `edit_memory`.

The Skill's own instruction (`SKILL.md:44`) names `find_declaration` — which is **not** allowlisted. In an unattended flow that is a prompt-stall or a denial, i.e. a second, independent path to the same silent skip.

**Evidence** — the exposed set, from the startup log:

```
INFO  2026-08-09 17:17:32,673 serena.agent:__init__:681 - Number of exposed tools: 23. Exposed tools:
  ['activate_project','delete_memory','edit_memory','find_declaration','find_implementations',
   'find_referencing_symbols','find_symbol','get_current_config','get_diagnostics_for_file',
   'get_symbols_overview','initial_instructions','insert_after_symbol','insert_before_symbol',
   'list_memories','onboarding','read_memory','rename_memory','rename_symbol','replace_content',
   'replace_in_files','replace_symbol_body','safe_delete_symbol','write_memory']
```

---

#### A2-F9 — MINOR — the only `~/.claude.json` Serena entries point at directories that no longer exist

**Location**: `~/.claude.json`, `projects` map

**Problem**: Of seven project entries, four reference paths absent from disk, and **three of those four are the only entries carrying Serena**:

```
EXISTS  /home/pcalnon/Development/python/Juniper                          mcpServers: []
MISSING /home/pcalnon/Development/python/Juniper/JuniperData/juniper_data     mcpServers: ['serena']
MISSING /home/pcalnon/Development/python/Juniper/JuniperCanopy/juniper_canopy mcpServers: ['serena','hf-mcp-server','exa','alphavantage','kaggle']
MISSING /home/pcalnon/Development/python/Juniper/JuniperCascor/juniper_cascor mcpServers: ['serena','hf-mcp-server','kaggle']
MISSING /home/pcalnon/Development/python/Juniper/juniper                  mcpServers: []
EXISTS  /home/pcalnon/Development/python/Juniper/juniper-ml               mcpServers: ['playwright']
EXISTS  /home/pcalnon/Development/python/Juniper/juniper-cascor           mcpServers: []
```

User-scope `mcpServers` is `['deepwiki','chrome-devtools']` — **no Serena**. So `~/.claude.json` contributes exactly zero working Serena configuration, and the only live one is the `--project`-less `.mcp.json` entry of A2-F1.

---

#### A2-F10 — MINOR — Serena's registry mixes naming eras, so name-based activation is a guess

**Location**: `~/.serena/serena_config.yml` `projects`; `juniper-ml/.serena/project.yml:2`

**Problem**: Serena reports `Juniper, juniper-canopy, juniper-cascor-client, juniper-cascor-worker, juniper_cascor`. Four names derive from directory names (kebab-case, current era); `juniper_cascor` derives from that repo's `project_name` field (snake_case, pre-polyrepo era); `Juniper` is the parent directory. juniper-ml's own `project.yml` declares `project_name: "juniper_ml"`, so if registered it would appear as
`juniper_ml`, not `juniper-ml`. An agent attempting `activate_project("juniper-ml")` would fail even after A2-F2 is resolved, unless the naming is reconciled.

---

#### A2-F11 — OBSERVATION — `.serena/` tracking is inconsistent across the fleet

| Repo | `.serena/project.yml` | Tracking |
|---|---|---|
| juniper-ml | present (983 B, `project_name: juniper_ml`) | **git-tracked** (`git ls-files .serena/`) |
| juniper-cascor | present (9865 B) | not checked (sandbox) |
| juniper-canopy | present (9858 B) | **fully gitignored** — `juniper-canopy/.gitignore:82-90` ignores `.serena/**` |
| juniper-cascor-client | present (9865 B) | not checked |
| juniper-cascor-worker | present (9865 B) | not checked |
| juniper-data | present (7537 B, Feb 21) | not checked |
| juniper-data-client | **absent** | — |
| juniper-deploy | **absent** | — |
| juniper-recurrence | **absent** | — |
| Juniper (parent) | present (9851 B) | n/a — not a git repo |

Three repos have no Serena project config at all; one repo tracks it while another explicitly ignores it. A fleet-wide convention does not exist.

---

#### A2-F12 — OBSERVATION (security) — plaintext credentials at rest in MCP config files

**Locations**: `/home/pcalnon/Development/python/Juniper/juniper-ml/.mcp.json:7`; `/home/pcalnon/Development/python/Juniper/juniper-canopy/.mcp.json:5`

**Problem**: The juniper-ml file carries a Hugging Face bearer token in an `Authorization` header; the juniper-canopy file embeds an Exa API key as a URL query parameter. Values are deliberately not reproduced here.

**Mitigating factor (verified — this is why the severity is OBSERVATION, not CRITICAL)**: both files are gitignored and untracked, so neither credential is committed:

```
juniper-ml/.gitignore:170       .mcp.json
juniper-canopy/.gitignore:207   .mcp.json
$ git ls-files --error-unmatch .mcp.json   → error: did not match any file(s) known to git
```

Residual exposure is at-rest only: file mode 664 (readable by group/other on a multi-user host), plus capture by any whole-home backup, and the standing risk of an accidental `git add -f`. The canopy file's key is additionally in a URL, which is the most log-leak-prone position for a secret.

---

#### A2-F13 — OBSERVATION — the `claude-code` context strips six Serena tools

**Location**: `~/.serena/logs/2026-08-09/mcp_20260809-171732_1671024.txt:11`

```
INFO  serena.agent:apply:182 - SerenaAgentContext[name='claude-code'] excluded 6 tools:
  create_text_file, read_file, execute_shell_command, find_file, list_dir, search_for_pattern
```

Recorded so that any remediation is sized against the real surface: a correctly activated Serena provides the **symbol/LSP** tools only. The OQ-8 overlay design (`find_symbol` / `find_declaration`) is compatible with this; any plan assuming Serena's file/grep tools is not.

---

## 5. Silent-failure mechanism analysis

### 5.1 Area 2 — the four-layer silence

Serena's outage survived 123 days because four independent layers each convert a failure into a non-event. Removing any *one* of them would have surfaced it.

| Layer | Mechanism | Evidence | Effect |
|---|---|---|---|
| **L1 — Configuration** | Server starts successfully but binds no project; the failure is deferred to first tool use | `.mcp.json:14-26` (no `--project`); `serena_config.yml projects` lacks juniper-ml | Startup looks healthy: process runs, 23 tools registered, dashboard binds. Nothing signals a defect until a symbol is requested. |
| **L2 — Instruction** | The agent is told to abandon Serena on error, with no diagnosis or retry | `SKILL.md:47` "Skip silently if Serena is unavailable" | A `ToolCallError: No active project` becomes a no-op. The adjacent discovery-CLI dependency has the opposite doctrine (`SKILL.md:39` "stop and report"). |
| **L3 — Provenance** | The artifact claims Serena enrichment even with zero Serena input | `symbol_overlay.py:50` unconditional `overlay = "serena"`; `:35` tolerates empty input; pinned by `test_symbol_overlay.py:93` | A pure-grep bundle is indistinguishable from an enriched one. The one downstream consumer that could notice (`prompt-validator.md:96`, R3.4b) is reading a marker that is always present. |
| **L4 — Health check** | The suite's own doctor has no MCP awareness | `agent_suite_doctor.py:219-224` — seven checks, none MCP | The mechanism designed to detect suite rot is blind to this class. Reports OK indefinitely. |

**Amplifier — the worktree convention (A2-F4).** Because `.mcp.json` is gitignored, a worktree-launched session has no project MCP servers at all. Under a mandatory-worktree policy this is the common case, so even a *correct* `.mcp.json` would be absent for most task sessions. This converts a config bug into an environment-dependent one — the hardest kind to reproduce, and a strong explanation for why nobody noticed a regression that began in April.

**Secondary amplifier — permission drift (A2-F8).** Even had L1-L3 been fixed, `find_declaration` — the tool `SKILL.md:44` explicitly names — is not allowlisted, so an unattended flow would hit a permission prompt and take the same silent-skip path.

**No telemetry exists.** `util/prompt_discovery/cli.py:59-65` stamps a provenance envelope with `schema_version`, `captured_at`, `head_sha`, `dirty`, `ttl_seconds`, and `per_probe_status` — but the Serena overlay is applied *after* `cli.py` by a different module, so no probe status ever describes it. There is no field in any artifact whose value would differ between "Serena worked" and "Serena has been dead for four months".

### 5.2 Area 1 — the signing silence classes

Signing has the opposite profile: most of its failure modes are **loud**, and the audit should say so plainly rather than manufacture alarm.

| Class | Loud or silent | Basis |
|---|---|---|
| Signing with the retired RSA key today | **Loud** | Key absent from the account's public GPG list (A1-F12) → Unverified + `required_signatures` rejection |
| Local signing fails (card absent / PIN uncached) | **Loud locally** | `git commit` fails or pinentry blocks; the 2026-07-16 incident is precisely this (`…MIGRATION-STATUS.md:48-53`) |
| Headless flows are unsigned | **Silent by design** | `propose.py:1441-1444`, `release-train.yml:478,687` disable signing deliberately; five unsigned main commits observed (A1-F3b) |
| Card-serial stub mismatch | **Silent-to-stalling** | A1-F4 — an interactive session resolves it; a non-interactive one has nowhere to render the insert-card prompt |
| Documentation drift | **Silent** | A1-F1, A1-F2 — a stale validator and a stale note both report a superseded key as current; nothing gates either |

**The one genuinely silent signing class is documentation.** No CI job, lint, or test anywhere in the fleet asserts anything about signing configuration — verified by the absence of any `signingkey` / `default-key` / `local-user` reference in all nine repos' `.github/` trees. `util/test_gpg_signing.bash` is manual and, per A1-F1, checks the wrong key. So a key rotation can leave the repo's own tooling and its only signing
document stale indefinitely, which is very likely what produced the report that opened this audit.

---

## 6. Guardrail attachment-point inventory

Attachment points only — designs belong to the separate plan document.

### 6.1 Area 2 attachment points

| # | Point | Location | Current state | Why it is the right seam |
|---|---|---|---|---|
| G1 | Doctor check registry | `util/agent_suite_doctor.py:219-224` | 7 checks, no MCP | The suite's only health gate; adding a member to `checks` is the whole integration. `tests/test_agent_suite_doctor.py` already exercises per-check FAIL arms. |
| G2 | Doctor fail-closed template | `util/agent_suite_doctor.py:167-186` (`check_discovery`) | Correct doctrine already implemented | Existing in-file precedent for subprocess-probe + FAIL on missing/non-zero/malformed. |
| G3 | Overlay provenance marker | `util/prompt_discovery/symbol_overlay.py:50` (and `:35`, `:48`) | Unconditional `overlay = "serena"` | The single line that makes an unenriched bundle indistinguishable from an enriched one. |
| G4 | Overlay pinning test | `tests/test_symbol_overlay.py:90-93` | Asserts the unconditional marker | Any provenance change must edit this test; naming it prevents a surprise red. |
| G5 | Discovery provenance envelope | `util/prompt_discovery/cli.py:59-65` (`per_probe_status`) | Has a per-probe status map; overlay not represented | The natural home for a machine-readable `serena: ok/unavailable/skipped` status. |
| G6 | Skill failure doctrine | `.claude/skills/template-agent/SKILL.md:47` (contrast `:39`) | "Skip silently"; sibling dependency says "stop and report" | The instruction-level decision point; the stricter doctrine already exists two lines up. |
| G7 | MCP server definition | `juniper-ml/.mcp.json:14-26` | No `--project` | Root cause 1's single edit site. |
| G8 | Serena project registry | `~/.serena/serena_config.yml` `projects` | 5 paths; juniper-ml + 4 others absent | Root cause 2's site. Machine-level, so it needs a provisioning story, not a repo edit. |
| G9 | Worktree MCP inheritance | `.gitignore:170`; `juniper-canopy/.gitignore:207` | `.mcp.json` untracked → absent from all worktrees | Governs whether *any* MCP fix reaches the sessions that do the work. Interacts with the secrets issue (A2-F12): the file cannot simply be tracked as-is. |
| G10 | Permission allowlist | `juniper-ml/.claude/settings.local.json:7-20` | 14 entries, 6 dead, `find_declaration` missing | Determines whether an activated Serena is usable unattended. Also untracked → absent in worktrees. |
| G11 | Downstream consumer | `.claude/agents/prompt-validator.md:96` (R3.4b) | Consumes symbol facts; trusts the marker | The one place that could reject a falsely-labelled bundle. |
| G12 | Repo-side Serena config | `juniper-ml/.serena/project.yml` (tracked) | Valid; `project_name: juniper_ml` | Already correct and version-controlled — the naming reconciliation of A2-F10 lands here. |

### 6.2 Area 1 attachment points

| # | Point | Location | Current state |
|---|---|---|---|
| G13 | Signing validation utility | `util/test_gpg_signing.bash:4,6,7` | Hard-codes the superseded ed448 key; the only in-repo signing check |
| G14 | Canonical signing document | `notes/JUNIPER_2026-07-16_JUNIPER-ECOSYSTEM_CODE-SIGNING-KEY-MIGRATION-STATUS.md` | Stale; the only signing doc in `notes/` |
| G15 | Card/agent posture | `~/.gnupg/gpg-agent.conf`, `~/.gnupg/scdaemon.conf`, card `UIF`/`forcesig` | No TTLs set (defaults apply); one deprecated no-op; posture undocumented |
| G16 | Headless signing-disable convention | `propose.py:1441-1444`, `predict_merge.py:84-90`, `release-train.yml:478,687` | Consistently applied — the mitigation that makes A1-F4/A1-F5 tolerable today |
| G17 | GitHub-side signing path | `ceremony.py:250-257` (`createCommitOnBranch`) | Working; produces GitHub-signed commits satisfying `required_signatures` |
| G18 | CI signing gate | **none exists** | No `.github/` reference to signing config in any of the nine repos |

---

## 7. Additional latent issues

Flagged in passing; none was the audit's target.

| ID | Severity | Issue |
|---|---|---|
| L1 | OBSERVATION | `~/.gnupg` holds a key-backup archive plus two `*-DELETE_ME` directories at mode 664/775 (A1-F8). |
| L2 | OBSERVATION | `sshcontrol` lists a fingerprint where a keygrip is required, and a keygrip for a key on an absent card (A1-F9). Latent because `enable-ssh-support` is on; inert because `~/.ssh/config` pins file-based identities. |
| L3 | OBSERVATION | `scdaemon.conf:6 card-timeout 1` is a documented no-op (A1-F10) — a false lead for future headless-signing diagnosis. |
| L4 | MINOR | No reset code on the connected card (`PIN retry counter : 3 0 3`, A1-F11). |
| L5 | OBSERVATION | Plaintext credentials at rest in two `.mcp.json` files; both gitignored, so no commit leak (A2-F12). |
| L6 | OBSERVATION | Worktree `.claude/` holds six stale `settings.local-*` backups and no active settings file (A2-F4 detail). |
| L7 | OBSERVATION | Two `~/.claude.json` project entries beyond the Serena three also point at non-existent paths (`…/Juniper/juniper`) (A2-F9). |
| L8 | OBSERVATION | Three of nine repos have no `.serena/project.yml`; one tracks it, one ignores it (A2-F11). |
| L9 | MINOR | `juniper-recurrence` has no `util/` directory, unlike the other seven code repos — noted while enumerating grep targets; may be intentional. |

---

## 8. Could not verify

Recorded explicitly so none of these is mistaken for a pass.

1. **Whether the legacy RSA key is still registered on the GitHub account.** The public endpoint returns exactly one key (A1-F12), but the session token lacks the scope for the authenticated list: `gh api /user/gpg_keys` → `404 Not Found` plus `gh: This API operation needs the "admin:gpg_key" scope`. I therefore cannot distinguish "removed, with historical verification records persisting" from "still registered but filtered from
   the public view". Both are consistent with the observed `verified:true` on the 2026-07-14 RSA commit. This matters only for whether a *future* stale-key signature fails loudly; it does not affect any other finding. Resolve with `gh auth refresh -h github.com -s admin:gpg_key`.
2. **Whether another host carries a stale `user.signingkey`.** No access to the idle "Turing" machine or any other host. Evidence bearing on it: this host is `yamaguchi`, and the legacy RSA key's UID comment is `…_yamaguchi_gpg2-yubikey-ssh_rsa-4096_2019-01-10_2025-08-15`, so the legacy key was **this** machine's key; a second host would need its own copy of a card-resident key. Further, no main-branch commit in any of the nine
   repos carries the RSA key after 2026-07-14 — so if a stale reference does exist elsewhere, it has not produced a main-branch commit in 26 days. This does not prove absence, only that the blast radius is currently zero on `main`.
3. **Whether the card-serial mismatch actually stalls a fully non-interactive signature.** Reproducing it would require killing the agent, clearing the PIN cache, or removing the card — all mutations, all out of scope for a read-only audit. What is verified: the stub/card serials differ, and signing succeeded in an interactive-capable session. The stall is a documented GnuPG behaviour class, not an observed event on this host.
4. **The provenance of the reported "22 sessions" figure.** The log-derived count is 248 server sessions over 123 days (A2-F7). I could not reconcile the two; the reported figure may come from a different source or a narrower window. The log evidence is presented as primary because it is directly reproducible.
5. **Historical MCP availability in past worktree sessions.** A2-F4 is established structurally (the file is gitignored; three worktrees verified to lack it) rather than by sampling historical session transcripts, which are not retained in a queryable form.

---

## 9. Summary

### 9.1 Counts by severity

| Severity | Area 1 | Area 2 | Total |
|---|---|---|---|
| CRITICAL (to area) | 0 | 2 | **2** |
| MAJOR | 6 | 4 | **10** |
| MINOR | 4 | 2 | **6** |
| OBSERVATION | 5 | 4 | **9** |
| **Total** | **15** | **12** | **27** |

No finding is CRITICAL to production: no service, published package, or CI gate is impaired. The two CRITICALs are scoped to Area 2's own function — the symbol-enrichment layer is wholly non-operational.

### 9.2 Checklist verdicts

11 pass, 7 fail, of 18 items (§2.2).

### 9.3 The three things that matter most

1. **Area 1's regression is historical, not live.** Last old-RSA main commit: 2026-07-14. Every live signing knob is correct. The most probable source of the "still referencing an old key" impression is documentation: a stale validator script (A1-F1) and the only signing note in `notes/`, which states the wrong current key (A1-F2). Both are cheap to correct and both are load-bearing for the next diagnosis.
2. **Area 2 has three stacked root causes and four layers of silence.** No `--project` (A2-F1), no registry entry (A2-F2), no activation instruction plus explicit permission to skip (A2-F3) — masked by an unconditional provenance marker (A2-F5) and a health check that cannot see MCP (A2-F6). True outage: 123 days, 248 sessions, zero tool calls.
3. **The worktree/`.mcp.json` interaction is the cross-cutting amplifier.** Because `.mcp.json` is gitignored, no worktree checkout has it — and worktrees are where the work happens. Any Area 2 remediation that edits `.mcp.json` alone will not reach the sessions it is meant to fix, and the file cannot simply be tracked while it holds plaintext credentials (A2-F12).

---

## Appendix A — signature census, last 15 main commits per repo

Method: `gh api graphql` → `repository.ref("refs/heads/main").target … on Commit { history(first:15) { nodes { oid committedDate messageHeadline signature { __typename isValid state … on GpgSignature { keyId } … on SshSignature { keyFingerprint } } } } }`, executed 2026-08-09.

Key legend: **ed25519 OK** = `BA18D1A733B1831A` (correct current subkey) · **GH web-flow** = `B5690EEEBB952194` (GitHub's current web-flow key, verified via `gh api /users/web-flow/gpg_keys`) · **OLD RSA** = `B5AFCD0686585249` · **ed448** = `93E8591643C507FF`.

| Repo | Window (newest → oldest) | ed25519 OK | GH web-flow | OLD RSA | ed448 | Unsigned |
|---|---|---|---|---|---|---|
| juniper-ml | 2026-08-09 → 2026-08-09 | 8 | 7 | **0** | 0 | 0 |
| juniper-cascor | 2026-08-09 → 2026-08-08 | 2 | 13 | **0** | 0 | 0 |
| juniper-data | 2026-08-08 → 2026-07-21 | 0 | 15 | **0** | 0 | 0 |
| juniper-data-client | 2026-08-08 → 2026-07-21 | 0 | 15 | **0** | 0 | 0 |
| juniper-cascor-client | 2026-08-08 → 2026-07-20 | 0 | 14 | **0** | 0 | 1 |
| juniper-cascor-worker | 2026-08-08 → 2026-07-20 | 0 | 15 | **0** | 0 | 0 |
| juniper-canopy | 2026-08-09 → 2026-07-28 | 0 | 12 | **0** | 0 | 3 |
| juniper-deploy | 2026-08-08 → 2026-07-20 | 0 | 15 | **0** | 0 | 0 |
| juniper-recurrence | 2026-08-09 → 2026-08-03 | 0 | 14 | **0** | 0 | 1 |
| **Totals (135)** | | **10** | **120** | **0** | **0** | **5** |

**Non-web-flow rows in detail** (all `state: VALID`, `isValid: true` where signed):

| Repo | SHA | Committed | Key | Headline |
|---|---|---|---|---|
| juniper-ml | `be9f1319` | 2026-08-09T20:37:24 | ed25519 OK | test yubi 2 |
| juniper-ml | `29b9ff7f` | 2026-08-09T20:36:33 | ed25519 OK | test 1 |
| juniper-ml | `6ea44eec` | 2026-08-09T20:30:46 | ed25519 OK | moving prompt into correct dir |
| juniper-ml | `10c22895` | 2026-08-09T20:08:36 | ed25519 OK | formatting markdown |
| juniper-ml | `2b4ac759` | 2026-08-09T19:26:35 | ed25519 OK | formatting updates notes files |
| juniper-ml | `731302ad` | 2026-08-09T07:17:41 | ed25519 OK | second Testing Backup Yubikey Sign |
| juniper-ml | `5ff81d88` | 2026-08-09T07:17:41 | ed25519 OK | First Testing Backup Yubikey Sign |
| juniper-ml | `1d2e3765` | 2026-08-09T07:17:40 | ed25519 OK | (support): adding manual prompt … |
| juniper-cascor | `4d07a88c` | 2026-08-09T08:16:50 | ed25519 OK | Merge branch 'main' … |
| juniper-cascor | `4081f5bb` | 2026-08-09T08:16:28 | ed25519 OK | removing old snapshots |
| juniper-cascor-client | `94a21a55` | 2026-07-30T03:01:02 | **unsigned** | serena config file |
| juniper-canopy | `91edcbeb` | 2026-08-03T14:14:00 | **unsigned** | … Update requirements.lock |
| juniper-canopy | `375634c9` | 2026-07-28T16:36:29 | **unsigned** | chore(deps): auto-regenerate requirements.lock … |
| juniper-canopy | `37645b78` | 2026-07-28T16:36:19 | **unsigned** | chore(agents-md): bump Last Updated to 2026-07-28 … |
| juniper-recurrence | `1c604b31` | 2026-08-08T04:37:19 | **unsigned** | feat(settings): Wave 3.3 — experiment YAML config layer … |

*(Two headlines above are truncated at the ellipsis; the omitted tails contain CI-control markers that are deliberately not reproduced in prose.)*

The `juniper-cascor-client` unsigned commit is titled "serena config file" (2026-07-30) — an incidental cross-link between the two audit areas.

---

## Appendix B — deep signature census (3,208 commits)

Method: same GraphQL query paginated at `first:100`, up to 500 commits per repo (1,600 for juniper-ml, to reach past the 2026-07-14 boundary).

| Repo | Scanned | Window oldest | ed25519 OK | GH web-flow | OLD RSA | ed448 | Unsigned | Last OLD-RSA commit |
|---|---|---|---|---|---|---|---|---|
| juniper-ml | 1600 | 2026-05-04 | 9 | 955 | 228 | 0 | 408 | `112dc0d7` (**2026-07-14**) |
| juniper-cascor | 500 | 2026-04-05 | 2 | 366 | 85 | 0 | 47 | `990697c0` (2026-07-12) |
| juniper-data | 500 | 2026-02-13 | 0 | 319 | 164 | 0 | 17 | `3d2c15d0` (2026-05-18) |
| juniper-data-client | 273 | 2026-02-19 | 0 | 178 | 95 | 0 | 0 | `b24dfe53` (2026-05-21) |
| juniper-cascor-client | 197 | 2026-02-21 | 0 | 120 | 75 | 0 | 2 | `7fbb4969` (2026-07-12) |
| juniper-cascor-worker | 246 | 2026-02-21 | 0 | 163 | 80 | 0 | 3 | `86421921` (2026-05-21) |
| juniper-canopy | 500 | 2026-04-29 | 0 | 305 | 150 | 0 | 45 | `1bff2b5d` (2026-07-12) |
| juniper-deploy | 274 | 2026-02-25 | 0 | 185 | 82 | 0 | 7 | `29501b66` (2026-07-12) |
| juniper-recurrence | 218 | 2026-06-14 | 0 | 128 | 80 | 0 | 10 | `d7df91f5` (2026-07-12) |
| **Total** | **3208** | — | **11** | **2719** | **1039** | **0** | **539** | **2026-07-14** |

Observations:

- **Zero ed448 signatures across 3,208 commits.** The interim key configured 2026-07-16 and superseded 2026-08-07 never signed a main-branch commit anywhere.
- **The 2026-07-12/14 cliff is sharp.** No repo has an old-RSA signature after 2026-07-14, matching the migration note's incident date exactly.
- **539 unsigned commits** overall, concentrated in juniper-ml (408) and juniper-canopy (45) — the automation-heavy repos, consistent with the deliberate headless signing-disable of §3.5.
- juniper-ml's 500-commit window reached only to 2026-07-26, which is why it was extended to 1,600 to cross the boundary.

---

## Appendix C — evidence command index

Every command below is read-only and was executed during this audit on 2026-08-09.

| Purpose | Command |
|---|---|
| Live git signing config | `git config --global --list` ; `git config --global --show-origin --get user.signingkey` |
| System-level signing config | `git config --system --get-regexp "sign\|gpg"` → exit 1 (no matches) |
| Stale-key hunt, this worktree | `grep -rniI -e 'B5AFCD0686585249' -e '9F5D0FDE' . --exclude-dir=.git` |
| Signing-vocabulary hunt | `grep -rniI -e signingkey -e default-key -e local-user -e gpgsign scripts/ util/ conf/ .github/ notes/templates/` |
| Stale-key hunt, siblings | `grep -rniI … juniper-cascor juniper-data juniper-data-client juniper-cascor-client juniper-cascor-worker juniper-canopy juniper-deploy juniper-recurrence --exclude-dir=.git -l` → exit 1 |
| Per-repo git config | `grep -niI -e sign -e gpg -e user <9 × .git/config>` → exit 1 |
| Git hooks | `grep -niI -e gpg -e sign -e yubi <4 active hooks>` → exit 1 |
| Keyring inventory | `gpg2 --list-secret-keys --keyid-format long --with-colons` |
| Card state | `gpg2 --card-status` |
| Shadow-key card bindings | `python3 -c` scan of `~/.gnupg/private-keys-v1.d/*.key` for `D276000124010…` serials |
| Local signature verification | `git log --format='%h %G? %GK %GS \| %an \| %ad \| %s' --date=short -12 origin/main` |
| Signature census | `gh api graphql` per repo (Appendix A/B queries) |
| GitHub web-flow key identity | `gh api /users/web-flow/gpg_keys` |
| Account GPG keys | `gh api /users/pcalnon/gpg_keys` ; `gh api /users/pcalnon/ssh_signing_keys` |
| Commit verification state | `gh api /repos/pcalnon/<repo>/commits/<sha> --jq '{verified,reason}'` |
| MCP wiring | `python3 -c` parse of `~/.claude.json` `projects[*].mcpServers` ; read of `juniper-ml/.mcp.json`, `juniper-canopy/.mcp.json` |
| Serena registry | `python3 -c` YAML parse of `~/.serena/serena_config.yml` |
| Serena usage quantification | `python3 -c` scan of `~/.serena/logs/**/*.txt` for `_log_tool_application` |
| MCP tracking status | `git ls-files --error-unmatch .mcp.json` ; `git check-ignore -v .mcp.json` |
| Worktree MCP absence | `ls <worktree>/.mcp.json` × 3 → not found |
| GnuPG documentation | WebFetch `https://www.gnupg.org/documentation/manuals/gnupg/Agent-Options.html` ; `…/Scdaemon-Options.html` |
| GitHub documentation | WebFetch `https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification` |

---

**End of audit.** No repository file outside this document was created, modified, or deleted; no git state, git configuration, GnuPG configuration, MCP configuration, or GitHub resource was changed.
