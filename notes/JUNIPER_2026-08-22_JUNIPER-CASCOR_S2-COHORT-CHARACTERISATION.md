# S-2 — characterising the March–April 2026 snapshot cohort

**Project**: Juniper — CLI test/validation/experimentation program
**Sub-Project**: juniper-cascor / juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-22

**Status**: FINDINGS — **no retention policy is proposed here, and nothing was deleted.**
S-2 asks *"is the March–April 2026 cohort of retained research value?"*. This characterises
the cohort so that question can be answered; the answer, and any policy, is the owner's
under design §6.4.

Every number is measured from the §6.2 index
(`util/snapshot_index.py`, ml#1238) by
`util/ad-hoc/2026-08-22_s2_cohort_characterisation.py`, which is read-only and never opens
a snapshot for writing. Index built 2026-08-22 over 27,908 files.

---

## 1. Why this was not answerable before, and is now

S-2 has been gated since the 2026-08-16 census, on the design's ordering: **identity →
index → retention**, because a deletion rule over anonymous artifacts is guesswork.

D-C (cascor#554 + ml#1230) delivered identity and §6.2 (ml#1238) delivered the index — but
neither retroactively explains this cohort, for a reason that turns out to be the single
most consequential finding here (§4).

Dates come from each file's internal `created` attribute, never mtime: a copy reset every
mtime in this archive, so anything mtime-derived would misjudge the whole corpus.

---

## 2. Scale

| | snapshots | bytes |
|---|---|---|
| whole archive | 27,908 | 1.7 GiB |
| **Mar–Apr 2026 cohort** | **27,005 (96.8%)** | **1.7 GiB** |
| everything else | 903 | ~93 MiB |

The cohort holds **16,462 distinct networks** (by `meta.uuid`). Median snapshots per
network is **1**; the maximum is 174. All 27,005 are readable, and all are written by
cascor **0.3.2** (26,970) or 0.4.0 (35) — six minors behind current.

---

## 3. The split that matters

Grouping the cohort's networks by whether they ever grew a hidden unit — i.e. whether the
cascade actually ran:

| | networks | snapshots | bytes |
|---|---|---|---|
| **grew ≥1 hidden unit** | 4,711 | 15,057 (55.8%) | **1.17 GiB** |
| **never grew** | 11,751 | 11,948 (44.2%) | **499 MiB** |

The never-grew group is ~1.02 snapshots per network — almost exactly one each. That is the
signature of a run that performed its initial output-layer pass (which auto-snapshots) and
then ended before any growth.

**They are not untrained.** In a 200-file random sample, **200/200 had non-zero
`output_weights`**, so the output layer was genuinely fitted. A never-grown snapshot is a
real trained linear solution for its dataset — just not a cascade.

Nearly half the never-grew snapshots fall on four consecutive days:

| day | never-grew snapshots |
|---|---|
| 2026-04-01 | 2,059 |
| 2026-04-03 | 1,962 |
| 2026-03-31 | 1,263 |
| 2026-04-02 | 751 |

~6,035 of 11,948 in four days is a campaign or an incident, not steady accumulation.

Architecture is highly uniform: **(2 in, 2 out, 0 hidden)** accounts for 14,919 of the
whole archive, with the rest concentrated in (2,2,1) / (2,2,2) / (2,2,3). Two-dimensional
input and output is the spiral/moons/xor family — consistent with the synthetic-generator
suites, not with equities or any wide-input work.

---

## 4. Attribution is unrecoverable for this cohort

**There are zero surviving experiment run directories from before 2026-07-30.**

267 run dirs exist under `~/.local/state/juniper-experiments`; the earliest is
`20260730T…`. The cohort is March–April.

This forecloses the obvious rescue. D-C records `run_id` in new snapshots and ml#1244 can
join `run_id → <RUN_ROOT>/<run_id>/manifest.json → dataset_id` — but **that join needs both
halves**, and for this cohort neither exists: the files predate provenance, and the run
dirs they would have joined to are gone.

So the cohort's identity is not merely unrecorded, it is **unrecoverable**. Any judgement
about it has to rest on intrinsic evidence alone.

---

## 5. A metadata defect found while measuring

**`meta.current_epoch`, `meta.snapshot_counter` and `meta.best_value_loss` are never
populated.** Across all 27,908 snapshots, `current_epoch` is `0` — including every one of
the 174 snapshots of the network that grew **from 0 to 260 hidden units**. `snapshot_counter`
is likewise `0` and `best_value_loss` is `inf`.

This is worth its own attention for two reasons:

1. **It is a trap for exactly this kind of analysis.** Those three fields look like
   training-progress metadata. Reasoning from them — "every snapshot is at epoch 0, so
   nothing was trained" — produces a confident and completely wrong conclusion. It was the
   first reading of the data here, and was only caught by checking a network known to have
   grown.
2. **It removes the natural measure.** With the counters dead, `arch.num_hidden_units` is
   the only usable signal for how much training a snapshot represents, which is why §3 is
   framed on growth rather than on epochs.

Not fixed here — it is a cascor writer defect, distinct from S-2, and belongs in the defect
register.

---

## 6. What this does and does not settle

**Settled:**

- The cohort is 27,005 readable, structurally valid, genuinely trained snapshots.
- It divides cleanly: ~4,700 networks that cascaded (1.17 GiB) and ~11,750 that did not
  (499 MiB).
- Its identity cannot be recovered — no provenance, no surviving run dirs.
- Its architectures are uniformly small and 2-D, i.e. synthetic-generator work.

**Not settled — and these are judgement calls, not measurements:**

- **Whether a never-grown snapshot has research value.** It is a real fitted output layer,
  but it records a run that produced no cascade. Whether that is a useful baseline or the
  residue of an aborted sweep is a question about intent, and intent is exactly what was
  lost with the run dirs.
- **What the four-day cluster was.** ~6,000 near-identical snapshots over 2026-03-31 →
  04-03 is the single largest concentration in the archive. If it was one sweep, it may be
  reproducible today for a fraction of the storage; if it was an incident, it is residue.
  Nothing in the files answers this — but it is the kind of thing the owner may simply
  remember.
- **Whether 1.7 GiB is worth acting on at all.** The design's own position is that the
  index is worth building *even if no file is ever deleted*, and 1.7 GiB is less than a
  single container image.

---

## 7. If the owner does want to act

Recorded for completeness, in increasing order of irreversibility. **None is recommended
here**, and no tooling for any of them exists — `util/snapshot_index.py` is read-only by
construction and an AST test enforces that.

1. **Do nothing.** The archive is legible now; that was the actual problem.
2. **Freeze and forget.** Leave it, and let D-C provenance make everything *new*
   attributable, so the anonymous fraction shrinks by attrition.
3. **Reproduce-then-release.** Re-run the four-day cluster's suite under the current stack
   with provenance, keep the attributed results, and release the anonymous originals once
   the new run is verified equivalent. Trades compute for storage and identity.
4. **Prune the never-grew group.** ~11,948 snapshots / 499 MiB. The narrowest defensible
   cut, and still a deletion of trained models that nobody can identify.

Any of 3–4 needs the §6.4 policy, a dry-run path, and the shared-root protections that
already exist in `HDF5Utils.cleanup_old_files` — which refuses the shared root by default
precisely because mtime-ordered "keep the N most recent" would select the wrong files here.

---

## 8. Reproducing this

```bash
conda activate JuniperCascor1
python util/snapshot_index.py --scan          # ~3m27s first time; append-only after
python util/ad-hoc/2026-08-22_s2_cohort_characterisation.py
```

Both are read-only. The characterisation reads the index, not the snapshots, so it runs in
about a second.
