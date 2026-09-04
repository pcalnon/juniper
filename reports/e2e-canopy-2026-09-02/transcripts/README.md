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
