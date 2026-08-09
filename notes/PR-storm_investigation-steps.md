# PR storm investigation

The remediation plan is merged and self-contained — dispatch it by pasting the file into a fresh session whenever you're ready.

It will run the following:

- damage census
- consolidate root cause
- produce the three validated guardrail proposals
- generate the notes/…-ANALYSIS.md decision document

Until then, the standing items are unchanged:

- the plan's owner-side probes when you get a moment (naming bypass integrations 1236702/1276151; the three Cursor automation configs behind the dashboard UUIDs),
- the recurrence auth-on smoke at your next stack bring-up,
- a merge queue (or strict=true) on main
  - the plan's P1 proposal formalizes this.
  - this is the one control the forensics showed would have prevented all eight damage incidents
  - worth weighing before the next monthly Cursor storm

---

## Standing issues

1. PR #925 bypass decisions:
    - identify 1276151
    - cursor/claude removal
    - code_quality deadlock
    - queue coupling
2. the merge-queue availability check
3. the item-1 promotion call around Aug 21
4. plus an eventual ff-pull of your local recurrence checkout
