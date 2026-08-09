# HANDOFF 2026-08-09 — standing-items closeout + agentic-harness remediation (EXECUTION phase)

Continue the standing-items closeout + harness-remediation arc (juniper-ml + ecosystem). The investigation/planning phase is COMPLETE; execute per the plan doc, which is the authority — read it first:
`notes/JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_STANDING-ITEMS-CLOSEOUT-AND-HARNESS-REMEDIATION-PLAN.md` (grounded findings: `notes/JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_HEADLESS-SIGNING-AND-SERENA-HARNESS-AUDIT.md`).

## Completed so far (2026-08-09 session)

- recurrence#104 + #105 MERGED (seq-safety net live on recurrence, soak started; ci-tools pins widened). Owner decisions recorded: Turing deploy keys RETAINED; codeql merge_group divergence ACCEPTED; recurrence rollout EXECUTED.
- /doctor: AGENTS.md trimmed (-5,029 chars, 3 derivable blocks; drift gates green) — **UNCOMMITTED in session worktree `cryptic-dancing-badger`**; chrome-devtools + deepwiki disabled for juniper-ml; auto-mode declined.
- Audit + plan docs authored by the custom auditor/planner agents and PR'd (with this handoff) from branch `docs/standing-items-closeout-harness-remediation`.

## Remaining work (slice IDs per plan §Part D)

1. **S-B signing preflight (PR)**: `util/headless_signing_preflight.bash` + hermetic tests; DELETE `util/test_gpg_signing.bash` (pins superseded ed448 `93E8591643C507FF`); retire/annotate the stale 2026-07-16 key-migration status note. Preflight contract: 4 checks (configured signingkey == ed25519 `B5619F58FDA4D94E2D73D8BABA18D1A733B1831A`; gpg2 + card present, timeout-bounded; card SIGNATURE-SLOT fingerprint match — accept ANY card serial: backup `24955114` signs fine while stubs bind `24955323`, a serial compare would false-fail today; bounded live test signature proving PIN cached). Loud-fail: nonzero + banner + stable-title issue upsert (authorship-bound dedup per `main-verify.yml` notify). Auto-resume on re-run.
2. **S-C serena re-enablement**: fix `.mcp.json` `--project` binding in the MAIN checkout (gitignored file — local op, no PR); register juniper-ml (+juniper-data) in `~/.serena/serena_config.yml`; one AGENTS.md steering line; doctor `serena_wiring` check + HONEST overlay provenance (`symbol_overlay.py:50` stamps `overlay="serena"` unconditionally; `tests/test_symbol_overlay.py:93` pins the lie) + hermetic tests (PR). Post-fix live smoke: activate + `find_symbol` on a real symbol.
3. **Part A owner decisions** (package ready in plan §Part A; Paul executes/directs): A1 identify Integration **1276151** + NEW unrecorded always-bypass actor **946600** (juniper-data / cascor-client / deploy rulesets) via owner UI — `1143301` RESOLVED = copilot-swe-agent; A3 drop `code_quality` BEFORE A2 (remove cursor 1210556 + claude 1236702 always-bypasses; KEEP Role 5 + DeployKey + 4362741/pull_request); A4 merge-queue UI availability check, rule coupled with A2 — NOTE: consumer seq-safety workflows are `pull_request`-only, requiring them under a queue STALLS it (plan covers); A5 promotion call ~2026-08-21 (6-point checklist; context names: ml `Sequence Safety`, consumers `Sequence Safety (Advisory)`, recurrence CLASSIC protection — copy its em-dash context exactly from a live GET).
4. **Housekeeping**: ff-pull behind primaries — juniper-ml (2 behind), juniper-cascor-client (3), juniper-data-client (1); recurrence already current. Land the doctor AGENTS.md trim as its own small PR (docs screen will flag deletion runs — owner waiver route at squash).

## Key context / doctrine

- **MERGE GATE (owner, 2026-08-09)**: arc PRs — including the docs PR carrying this handoff — merge headlessly ONLY after the signing preflight verifies the correct ed25519 key on this host. Run the preflight (or plan §B manual equivalent) first, then merge.
- Ground on `origin/main` LIVE (it advanced 3× during this session; last seen `0820863`). `gh pr list` dup-guard; GitHub-signed API commits (`createCommitOnBranch`) for PR branches; never touch concurrent-session PRs (canopy E2E arc in flight: ml#1049 + release-notes lanes open at handoff time).
- Memory tracker: `project_standing_items_arc_2026-08.md` (updated through this phase). Signing regression is HISTORICAL (last RSA signature 2026-07-14, fleet-wide census in audit §appendix); GitHub account holds exactly one GPG key, so wrong-key pushes fail loud at GitHub — the preflight makes them fail loud BEFORE push.

## Verification

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml && git fetch origin && git log --oneline -3 origin/main
gh pr list --repo pcalnon/juniper-ml --state open   # classify: this arc's docs PR / concurrent-session / release lanes
ls notes/JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_*.md  # on the docs branch or post-merge main
```

Git state at handoff: worktree `cryptic-dancing-badger` holds the uncommitted doctor AGENTS.md trim; the two notes docs + this handoff are committed on `docs/standing-items-closeout-harness-remediation` (signed API commit) with the PR open and HELD under the merge gate.
