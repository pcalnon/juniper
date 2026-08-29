"""
Numpy-only PoC for the "P4" delay-line / shift-register recurrent OUTPUT module
for Cascade-Correlation candidate nodes. Evaluates BOTH arms as single
cascor-style candidate nodes that maximize |correlation(activation, residual)|:

  ARM A (FIR / tapped delay line):  a(t)=f(W.x(t)); node EMITS taps
      [a(t), a(t-1), ..., a(t-K+1)] (K=35); a downstream LINEAR readout over the
      K taps is trained.  a(t) has NO self-dependency -> no cycle -> finite
      impulse response (TDNN). Gradients are single-shot (cascor-faithful).
  ARM B (IIR / self-feedback):  a(t)=f(W.x(t) + sum_{k=1..K} v_k a(t-k)); the
      delayed taps feed BACK with learnable weights v_k. Genuine feedback (IIR);
      candidate training needs a recurrence-aware gradient (BPTT-over-window).

Experiments (each prints a labeled result line; final RESULTS TABLE at end):
  E1  precompute == sequential (ARM A): sequential shift loop vs vectorized
      sliding window; assert max|diff| < 1e-10 on a shuffled batch.
  E2  effective horizon / fixed-lag recall (both arms): target=x(t-L0),
      sweep L0 in {1,5,10,20,30,35,40,45,50} at K=35; report corr vs L0.
  E3  counting/parity ceiling (both arms): parity of last m bits + mod-3 count,
      m within and beyond K. OQ-4 star-free-ceiling probe.
  E4  irregular-dt grid (in)variance (both arms): sin(w t) on regular vs
      irregular grid; readout reconstructs a delayed value; RMSE reg vs irr;
      include a +dt-feature variant. Mirrors the Delta-t doc S8.6 structure.
  E5  IIR BPTT-gradient correctness (ARM B): analytic BPTT of the correlation
      loss through the K-tap recurrence vs central finite differences
      (max relative error; expect < 1e-5).
  E6  REAL equities: load the equities-1.0.0 npz, pick a few tickers, window
      per-ticker (lookback=35, no cross-ticker; target=next-step y_reg), print
      the calendar-day-gap dt distribution (Fri->Mon=3 mass), run BOTH arms as
      candidates maximizing corr with the y_reg residual; report achievable
      correlation, realized effective horizon, and dt stats.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Claude (P4 design evaluation, for Paul Calnon)
Created: 2026-06-09
Status: ad-hoc - investigation (P4 delay-line / shift-register ARM A vs ARM B)
Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: P4 design decision (FIR vs IIR) is ratified or the arm is dropped;
             this PoC's measured numbers are folded into the design doc.
Related: notes/JUNIPER_2026-06-04_JUNIPER-RECURRENCE_RECURSE-OQ4-RECURRENT-CASCOR-PROPOSALS.md,
         notes/JUNIPER_2026-06-05_JUNIPER-RECURRENCE_RECURSE-DELTA-T-HANDLING.md (S8.6/S8.7),
         util/ad-hoc/verify_delta_t_reference_code.py
"""

from __future__ import annotations

import datetime as _dt
import sys
import time

import numpy as np

# Deterministic across the whole PoC.
SEED = 20260609
RNG = np.random.default_rng(SEED)
EQUITIES_NPZ = (
    "/home/pcalnon/Development/python/Juniper/juniper-data/data/datasets/"
    "equities-1.0.0-6db8f4eb77108875.npz"
)
K_DEFAULT = 35  # shift-register depth / embedding dim (design says ~35)

_RESULTS: list[tuple[str, str]] = []  # (label, one-line measured result)


def _rec(label: str, msg: str) -> None:
    _RESULTS.append((label, msg))
    print(f"[{label}] {msg}", flush=True)


# ---------------------------------------------------------------------------
# Core cascor-style activation + the two delay-line arms (pure numpy)
# ---------------------------------------------------------------------------
def f_act(z: np.ndarray) -> np.ndarray:
    """Bounded saturating activation (tanh) - cascor's candidate nonlinearity
    family. Used by both arms. (cascor candidate forward = activation_fn(W.x+b).)"""
    return np.tanh(z)


def df_act(z: np.ndarray) -> np.ndarray:
    t = np.tanh(z)
    return 1.0 - t * t


def fir_activation(X_seq: np.ndarray, W: np.ndarray, b: float) -> np.ndarray:
    """ARM A pre-tap node activation, per timestep, NO self-dependency.

    X_seq: (T, F) single sequence. Returns a: (T,) where a(t)=f(W.x(t)+b).
    Mini-batch / shuffle invariant by construction (each t independent)."""
    z = X_seq @ W + b
    return f_act(z)


def fir_taps_sequential(a: np.ndarray, K: int) -> np.ndarray:
    """ARM A shift-register EMIT, the literal hardware semantics: at each t the
    register holds [a(t), a(t-1), ..., a(t-K+1)] (zero-filled before t=0).

    Returns taps: (T, K), taps[t, j] = a(t-j) (0 if t-j < 0)."""
    T = a.shape[0]
    taps = np.zeros((T, K), dtype=a.dtype)
    reg = np.zeros(K, dtype=a.dtype)  # reg[0]=newest
    for t in range(T):
        reg[1:] = reg[:-1]  # shift older
        reg[0] = a[t]  # clock in newest
        taps[t] = reg
    return taps


def fir_taps_vectorized(a: np.ndarray, K: int) -> np.ndarray:
    """ARM A shift-register EMIT via a vectorized sliding window (the
    'precompute' path used during mini-batch candidate training). Same
    [a(t), a(t-1), ..., a(t-K+1)] semantics as the sequential register."""
    T = a.shape[0]
    a_pad = np.concatenate([np.zeros(K - 1, dtype=a.dtype), a])  # left zero-pad
    # sliding_window_view gives ascending windows [a(t-K+1) .. a(t)];
    # reverse the last axis to get [a(t) .. a(t-K+1)] (newest-first taps).
    win = np.lib.stride_tricks.sliding_window_view(a_pad, K)  # (T, K) ascending
    return win[:, ::-1].copy()


def iir_rollout(
    X_seq: np.ndarray, W: np.ndarray, b: float, v: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """ARM B feedback rollout: a(t)=f(W.x(t)+b + sum_{k=1..K} v_k a(t-k)).

    X_seq: (T, F); v: (K,). Returns (a, z) each (T,), with a(t-k)=0 for t-k<0.
    This is a genuine recurrence (IIR) - the source of BPTT below."""
    T = X_seq.shape[0]
    K = v.shape[0]
    base = X_seq @ W + b  # feed-forward drive, (T,)
    a = np.zeros(T, dtype=np.float64)
    z = np.zeros(T, dtype=np.float64)
    hist = np.zeros(K, dtype=np.float64)  # hist[k-1]=a(t-k), newest at idx0
    for t in range(T):
        z[t] = base[t] + float(v @ hist)
        a[t] = f_act(z[t])
        hist[1:] = hist[:-1]
        hist[0] = a[t]
    return a, z


# ---------------------------------------------------------------------------
# Cascor correlation objective + small trainers (manual gradients, no torch)
# ---------------------------------------------------------------------------
def pearson_abs(out: np.ndarray, err: np.ndarray) -> float:
    """Fahlman |Pearson| score over a 1-D activation vector vs one residual
    column (cascor _calculate_correlation: mean-center, dot / (||.||*||.||+eps),
    abs)."""
    o = out - out.mean()
    e = err - err.mean()
    denom = np.linalg.norm(o) * np.linalg.norm(e) + 1e-8
    return float(abs(float(o @ e) / denom))


def signed_pearson(out: np.ndarray, err: np.ndarray) -> float:
    o = out - out.mean()
    e = err - err.mean()
    denom = np.linalg.norm(o) * np.linalg.norm(e) + 1e-8
    return float((o @ e) / denom)


def fit_linear_readout(taps: np.ndarray, target: np.ndarray) -> tuple[np.ndarray, float]:
    """ARM A downstream LINEAR readout over the K taps, trained by least squares
    (closed-form; the cascor output layer is a linear solve over frozen-unit
    features). Returns (coef, |corr(readout, target)|)."""
    A = np.concatenate([taps, np.ones((taps.shape[0], 1))], axis=1)  # +bias col
    coef, *_ = np.linalg.lstsq(A, target, rcond=None)
    pred = A @ coef
    return coef, pearson_abs(pred, target)


def train_fir_node(
    X_seq: np.ndarray,
    residual: np.ndarray,
    K: int,
    *,
    epochs: int = 400,
    lr: float = 0.05,
    n_restart: int = 4,
) -> tuple[float, np.ndarray, float, np.ndarray]:
    """ARM A candidate: learn W,b so the K-tap readout correlates with residual.

    Single-shot gradient each epoch (a(t) has no self-dependency, so this is
    cascor-faithful: no BPTT). The readout is re-solved (lstsq) each epoch and
    the |corr| of the readout is the maximized objective. Multi-restart on W.
    Returns (best_abscorr, best_W, best_b, best_readout_coef)."""
    F = X_seq.shape[1]
    T = X_seq.shape[0]
    best = (-1.0, None, None, None)
    for _ in range(n_restart):
        W = RNG.standard_normal(F) * (1.0 / np.sqrt(F))
        b = 0.0
        for _ep in range(epochs):
            z = X_seq @ W + b  # (T,)
            a = f_act(z)
            taps = fir_taps_vectorized(a, K)  # (T, K)
            coef, _ = fit_linear_readout(taps, residual)
            wt, bt = coef[:K], coef[K]
            pred = taps @ wt + bt  # (T,)
            r = signed_pearson(pred, residual)
            # d|r|/dW via chain rule through pred->taps->a->z (readout coef held
            # fixed for this step; it is re-solved next epoch).
            p = pred - pred.mean()
            e = residual - residual.mean()
            np_ = np.linalg.norm(p) + 1e-12
            ne = np.linalg.norm(e) + 1e-12
            # d r / d pred_t  (signed corr grad)
            drd_pred = (e / (np_ * ne)) - (p * (p @ e)) / (np_**3 * ne)
            # pred_t = sum_j wt_j * taps[t,j] = sum_j wt_j * a(t-j)
            # d pred_t / d a(s) = wt_{t-s} when 0<=t-s<K
            # => d r / d a(s) = sum_{j} drd_pred[s+j] * wt_j  (correlation in t)
            dr_da = np.zeros(T)
            for j in range(K):
                # contribution of a(s) to pred at t=s+j
                dr_da[: T - j] += drd_pred[j:] * wt[j] if j > 0 else drd_pred * wt[0]
            # a = f(z); z = X.W+b
            dz = dr_da * df_act(z)  # (T,)
            gW = X_seq.T @ dz
            gb = float(dz.sum())
            sign = 1.0 if r >= 0 else -1.0  # maximize |r|
            W += lr * sign * gW
            b += lr * sign * gb
        z = X_seq @ W + b
        a = f_act(z)
        taps = fir_taps_vectorized(a, K)
        coef, ac = fit_linear_readout(taps, residual)
        if ac > best[0]:
            best = (ac, W.copy(), b, coef.copy())
    return best


def corr_loss_and_bptt(
    X_seq: np.ndarray, residual: np.ndarray, W: np.ndarray, b: float, v: np.ndarray
) -> tuple[float, np.ndarray, np.ndarray, float]:
    """ARM B: L = -|corr(a, residual)| and its analytic BPTT gradient wrt
    (v, W, b), where a is the IIR rollout. Returns (L, gv, gW, gb).

    BPTT: a(t)=f(z(t)); z(t)=base(t)+sum_k v_k a(t-k); base(t)=W.x(t)+b.
    adj_a(t) = dL/da(t) (direct, from corr) + sum_k v_k * adj_z(t+k);
    adj_z(t) = adj_a(t) * f'(z(t)).  Processed t = T-1 .. 0."""
    T = X_seq.shape[0]
    K = v.shape[0]
    a, z = iir_rollout(X_seq, W, b, v)
    r = signed_pearson(a, residual)
    L = -abs(r)
    # dL/da(t) direct term (through the correlation, before recurrence):
    o = a - a.mean()
    e = residual - residual.mean()
    no = np.linalg.norm(o) + 1e-12
    ne = np.linalg.norm(e) + 1e-12
    dabs = 1.0 if r >= 0 else -1.0  # d|r|/dr
    dr_da_direct = dabs * ((e / (no * ne)) - (o * (o @ e)) / (no**3 * ne))
    dL_da_direct = -dr_da_direct  # L = -|r|
    adj_z = np.zeros(T)
    adj_a = np.zeros(T)
    gv = np.zeros(K)
    for t in range(T - 1, -1, -1):
        s = dL_da_direct[t]
        for k in range(1, K + 1):
            if t + k < T:
                s += v[k - 1] * adj_z[t + k]
        adj_a[t] = s
        adj_z[t] = adj_a[t] * df_act(z[t])
    # accumulate gv: dz(t)/dv_k = a(t-k)
    for t in range(T):
        for k in range(1, K + 1):
            if t - k >= 0:
                gv[k - 1] += adj_z[t] * a[t - k]
    gW = X_seq.T @ adj_z  # dz(t)/dW = x(t)
    gb = float(adj_z.sum())  # dz(t)/db = 1
    return L, gv, gW, gb


def train_iir_node(
    X_seq: np.ndarray,
    residual: np.ndarray,
    K: int,
    *,
    epochs: int = 300,
    lr: float = 0.02,
    n_restart: int = 3,
    v_scale: float = 0.1,
) -> tuple[float, np.ndarray, float, np.ndarray]:
    """ARM B candidate: BPTT-trained W,b,v maximizing |corr(a, residual)|.
    Returns (best_abscorr, best_W, best_b, best_v)."""
    F = X_seq.shape[1]
    best = (-1.0, None, None, None)
    for _ in range(n_restart):
        W = RNG.standard_normal(F) * (1.0 / np.sqrt(F))
        b = 0.0
        v = RNG.standard_normal(K) * v_scale
        for _ep in range(epochs):
            L, gv, gW, gb = corr_loss_and_bptt(X_seq, residual, W, b, v)
            # gradient DESCENT on L = -|corr| (== maximize |corr|)
            v -= lr * gv
            W -= lr * gW
            b -= lr * gb
            v = np.clip(v, -1.5, 1.5)  # keep the recurrence from blowing up
        a, _z = iir_rollout(X_seq, W, b, v)
        ac = pearson_abs(a, residual)
        if ac > best[0]:
            best = (ac, W.copy(), b, v.copy())
    return best


# ---------------------------------------------------------------------------
# Helpers shared by experiments
# ---------------------------------------------------------------------------
def _yyyymmdd_to_ordinal(dates: np.ndarray) -> np.ndarray:
    y, m, d = dates // 10000, (dates // 100) % 100, dates % 100
    return np.fromiter(
        (_dt.date(int(yy), int(mm), int(dd)).toordinal() for yy, mm, dd in zip(y, m, d)),
        dtype=np.int64,
        count=len(dates),
    )


def standardize(X: np.ndarray) -> np.ndarray:
    mu = X.mean(axis=0, keepdims=True)
    sd = X.std(axis=0, keepdims=True)
    sd[sd < 1e-8] = 1.0
    return (X - mu) / sd


# ===========================================================================
# E1  precompute == sequential (ARM A)
# ===========================================================================
def exp_E1() -> None:
    T, F, K = 600, 6, K_DEFAULT
    X = RNG.standard_normal((T, F))
    W = RNG.standard_normal(F)
    b = 0.3
    a = fir_activation(X, W, b)  # per-t, order-independent
    seq = fir_taps_sequential(a, K)
    vec = fir_taps_vectorized(a, K)
    dmax = float(np.max(np.abs(seq - vec)))
    # shuffle-invariance: a(t) does not depend on batch order; permuting the
    # ROWS of X permutes a identically, so per-row tap windows built from the
    # PERMUTED contiguous stream still match the sequential register on that
    # same permuted stream.
    perm = RNG.permutation(T)
    a_p = fir_activation(X[perm], W, b)
    seq_p = fir_taps_sequential(a_p, K)
    vec_p = fir_taps_vectorized(a_p, K)
    dmax_p = float(np.max(np.abs(seq_p - vec_p)))
    # also confirm a(t) itself is permutation-equivariant (mini-batch invariance)
    equiv = float(np.max(np.abs(a[perm] - a_p)))
    ok = dmax < 1e-10 and dmax_p < 1e-10 and equiv < 1e-12
    _rec(
        "E1",
        f"ARM A taps sequential==vectorized: max|diff|={dmax:.2e} "
        f"(shuffled={dmax_p:.2e}); a(t) perm-equivariance={equiv:.2e}; "
        f"PASS={ok} (threshold 1e-10)",
    )


# ===========================================================================
# E2  effective horizon / fixed-lag recall (both arms)
# ===========================================================================
def exp_E2() -> None:
    T, K = 1200, K_DEFAULT
    F = 1
    # white-ish input so x(t-L0) is recoverable iff the mechanism reaches lag L0
    x = RNG.standard_normal(T)
    X = x.reshape(T, 1)
    L0_grid = [1, 5, 10, 20, 30, 35, 40, 45, 50]
    fir_corr: dict[int, float] = {}
    iir_corr: dict[int, float] = {}
    for L0 in L0_grid:
        tgt = np.zeros(T)
        tgt[L0:] = x[: T - L0]  # target = x(t-L0)
        # --- ARM A: identity node then linear readout over K taps. With a near-
        # identity activation the taps literally contain x(t-j) for j<K, so the
        # readout recovers lag L0 exactly iff L0<K. Use the actual trained node.
        acc, _W, _b, _coef = train_fir_node(X, tgt, K, epochs=120, lr=0.05, n_restart=2)
        fir_corr[L0] = acc
        # --- ARM B: feedback can carry information beyond K via the recurrent
        # state (echo), decaying with lag.
        acb, _Wb, _bb, _vb = train_iir_node(X, tgt, K, epochs=120, lr=0.02, n_restart=2)
        iir_corr[L0] = acb
    fir_str = " ".join(f"L{L}:{fir_corr[L]:.2f}" for L in L0_grid)
    iir_str = " ".join(f"L{L}:{iir_corr[L]:.2f}" for L in L0_grid)
    # cutoff = largest L0 with corr >= 0.5
    fir_cut = max([L for L in L0_grid if fir_corr[L] >= 0.5], default=0)
    iir_cut = max([L for L in L0_grid if iir_corr[L] >= 0.5], default=0)
    _rec("E2", f"ARM A FIR corr-vs-lag (K={K}): {fir_str}")
    _rec("E2", f"ARM B IIR corr-vs-lag (K={K}): {iir_str}")
    _rec(
        "E2",
        f"effective-horizon cutoff (corr>=0.5): FIR={fir_cut} (expect ~<=K={K}), "
        f"IIR={iir_cut}",
    )


# ===========================================================================
# E3  counting / parity ceiling (both arms)  -- OQ-4 star-free probe
# ===========================================================================
def exp_E3() -> None:
    T, K = 1500, K_DEFAULT
    bits = RNG.integers(0, 2, size=T).astype(np.float64)
    X = bits.reshape(T, 1) * 2.0 - 1.0  # +/-1 input
    results = []
    for m in [3, 8, 35, 60]:  # parity of last m bits (m within & beyond K)
        par = np.zeros(T)
        for t in range(T):
            lo = max(0, t - m + 1)
            par[t] = (bits[lo : t + 1].sum() % 2) * 2 - 1  # +/-1 parity
        acc, *_ = train_fir_node(X, par, K, epochs=150, lr=0.05, n_restart=3)
        acb, *_ = train_iir_node(X, par, K, epochs=150, lr=0.02, n_restart=2)
        results.append((f"parity(m={m})", acc, acb))
    # mod-3 running count of 1-bits (a counting task, not star-free)
    cnt = np.cumsum(bits) % 3
    cnt_c = cnt - cnt.mean()
    accm, *_ = train_fir_node(X, cnt_c, K, epochs=150, lr=0.05, n_restart=3)
    acbm, *_ = train_iir_node(X, cnt_c, K, epochs=150, lr=0.02, n_restart=2)
    results.append(("mod3-count(unbounded)", accm, acbm))
    for name, af, bi in results:
        _rec("E3", f"{name}: FIR|corr|={af:.2f}  IIR|corr|={bi:.2f}")
    pin = {r[0]: (r[1], r[2]) for r in results}
    fir3, iir3 = pin["parity(m=3)"]
    fir60, iir60 = pin["parity(m=60)"]
    _rec(
        "E3",
        f"ceiling summary (|corr|; ~0 == NOT learned): parity m=3 "
        f"FIR={fir3:.2f}/IIR={iir3:.2f}, parity m=60 FIR={fir60:.2f}/IIR={iir60:.2f}; "
        f"unbounded mod-3 count FIR={accm:.2f}/IIR={acbm:.2f}. A single node + linear "
        f"readout cannot REPRESENT parity at any m (parity is not linearly separable); a "
        f"single IIR neuron does not LEARN it here either. POC shows failure-to-learn, "
        f"consistent with (NOT a proof of) the star-free/no-count ceiling -- the "
        f"impossibility proof is the literature's (Giles 1995 / Kremer 1996).",
    )


# ===========================================================================
# E4  irregular-dt grid (in)variance (both arms)   -- mirrors Delta-t S8.6
# ===========================================================================
def exp_E4() -> None:
    """Irregular-dt grid-(in)variance, mirroring Delta-t doc S8.6. Target is a fixed
    REAL-TIME delay tau (NOT an index lag): tgt(t)=sin(w*(t_axis[t]-tau)). On a regular
    grid tau == a single integer tap; on an irregular grid no fixed index tap matches a
    fixed real-time delay -> the index-tap delay line degrades. +dt-feature is Approach A
    (the model must LEARN to use dt). Using a real-time-delay target isolates the
    index-vs-time mismatch that an index-lag target would hide (the tap would match it on
    any grid)."""
    K = K_DEFAULT
    n = 800
    omega = 2.0 * np.pi / 23.0  # period ~23 time-units
    span = float(n)
    t_reg = np.arange(n, dtype=np.float64)
    gaps = RNG.uniform(0.3, 1.7, size=n - 1)
    gaps *= span / gaps.sum()  # same total span; mean gap ~1
    t_irr = np.concatenate([[0.0], np.cumsum(gaps)])
    tau = 8.0  # fixed REAL-TIME delay; equals 8 taps ONLY on the regular grid

    def run(t_axis: np.ndarray, use_dt: bool) -> float:
        sig = np.sin(omega * t_axis)
        X = sig.reshape(-1, 1)
        if use_dt:
            dt = np.zeros(n)
            dt[1:] = np.diff(t_axis)
            X = np.concatenate([X, dt.reshape(-1, 1)], axis=1)
        tgt = np.sin(omega * (t_axis - tau))  # value at a fixed REAL-TIME delay tau
        warm = t_axis >= (t_axis[0] + tau)    # score only once the delay is in-window
        Xs = standardize(X)
        _ac, _W, _b, _c = train_fir_node(Xs, tgt, K, epochs=140, lr=0.05, n_restart=2)
        a = f_act(Xs @ _W + _b)
        taps = fir_taps_vectorized(a, K)
        coef, _ = fit_linear_readout(taps, tgt)
        Aug = np.concatenate([taps, np.ones((n, 1))], axis=1)
        pred = Aug @ coef
        return float(np.sqrt(np.mean((pred[warm] - tgt[warm]) ** 2)))

    rmse_reg = run(t_reg, use_dt=False)
    rmse_irr = run(t_irr, use_dt=False)
    rmse_irr_dt = run(t_irr, use_dt=True)
    ratio = rmse_irr / (rmse_reg + 1e-12)
    ratio_dt = rmse_irr_dt / (rmse_reg + 1e-12)
    _rec(
        "E4",
        f"FIR index-tap, fixed REAL-TIME delay tau={tau:g}: RMSE reg={rmse_reg:.3f} "
        f"irr={rmse_irr:.3f} (irr/reg={ratio:.2f}); +dt-feature irr={rmse_irr_dt:.3f} "
        f"(irr/reg={ratio_dt:.2f})",
    )
    _rec(
        "E4",
        f"interpretation: index-tap delays are grid-DEPENDENT (irr/reg={ratio:.2f}; "
        f">1 == degradation on the irregular grid); dt-as-feature is a partial, "
        f"must-learn mitigation (irr/reg={ratio_dt:.2f}). Contrast Delta-t doc S8.6 LMU: "
        f"e_irr ~= 1.15x e_reg (grid-invariant by construction).",
    )


# ===========================================================================
# E5  IIR BPTT-gradient correctness (ARM B)
# ===========================================================================
def exp_E5() -> None:
    T, F, K = 60, 3, 6  # small window so finite-diff is cheap & well-conditioned
    X = RNG.standard_normal((T, F))
    residual = RNG.standard_normal(T)
    W = RNG.standard_normal(F) * 0.5
    b = 0.2
    v = RNG.standard_normal(K) * 0.15

    L0, gv, gW, gb = corr_loss_and_bptt(X, residual, W, b, v)

    eps = 1e-6

    def L_only(W_, b_, v_) -> float:
        a, _ = iir_rollout(X, W_, b_, v_)
        return -abs(signed_pearson(a, residual))

    # central finite differences for every parameter
    max_rel = 0.0

    def rel(an: float, fd: float) -> float:
        return abs(an - fd) / (abs(fd) + 1e-9)

    for k in range(K):
        vp = v.copy(); vp[k] += eps
        vm = v.copy(); vm[k] -= eps
        fd = (L_only(W, b, vp) - L_only(W, b, vm)) / (2 * eps)
        max_rel = max(max_rel, rel(gv[k], fd))
    for j in range(F):
        Wp = W.copy(); Wp[j] += eps
        Wm = W.copy(); Wm[j] -= eps
        fd = (L_only(Wp, b, v) - L_only(Wm, b, v)) / (2 * eps)
        max_rel = max(max_rel, rel(gW[j], fd))
    fd_b = (L_only(W, b + eps, v) - L_only(W, b - eps, v)) / (2 * eps)
    max_rel = max(max_rel, rel(gb, fd_b))

    _rec(
        "E5",
        f"ARM B BPTT vs central-FD (K={K},T={T}): max rel err={max_rel:.2e} "
        f"PASS={max_rel < 1e-5} (threshold 1e-5)",
    )


# ===========================================================================
# E6  REAL equities
# ===========================================================================
def _window_one_ticker(feats, dates_yyyymmdd, y_reg, *, lookback):
    """Per-ticker windowing (NO cross-ticker). Emits X (W, L, F), the next-step
    regression target y_reg[i] (= close.shift(-1) at the window-end row i), and
    per-window dt (calendar-day gaps). Window-end i in [L-1, n-2] predicts i+1."""
    n, f = feats.shape
    ords = _yyyymmdd_to_ordinal(dates_yyyymmdd)
    assert np.all(np.diff(ords) > 0), "dates must be strictly increasing per ticker"
    Xs, ys, dts, endrows = [], [], [], []
    for i in range(lookback - 1, n - 1):
        lo = i - lookback + 1
        win = feats[lo : i + 1]  # (L, F)
        dt = np.empty(lookback, dtype=np.float32)
        dt[0] = 0.0
        dt[1:] = np.diff(ords[lo : i + 1]).astype(np.float32)
        Xs.append(win)
        ys.append(y_reg[i])  # next-step target at the window-end row
        dts.append(dt)
        endrows.append(i)
    X = np.asarray(Xs, dtype=np.float32)
    y = np.asarray(ys, dtype=np.float32).reshape(-1, 1)
    dt = np.asarray(dts, dtype=np.float32)
    return X, y, dt, np.asarray(endrows)


def exp_E6() -> None:
    """REAL equities, modeling P4 over the genuine per-ticker DAY axis: the node's
    activation a(t)=f(W.x(t)) is shift-registered across consecutive trading days
    (NO pre-windowing, NO cross-ticker taps). dt stats are pooled across the picked
    tickers; the delay-line candidate is trained on the longest single ticker's day
    sequence (capped to the most recent NMAX days to bound IIR BPTT runtime)."""
    try:
        z = np.load(EQUITIES_NPZ, allow_pickle=False)
    except Exception as exc:  # pragma: no cover - defensive
        _rec("E6", f"SKIP: could not load equities npz: {exc!r}")
        return
    vocab = list(z["ticker_vocab"])
    pick = ["AAPL", "MSFT", "KO", "BRK.B"]
    X_full = z["X_full"]
    yreg_full = z["y_reg_full"]
    date_full = z["date_full"]
    code_full = z["ticker_code_full"]

    seqs = {}  # name -> (X_days_std (n,F), yreg (n,))
    all_dt = []
    for nm in pick:
        try:
            code = vocab.index(np.str_(nm))
        except ValueError:
            _rec("E6", f"note: ticker {nm} not in vocab; skipping")
            continue
        mask = code_full == code
        order = np.argsort(date_full[mask])  # chronological within ticker
        Xt = X_full[mask][order].astype(np.float64)
        yr = yreg_full[mask][order].reshape(-1)
        ords = _yyyymmdd_to_ordinal(date_full[mask][order])
        all_dt.append(np.diff(ords))  # consecutive-trading-day calendar gaps
        seqs[nm] = (standardize(Xt), yr)
    if not seqs:
        _rec("E6", "SKIP: none of the picked tickers were in vocab")
        return
    _rec("E6", "tickers(rows): " + ", ".join(f"{nm}({seqs[nm][0].shape[0]})" for nm in seqs))

    dt_all = np.concatenate(all_dt)
    vals, counts = np.unique(dt_all.astype(int), return_counts=True)
    dist = {int(v): int(c) for v, c in zip(vals, counts)}
    total = dt_all.size
    _rec(
        "E6",
        "calendar-day-gap dt distribution (consecutive trading days): "
        + " ".join(f"{g}d:{100*c/total:.1f}%" for g, c in sorted(dist.items()) if c / total > 0.004),
    )
    _rec(
        "E6",
        f"dt mass: 1d={100*dist.get(1,0)/total:.1f}%  3d(Fri->Mon)={100*dist.get(3,0)/total:.1f}%  "
        f"4d(holiday)={100*dist.get(4,0)/total:.1f}%",
    )

    # P4 over the day axis on the LONGEST ticker (delay line = days; no cross-ticker taps)
    nm = max(seqs, key=lambda k: seqs[k][0].shape[0])
    Xstd, yr = seqs[nm]
    NMAX = 2000  # cap to most-recent NMAX days to bound IIR BPTT runtime (logged)
    capped = Xstd.shape[0] > NMAX
    if capped:
        Xstd, yr = Xstd[-NMAX:], yr[-NMAX:]
    K = K_DEFAULT
    # next-day close regression target; residual vs a 1-tap (last-close) baseline so the
    # delay-line candidate must explain what a memory-less node cannot (the cascor regime).
    close = Xstd[:, 3]  # standardized close (col 3 = close)
    ytgt = (yr - yr.mean()) / (yr.std() + 1e-8)
    A0 = np.stack([close, np.ones_like(close)], axis=1)
    c0, *_ = np.linalg.lstsq(A0, ytgt, rcond=None)
    residual = ytgt - A0 @ c0
    base_corr = pearson_abs(close, ytgt)
    accA, *_ = train_fir_node(Xstd, residual, K, epochs=200, lr=0.04, n_restart=3)
    accB, *_ = train_iir_node(Xstd, residual, K, epochs=150, lr=0.02, n_restart=2)
    _rec(
        "E6",
        f"[{nm}, n={Xstd.shape[0]} days{' (most-recent cap)' if capped else ''}] "
        f"baseline |corr(last_close,next_close)|={base_corr:.3f}; day-axis delay-line "
        f"candidate vs residual: ARM A FIR |corr|={accA:.3f}, ARM B IIR |corr|={accB:.3f}",
    )
    # realized horizon over the TRUE day axis: tap[:,lag] vs residual at increasing lags
    Wv = RNG.standard_normal(Xstd.shape[1]) * (1.0 / np.sqrt(Xstd.shape[1]))
    a_seq = f_act(Xstd @ Wv)
    taps = fir_taps_vectorized(a_seq, K)
    lag_corrs = [(lag, pearson_abs(taps[:, lag], residual)) for lag in [1, 5, 10, 20, 34]]
    _rec(
        "E6",
        "realized day-axis tap |corr| vs residual at lags: "
        + " ".join(f"L{lag}:{c:.3f}" for lag, c in lag_corrs),
    )


# ===========================================================================
# Driver
# ===========================================================================
def main() -> int:
    t0 = time.time()
    print(f"P4 delay-line node PoC  (seed={SEED}, K={K_DEFAULT}, "
          f"numpy {np.__version__}, py {sys.version.split()[0]})", flush=True)
    print("=" * 78, flush=True)
    exp_E1()
    exp_E2()
    exp_E3()
    exp_E4()
    exp_E5()
    exp_E6()
    print("=" * 78, flush=True)
    print("RESULTS TABLE", flush=True)
    print("-" * 78, flush=True)
    for label, msg in _RESULTS:
        print(f"  {label:4s} | {msg}", flush=True)
    print("-" * 78, flush=True)
    print(f"total runtime: {time.time() - t0:.1f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
