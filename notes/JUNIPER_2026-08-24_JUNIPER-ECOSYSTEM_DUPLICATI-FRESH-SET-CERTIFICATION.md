# Duplicati Fresh-Set Certification — Coverage, Integrity, and Restore Drill

**Project**: Juniper — Backup Infrastructure
**Author**: Paul Calnon (campaign executed by Claude Code session "backup sys work")
**Date**: 2026-08-24
**Status**: COMPLETE — handoff §4 item 2 gate cleared at its capped verdict (§1)
**Companion**: [`JUNIPER_2026-08-24_JUNIPER-ECOSYSTEM_DUPLICATI-GPG-FLUSH-FAILURE-INVESTIGATION.md`](JUNIPER_2026-08-24_JUNIPER-ECOSYSTEM_DUPLICATI-GPG-FLUSH-FAILURE-INVESTIGATION.md) (the failure mechanism; PR #1319, merged)

---

## 1. Verdict — read the caps before the pass

> **The fresh set's only restore point is VERIFIED RESTORABLE — and PARTIAL.**
> 15/15 stratified candidates restored end-to-end from the destination alone
> (the true disaster path): 13 byte-matched both the manifest's per-file
> SHA-256 and a fresh hash of the live source file, the empty file restored at
> exactly 0 bytes, and the symlink's restored target matched the live link —
> 14 live-oracle engagements, 0 contradictions. But the fileset is a
> **synthetic manifest** Duplicati itself
> stamps `IsFullBackup: false`, and it **omits ≥ ~45% of the in-scope files**:
> 296,963 files listed vs ≥ 538,168 enumerated for the identical scope the
> same evening. The strongest honest claim is *"synthetic partial fileset
> verified restorable."* "Restore point verified" — the fresh-backup-set
> plan's §7 language — remains **unearned** until a backup run completes and
> writes its own dlist, which is gated on the GPGFlushError fix decision
> (companion note §9).

Everything below was adversarially validated per the standing SOP; the drill
driver itself was refuted-and-fixed twice before launch (§5).

## 2. What the fileset is (provenance, verified in the fresh job DB)

The destination (`/media/pcalnon/temp_backups/Ubuntu`: 1 dlist + 104 dindex +
104 dblock; 50.79 GiB of dblocks, 50.83 GiB total) holds the dlist of
**fileset 2** (2026-08-23T17:15:12),
written not by its own run but by run 2's reconciliation pass at 22:51:50 —
24 s after run 2 started, hours after the last data volume landed. The fresh
DB holds three filesets: a deleted twin one second earlier (fs1, 17:15:11 —
same 362,172 entries), fs2 itself, and run 2's crashed fs3 (22:51:26; 446,233
entries; needs 97,944 blocks that sit in 12 volumes recorded but never
uploaded). **Restore traps**: against the live DB, `--time` must pin
`2026-08-23T17:15:12-05:00` exactly and "latest" must never be used (it
resolves to fs3). Destination-only restores are immune: only fs2's dlist was
ever uploaded, so `--version=0` is unambiguous.

## 3. The partiality finding (the campaign's most important number)

| measure | value | source |
|---|---|---|
| files in the on-disk manifest (fs2) | **296,963** | filelist.json (parsed twice) |
| entries in fs2 / the deleted twin | 362,172 each | fresh DB `FilesetEntry` |
| entries run 2's fs3 had already catalogued | 446,233 | fresh DB `FilesetEntry` |
| enumeration high-water, same scope, same evening | **≥ 538,168** | run-2 log (self-verified) |
| logical bytes the manifest claims | 110.20 GiB (stored 50.79 GiB, ≈2.17:1) | manifest + destination |

At least ~241,000 in-scope files (~45%) are absent from the manifest —
**silently**: absence is invisible by construction to the coverage check (it
verifies only what the dlist references) and to any manifest-driven drill
(candidates are drawn from the manifest). The omission is *omission only*:
adversarial review confirmed every file the manifest does list carries a
complete, verified block chain — run 2's reconciliation was internally sound,
just early. Bounding the omission precisely (manifest paths vs a fresh source
enumeration under the runner's exclusions) is optional follow-up; the number
above is already decision-grade.

## 4. The certification ladder (each rung independently re-verified)

1. **Coverage** — `util/ad-hoc/duplicati_dlist_crosscheck.py`: every hash the
   dlist references (single-block files, metadata, blocklist hashes, and each
   blocklist's expanded data blocks) is declared by the dindex set:
   **486,300 / 486,300, zero unexpandable**, across 104/104 indexed dblocks
   (2,693 surplus blocks — normal wastage). Validated two further ways, both
   in-session (transcript-only, not archived as artifacts): an independent
   re-implementation under Duplicati v2.3.0.4's own recreate semantics
   (set-identical), and an independent DB-side relational join (identical
   count; also proved zero needed blocks sit in absent volumes).
   Hardened after review: `list/` blocklist contents are hash-verified inline
   (4,196/4,196 per the archived log — Duplicati's own recreate path
   distrusts unverified blocklists, `RecreateDatabaseHandler.cs:437-456` at
   the installed tag), manifest drives blocksize/hash-algo, odd-length
   entries are fatal. Log: `_fresh_dlist_check/crosscheck-hardened.log`.
2. **Physical integrity** — `util/ad-hoc/duplicati_verify_volumes.py` against
   the fresh DB (immutable read-only): **209/209 volumes** match recorded
   `Remotevolume.Size` and full-file SHA-256 — full population, stronger than
   the old archive's 30-sample pass. Log: `verify_volumes_fresh.log`.
3. **Ciphertext integrity** — `util/ad-hoc/duplicati_decrypt_validate_all.bash`:
   all **209 volumes decrypt with full MDC verification** (473 s). Closes the
   layer whole-file hashing cannot: `Remotevolume.Hash` records whatever the
   encryption stage wrote. Log: `decrypt_validate_all.log`.
4. **Restore drill** — `util/ad-hoc/duplicati_drill_fresh.py` (§5): 15/15
   verified, 28/104 dblocks exercised, 14 live-oracle matches, 0
   contradictions. Run dir: `_fresh_drill/drill-20260824-142353/` (candidates,
   per-restore logs, results.json, provenance snapshot, restored copies);
   summary log `_fresh_drill/drill-full-run.log`. (`drill-20260824-140902/`
   is the pre-diversity-fix selection record; two false-start selection dirs
   were deleted.)

## 5. Drill design (what makes the pass meaningful)

- **Destination-only**: `--dbpath` at a nonexistent path makes duplicati-cli
  build a temporary DB from the destination per invocation
  (source-verified at the installed tag: the dbpath file is never created;
  with `--dbpath` explicit, the live job DB and `dbconfig.json` are
  unreachable; restore performs no destination writes). The driver aborts if
  the dbpath ever materializes — the exists-branch would silently reuse it.
- **`--no-local-blocks=true` on every restore** (mandatory: most candidates
  still exist locally; without it Duplicati rebuilds from the live source —
  a false pass indistinguishable from proof; source-verified honored).
- **Dual, job-DB-independent oracle**: restored bytes vs the manifest's own
  per-file SHA-256, AND vs a fresh hash of the live source. A divergence on a
  live file whose filesystem mtime predates the backup start would be the
  shared-author corruption signal (manifest, dindex, and Remotevolume share
  one author; the unchanged live file is the only independent witness) and
  FAILS the drill. All 15 candidates had pre-backup mtimes; **14 engaged and
  matched** (the empty file has nothing to hash). PASS additionally requires
  ≥ 10 live-oracle matches — a vacuous-oracle run is INCONCLUSIVE, not PASS.
- **Stratified sample**: single- and multi-block × early/mid/late upload
  window, plus a 1.24 GB file spanning 12 dblocks, an empty file, and a
  symlink (target verified against the live link). Byte-identical duplicates
  deduped (this demonstrably worked); the per-directory cap did NOT bind in
  the executed sample — a path-keying defect, since fixed in the driver, let
  7/15 candidates come from `StarfieldSaves/` (distinct multi-MB saves from
  different dates, so the concentration is benign here); glob metacharacters
  in candidate paths rejected (the positional filespec is a filter).
- **rc semantics**: duplicati-cli returns 1 ("success, no files changed") and
  2 ("success with warnings") as SUCCESS variants; only rc ≥ 3 fails a
  restore. All 15 restores returned rc=2 (scratch-restore metadata warnings)
  — under the naive `rc != 0` reading the entire passing drill would have
  been reported as 15 failures.

Adversarial review history: the driver was REFUTED as-written twice — first
the design requirements (six items, from the gate review), then three
blocking defects in the implementation (rc mapping; the live-oracle
divergence mislabel that would have excused the corruption signal as benign;
symlink verdicts with no oracle). All fixed before launch; the
destination-only architecture itself survived source-grade attack.

## 6. What remains open for the arc (unchanged by this note)

- **A complete restore point does not exist.** Getting one requires a
  successful full backup, gated on the GPGFlushError fix decision
  (companion §9 — Paul's call; nothing has been changed).
- Handoff §4 items 3–8: old-archive intact-arm re-run, purge decision,
  migration, timer enablement (its acceptance criteria also require a
  *second* drill after an incremental plus reboot survival), Recreate
  disposition, cleanups. The old-archive items still contend with the
  Recreate (2-day-14-hour+ elapsed, alive and writing at last check).
- Cleanup candidates when convenient: `_gpg_repro/` (2.3 GB incl. macro run),
  `_fresh_dlist_check/` (logs, keep), `_fresh_drill/` (restored copies ~1.3 GB
  — deletable after review; logs keep).
- MINOR side-finding for hygiene: `~/.config/Duplicati/dbconfig.json` maps
  the old archive to `KCSYQNVYOP.sqlite` — a path that is neither the old
  job's DB (`SJTCQIIZSJ`) nor the fresh job's (`DQRVQNDIFX`). Orphaned
  mapping; a future `--dbpath`-less CLI operation against the old archive
  would silently build an empty DB there. Flag for cleanup, touch nothing now.
