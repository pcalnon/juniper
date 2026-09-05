# Driver transcripts — canopy E2E, 2026-09-02/03

Run logs for the M-TOPOLOGY re-drive and the scorers built during it. Kept as
`.txt`, in `transcripts/` rather than `logs/`, **because `.gitignore` silently
swallows both `**/logs/` (line 48) and `*.log` (line 52).**

That is not a style preference. Earlier commits in this arc copied run logs to
`reports/e2e-canopy-2026-09-02/logs/*.log` and ran `git add -A`, which skipped
every one of them **without a word** — 25 files were tracked under that report
directory and not one was a log, while the summaries said the logs were archived.
They survived only because `/tmp/juniper-e2e/` had not been reaped yet.

Same class as the `tar`/`du` `--exclude` trap already in the arc's notes: an
exclusion that fails silently and lint-clean, leaving a confident claim about
evidence that was never stored. `git check-ignore -v <path>` is the check; run it
before claiming an artifact is archived.

Contents pair with the JSON result files one level up:

| transcript | run |
|---|---|
| `topo_postf561_A/B.txt`, `topo_post562_C.txt` | the three post-#561/#562 M-TOPOLOGY re-drives (9 PASS each) |
| `topoevents_D/E.txt` | M-TOPOLOGY-09/-10/-12/-15 scorer, fixed build |
| `topoevents_prefix.txt` | the same scorer against pre-canopy#564 — the falsification |
| `topostate_C/D.txt` | M-TOPOLOGY-13/-18 scorer |
| `topoexport_B/C.txt` | M-TOPOLOGY-14 FAIL on F-CANOPY-047 |
| `topoexport_f047/f047b.txt` | M-TOPOLOGY-14 PASS after canopy#565 (2204x1200, scale 2.0) |
| `plotly_probe4/9.txt` | the plotly-event idiom probe, incl. the 0-of-7 hit sweep |
| `modebar_probe7.txt` | the blob:-vs-data: control that exposed the CSP |
| `store_read_probe*.txt` | the `dcc.Store` reader diagnosis (5 of 5 unreadable, then fixed) |
| `f044_live_verify.txt` | F-CANOPY-044/-045 fix driven live |

## 2026-09-04 — the F-CANOPY-042 / F-CANOPY-046 A/B pairs

These eight files come in **pairs by port**, and the pairing is the method. Rather
than restarting the shared `:8051` instance against a fix branch and hoping — the
mistake behind this arc's "a checkout is not a deployment" entry — a **second
canopy was launched on `:8052`** from the fix worktree, beside the running one,
both pointed at the same cascor (`:8202`) and juniper-data (`:8101`). The 2/40/2/944
fixture was never touched, and the only thing differing between the two runs of a
pair is which code the process imported.
(`util/ad-hoc/2026-09-04_canopy_verify_instance.bash` does the launching.)

| pair | parent `:8051` | fix `:8052` |
|---|---|---|
| `--step topo` (F-CANOPY-042, canopy#570) | `2026-09-04_f042_topo_parent_8051.{txt,json}` — 7 PASS / 2 FAIL | `2026-09-04_f042_topo_fix_8052.{txt,json}` — 9 PASS / 0 FAIL |
| `--step topoevents` (F-CANOPY-046, canopy#573) | `2026-09-04_f046_topoevents_parent_8051.{txt,json}` — 3 PASS / 1 BLOCKED | `2026-09-04_f046_topoevents_fix_8052.{txt,json}` — 4 PASS / 0 BLOCKED |

Read the parent halves first: they carry `label='0 of 40'` on both M-TOPOLOGY-06
and -07, and `control={'present': False, ...}` with `plotly_click_events=0` on
M-TOPOLOGY-12. The parent `topo` transcript is the grep-filtered stdout of that
run rather than the full log — the pipeline was written that way before the value
of the whole log was obvious; its result JSON beside it is complete.

## 2026-09-04 (later) — the F-CANOPY-037 closure drive, and its one control

`2026-09-04_f037_closure_main_94220f0.{txt,json}` is the full topology surface
(`--step topo,topoevents,topostate,topoexport`) driven against **canopy main
`94220f0`** — both of this arc's fixes plus another session's canopy#567. It is the
live re-drive F-CANOPY-037's entry had been owed since 2026-08-28, and it closes the
arc's last P0/P1: **16 PASS / 0 FAIL** across every scoreable M-TOPOLOGY row.

`2026-09-04_f037_m18_isolated.{txt,json}` is the **control**, and the reason to keep
it. In the combined run M-TOPOLOGY-18 scored **INDETERMINATE**, not PASS —
`empty_in_node_graph=False`. That row's first half needs the raw-topology store still
empty, and `topo` fills it permanently when M-TOPOLOGY-03 opens the Weight Matrix.
Re-driven **alone against the same build minutes later**: **PASS**,
`empty_in_node_graph=True`, filled in 6.6 s.

So the INDETERMINATE is a harness ordering artifact, not a regression — and the row
saying INDETERMINATE instead of FAIL is the scorer behaving correctly. Read the two
files together or the first one alone will look like a defect. **The steps are not
order-independent**; `topostate` must be driven first or alone.
