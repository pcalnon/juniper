# Dataset-partition naming — external validation record

**Project**: Juniper
**Sub-Project**: juniper-ecosystem (data contract)
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-29
**Status**: VALIDATION RECORD — supports §10 of [`JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md`](JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md)
**Question**: what are the generally accepted names for ML dataset partitions and their roles, and
is `X_eval` an appropriate name for the in-loop partition?

---

## 1. Method

Three agents, launched together, **none shown another's findings**, per the 2026-08-23 adversarial
SOP (different lenses, prompted to refute rather than confirm):

| lens | brief |
| --- | --- |
| **L1 — authoritative literature** | Canonical textbooks, official glossaries, library user guides. What is the convention and what is each partition's role? |
| **L2 — framework APIs** | An *empirical* survey of what code literally names things — parameters, enums, split strings — not what is theoretically correct. |
| **L3 — adversarial** | Briefed to **refute** the premise "there is one accepted convention, so adopt `train`/`eval`/`test`". Explicitly told a confident refutation with a fabricated citation is worse than none. |

**Anti-hallucination protocol**, applied to all three and the reason this record exists:

- No answering from memory. Every claim required a URL **fetched during the task** plus a
  **verbatim quote** from it.
- A claim that could not be sourced had to be reported as unverified rather than asserted.
- Each agent had to produce an explicit **UNVERIFIED** section listing what it believed but could
  not source — §5 aggregates those, and it is the most important section here.

## 2. Convergent findings — all three lenses independently

These are the claims that arrived from more than one lens without any lens seeing another's work.
Independent convergence is the signal that a finding is real.

1. **`train` / `validation` / `test` is the dominant mainstream-ML convention.** L1 (Google ML
   Glossary, ESL, Goodfellow, scikit-learn, TFDS, HF), L2 (HF `Split` enum, TFDS `Split`, Keras
   `validation_*`), and L3 — which *tried to break this and could not*.
2. **`eval` does not name a partition.** L1: 0 occurrences of standalone "eval" in Google's full ML
   Glossary; 0 occurrences of `X_eval` across 17 fetched corpora. L2: no `EVAL` member in
   `datasets.Split`; `eval` appears only as a parameter prefix and metric-key prefix. L3: `eval` is
   overloaded across action, model mode, benchmark suite, and *both* partitions.
3. **`train` is universal.** No counter-example found by any lens.
4. **Roles are unambiguous in the literature**: train fits; validation is the in-loop partition for
   tuning, selection and early stopping; test is touched once for final assessment.

## 3. The decisive finding — from the adversarial lens alone

L3 found what L1 and L2 did not, and it inverts the proposal rather than merely disfavouring it.

> "There are several ways to refer to train/validation/test splits. Validation splits are sometimes
> called "dev", and test splits may be referred to as "eval". These other split names are also
> supported, and the following keywords are equivalent:
> - train, training
> - validation, valid, val, dev
> - **test, testing, eval, evaluation**"
>
> — <https://huggingface.co/docs/hub/en/datasets-file-names-and-splits> (L3 verified byte-for-byte via curl)

**On the largest dataset registry, `eval` is an alias for `test`.** A contract shipping
`X_train` / `X_eval` / `X_test` would be resolved by HF-shaped tooling as two test splits and no
validation split.

Corroborating, each with a fetched quote:

- **XGBoost**: `evallist = [(dtrain, 'train'), (dtest, 'eval')]` — `'eval'` labels the *test* matrix
  (<https://xgboost.readthedocs.io/en/stable/python/python_intro.html>).
- **TRIPOD+AI** (BMJ): renamed "validation" *because it is ambiguous*, and its replacement means the
  test set — *"we refer to data used to evaluate model performance as evaluation data"*
  (<https://pmc.ncbi.nlm.nih.gov/articles/PMC11019967/>).
- **Hugging Face contradicts itself**: the Hub maps `eval`→test while `Trainer(eval_dataset=…)` uses
  it for the validation role.
- **`eval` as action/mode/suite**: `torch.nn.Module.eval()` — *"Set the module in evaluation mode"*;
  `Trainer.evaluate(… metric_key_prefix='eval')`; OpenAI Evals.

This is the finding that changed the answer. Neither the literature lens nor the API lens surfaced
it — the literature lens established `eval` was *absent*, the API lens established it named an
*action*; only the adversary found it actively means **the other partition**.

## 4. Where the premise genuinely broke — L3's successful refutations

The adversary was asked to break "there is one accepted convention". It largely succeeded, and this
tempers how strongly the project should assert *any* naming:

- **Clinical prediction modelling reverses the terms.** *"In the field of machine learning, the
  derivation (further divided into training and tuning) and validation datasets may be called the
  'training' (further divided into 'training' and 'validation') and 'test' datasets, respectively."*
  (<https://pmc.ncbi.nlm.nih.gov/articles/PMC10760493/>)
- **The reversal appears in named, famous papers**, and the same authors switch vocabulary by venue
  (Walston et al., <https://arxiv.org/pdf/2404.19303>). Its recommendation is that each paper define
  the terms locally — *a convention that must be redefined per-document is not a convention*.
- **NLP uses `dev`/`development`**, in the field's canonical textbook (Jurafsky & Martin SLP3 §4.10,
  "devset") and canonical shared task (CoNLL-2003, which has *four* files).
- **TFDS declines to prescribe**: *"Any alphabetical string can be used as split name, apart from
  `all`"*.
- **scikit-learn's default splitter yields two partitions**, not three.
- **Kaggle uses four** (public/private test), requiring papers to re-map names explicitly.

**Consequence for the design**: the data contract must *define the role* of each partition
explicitly rather than relying on the name to carry the meaning. The name reduces surprise; it does
not remove the need for a stated contract.

## 5. Unverified, unreachable, and second-hand — read this before citing anything above

Aggregated from all three agents' self-reported gaps. Nothing here is load-bearing for the decision,
but several items would be if quoted carelessly.

**Sources that could not be reached:**

- **ESL primary copy 404s on the publisher's own host.** `hastie.su.domains/ElemStatLearn/…` and two
  alternates all returned 404. All ESL quotes come from a mirror, verified as genuine by its front
  matter but **not** byte-compared against a publisher copy.
- **comp.ai.neural-nets FAQ** — the "most blatant example of terminological confusion" quote could
  not be traced to the primary text (FTP unsupported, SSL failure, 404). It rests on Wikipedia and
  HandWiki quoting it. **Second-hand.**
- **Ripley's glossary** — second-hand via Wikipedia and a blog. Not read.
- **ISO/IEC 22989** — paywalled. **No claim is made about it**, though a standards-body definition
  would be the strongest possible source if ever obtained.
- **PyTorch Lightning's rendered docs** would not fetch (JS SPA); names were taken from the
  project's reStructuredText sources on `master`, which is upstream of the stable site but not the
  pinned release.
- **Kaggle's own docs** are JS-rendered and returned only a title.

**Methodological weaknesses the agents flagged themselves:**

- **Negative claims rest on fetch summarisation, not literal grep.** "No 'validation' on this page",
  "no `validation_dataset` parameter" — these were reported over extracted page text, not a
  character-level search. These are the weakest claims in the record.
- **`holdout` was never directly searched for.** Reported as "not surveyed", not "disproven".
- **"Dominant in NLP" is an inference** from the canonical textbook's usage, not a corpus survey. No
  paper-frequency measurement was done by any lens.
- **Goodfellow's official HTML inserts spurious intra-word spaces** (PDF kerning artifacts); quotes
  were taken from a mirror PDF and cross-verified against the official HTML with whitespace removed.
  One genuine edition difference surfaced and was disclosed.
- **sklearn's "no three-way splitter"** is partly inference: the API listing contains none, but the
  assertion sentence in the fetch result was the summariser's, not the page's.
- **`X_val` is not established as a *documented* convention.** L1 found 0 occurrences in the sklearn
  docs against 11 each for `X_train`/`X_test`. Its support is practical (HF alias list, Keras
  docstring `(x_val, y_val)`, torchvision `split='val'`, Lightning `val_dataloader`, and cascor's
  own existing signatures) — not a style guide. **No style guide for this appears to exist.**

**Suspicions explicitly excluded from the decision** (L3 labelled these unsourced and they are
recorded only so nobody re-derives them as findings): that ISO/IEC 22989 defines the three-way
split; that pre-1990 statistics used "validation" for final assessment; that `X_eval` would be
misread as LLM eval-harness input in a 2026 codebase; that HF's `datasets` *library* (not just the
Hub docs) resolves `eval`→`test`.

## 6. Verdict

**`X_eval` is rejected.** Not on style grounds — on the evidence that `eval` resolves to `test` in
the largest dataset registry, labels the test matrix in XGBoost's canonical idiom, and denotes the
test set in a major clinical reporting standard, while simultaneously naming the validation role in
HF's own Trainer. It is the one candidate token that is actively ambiguous *between the two
partitions this design exists to separate*.

**`X_val` / `y_val` adopted for contract keys, `validation` for split and config vocabulary.** It is
an explicit HF alias for the validation split, it matches the contract's existing capitalisation,
and — decisively — cascor's two `fit` signatures already use `x_val` / `X_val`, so the contract comes
to agree with code that already exists rather than introducing a third spelling.

**Confidence: HIGH on rejecting `eval`; HIGH on `validation` as the role name; MEDIUM-HIGH on `X_val`
as the key spelling** (practical support is strong, documented-convention support is thin, and §5
records exactly why).

## 7. References

- [`JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md`](JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md) §10 — the decision this record supports
- [cascor#582](https://github.com/pcalnon/juniper-cascor/issues/582) — the issue that raised the partition question
- Ecosystem data contract — `Juniper/CLAUDE.md` § Data Contract
