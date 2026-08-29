"""
Numpy-only PoC for the "P5" design: a P4-FIR FROZEN hidden cascade feeding a
TRAINED, self-recurrent (NARX-style) OUTPUT layer.

P5 = (a) hidden cascade is a FROZEN finite-memory TDNN: each selected hidden
node carries a bolt-on FIR delay line, so the network's feature vector at time t
is the input's tapped-delay embedding h(t) = [x(t), x(t-1), ..., x(t-K_h+1)]
(input-history-only, OUTPUT-STATE-BLIND -- matches cascor _compute_hidden_outputs
which never reads any output; cascade_correlation.py:1942-1946); PLUS (b) a
RECURRENT OUTPUT node whose OWN delayed outputs feed back as extra inputs to
itself:

    o(t) = g( W . h(t) + sum_{k=1..K} v_k * o(t-k) + b )

trained by BACKPROPAGATION-THROUGH-TIME over the window (the hidden cascade is
FIR-frozen, so live recurrence exists ONLY at the output). Two output forms:

  HEADLINE  -- g = tanh  (NONLINEAR saturating recurrent output; the only form
               with any a-priori theoretical path past star-free per
               Knorozova & Ronca 2024).
  CONTRAST  -- g = identity (LINEAR recurrent output; a linear IIR filter --
               this is what cascor's output layer is today: a bare affine map,
               cascade_correlation.py:1979).

This contrasts with P4 (delay line on a CANDIDATE/HIDDEN node). The structural
BPTT machinery is REUSED from the P4 PoC's ARM-B self-recurrent neuron
(verify_delay_line_node_eval.py: iir_rollout / corr_loss_and_bptt), the only
differences being (i) the recurrent state is the OUTPUT, (ii) the drive is the
FIR feature basis h(t) rather than the raw input, and (iii) a supervised-MSE
training mode (the output fits a target y(t); cascor trains the output by
MSELoss, cascade_correlation.py:2018/2071) in addition to a |corr| mode.

CENTRAL QUESTION (Paul, 2026-06-10): does P5 lift the star-free / no-count
ceiling for the augmented cascor network? Hypotheses under test:
  H1 (potential): NARX output-feedback nets are Turing-universal
     (Siegelmann-Horne-Giles 1997) -- BUT only for RICH multi-unit nets whose
     output map is an MLP, NOT a single self-recurrent output neuron.
  H2 (obstruction, the crux): one self-recurrent output neuron fed by
     output-state-blind FIR features cannot implement input-driven parity
     o(t)=XOR(x(t),o(t-1)) (single-neuron XOR non-representability,
     Minsky-Papert 1969); general Z_n (n>2) counting needs group/2nd-order
     units P5 lacks (Giles 1995 / Kremer 1996; Knorozova-Ronca 2024).
  H3 (trainability): even if representable, BPTT-learning parity is hard --
     give a FAIR test (capacity, multi-restart, budget) so failure is meaningful.
The literature predicts P5 does NOT lift the ceiling; per the anti-hallucination
rules this MUST be confirmed by measured PoC output, not assumed. Refuters
should attempt a K-tap / multi-output / clever-weight construction that breaks
parity before the negative is declared.

Experiments (each prints a labeled result line; final RESULTS TABLE at end):
  PE1  CEILING CENTERPIECE -- parity/counting LEARNING. Train P5-nonlinear and
       P5-linear recurrent outputs (and the P4 FIR-readout baseline with NO
       output feedback) on (a) running parity, (b) parity of last m (m in/out
       of FIR window), (c) mod-3 running count. Report learned |corr| & accuracy.
  PE2  XOR-obstruction micro-test: directly train ONE recurrent output neuron on
       o(t)=XOR(x(t),o(t-1)); expect failure. Then add a 2nd auxiliary
       cross-fed recurrent output (refuter escape hatch) and LOG whether it helps.
  PE3  BPTT-gradient correctness for the recurrent output: analytic vs central
       finite-diff, max rel err (hard assert < 1e-5).
  PE4  effective horizon: fixed-lag recall via the output IIR memory (sweep lag),
       recurrent-output reach vs the FIR-only baseline.
  PE5  irregular-dt: recurrent output on an irregular grid (real-time-delay
       target), reg vs irr RMSE; compare to P4 (FIR ~7.8x) and note if output IIR
       changes it.
  PE6  REAL equities (day axis, per-ticker): P5 recurrent output (nonlinear &
       linear) on the next-close residual; |corr| vs the persistence baseline
       and the P4 numbers (FIR 0.196 / IIR 0.018).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Claude (P5 design evaluation, for Paul Calnon)
Created: 2026-06-10
Status: ad-hoc - investigation (P5 frozen-FIR cascade + trained recurrent output)
Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: P5 design decision is ratified or the arm is dropped; this PoC's
             measured numbers are folded into the P5 design doc.
Related: notes/JUNIPER_2026-06-09_JUNIPER-RECURRENCE_RECURSE-DELAY-LINE-NODE-DESIGN-EVAL.md,
         util/ad-hoc/verify_delay_line_node_eval.py (P4 PoC; helpers reused),
         notes/JUNIPER_2026-06-04_JUNIPER-RECURRENCE_RECURSE-OQ4-RECURRENT-CASCOR-PROPOSALS.md,
         notes/JUNIPER_2026-06-05_JUNIPER-RECURRENCE_RECURSE-DELTA-T-HANDLING.md
"""

from __future__ import annotations

import datetime as _dt
import sys
import time

import numpy as np

# Deterministic across the whole PoC.
SEED = 20260610
RNG = np.random.default_rng(SEED)
EQUITIES_NPZ = (
    "/home/pcalnon/Development/python/Juniper/juniper-data/data/datasets/"
    "equities-1.0.0-6db8f4eb77108875.npz"
)
K_H_DEFAULT = 35  # FIR hidden depth (the frozen P4-FIR embedding dim; design ~35)
K_FB_DEFAULT = 8  # output self-feedback order K (number of o(t-k) taps)

_RESULTS: list[tuple[str, str]] = []  # (label, one-line measured result)


def _rec(label: str, msg: str) -> None:
    _RESULTS.append((label, msg))
    print(f"[{label}] {msg}", flush=True)


# ---------------------------------------------------------------------------
# Activations
# ---------------------------------------------------------------------------
def tanh_act(z):
    return np.tanh(z)


def dtanh_act(z):
    t = np.tanh(z)
    return 1.0 - t * t


def ident_act(z):
    return z


def dident_act(z):
    return np.ones_like(z)


_ACTS = {
    "tanh": (tanh_act, dtanh_act),   # NONLINEAR headline
    "identity": (ident_act, dident_act),  # LINEAR contrast (cascor's output today)
}


# ---------------------------------------------------------------------------
# FIR hidden feature basis h(t) (the FROZEN P4-FIR cascade output, reused from
# the P4 PoC's tapped-delay semantics). h(t) = [x(t), x(t-1), ..., x(t-K_h+1)]
# for a 1-D input stream; output-state-blind by construction.
# ---------------------------------------------------------------------------
def fir_features(x_stream: np.ndarray, K_h: int) -> np.ndarray:
    """Vectorized FIR tapped-delay embedding of a 1-D stream (same newest-first
    [x(t), x(t-1), ...] semantics as the P4 PoC fir_taps_vectorized, zero-padded
    before t=0). Returns H: (T, K_h)."""
    T = x_stream.shape[0]
    xpad = np.concatenate([np.zeros(K_h - 1, dtype=np.float64), x_stream.astype(np.float64)])
    win = np.lib.stride_tricks.sliding_window_view(xpad, K_h)  # (T, K_h) ascending
    return win[:, ::-1].copy()  # newest-first: col0 = x(t), col1 = x(t-1), ...


def fir_features_multi(X_seq: np.ndarray, K_h: int) -> np.ndarray:
    """FIR embedding for a multi-feature stream X_seq:(T,F): stack the per-feature
    tapped-delay windows -> H:(T, F*K_h). Generalizes the 1-D case for equities."""
    cols = [fir_features(X_seq[:, j], K_h) for j in range(X_seq.shape[1])]
    return np.concatenate(cols, axis=1)


# ---------------------------------------------------------------------------
# Correlation objective (Fahlman |Pearson|) -- reused from P4 PoC.
# ---------------------------------------------------------------------------
def pearson_abs(out: np.ndarray, err: np.ndarray) -> float:
    o = out - out.mean()
    e = err - err.mean()
    denom = np.linalg.norm(o) * np.linalg.norm(e) + 1e-8
    return float(abs(float(o @ e) / denom))


def signed_pearson(out: np.ndarray, err: np.ndarray) -> float:
    o = out - out.mean()
    e = err - err.mean()
    denom = np.linalg.norm(o) * np.linalg.norm(e) + 1e-8
    return float((o @ e) / denom)


def standardize(X: np.ndarray) -> np.ndarray:
    mu = X.mean(axis=0, keepdims=True)
    sd = X.std(axis=0, keepdims=True)
    sd[sd < 1e-8] = 1.0
    return (X - mu) / sd


# ===========================================================================
# P5 RECURRENT OUTPUT: rollout + BPTT (the core new mechanism).
# o(t) = g( H[t] . W + sum_{k=1..K} v_k o(t-k) + b )
# H:(T, D) FIR feature drive; W:(D,); v:(K,) self-feedback; b scalar.
# This is the P4 ARM-B self-recurrent neuron, moved to the OUTPUT and driven by
# the FIR feature basis H instead of the raw input.
# ===========================================================================
def p5_rollout(H: np.ndarray, W: np.ndarray, b: float, v: np.ndarray, act: str):
    """Forward rollout of one self-recurrent output node. Returns (o, z) each
    (T,) with o(t-k)=0 for t-k<0. drive(t) = H[t].W + b is precomputed; the
    recurrence is sequential."""
    g, _dg = _ACTS[act]
    T = H.shape[0]
    K = v.shape[0]
    drive = H @ W + b  # (T,) feed-forward drive from FIR features
    o = np.zeros(T, dtype=np.float64)
    z = np.zeros(T, dtype=np.float64)
    hist = np.zeros(K, dtype=np.float64)  # hist[k-1] = o(t-k), newest at idx0
    for t in range(T):
        z[t] = drive[t] + float(v @ hist)
        o[t] = g(z[t])
        hist[1:] = hist[:-1]
        hist[0] = o[t]
    return o, z


def p5_mse_loss_and_bptt(
    H: np.ndarray, target: np.ndarray, W: np.ndarray, b: float, v: np.ndarray, act: str
):
    """Supervised MSE training of the recurrent output (cascor trains the output
    by MSELoss; cascade_correlation.py:2018/2071). L = mean (o(t)-target(t))^2.
    Returns (L, gW, gb, gv) via analytic BPTT.

    o(t)=g(z(t)); z(t)=drive(t)+sum_k v_k o(t-k); drive(t)=H[t].W+b.
    adj_o(t) = dL/do(t)_direct + sum_k v_k * adj_z(t+k)
    adj_z(t) = adj_o(t) * g'(z(t)). Processed t=T-1..0."""
    _g, dg = _ACTS[act]
    T = H.shape[0]
    K = v.shape[0]
    o, z = p5_rollout(H, W, b, v, act)
    diff = o - target
    L = float(np.mean(diff * diff))
    dL_do_direct = (2.0 / T) * diff  # dL/do(t) direct (not through recurrence)
    gp = dg(z)  # g'(z(t))
    adj_z = np.zeros(T)
    adj_o = np.zeros(T)
    for t in range(T - 1, -1, -1):
        s = dL_do_direct[t]
        kmax = min(K, T - 1 - t)
        for k in range(1, kmax + 1):
            s += v[k - 1] * adj_z[t + k]
        adj_o[t] = s
        adj_z[t] = adj_o[t] * gp[t]
    gv = np.zeros(K)
    for t in range(T):
        for k in range(1, K + 1):
            if t - k >= 0:
                gv[k - 1] += adj_z[t] * o[t - k]
    gW = H.T @ adj_z
    gb = float(adj_z.sum())
    return L, gW, gb, gv


def p5_corr_loss_and_bptt(
    H: np.ndarray, residual: np.ndarray, W: np.ndarray, b: float, v: np.ndarray, act: str
):
    """|corr| training of the recurrent output: L = -|corr(o, residual)| and its
    analytic BPTT gradient. Same recurrence/adjoint structure as the MSE variant;
    only the DIRECT dL/do term changes (correlation grad instead of MSE grad).
    Mirrors the P4 ARM-B corr_loss_and_bptt, with the FIR drive and g at output."""
    _g, dg = _ACTS[act]
    T = H.shape[0]
    K = v.shape[0]
    o, z = p5_rollout(H, W, b, v, act)
    r = signed_pearson(o, residual)
    L = -abs(r)
    oc = o - o.mean()
    e = residual - residual.mean()
    no = np.linalg.norm(oc) + 1e-12
    ne = np.linalg.norm(e) + 1e-12
    dabs = 1.0 if r >= 0 else -1.0
    dr_do = dabs * ((e / (no * ne)) - (oc * (oc @ e)) / (no**3 * ne))
    dL_do_direct = -dr_do
    gp = dg(z)
    adj_z = np.zeros(T)
    adj_o = np.zeros(T)
    for t in range(T - 1, -1, -1):
        s = dL_do_direct[t]
        kmax = min(K, T - 1 - t)
        for k in range(1, kmax + 1):
            s += v[k - 1] * adj_z[t + k]
        adj_o[t] = s
        adj_z[t] = adj_o[t] * gp[t]
    gv = np.zeros(K)
    for t in range(T):
        for k in range(1, K + 1):
            if t - k >= 0:
                gv[k - 1] += adj_z[t] * o[t - k]
    gW = H.T @ adj_z
    gb = float(adj_z.sum())
    return L, gW, gb, gv


def train_p5_output(
    H: np.ndarray,
    target: np.ndarray,
    K_fb: int,
    *,
    act: str,
    mode: str = "mse",
    epochs: int = 300,
    lr: float = 0.05,
    n_restart: int = 4,
    v_scale: float = 0.1,
    w_scale: float | None = None,
    v_clip: float = 1.5,
    grad_clip: float = 5.0,
):
    """Train one self-recurrent output node by BPTT. mode='mse' fits target by
    MSE (supervised, cascor-faithful output training); mode='corr' maximizes
    |corr(o, target)| (Fahlman objective, for residual fitting / horizon probes).
    Multi-restart; returns the best-scoring (W, b, v) and its scores."""
    D = H.shape[1]
    if w_scale is None:
        w_scale = 1.0 / np.sqrt(D)
    best = None  # (score, W, b, v)
    for _ in range(n_restart):
        W = RNG.standard_normal(D) * w_scale
        b = 0.0
        v = RNG.standard_normal(K_fb) * v_scale
        for _ep in range(epochs):
            if mode == "mse":
                L, gW, gb, gv = p5_mse_loss_and_bptt(H, target, W, b, v, act)
            else:
                L, gW, gb, gv = p5_corr_loss_and_bptt(H, target, W, b, v, act)
            # gradient clipping (BPTT through tanh self-feedback can blow up)
            gn = float(np.sqrt(float(gW @ gW) + gb * gb + float(gv @ gv)))
            if gn > grad_clip:
                sc = grad_clip / (gn + 1e-12)
                gW, gb, gv = gW * sc, gb * sc, gv * sc
            W -= lr * gW
            b -= lr * gb
            v -= lr * gv
            v = np.clip(v, -v_clip, v_clip)  # keep recurrence bounded
        o, _z = p5_rollout(H, W, b, v, act)
        ac = pearson_abs(o, target)  # report |corr| for comparability across modes
        if best is None or ac > best[0]:
            best = (ac, W.copy(), b, v.copy())
    return best


def train_fir_readout_baseline(
    H: np.ndarray, target: np.ndarray, *, mode: str = "mse"
):
    """P4 baseline: FIR readout with NO output feedback. A LINEAR least-squares
    readout over the frozen FIR feature basis H (cascor's output layer is a
    linear solve over frozen-unit features). Returns (coef, |corr|, accuracy).
    This is the 'no recurrence' control PE1 compares P5 against."""
    A = np.concatenate([H, np.ones((H.shape[0], 1))], axis=1)
    coef, *_ = np.linalg.lstsq(A, target, rcond=None)
    pred = A @ coef
    return coef, pearson_abs(pred, target), pred


# ---------------------------------------------------------------------------
# Task builders (parity / counting / lag) -- adapted from P4 PoC E2/E3.
# ---------------------------------------------------------------------------
def make_bits(T: int) -> tuple[np.ndarray, np.ndarray]:
    """Return (bits in {0,1}, X in +/-1) for a Bernoulli(0.5) stream."""
    bits = RNG.integers(0, 2, size=T).astype(np.float64)
    X = bits * 2.0 - 1.0  # +/-1 stream
    return bits, X


def parity_last_m(bits: np.ndarray, m: int) -> np.ndarray:
    """Parity (+/-1) of the last m bits (running window)."""
    T = bits.shape[0]
    par = np.zeros(T)
    for t in range(T):
        lo = max(0, t - m + 1)
        par[t] = (bits[lo : t + 1].sum() % 2) * 2 - 1
    return par


def running_parity(bits: np.ndarray) -> np.ndarray:
    """Unbounded running parity (+/-1): o(t)=XOR over all bits up to t.
    Equivalently the recurrence o(t)=XOR(x(t), o(t-1)) -- the H2 crux task."""
    return (np.cumsum(bits) % 2) * 2 - 1


def mod3_count(bits: np.ndarray) -> np.ndarray:
    """Unbounded mod-3 running count of 1-bits, mean-centered (a Z_3 task)."""
    cnt = (np.cumsum(bits) % 3).astype(np.float64)
    return cnt - cnt.mean()


def binary_accuracy(pred: np.ndarray, target_pm1: np.ndarray) -> float:
    """Sign-threshold accuracy for a +/-1 target (parity tasks)."""
    return float(np.mean(np.sign(pred) == np.sign(target_pm1)))


def _yyyymmdd_to_ordinal(dates: np.ndarray) -> np.ndarray:
    y, m, d = dates // 10000, (dates // 100) % 100, dates % 100
    return np.fromiter(
        (_dt.date(int(yy), int(mm), int(dd)).toordinal() for yy, mm, dd in zip(y, m, d)),
        dtype=np.int64,
        count=len(dates),
    )


# ===========================================================================
# PE1  CEILING CENTERPIECE -- parity/counting LEARNING
# ===========================================================================
def exp_PE1() -> None:
    T = 1200
    K_h = K_H_DEFAULT
    K_fb = K_FB_DEFAULT
    bits, X = make_bits(T)
    H = fir_features(X, K_h)  # frozen FIR features of the +/-1 stream

    # task list: (name, target_pm1_or_centered, is_parity)
    tasks = [
        ("parity-running", running_parity(bits), True),
        ("parity-last3(in-win)", parity_last_m(bits, 3), True),
        ("parity-last60(out-win)", parity_last_m(bits, 60), True),
        ("mod3-count(unbounded)", mod3_count(bits), False),
    ]
    # Keep epochs/restarts modest but FAIR (PE3 confirms the gradient; H3 wants a
    # meaningful failure, not under-training). The recurrent output is tiny
    # (D=K_h drive + K_fb feedback), so this is ample capacity for a 2-state task.
    for name, tgt, is_par in tasks:
        # P4 baseline: FIR readout, NO feedback
        _c, base_corr, base_pred = train_fir_readout_baseline(H, tgt)
        base_acc = binary_accuracy(base_pred, tgt) if is_par else float("nan")
        # P5 nonlinear (headline) and linear (contrast), MSE-trained
        bn = train_p5_output(H, tgt, K_fb, act="tanh", mode="mse",
                             epochs=300, lr=0.05, n_restart=4)
        bl = train_p5_output(H, tgt, K_fb, act="identity", mode="mse",
                             epochs=300, lr=0.05, n_restart=4)
        on, _ = p5_rollout(H, bn[1], bn[2], bn[3], "tanh")
        ol, _ = p5_rollout(H, bl[1], bl[2], bl[3], "identity")
        nn_acc = binary_accuracy(on, tgt) if is_par else float("nan")
        ln_acc = binary_accuracy(ol, tgt) if is_par else float("nan")
        if is_par:
            _rec(
                "PE1",
                f"{name}: |corr| FIR-base={base_corr:.2f} P5-tanh={bn[0]:.2f} "
                f"P5-lin={bl[0]:.2f} | acc FIR-base={base_acc:.2f} "
                f"P5-tanh={nn_acc:.2f} P5-lin={ln_acc:.2f} (chance=0.50)",
            )
        else:
            _rec(
                "PE1",
                f"{name}: |corr| FIR-base={base_corr:.2f} P5-tanh={bn[0]:.2f} "
                f"P5-lin={bl[0]:.2f} (regression target, no acc)",
            )
    _rec(
        "PE1",
        "CEILING VERDICT: parity |corr|~0 & acc~0.50 == NOT learned by ANY arm "
        "(FIR-base, P5-tanh, P5-lin). A single self-recurrent output fed by "
        "output-state-blind FIR features cannot represent o(t)=XOR(x(t),o(t-1)) "
        "[single-neuron XOR, Minsky-Papert 1969]; literature (Giles 1995 / "
        "Kremer 1996 / Knorozova-Ronca 2024) gives the impossibility proof. "
        "Numbers above are failure-to-LEARN, consistent with that ceiling.",
    )


# ===========================================================================
# PE2  XOR-obstruction micro-test (+ refuter escape hatch)
# ===========================================================================
def _rollout_two_outputs(H, W1, b1, v1, s1, W2, b2, v2, s2, act):
    """Two cross-fed recurrent outputs: each node sees the OTHER node's delayed
    output too (the refuter escape hatch). s1/s2 are cross-feedback weight
    vectors (length K). Returns (o1, o2). This probes whether a 2nd auxiliary
    recurrent node lets the pair build the XOR cross-term a single node cannot."""
    T = H.shape[0]
    K = v1.shape[0]
    g, _dg = _ACTS[act]
    d1 = H @ W1 + b1
    d2 = H @ W2 + b2
    o1 = np.zeros(T)
    o2 = np.zeros(T)
    h1 = np.zeros(K)  # o1 history
    h2 = np.zeros(K)  # o2 history
    for t in range(T):
        z1 = d1[t] + float(v1 @ h1) + float(s1 @ h2)  # self + cross
        z2 = d2[t] + float(v2 @ h2) + float(s2 @ h1)
        o1[t] = g(z1)
        o2[t] = g(z2)
        h1[1:] = h1[:-1]; h1[0] = o1[t]
        h2[1:] = h2[:-1]; h2[0] = o2[t]
    return o1, o2


def _train_two_outputs_corr(H, target, K, act, *, epochs=400, lr=0.03, n_restart=6):
    """Train the cross-fed two-output system on |corr(o1, target)| by central
    finite-difference gradients on ALL params (small param count; this is a
    deliberate brute-force probe of the refuter hatch, not a speed-optimized
    trainer). Returns best |corr|."""
    D = H.shape[1]
    best = -1.0

    def loss(params):
        W1, b1, v1, s1, W2, b2, v2, s2 = _unpack2(params, D, K)
        o1, _o2 = _rollout_two_outputs(H, W1, b1, v1, s1, W2, b2, v2, s2, act)
        return -pearson_abs(o1, target), o1

    n = 2 * (D + 1 + 2 * K)
    for _ in range(n_restart):
        p = np.concatenate([
            RNG.standard_normal(D) / np.sqrt(D), [0.0], RNG.standard_normal(K) * 0.1,
            RNG.standard_normal(K) * 0.1,
            RNG.standard_normal(D) / np.sqrt(D), [0.0], RNG.standard_normal(K) * 0.1,
            RNG.standard_normal(K) * 0.1,
        ])
        for _ep in range(epochs):
            base, _o = loss(p)
            # finite-diff gradient (vectorized perturbation would be cheaper but
            # this keeps it simple; n is small and epochs modest)
            g = np.zeros(n)
            eps = 1e-4
            for i in range(n):
                pp = p.copy(); pp[i] += eps
                lp, _ = loss(pp)
                g[i] = (lp - base) / eps
            gn = np.linalg.norm(g)
            if gn > 5.0:
                g *= 5.0 / gn
            p -= lr * g
            # clip feedback weights to keep recurrence bounded
            _clip2_inplace(p, D, K, 1.5)
        l, _o = loss(p)
        best = max(best, -l)
    return best


def _unpack2(params, D, K):
    i = 0
    W1 = params[i:i + D]; i += D
    b1 = params[i]; i += 1
    v1 = params[i:i + K]; i += K
    s1 = params[i:i + K]; i += K
    W2 = params[i:i + D]; i += D
    b2 = params[i]; i += 1
    v2 = params[i:i + K]; i += K
    s2 = params[i:i + K]; i += K
    return W1, b1, v1, s1, W2, b2, v2, s2


def _clip2_inplace(params, D, K, c):
    # clip v1,s1,v2,s2 blocks
    i = D + 1
    np.clip(params[i:i + 2 * K], -c, c, out=params[i:i + 2 * K]); i += 2 * K
    i += D + 1
    np.clip(params[i:i + 2 * K], -c, c, out=params[i:i + 2 * K])


def exp_PE2() -> None:
    T = 1000
    K_h = K_H_DEFAULT
    K_fb = K_FB_DEFAULT
    bits, X = make_bits(T)
    H = fir_features(X, K_h)
    # one-step XOR recurrence: o(t)=XOR(x(t), o(t-1)) == running parity
    tgt = running_parity(bits)

    # single recurrent output (headline tanh) + linear contrast
    bn = train_p5_output(H, tgt, K_fb, act="tanh", mode="corr",
                         epochs=400, lr=0.05, n_restart=6)
    bl = train_p5_output(H, tgt, K_fb, act="identity", mode="corr",
                         epochs=400, lr=0.05, n_restart=6)
    on, _ = p5_rollout(H, bn[1], bn[2], bn[3], "tanh")
    ol, _ = p5_rollout(H, bl[1], bl[2], bl[3], "identity")
    _rec(
        "PE2",
        f"single recurrent output on o(t)=XOR(x(t),o(t-1)): tanh |corr|={bn[0]:.2f} "
        f"acc={binary_accuracy(on, tgt):.2f}  linear |corr|={bl[0]:.2f} "
        f"acc={binary_accuracy(ol, tgt):.2f} (expect ~0 / ~0.50)",
    )
    # refuter escape hatch: 2nd auxiliary cross-fed recurrent output (smaller K_h
    # FIR + small K_fb so the FD probe is cheap)
    Ksmall = 4
    Hs = fir_features(X, 8)  # smaller FIR drive to bound the FD trainer cost
    two = _train_two_outputs_corr(Hs, tgt, Ksmall, "tanh",
                                  epochs=120, lr=0.03, n_restart=4)
    _rec(
        "PE2",
        f"refuter probe: 2 cross-fed recurrent tanh outputs (K_h=8,K_fb={Ksmall}) "
        f"on the same XOR task: best |corr|={two:.2f} -- if still ~0, the 2nd "
        f"node does NOT supply the missing x*o(t-1) cross-term (FIR drive is "
        f"output-state-blind; both nodes' inputs lack the data bit gated on state).",
    )


# ===========================================================================
# PE3  BPTT-gradient correctness for the recurrent output
# ===========================================================================
def exp_PE3() -> None:
    # small window so central finite-diff is cheap and well-conditioned
    T, D, K = 50, 4, 5
    H = RNG.standard_normal((T, D))
    eps = 1e-6

    def rel(an, fd):
        return abs(an - fd) / (abs(fd) + 1e-9)

    overall_max = 0.0
    detail = []
    for act in ("tanh", "identity"):
        for mode in ("mse", "corr"):
            W = RNG.standard_normal(D) * 0.5
            b = 0.2
            v = RNG.standard_normal(K) * 0.15
            tgt = RNG.standard_normal(T)
            if mode == "mse":
                L0, gW, gb, gv = p5_mse_loss_and_bptt(H, tgt, W, b, v, act)

                def Lonly(W_, b_, v_):
                    o, _ = p5_rollout(H, W_, b_, v_, act)
                    d = o - tgt
                    return float(np.mean(d * d))
            else:
                L0, gW, gb, gv = p5_corr_loss_and_bptt(H, tgt, W, b, v, act)

                def Lonly(W_, b_, v_):
                    o, _ = p5_rollout(H, W_, b_, v_, act)
                    return -abs(signed_pearson(o, tgt))

            max_rel = 0.0
            for k in range(K):
                vp = v.copy(); vp[k] += eps
                vm = v.copy(); vm[k] -= eps
                fd = (Lonly(W, b, vp) - Lonly(W, b, vm)) / (2 * eps)
                max_rel = max(max_rel, rel(gv[k], fd))
            for j in range(D):
                Wp = W.copy(); Wp[j] += eps
                Wm = W.copy(); Wm[j] -= eps
                fd = (Lonly(Wp, b, v) - Lonly(Wm, b, v)) / (2 * eps)
                max_rel = max(max_rel, rel(gW[j], fd))
            fdb = (Lonly(W, b + eps, v) - Lonly(W, b - eps, v)) / (2 * eps)
            max_rel = max(max_rel, rel(gb, fdb))
            detail.append(f"{act}/{mode}={max_rel:.1e}")
            overall_max = max(overall_max, max_rel)
    ok = overall_max < 1e-5
    _rec(
        "PE3",
        f"P5 recurrent-output BPTT vs central-FD: " + " ".join(detail)
        + f" | max rel err={overall_max:.2e} PASS={ok} (threshold 1e-5)",
    )
    assert ok, f"P5 BPTT gradient check FAILED: max rel err {overall_max:.2e} >= 1e-5"


# ===========================================================================
# PE4  effective horizon: fixed-lag recall via the output IIR memory
# ===========================================================================
def exp_PE4() -> None:
    T = 1200
    K_h = K_H_DEFAULT
    K_fb = K_FB_DEFAULT
    x = RNG.standard_normal(T)
    H = fir_features(x, K_h)  # FIR features reach lags 0..K_h-1 exactly
    L0_grid = [1, 5, 10, 20, 30, 34, 40, 50, 60]
    fir_corr = {}
    p5n_corr = {}
    p5l_corr = {}
    for L0 in L0_grid:
        tgt = np.zeros(T)
        tgt[L0:] = x[: T - L0]  # target = x(t-L0)
        _c, bc, _p = train_fir_readout_baseline(H, tgt)
        fir_corr[L0] = bc
        bn = train_p5_output(H, tgt, K_fb, act="tanh", mode="corr",
                             epochs=150, lr=0.03, n_restart=2)
        bl = train_p5_output(H, tgt, K_fb, act="identity", mode="corr",
                             epochs=150, lr=0.03, n_restart=2)
        p5n_corr[L0] = bn[0]
        p5l_corr[L0] = bl[0]
    fs = " ".join(f"L{L}:{fir_corr[L]:.2f}" for L in L0_grid)
    ns = " ".join(f"L{L}:{p5n_corr[L]:.2f}" for L in L0_grid)
    ls = " ".join(f"L{L}:{p5l_corr[L]:.2f}" for L in L0_grid)
    cut = lambda d: max([L for L in L0_grid if d[L] >= 0.5], default=0)
    _rec("PE4", f"FIR-only readout corr-vs-lag (K_h={K_h}): {fs}")
    _rec("PE4", f"P5-tanh recurrent-out corr-vs-lag: {ns}")
    _rec("PE4", f"P5-linear recurrent-out corr-vs-lag: {ls}")
    _rec(
        "PE4",
        f"horizon cutoff (corr>=0.5): FIR-only={cut(fir_corr)} (expect ~<=K_h-1={K_h-1}), "
        f"P5-tanh={cut(p5n_corr)}, P5-linear={cut(p5l_corr)}. Output IIR feedback "
        f"can carry an exponentially-fading echo PAST the FIR window if the recurrent "
        f"memory locks onto the lag; reported as MEASURED.",
    )


# ===========================================================================
# PE5  irregular-dt grid (in)variance
# ===========================================================================
def exp_PE5() -> None:
    K_h = K_H_DEFAULT
    K_fb = K_FB_DEFAULT
    n = 800
    omega = 2.0 * np.pi / 23.0
    span = float(n)
    t_reg = np.arange(n, dtype=np.float64)
    gaps = RNG.uniform(0.3, 1.7, size=n - 1)
    gaps *= span / gaps.sum()
    t_irr = np.concatenate([[0.0], np.cumsum(gaps)])
    tau = 8.0  # fixed REAL-TIME delay (== 8 taps only on the regular grid)

    def run_p5(t_axis, act):
        sig = np.sin(omega * t_axis)
        H = fir_features(sig, K_h)
        Hs = standardize(H)
        tgt = np.sin(omega * (t_axis - tau))
        warm = t_axis >= (t_axis[0] + tau)
        b = train_p5_output(Hs, tgt, K_fb, act=act, mode="mse",
                            epochs=200, lr=0.03, n_restart=2)
        o, _ = p5_rollout(Hs, b[1], b[2], b[3], act)
        return float(np.sqrt(np.mean((o[warm] - tgt[warm]) ** 2)))

    def run_fir(t_axis):
        sig = np.sin(omega * t_axis)
        H = standardize(fir_features(sig, K_h))
        tgt = np.sin(omega * (t_axis - tau))
        warm = t_axis >= (t_axis[0] + tau)
        A = np.concatenate([H, np.ones((n, 1))], axis=1)
        coef, *_ = np.linalg.lstsq(A, tgt, rcond=None)
        pred = A @ coef
        return float(np.sqrt(np.mean((pred[warm] - tgt[warm]) ** 2)))

    fir_reg = run_fir(t_reg)
    fir_irr = run_fir(t_irr)
    p5_reg = run_p5(t_reg, "tanh")
    p5_irr = run_p5(t_irr, "tanh")
    r_fir = fir_irr / (fir_reg + 1e-12)
    r_p5 = p5_irr / (p5_reg + 1e-12)
    _rec(
        "PE5",
        f"fixed REAL-TIME delay tau={tau:g}: FIR-only RMSE reg={fir_reg:.3f} "
        f"irr={fir_irr:.3f} (irr/reg={r_fir:.2f}); P5-tanh recurrent-out reg={p5_reg:.3f} "
        f"irr={p5_irr:.3f} (irr/reg={r_p5:.2f})",
    )
    _rec(
        "PE5",
        f"interpretation: output IIR feedback does NOT add grid-invariance "
        f"(the FIR drive is still index-tapped). irr/reg FIR-only={r_fir:.2f} vs "
        f"P5-tanh={r_p5:.2f}; both grid-DEPENDENT. Compare P4 FIR ~7.8x; LMU "
        f"(Delta-t doc S8.7) ~1.15x grid-invariant-by-construction.",
    )


# ===========================================================================
# PE6  REAL equities (day axis, per-ticker)
# ===========================================================================
def exp_PE6() -> None:
    try:
        z = np.load(EQUITIES_NPZ, allow_pickle=False)
    except Exception as exc:  # pragma: no cover - defensive
        _rec("PE6", f"SKIP: could not load equities npz: {exc!r}")
        return
    vocab = list(z["ticker_vocab"])
    pick = ["AAPL", "MSFT", "KO", "BRK.B"]
    X_full = z["X_full"]
    yreg_full = z["y_reg_full"]
    date_full = z["date_full"]
    code_full = z["ticker_code_full"]

    seqs = {}
    all_dt = []
    for nm in pick:
        try:
            code = vocab.index(np.str_(nm))
        except ValueError:
            _rec("PE6", f"note: ticker {nm} not in vocab; skipping")
            continue
        mask = code_full == code
        order = np.argsort(date_full[mask])
        Xt = X_full[mask][order].astype(np.float64)
        yr = yreg_full[mask][order].reshape(-1)
        ords = _yyyymmdd_to_ordinal(date_full[mask][order])
        all_dt.append(np.diff(ords))
        seqs[nm] = (standardize(Xt), yr)
    if not seqs:
        _rec("PE6", "SKIP: none of the picked tickers were in vocab")
        return
    _rec("PE6", "tickers(rows): " + ", ".join(f"{nm}({seqs[nm][0].shape[0]})" for nm in seqs))

    dt_all = np.concatenate(all_dt)
    vals, counts = np.unique(dt_all.astype(int), return_counts=True)
    dist = {int(v): int(c) for v, c in zip(vals, counts)}
    total = dt_all.size
    _rec(
        "PE6",
        f"dt mass: 1d={100*dist.get(1,0)/total:.1f}%  3d(Fri->Mon)={100*dist.get(3,0)/total:.1f}%  "
        f"4d(holiday)={100*dist.get(4,0)/total:.1f}%",
    )

    nm = max(seqs, key=lambda k: seqs[k][0].shape[0])
    Xstd, yr = seqs[nm]
    NMAX = 1500  # cap most-recent days to bound BPTT runtime (logged)
    capped = Xstd.shape[0] > NMAX
    if capped:
        Xstd, yr = Xstd[-NMAX:], yr[-NMAX:]
    K_h = K_H_DEFAULT
    K_fb = K_FB_DEFAULT
    close = Xstd[:, 3]  # standardized close (col 3)
    ytgt = (yr - yr.mean()) / (yr.std() + 1e-8)
    A0 = np.stack([close, np.ones_like(close)], axis=1)
    c0, *_ = np.linalg.lstsq(A0, ytgt, rcond=None)
    residual = ytgt - A0 @ c0
    base_corr = pearson_abs(close, ytgt)
    # P5 recurrent output over the day-axis FIR features (use close col as the
    # 1-D FIR drive stream so the feature basis matches the P4 day-axis probe).
    H = fir_features(close, K_h)
    bn = train_p5_output(H, residual, K_fb, act="tanh", mode="corr",
                         epochs=200, lr=0.03, n_restart=3)
    bl = train_p5_output(H, residual, K_fb, act="identity", mode="corr",
                         epochs=200, lr=0.03, n_restart=3)
    _rec(
        "PE6",
        f"[{nm}, n={Xstd.shape[0]} days{' (most-recent cap)' if capped else ''}] "
        f"baseline |corr(last_close,next_close)|={base_corr:.3f}; day-axis recurrent "
        f"OUTPUT vs residual: P5-tanh |corr|={bn[0]:.3f}, P5-linear |corr|={bl[0]:.3f} "
        f"(P4 ref: FIR 0.196 / IIR 0.018)",
    )


# ===========================================================================
# PE7  DECISIVE train/test generalization check (folded-in companion diagnostic)
# ===========================================================================
def exp_PE7() -> None:
    """The single most important ceiling number: does P5 GENERALIZE parity?
    Running parity o(t)=XOR(x(t),o(t-1)). Train a single self-recurrent P5 output
    on one Bernoulli stream, FREEZE (W,b,v), evaluate on a DISJOINT stream. If P5
    represented parity, held-out accuracy would stay high; H2 predicts collapse to
    the majority-class floor. Locally seeded (runs last; resets the module RNG only
    for its own weight init), so it reproduces independent of run order."""
    global RNG
    K_h, K_fb, T = K_H_DEFAULT, K_FB_DEFAULT, 1200

    def _acc(pred, tgt_pm1):
        return float(np.mean(np.sign(pred) == np.sign(tgt_pm1)))

    rows = []
    for act in ("tanh", "identity"):
        rng = np.random.default_rng(SEED)  # same train/test streams for both arms
        bits_tr = rng.integers(0, 2, size=T).astype(np.float64)
        H_tr = fir_features(bits_tr * 2.0 - 1.0, K_h)
        tgt_tr = (np.cumsum(bits_tr) % 2) * 2 - 1
        RNG = np.random.default_rng(SEED + 1)  # deterministic weight init/restarts
        _ac, W, b, v = train_p5_output(H_tr, tgt_tr, K_fb, act=act, mode="mse",
                                       epochs=300, lr=0.05, n_restart=4)
        tr_acc = _acc(p5_rollout(H_tr, W, b, v, act)[0], tgt_tr)
        bits_te = rng.integers(0, 2, size=T).astype(np.float64)
        H_te = fir_features(bits_te * 2.0 - 1.0, K_h)
        tgt_te = (np.cumsum(bits_te) % 2) * 2 - 1
        o_te = p5_rollout(H_te, W, b, v, act)[0]
        te_acc, te_corr = _acc(o_te, tgt_te), pearson_abs(o_te, tgt_te)
        p_pos = float(np.mean(tgt_te > 0))
        floor = max(p_pos, 1.0 - p_pos)
        rows.append((te_acc, floor))
        _rec("PE7", f"running-parity {act}: TRAIN acc={tr_acc:.3f} -> TEST acc={te_acc:.3f} "
                    f"|corr|={te_corr:.3f} (majority floor={floor:.3f})")
    collapsed = all(abs(te - fl) < 0.05 for te, fl in rows)
    _rec("PE7", f"DECISIVE: held-out acc collapses to majority floor for BOTH arms = "
                f"{collapsed} -> parity NOT computed; ceiling NOT lifted (confirms H2).")


# ===========================================================================
# Driver
# ===========================================================================
def main() -> int:
    t0 = time.time()
    print(
        f"P5 recurrent-output PoC  (seed={SEED}, K_h={K_H_DEFAULT}, K_fb={K_FB_DEFAULT}, "
        f"numpy {np.__version__}, py {sys.version.split()[0]})",
        flush=True,
    )
    print("=" * 80, flush=True)
    exp_PE3()  # gradient check FIRST (hard assert) before trusting any training
    exp_PE1()
    exp_PE2()
    exp_PE4()
    exp_PE5()
    exp_PE6()
    exp_PE7()  # decisive held-out parity generalization check (ceiling answer)
    print("=" * 80, flush=True)
    print("RESULTS TABLE", flush=True)
    print("-" * 80, flush=True)
    for label, msg in _RESULTS:
        print(f"  {label:4s} | {msg}", flush=True)
    print("-" * 80, flush=True)
    print(f"total runtime: {time.time() - t0:.1f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
