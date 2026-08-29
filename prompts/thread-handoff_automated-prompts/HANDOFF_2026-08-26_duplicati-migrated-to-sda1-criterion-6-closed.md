# HANDOFF 2026-08-26 — Duplicati: MIGRATED to sda1, criterion 6 CLOSED; the tail is root/decisions only

**Continue the backup arc from a goal state where the destination has moved.**
Predecessor: [`HANDOFF_2026-08-26_duplicati-decisions-executed-root-gated-tail.md`](HANDOFF_2026-08-26_duplicati-decisions-executed-root-gated-tail.md)
— its §0 outcomes, §2 traps and the prohibitions it inherits remain binding and are NOT
restated. Read it, then note
[§8.10–§8.13](../../notes/JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md).

> ⚠️ **The destination changed.** It is now **`/mnt/Backups/Ubuntu/Yamaguchi`** (sda1), not
> `/media/pcalnon/temp_backups/Yamaguchi`. Any command, script or memory naming the old path
> is stale. Two tools were already invalidated this way — see §2.

## 0. Settled this session — do not redo

| item | outcome |
|---|---|
| #1404 | **MERGED** (`40dff6eb`) — §8.10 findings + §8.11 decision packets + Tier-1/Tier-2 tooling |
| #1425 | **OPEN**, CI running at handoff time — the §8.13 execution record. Merge under Paul's standing arc-wide approval once green |
| **Migration (criterion 6)** | **CLOSED.** copy 811 files / 210,349,834,271 B identical → decrypt-validate **811/811, 0 failures** → PUT 200, **8/8** post-checks → proof run **Success 9 m 31 s**, 199 MB up, `TestResults` verified from sda1 → census **813 / 210,486,704,937 B AGREE** → drill **17/17 VERIFIED**, 245/405 dblocks, **16 live matches / 0 contradictions** |
| Daily cost | **under 10 minutes** — supersedes the "~12–16 min" in §8.10.1 (that run carried 4 h of churn) |
| `dbconfig.json` | **deleted** (archived to `_yamaguchi_check/dbconfig.json.retired-20260826`) |
| Retirements | Tier 1 (77 GB) + Tier 2 group 1 (51 GB) = **128 GB**; sdc4 21 % → 17 % |
| Tier 3 | `_drill_scratch/` 35 GB **still BLOCKED** on the old-archive purge decision |
| VDI exclusion | live-proven by the 18:12Z run: modified 56.39 → 0.85 GB, upload −92.3 % |

## 1. Open — all root or Paul's call

1. **The 196 GB sdc4 `Yamaguchi/` copy** — deliberately KEPT. §8.6-8 step 5's "keep until the
   drill passes" is a floor, not a delete order; post-drill it is a second, independently
   decrypt-validated copy on a different disk (materially option (c)), and sdc4 has 1.5 T free.
   **Recommendation: keep.** `yamaguchi_retire_tier2.bash --execute --execute-old-destination`
   removes it. It is frozen pre-migration (811 volumes) and does not track further runs.
2. **`--tempdir` residual** (§8.13.3) — still on the non-durable sdc4. Options (i) leave,
   (ii) sda1, (iii) `/home`. **Recommendation (iii)**: fstab-managed *and* off the destination
   spindle. A live-job PUT, so Paul's call.
3. **Today's drill `restored/` tree** ~64 GB under `_yamaguchi_drill/drill-20260826-175815/` —
   same Tier-1 class Paul approved, created after that approval. Keep `results.json`,
   `drill-meta.json`, `provenance.txt`.
4. **Criterion 5 (reboot)** — the §8.10.2 mechanism is retired for the destination, but the
   criterion has never been exercised. After the next reboot check: `duplicati.service` active,
   job 2 + `ProposedSchedule` present, **`bash util/ad-hoc/yamaguchi_destination_durability_check.bash`**,
   `loginctl show-user pcalnon -p Linger` = yes, `systemctl --user is-enabled yamaguchi-watchdog.timer`.
5. **Loopback restage** (root), **server-brain backup** (root), **old-archive tail** — unchanged,
   by the predecessor's precise reference.

## 2. Traps added

- **A checker that hardcodes a path describes the resource it USED to watch.** Bit twice:
  `yamaguchi_census.py` (the arc's primary invariant) censused the OLD directory while printing
  the NEW `TargetURL` and printed a false **`DIVERGE`** with both witnesses actually identical;
  `yamaguchi_watch.bash` pointed into sibling worktree `mossy-growing-salamander`, itself a
  retirement candidate. Both now derive from the job's `TargetURL`. **Grep `util/ad-hoc/` for
  `temp_backups/Yamaguchi` before trusting any other tool.**
- **`grep -q` over a JSON list is an existential test.** My Tier-2 gate accepted "any candidate
  VERIFIED" — 1 pass + 16 failures would have authorised deleting the last fallback. Now total.
- **`git commit -m "…backticks…"` in DOUBLE quotes executes them.** A backticked
  `` `rsync -a --checksum` `` ran and silently ate the text from the message. **Use `-F <file>`.**
- **`rsync --checksum` on an EMPTY destination decides nothing** and costs a full extra source
  read (measured: 21.8 GB read, 0 written, ~20 min wasted). §8.6-8 step 2 is corrected in §8.12.3.
- **A merged PR's branch is deleted; pushing again RECREATES it** diverged from the squash. #1404
  merged mid-session; recovery was to rebase the one new commit onto main.
- Background waiters get killed (~lease); the systemd unit survives. Poll the unit, not the waiter.

## 3. Verify starting state (one per call)

```bash
git fetch origin && git status -sb
python3 util/ad-hoc/yamaguchi_census.py --runs 2          # target=…/mnt/Backups/Ubuntu/Yamaguchi, literal "-> AGREE"
bash util/ad-hoc/yamaguchi_destination_durability_check.bash   # sda1 DURABLE; sdc4 NOT DURABLE
python3 util/ad-hoc/yamaguchi_server_api.py status        # job 2; ActiveTask null; ProposedSchedule 2026-08-27T14:00Z
cat ~/.local/state/duplicati/server-watchdog.status       # OK
bash util/ad-hoc/yamaguchi_retire_tier2.bash              # all 5 gates PASS, dry run, nothing deleted
ls /mnt/Backups/Ubuntu/                                   # Yamaguchi, _yamaguchi_records, then the old archive's .gpg
```

## 4. Git / session state

Branch **`feat/yamaguchi-migration-execution`** (from main `85ed19b3`) in worktree
`.claude/worktrees/idempotent-sparking-crayon`, session "duplicati". Three GPG-signed commits:
`bb74e46e` (watch de-drift + `wait_for_user_unit.bash`), `57826ef8` (census derives its
destination), `e1490578` (§8.13 + criterion 6 closed + Tier-2 gate made total). Pushed; **PR
#1425** open. New tooling this session: `yamaguchi_retire_tier1.bash`, `yamaguchi_retire_tier2.bash`,
`yamaguchi_migrate_copy.bash`, `yamaguchi_edit_target.py`,
`yamaguchi_destination_durability_check.bash`, `wait_for_user_unit.bash`, two idempotent patch
scripts. Evidence under `/media/pcalnon/temp_backups/_yamaguchi_check/` and **re-synced to sda1**
(`_yamaguchi_records/`, 19:2x CDT) — includes this session's copy log, the migrated
decrypt-validate log, the post-migration config record and census, the durability probe, and
drill `drill-20260826-175815/`'s results/meta/provenance. Memory updated:
`project_duplicati_gpg_flush_mechanism_2026-08-24.md`, `reference_vacuous_pass_check_class.md`
(instances 13–14), both MEMORY.md index lines.
