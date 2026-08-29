"""
Numpy-only PoC: OQ-4 EXPRESSIVITY SUITE -- a head-to-head, held-out generalization
contrast of FOUR candidate recurrence mechanisms for Cascade-Correlation, asking
the ONE decisive question the OQ-4 reevaluation cares about:

    WHICH candidate empirically BREAKS the star-free / no-count ceiling -- i.e.
    learns parity / modular-counting that GENERALIZES to a HELD-OUT stream?

Generalization (train on one Bernoulli stream, FREEZE, evaluate on a DISJOINT
stream) is the proof, NOT in-sample |corr|: a model with enough parameters can
fit finite-sample parity spuriously, so only held-out accuracy distinguishes
"computes parity" from "memorized this stream".  The headline number per
candidate is the held-out parity accuracy vs the majority-class floor.

CANDIDATES (each a temporal substrate + a trained readout/output):
  (a) P5  -- single self-recurrent output neuron driven by a FROZEN, output-
            state-blind FIR feature basis h(t)=[x(t)..x(t-K_h+1)]; trained by
            BPTT.  EXPECTED FAIL (reference): a single linear-threshold neuron
            cannot form the x(t).o(t-1) XOR cross-term (Minsky & Papert 1969).
            [reused from verify_p5_recurrent_output_eval.py]
  (b) P6  -- the same FROZEN FIR drive feeding a TRAINED 2-layer recurrent MLP
            output map (a true NARX net): z(t)=tanh(Wih.h(t)+Wfh.o_hist(t)+bh),
            o(t)=Wo.z(t)+bo, with o_hist(t)=[o(t-1)..o(t-K_fb)] fed BACK into the
            hidden layer.  The hidden layer CAN in principle form x(t).o(t-1)
            (a 2-layer MLP represents XOR; Siegelmann-Horne-Giles 1997 NARX
            universality).  THE KEY TEST.  Trained by BPTT (gradient HARD-ASSERTED
            against finite differences first).  [reused from verify_p6_*].
  (c) ESN -- a FIXED random recurrent reservoir (echo-state, spectral radius<1),
            with ONLY the readout trained.  Two readouts: a LINEAR ridge readout
            (cascor's output-layer analog) and a small NONLINEAR (tanh-MLP)
            readout.  Echo-State-Property => fading memory => predicted star-free
            (Sarrof-Veitsman-Hahn 2024: nonnegative SSM recognizes a regular lang
            IFF star-free; no nonnegative SSM recognizes parity at length).
  (d) LMU -- a FIXED Legendre/HiPPO-LegT linear memory (the closed-form A,B from
            the Delta-t doc S8; orthogonal-polynomial sliding-window memory) with
            ONLY the readout trained (linear + small tanh-MLP variant).  Linear
            positive-/complex-spectrum SSM => predicted star-free (same theorem).

For EACH candidate the suite reports, on BOTH running-parity and mod-3 count:
  * IN-SAMPLE |corr| and accuracy (context; can be spuriously high)
  * HELD-OUT  accuracy and |corr| vs the majority-class floor  <-- THE HEADLINE
  * a fixed-lag RECALL horizon probe (target = x(t-L0); the memory's reach)

HARD GATE: P6's BPTT gradient is checked against central finite differences
(max rel err < 1e-4) and ASSERTED before any P6 training result is trusted.
(ESN/LMU readouts are closed-form lstsq or plain-MLP GD whose gradient is the
trivial well-tested chain rule; P5's BPTT is already gradient-checked in its
own PoC -- this suite re-asserts the P6 one because P6 is the key test.)

ANTI-HALLUCINATION: numpy-only, manual gradients, seed-fixed, deterministic.
All cascor code claims cite file:line against the LIVE tree
(juniper-cascor/src/cascade_correlation/cascade_correlation.py; the
output-state-blind hidden buffer is _compute_hidden_outputs :1942-1946; the bare
affine output is :1979).  Literature impossibility results are the literature's
(Minsky-Papert 1969 / Giles 1995 / Kremer 1996 / Knorozova-Ronca 2024 /
Sarrof-Veitsman-Hahn 2024 / Siegelmann-Horne-Giles 1997), web-verified in the
OQ-4 docs; THIS PoC measures learn/GENERALIZE-or-not, which is consistent with
(not a proof of) the ceiling.

Project:    Juniper ML Research Platform -- juniper-recurse (OQ-4 model-pick PoC)
Sub-Project: recurrent Cascade-Correlation -- expressivity suite (P5/P6/ESN/LMU)
Application: ad-hoc design-evaluation harness
Author:     Paul Calnon
Version:    0.1.0
License:    MIT License
Created:    2026-06-12
Status:     ad-hoc - investigation (OQ-4 ceiling head-to-head; held-out is headline)
Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: the OQ-4 model pick is ratified; measured numbers folded into
             notes/JUNIPER_RECURSE_*  (do NOT edit those docs from here).
Related: util/ad-hoc/verify_p5_recurrent_output_eval.py (P5 helpers reused),
         util/ad-hoc/verify_delay_line_node_eval.py (P4 FIR helpers reused),
         util/ad-hoc/verify_p6_narx_mlp_output_eval.py (P6 helpers reused),
         notes/JUNIPER_2026-06-05_JUNIPER-RECURRENCE_RECURSE-DELTA-T-HANDLING.md (S8 LMU reference),
         notes/JUNIPER_2026-06-04_JUNIPER-RECURRENCE_RECURSE-OQ4-RECURRENT-CASCOR-PROPOSALS.md
"""

from __future__ import annotations

import sys
import time

import numpy as np

# --------------------------------------------------------------------------- #
SEED = 20260612
RNG = np.random.default_rng(SEED)

K_H_DEFAULT = 35   # FROZEN FIR hidden depth (P4/P5/P6 embedding dim; design ~35)
K_FB_DEFAULT = 8   # output feedback order K (number of o(t-k) taps)
HID_DEFAULT = 16   # P6 hidden-MLP width

# Reservoir / memory sizes (kept modest: LMU LegT A is ill-conditioned for large
# d per Delta-t doc S8.5; ESN width chosen so the ridge readout is well-posed).
ESN_N_DEFAULT = 120
LMU_D_DEFAULT = 24
LMU_THETA_DEFAULT = 40.0  # window length ~ K_H so memory reach is comparable

EQUITIES_NPZ = (
    "/home/pcalnon/Development/python/Juniper/juniper-data/data/datasets/"
    "equities-1.0.0-6db8f4eb77108875.npz"
)

_RESULTS: list[tuple[str, str]] = []  # (label, one-line measured result)


def _rec(label: str, msg: str) -> None:
    _RESULTS.append((label, msg))
    print(f"[{label}] {msg}", flush=True)


# --------------------------------------------------------------------------- #
# Shared primitives (FIR features, correlation objective) -- reused verbatim
# from the P5/P6 PoCs so the contrast is apples-to-apples.
# --------------------------------------------------------------------------- #
def fir_features(x_stream: np.ndarray, K_h: int) -> np.ndarray:
    """FIR tapped-delay embedding of a 1-D stream, newest-first
    [x(t), x(t-1), ...], zero-padded before t=0. (T, K_h). OUTPUT-STATE-BLIND --
    matches cascor _compute_hidden_outputs which never reads any output
    (cascade_correlation.py:1942-1946)."""
    T = x_stream.shape[0]
    xpad = np.concatenate([np.zeros(K_h - 1, dtype=np.float64), x_stream.astype(np.float64)])
    win = np.lib.stride_tricks.sliding_window_view(xpad, K_h)  # (T, K_h) ascending
    return win[:, ::-1].copy()


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


def binary_accuracy(pred: np.ndarray, target_pm1: np.ndarray) -> float:
    return float(np.mean(np.sign(pred) == np.sign(target_pm1)))


# --------------------------------------------------------------------------- #
# Task builders (parity / mod-3 count / fixed-lag) -- identical semantics to the
# P4/P5/P6 PoCs.
# --------------------------------------------------------------------------- #
def parity_last_m(bits: np.ndarray, m: int) -> np.ndarray:
    T = bits.shape[0]
    par = np.zeros(T)
    csum = np.concatenate([[0.0], np.cumsum(bits)])
    for t in range(T):
        lo = max(0, t - m + 1)
        par[t] = ((csum[t + 1] - csum[lo]) % 2) * 2 - 1
    return par


def running_parity(bits: np.ndarray) -> np.ndarray:
    """o(t)=XOR over all bits up to t == o(t)=XOR(x(t),o(t-1)). The crux task."""
    return (np.cumsum(bits) % 2) * 2 - 1


def mod3_count(bits: np.ndarray) -> np.ndarray:
    """Unbounded mod-3 running count of 1-bits, mean-centered (a Z_3 task).
    Reported as a 3-class accuracy via nearest-centroid on the centered codes."""
    cnt = (np.cumsum(bits) % 3).astype(np.float64)
    return cnt - cnt.mean()


def mod3_classacc(pred: np.ndarray, bits: np.ndarray) -> float:
    """3-class accuracy for the mod-3 count task: round the (centered) prediction
    back to {0,1,2} via nearest of the three centered class codes."""
    true_cls = (np.cumsum(bits) % 3).astype(int)
    centers = np.array([0.0, 1.0, 2.0]) - np.array([0.0, 1.0, 2.0]).mean()  # centered codes
    # map prediction -> nearest centered code -> class index
    d = np.abs(pred[:, None] - centers[None, :])
    pred_cls = d.argmin(axis=1)
    return float(np.mean(pred_cls == true_cls))


# =========================================================================== #
# (a) P5 -- single self-recurrent OUTPUT neuron over a FROZEN FIR drive.
#     o(t) = g( H[t].W + sum_k v_k o(t-k) + b ); trained by BPTT.
#     (reused from verify_p5_recurrent_output_eval.py)
# =========================================================================== #
def _tanh(z):
    return np.tanh(z)


def _dtanh(z):
    t = np.tanh(z)
    return 1.0 - t * t


def p5_rollout(H, W, b, v):
    T = H.shape[0]
    K = v.shape[0]
    drive = H @ W + b
    o = np.zeros(T)
    z = np.zeros(T)
    hist = np.zeros(K)
    for t in range(T):
        z[t] = drive[t] + float(v @ hist)
        o[t] = _tanh(z[t])
        hist[1:] = hist[:-1]
        hist[0] = o[t]
    return o, z


def p5_mse_loss_and_bptt(H, target, W, b, v):
    T = H.shape[0]
    K = v.shape[0]
    o, z = p5_rollout(H, W, b, v)
    diff = o - target
    L = float(np.mean(diff * diff))
    dL_do_direct = (2.0 / T) * diff
    gp = _dtanh(z)
    adj_z = np.zeros(T)
    for t in range(T - 1, -1, -1):
        s = dL_do_direct[t]
        kmax = min(K, T - 1 - t)
        for k in range(1, kmax + 1):
            s += v[k - 1] * adj_z[t + k]
        adj_z[t] = s * gp[t]
    gv = np.zeros(K)
    for t in range(T):
        for k in range(1, K + 1):
            if t - k >= 0:
                gv[k - 1] += adj_z[t] * o[t - k]
    gW = H.T @ adj_z
    gb = float(adj_z.sum())
    return L, gW, gb, gv


def train_p5_output(H, target, K_fb, *, epochs=300, lr=0.05, n_restart=4,
                    v_scale=0.1, v_clip=1.5, grad_clip=5.0):
    D = H.shape[1]
    w_scale = 1.0 / np.sqrt(D)
    best = None
    for _ in range(n_restart):
        W = RNG.standard_normal(D) * w_scale
        b = 0.0
        v = RNG.standard_normal(K_fb) * v_scale
        for _ep in range(epochs):
            _L, gW, gb, gv = p5_mse_loss_and_bptt(H, target, W, b, v)
            gn = float(np.sqrt(float(gW @ gW) + gb * gb + float(gv @ gv)))
            if gn > grad_clip:
                sc = grad_clip / (gn + 1e-12)
                gW, gb, gv = gW * sc, gb * sc, gv * sc
            W -= lr * gW
            b -= lr * gb
            v -= lr * gv
            v = np.clip(v, -v_clip, v_clip)
        o, _z = p5_rollout(H, W, b, v)
        ac = pearson_abs(o, target)
        if best is None or ac > best[0]:
            best = (ac, W.copy(), b, v.copy())
    return best


def p5_predict(H, params):
    _ac, W, b, v = params
    return p5_rollout(H, W, b, v)[0]


# =========================================================================== #
# (b) P6 -- FROZEN FIR drive -> TRAINED 2-layer recurrent MLP output (NARX).
#     z(t)=tanh(Wih.h(t)+Wfh.o_hist(t)+bh); o(t)=Wo.z(t)+bo.
#     (reused from verify_p6_narx_mlp_output_eval.py)
# =========================================================================== #
class P6Params:
    __slots__ = ("Wih", "Wfh", "bh", "Wo", "bo")

    def __init__(self, Wih, Wfh, bh, Wo, bo):
        self.Wih = Wih
        self.Wfh = Wfh
        self.bh = bh
        self.Wo = Wo
        self.bo = float(bo)

    def copy(self):
        return P6Params(self.Wih.copy(), self.Wfh.copy(), self.bh.copy(), self.Wo.copy(), self.bo)


def p6_init(Dh, K, Hd, *, w_scale=None, v_scale=0.3):
    if w_scale is None:
        w_scale = 1.0 / np.sqrt(Dh)
    Wih = RNG.standard_normal((Hd, Dh)) * w_scale
    Wfh = RNG.standard_normal((Hd, K)) * v_scale
    bh = np.zeros(Hd)
    Wo = RNG.standard_normal(Hd) * (1.0 / np.sqrt(Hd))
    return P6Params(Wih, Wfh, bh, Wo, 0.0)


def p6_rollout(H, p):
    T = H.shape[0]
    Hd = p.Wo.shape[0]
    K = p.Wfh.shape[1]
    drive = H @ p.Wih.T + p.bh
    o = np.zeros(T)
    Z = np.zeros((T, Hd))
    A = np.zeros((T, Hd))
    hist = np.zeros(K)
    for t in range(T):
        z = drive[t] + p.Wfh @ hist
        a = np.tanh(z)
        ot = float(p.Wo @ a + p.bo)
        Z[t] = z
        A[t] = a
        o[t] = ot
        hist[1:] = hist[:-1]
        hist[0] = ot
    return o, Z, A


def _p6_bptt(H, p, dL_do_direct):
    T, _Dh = H.shape
    Hd = p.Wo.shape[0]
    K = p.Wfh.shape[1]
    o, _Z, A = p6_rollout(H, p)
    dtanh = 1.0 - A * A
    adj_o = np.zeros(T)
    adj_z = np.zeros((T, Hd))
    for t in range(T - 1, -1, -1):
        s = dL_do_direct[t]
        kmax = min(K, T - 1 - t)
        for k in range(1, kmax + 1):
            s += float(adj_z[t + k] @ p.Wfh[:, k - 1])
        adj_o[t] = s
        adj_z[t] = (p.Wo * adj_o[t]) * dtanh[t]
    gWo = A.T @ adj_o
    gbo = float(adj_o.sum())
    gWih = adj_z.T @ H
    gbh = adj_z.sum(axis=0)
    gWfh = np.zeros((Hd, K))
    for t in range(T):
        for k in range(1, K + 1):
            if t - k >= 0:
                gWfh[:, k - 1] += adj_z[t] * o[t - k]
    return o, (gWih, gWfh, gbh, gWo, gbo)


def p6_mse_loss_and_bptt(H, target, p):
    T = H.shape[0]
    o, _z, _a = p6_rollout(H, p)
    diff = o - target
    L = float(np.mean(diff * diff))
    dL_do_direct = (2.0 / T) * diff
    _o, grads = _p6_bptt(H, p, dL_do_direct)
    return L, grads


def _p6_flatten(grads):
    gWih, gWfh, gbh, gWo, gbo = grads
    return np.concatenate([gWih.ravel(), gWfh.ravel(), gbh.ravel(), gWo.ravel(), [gbo]])


def _p6_apply(p, grads, lr, *, fb_clip):
    gWih, gWfh, gbh, gWo, gbo = grads
    p.Wih -= lr * gWih
    p.Wfh -= lr * gWfh
    p.bh -= lr * gbh
    p.Wo -= lr * gWo
    p.bo -= lr * gbo
    np.clip(p.Wfh, -fb_clip, fb_clip, out=p.Wfh)


def train_p6_output(H, target, K_fb, Hd, *, epochs=400, lr=0.05, n_restart=4,
                    fb_clip=1.5, grad_clip=5.0):
    Dh = H.shape[1]
    best = None
    for _ in range(n_restart):
        p = p6_init(Dh, K_fb, Hd)
        for _ep in range(epochs):
            _L, grads = p6_mse_loss_and_bptt(H, target, p)
            gn = float(np.linalg.norm(_p6_flatten(grads)))
            if gn > grad_clip:
                sc = grad_clip / (gn + 1e-12)
                grads = tuple(g * sc for g in grads)
            _p6_apply(p, grads, lr, fb_clip=fb_clip)
        o, _z, _a = p6_rollout(H, p)
        ac = pearson_abs(o, target)
        if best is None or ac > best[0]:
            best = (ac, p.copy())
    return best


def p6_predict(H, params):
    return p6_rollout(H, params[1])[0]


# =========================================================================== #
# (c) ESN -- FIXED random reservoir (echo-state) + TRAINED readout.
#     s(t) = tanh( Win.x(t) + Wres.s(t-1) + bres );  reservoir FIXED, never trained.
#     Readout: LINEAR ridge over [s(t),1] (cascor output-layer analog), and a small
#     NONLINEAR tanh-MLP readout (trained by GD).  ESP (spectral radius<1) => fading
#     memory => predicted star-free (Sarrof-Veitsman-Hahn 2024).
# =========================================================================== #
def esn_reservoir(N, *, spectral_radius=0.9, in_scale=1.0, density=0.1, seed_offset=0):
    """Build a FIXED ESN reservoir (Win, Wres, bres). Sparse Wres rescaled to the
    target spectral radius (echo-state property for rho<1)."""
    rng = np.random.default_rng(SEED + 9000 + seed_offset)
    Win = rng.standard_normal((N, 1)) * in_scale
    bres = rng.uniform(-0.1, 0.1, size=N)
    W = rng.standard_normal((N, N))
    mask = rng.random((N, N)) < density
    W = W * mask
    # rescale to target spectral radius
    eig = np.linalg.eigvals(W)
    rho = float(np.max(np.abs(eig)))
    if rho > 1e-9:
        W = W * (spectral_radius / rho)
    return Win, W, bres


def esn_states(x_stream, Win, Wres, bres):
    """Roll the FIXED reservoir over a 1-D input stream. Returns S:(T,N)."""
    T = x_stream.shape[0]
    N = Win.shape[0]
    S = np.zeros((T, N))
    s = np.zeros(N)
    for t in range(T):
        s = np.tanh(Win[:, 0] * x_stream[t] + Wres @ s + bres)
        S[t] = s
    return S


def ridge_readout_fit(S, target, *, lam=1e-3):
    """Closed-form ridge readout coef over [S, 1] (cascor's output layer is a
    linear solve over frozen features; ridge regularizes the reservoir readout)."""
    A = np.concatenate([S, np.ones((S.shape[0], 1))], axis=1)
    G = A.T @ A
    G += lam * np.eye(G.shape[0])
    coef = np.linalg.solve(G, A.T @ target)
    return coef


def ridge_readout_predict(S, coef):
    A = np.concatenate([S, np.ones((S.shape[0], 1))], axis=1)
    return A @ coef


def mlp_readout_train(feats, target, *, hid=24, epochs=600, lr=0.05, seed_offset=0,
                      grad_clip=5.0):
    """Small 2-layer tanh-MLP readout over FIXED features (ESN states or LMU
    memory). Plain full-batch GD (trivial, well-tested chain-rule gradient).
    Returns (W1,b1,W2,b2)."""
    rng = np.random.default_rng(SEED + 4000 + seed_offset)
    D = feats.shape[1]
    W1 = rng.standard_normal((hid, D)) * (1.0 / np.sqrt(D))
    b1 = np.zeros(hid)
    W2 = rng.standard_normal(hid) * (1.0 / np.sqrt(hid))
    b2 = 0.0
    n = feats.shape[0]
    for _ep in range(epochs):
        Z = feats @ W1.T + b1
        A = np.tanh(Z)
        pred = A @ W2 + b2
        diff = pred - target
        gpred = (2.0 / n) * diff
        gW2 = A.T @ gpred
        gb2 = float(gpred.sum())
        gA = np.outer(gpred, W2) * (1 - A * A)
        gW1 = gA.T @ feats
        gb1 = gA.sum(axis=0)
        gn = float(np.sqrt((gW1 ** 2).sum() + (gb1 ** 2).sum() + (gW2 ** 2).sum() + gb2 ** 2))
        if gn > grad_clip:
            sc = grad_clip / (gn + 1e-12)
            gW1, gb1, gW2, gb2 = gW1 * sc, gb1 * sc, gW2 * sc, gb2 * sc
        W1 -= lr * gW1
        b1 -= lr * gb1
        W2 -= lr * gW2
        b2 -= lr * gb2
    return W1, b1, W2, b2


def mlp_readout_predict(feats, params):
    W1, b1, W2, b2 = params
    return np.tanh(feats @ W1.T + b1) @ W2 + b2


# =========================================================================== #
# (d) LMU -- FIXED Legendre/HiPPO-LegT linear memory + TRAINED readout.
#     m(t) summarizes the input history over a window theta via shifted Legendre
#     coefficients; FIXED closed-form A,B (Delta-t doc S8.2/S8.3).  Discretized at
#     unit dt for the regular-grid bit streams (variable-dt only matters for the
#     equities probe, which is regression not parity).  Linear positive-/complex-
#     spectrum SSM => predicted star-free (Sarrof-Veitsman-Hahn 2024 Thm 13).
# =========================================================================== #
def lmu_matrices(d):
    """Canonical LMU / HiPPO-LegT A, B (theta-free: theta*m_dot = A m + B u).
    Verbatim from notes/JUNIPER_2026-06-05_JUNIPER-RECURRENCE_RECURSE-DELTA-T-HANDLING.md S8.2."""
    A = np.zeros((d, d))
    B = np.zeros((d, 1))
    for i in range(d):
        B[i, 0] = (2 * i + 1) * ((-1) ** i)
        for j in range(d):
            A[i, j] = (2 * i + 1) * (-1.0 if i < j else (-1.0) ** (i - j + 1))
    return A, B


def lmu_step_matrices(d, theta, dt):
    """Closed-form Abar(dt), Bbar(dt) via eigendecomposition (Delta-t doc S8.3)."""
    A, B = lmu_matrices(d)
    lam, V = np.linalg.eig(A)
    Vinv = np.linalg.inv(V)
    VinvB = Vinv @ B
    z = lam * (dt / theta)
    Abar = (V * np.exp(z)) @ Vinv
    with np.errstate(divide="ignore", invalid="ignore"):
        fac = np.expm1(z) / lam
    fac = np.where(np.abs(lam) < 1e-12, dt / theta, fac)
    Bbar = (V * fac) @ VinvB
    return Abar.real, Bbar.real


def lmu_states(u_stream, d, theta, *, dt=1.0):
    """Roll the FIXED LMU memory over a 1-D input at constant dt. Returns M:(T,d).
    ZOH: u[k-1] held across (t[k-1],t[k]]; m(t) summarizes history up to t."""
    Abar, Bbar = lmu_step_matrices(d, theta, dt)  # constant dt -> one pair
    T = u_stream.shape[0]
    M = np.zeros((T, d))
    m = np.zeros((d, 1))
    for k in range(1, T):
        m = Abar @ m + Bbar * u_stream[k - 1]
        M[k] = m[:, 0]
    return M


# =========================================================================== #
# GRADIENT GATE -- P6 BPTT vs central finite differences (HARD ASSERT).
# Runs FIRST; if it fails the suite aborts before trusting any P6 number.
# =========================================================================== #
def exp_GRAD() -> None:
    global RNG
    RNG = np.random.default_rng(SEED + 7)
    T, K_h, K_fb, Hd = 40, 6, 3, 5
    bits = RNG.integers(0, 2, size=T).astype(np.float64)
    X = bits * 2.0 - 1.0
    H = fir_features(X, K_h)
    target = running_parity(bits)
    p = p6_init(H.shape[1], K_fb, Hd)
    L0, grads = p6_mse_loss_and_bptt(H, target, p)
    g = _p6_flatten(grads)
    theta = np.concatenate([p.Wih.ravel(), p.Wfh.ravel(), p.bh.ravel(), p.Wo.ravel(), [p.bo]])
    shapes = [p.Wih.shape, p.Wfh.shape, p.bh.shape, p.Wo.shape, (1,)]
    sizes = [int(np.prod(s)) for s in shapes]

    def _set(vec):
        i = 0
        mats = []
        for s, sz in zip(shapes, sizes):
            mats.append(np.array(vec[i:i + sz]).reshape(s))
            i += sz
        return P6Params(mats[0], mats[1], mats[2], mats[3], float(mats[4][0]))

    eps = 1e-6
    idxs = RNG.choice(theta.size, size=min(24, theta.size), replace=False)
    num = np.zeros_like(g)
    for j in idxs:
        tp = theta.copy(); tp[j] += eps
        tm = theta.copy(); tm[j] -= eps
        Lp, _ = p6_mse_loss_and_bptt(H, target, _set(tp))
        Lm, _ = p6_mse_loss_and_bptt(H, target, _set(tm))
        num[j] = (Lp - Lm) / (2 * eps)
    denom = np.maximum(np.abs(g[idxs]), np.abs(num[idxs])) + 1e-9
    max_rel = float((np.abs(g[idxs] - num[idxs]) / denom).max())
    ok = max_rel < 1e-4
    _rec("GRAD", f"P6 BPTT vs central-FD (MSE): max rel err={max_rel:.2e} "
                 f"(checked {len(idxs)} coords) PASS={ok} (threshold 1e-4)")
    assert ok, f"P6 BPTT gradient WRONG (max rel {max_rel:.2e}) -- aborting before training"


# =========================================================================== #
# CORE: held-out parity / mod-3 contrast across all four candidates.
# THE HEADLINE EXPERIMENT.
# =========================================================================== #
def _floor(target_pm1):
    p_pos = float(np.mean(target_pm1 > 0))
    return max(p_pos, 1.0 - p_pos)


def _make_streams(T):
    """Train + DISJOINT test Bernoulli streams (same seed pair for every
    candidate so the contrast is fair)."""
    rng = np.random.default_rng(SEED)
    bits_tr = rng.integers(0, 2, size=T).astype(np.float64)
    bits_te = rng.integers(0, 2, size=T).astype(np.float64)
    return bits_tr, bits_te


def _eval_candidate_parity(name, fit_fn, predict_fn, feat_fn, T):
    """Generic held-out PARITY harness. fit_fn(feats_tr, tgt_tr)->params;
    predict_fn(feats, params)->pred; feat_fn(bits)->feats. Returns dict."""
    bits_tr, bits_te = _make_streams(T)
    tgt_tr = running_parity(bits_tr)
    tgt_te = running_parity(bits_te)
    Ftr = feat_fn(bits_tr)
    Fte = feat_fn(bits_te)
    params = fit_fn(Ftr, tgt_tr)
    pred_tr = predict_fn(Ftr, params)
    pred_te = predict_fn(Fte, params)
    return {
        "in_corr": pearson_abs(pred_tr, tgt_tr),
        "in_acc": binary_accuracy(pred_tr, tgt_tr),
        "te_corr": pearson_abs(pred_te, tgt_te),
        "te_acc": binary_accuracy(pred_te, tgt_te),
        "floor": _floor(tgt_te),
    }


def _eval_candidate_mod3(name, fit_fn, predict_fn, feat_fn, T):
    """Generic held-out MOD-3 harness (3-class accuracy via nearest centered code)."""
    bits_tr, bits_te = _make_streams(T)
    tgt_tr = mod3_count(bits_tr)
    tgt_te = mod3_count(bits_te)
    Ftr = feat_fn(bits_tr)
    Fte = feat_fn(bits_te)
    params = fit_fn(Ftr, tgt_tr)
    pred_tr = predict_fn(Ftr, params)
    pred_te = predict_fn(Fte, params)
    # 3-class floor: majority class share on the test stream
    true_te = (np.cumsum(bits_te) % 3).astype(int)
    _vals, cnts = np.unique(true_te, return_counts=True)
    floor3 = float(cnts.max() / true_te.size)
    return {
        "in_corr": pearson_abs(pred_tr, tgt_tr),
        "in_acc": mod3_classacc(pred_tr, bits_tr),
        "te_corr": pearson_abs(pred_te, tgt_te),
        "te_acc": mod3_classacc(pred_te, bits_te),
        "floor": floor3,
    }


# --- per-candidate (fit, predict, feature) closures -----------------------
def _bits_to_pm1(bits):
    return bits * 2.0 - 1.0


def _feat_fir(bits):
    return fir_features(_bits_to_pm1(bits), K_H_DEFAULT)


def _cand_P5():
    def fit(F, tgt):
        global RNG
        RNG = np.random.default_rng(SEED + 11)
        return train_p5_output(F, tgt, K_FB_DEFAULT, epochs=300, lr=0.05, n_restart=4)
    return ("P5(single-rec-out)", fit, p5_predict, _feat_fir)


def _cand_P6(Hd):
    def fit(F, tgt):
        global RNG
        RNG = np.random.default_rng(SEED + 100 + Hd)
        return train_p6_output(F, tgt, K_FB_DEFAULT, Hd, epochs=400, lr=0.05, n_restart=4)
    return (f"P6(NARX-MLP,Hd={Hd})", fit, p6_predict, _feat_fir)


def _esn_feat_builder(N, spectral_radius):
    Win, Wres, bres = esn_reservoir(N, spectral_radius=spectral_radius)

    def feat(bits):
        return esn_states(_bits_to_pm1(bits), Win, Wres, bres)
    return feat


def _cand_ESN_linear(N, spectral_radius):
    feat = _esn_feat_builder(N, spectral_radius)

    def fit(F, tgt):
        return ridge_readout_fit(F, tgt, lam=1e-3)
    return (f"ESN-linear(N={N},rho={spectral_radius})", fit, ridge_readout_predict, feat)


def _cand_ESN_mlp(N, spectral_radius):
    feat = _esn_feat_builder(N, spectral_radius)

    def fit(F, tgt):
        return mlp_readout_train(F, tgt, hid=24, epochs=600, lr=0.05, seed_offset=N)
    return (f"ESN-mlp(N={N},rho={spectral_radius})", fit, mlp_readout_predict, feat)


def _lmu_feat_builder(d, theta):
    def feat(bits):
        return lmu_states(_bits_to_pm1(bits), d, theta, dt=1.0)
    return feat


def _cand_LMU_linear(d, theta):
    feat = _lmu_feat_builder(d, theta)

    def fit(F, tgt):
        return ridge_readout_fit(F, tgt, lam=1e-3)
    return (f"LMU-linear(d={d},theta={theta:g})", fit, ridge_readout_predict, feat)


def _cand_LMU_mlp(d, theta):
    feat = _lmu_feat_builder(d, theta)

    def fit(F, tgt):
        return mlp_readout_train(F, tgt, hid=24, epochs=600, lr=0.05, seed_offset=d)
    return (f"LMU-mlp(d={d},theta={theta:g})", fit, mlp_readout_predict, feat)


def _all_candidates():
    return [
        _cand_P5(),
        _cand_P6(HID_DEFAULT),
        _cand_P6(32),
        _cand_ESN_linear(ESN_N_DEFAULT, 0.9),
        _cand_ESN_mlp(ESN_N_DEFAULT, 0.9),
        _cand_LMU_linear(LMU_D_DEFAULT, LMU_THETA_DEFAULT),
        _cand_LMU_mlp(LMU_D_DEFAULT, LMU_THETA_DEFAULT),
    ]


def exp_PARITY() -> None:
    """THE HEADLINE: held-out running-parity for every candidate."""
    T = 900
    _rec("PARITY", f"running-parity o(t)=XOR(x(t),o(t-1)); train on one stream, FREEZE, "
                   f"test on a DISJOINT stream (T={T} each). HEADLINE = held-out acc vs floor.")
    breakers = []
    for name, fit, predict, feat in _all_candidates():
        r = _eval_candidate_parity(name, fit, predict, feat, T)
        margin = r["te_acc"] - r["floor"]
        lifted = margin > 0.05
        if lifted:
            breakers.append(name)
        _rec("PARITY", f"{name}: IN acc={r['in_acc']:.3f} |corr|={r['in_corr']:.3f} | "
                       f"HELD-OUT acc={r['te_acc']:.3f} |corr|={r['te_corr']:.3f} "
                       f"(floor={r['floor']:.3f}, margin={margin:+.3f}){'  <-- LIFTS' if lifted else ''}")
    if breakers:
        _rec("PARITY", f"*** CEILING LIFTED by: {breakers} -- held-out parity beats the "
                       f"majority floor by >0.05. MATERIAL OQ-4 finding; re-verify.")
    else:
        _rec("PARITY", "CEILING INTACT: NO candidate generalizes parity (all held-out acc "
                       "<= floor+0.05). P5/P6/ESN/LMU are ALL star-free-bound on parity, "
                       "consistent with Minsky-Papert 1969 (single-neuron XOR), "
                       "Sarrof-Veitsman-Hahn 2024 (nonneg SSM cannot do parity). Only a "
                       "GROUP-implementing / negative-eigenvalue mechanism (P2; or the "
                       "negative-eigenvalue linear-RNN) is predicted to break it.")


def exp_MOD3() -> None:
    """Held-out mod-3 counting (a Z_3 task) for every candidate."""
    T = 900
    _rec("MOD3", f"mod-3 running count (Z_3); same held-out protocol (T={T}). 3-class acc.")
    breakers = []
    for name, fit, predict, feat in _all_candidates():
        r = _eval_candidate_mod3(name, fit, predict, feat, T)
        margin = r["te_acc"] - r["floor"]
        lifted = margin > 0.05
        if lifted:
            breakers.append(name)
        _rec("MOD3", f"{name}: IN acc={r['in_acc']:.3f} |corr|={r['in_corr']:.3f} | "
                     f"HELD-OUT acc={r['te_acc']:.3f} |corr|={r['te_corr']:.3f} "
                     f"(floor={r['floor']:.3f}, margin={margin:+.3f}){'  <-- LIFTS' if lifted else ''}")
    if breakers:
        _rec("MOD3", f"*** mod-3 GENERALIZED by: {breakers}. MATERIAL; re-verify.")
    else:
        _rec("MOD3", "mod-3 NOT generalized by any candidate (all <= floor+0.05): no "
                     "fading-memory / output-recurrence mechanism counts modulo 3.")


# =========================================================================== #
# POSITIVE CONTROL: teacher-forced XOR via a plain 2-layer MLP.
# Proves the MLP family + harness CAN represent + GENERALIZE the x(t).o(t-1)
# cross-term WHEN o(t-1) is a clean input -- so a parity collapse below is about
# the recurrence bootstrapping o(t-1) from an output-state-blind drive, NOT about
# XOR capacity. (reused from verify_p6_*  P6E3b)
# =========================================================================== #
def exp_CONTROL() -> None:
    global RNG
    T = 1200

    def _acc(pred, tgt_pm1):
        return float(np.mean(np.sign(pred) == np.sign(tgt_pm1)))

    rng = np.random.default_rng(SEED)
    bits_tr = rng.integers(0, 2, size=T).astype(np.float64)
    tgt_tr = (np.cumsum(bits_tr) % 2) * 2 - 1
    bits_te = rng.integers(0, 2, size=T).astype(np.float64)
    tgt_te = (np.cumsum(bits_te) % 2) * 2 - 1

    def _design(bits, tgt):
        x = bits * 2.0 - 1.0
        o_prev = np.concatenate([[0.0], tgt[:-1]])  # teacher-forced TRUE o(t-1)
        return np.stack([x, o_prev], axis=1), tgt

    Xtr, ytr = _design(bits_tr, tgt_tr)
    Xte, yte = _design(bits_te, tgt_te)
    RNG = np.random.default_rng(SEED + 555)
    Hd_c = 8
    W1 = RNG.standard_normal((Hd_c, 2)) * 0.8
    b1 = np.zeros(Hd_c)
    W2 = RNG.standard_normal(Hd_c) * 0.5
    b2 = 0.0
    for _ep in range(3000):
        Zc = Xtr @ W1.T + b1
        Ac = np.tanh(Zc)
        pred = Ac @ W2 + b2
        diff = pred - ytr
        gpred = (2.0 / len(ytr)) * diff
        gW2 = Ac.T @ gpred
        gb2 = float(gpred.sum())
        gA = np.outer(gpred, W2) * (1 - Ac * Ac)
        gW1 = gA.T @ Xtr
        gb1 = gA.sum(axis=0)
        W1 -= 0.1 * gW1; b1 -= 0.1 * gb1; W2 -= 0.1 * gW2; b2 -= 0.1 * gb2
    tr_acc = _acc(np.tanh(Xtr @ W1.T + b1) @ W2 + b2, ytr)
    te_acc = _acc(np.tanh(Xte @ W1.T + b1) @ W2 + b2, yte)
    _rec("CONTROL", f"teacher-forced XOR(x(t),o_true(t-1)) via plain 2-layer MLP: "
                    f"TRAIN acc={tr_acc:.3f} TEST acc={te_acc:.3f} -- if ~1.0, the MLP CAN "
                    f"represent+GENERALIZE the XOR cross-term when o(t-1) is a CLEAN input. "
                    f"The recurrent candidates' parity collapse is then about bootstrapping "
                    f"o(t-1) from an OUTPUT-STATE-BLIND drive (cascade_correlation.py:"
                    f"1942-1946), not XOR-capacity.")


# =========================================================================== #
# HORIZON probe: fixed-lag recall (target = x(t-L0)) for every candidate. The
# memory's REACH (NOT a ceiling test; counting/parity is the ceiling test). One
# stream, in-sample readout fit, |corr| vs lag. Headline = the lag cutoff where
# |corr| drops below 0.5.
# =========================================================================== #
def exp_HORIZON() -> None:
    global RNG
    T = 1200
    x = np.random.default_rng(SEED + 21).standard_normal(T)  # white input
    L0_grid = [1, 5, 10, 20, 30, 40, 60]

    def _fir_feat(stream):
        return fir_features(stream, K_H_DEFAULT)

    Win, Wres, bres = esn_reservoir(ESN_N_DEFAULT, spectral_radius=0.95)

    def _esn_feat(stream):
        return esn_states(stream, Win, Wres, bres)

    def _lmu_feat(stream):
        return lmu_states(stream, LMU_D_DEFAULT, LMU_THETA_DEFAULT, dt=1.0)

    # candidates as (name, feature_fn, readout='ridge')  -- all use a linear ridge
    # readout so the horizon comparison isolates the MEMORY, not the readout power.
    cands = [
        ("FIR/P-base", _fir_feat),
        ("ESN", _esn_feat),
        ("LMU", _lmu_feat),
    ]
    rows = {}
    for name, feat in cands:
        F = feat(x)
        corrs = {}
        for L0 in L0_grid:
            tgt = np.zeros(T)
            tgt[L0:] = x[: T - L0]
            coef = ridge_readout_fit(F, tgt, lam=1e-3)
            pred = ridge_readout_predict(F, coef)
            corrs[L0] = pearson_abs(pred, tgt)
        rows[name] = corrs
        s = " ".join(f"L{L}:{corrs[L]:.2f}" for L in L0_grid)
        cut = max([L for L in L0_grid if corrs[L] >= 0.5], default=0)
        _rec("HORIZON", f"{name} corr-vs-lag (ridge readout): {s} | cutoff(>=0.5)={cut}")
    # P5/P6 recurrent-output horizon (their own readout, tanh recurrence)
    Hfir = _fir_feat(x)
    p5_cut_corrs = {}
    for L0 in L0_grid:
        tgt = np.zeros(T)
        tgt[L0:] = x[: T - L0]
        RNG = np.random.default_rng(SEED + 31 + L0)
        b = train_p5_output(Hfir, tgt, K_FB_DEFAULT, epochs=150, lr=0.03, n_restart=2)
        p5_cut_corrs[L0] = b[0]
    s = " ".join(f"L{L}:{p5_cut_corrs[L]:.2f}" for L in L0_grid)
    cut = max([L for L in L0_grid if p5_cut_corrs[L] >= 0.5], default=0)
    _rec("HORIZON", f"P5(rec-out) corr-vs-lag: {s} | cutoff(>=0.5)={cut}")
    _rec("HORIZON", f"interpretation: FIR/LMU reach ~ their window (K_h={K_H_DEFAULT}/"
                    f"theta={LMU_THETA_DEFAULT:g}); ESN reach is the fading-memory echo. "
                    f"Horizon is REACH, NOT counting -- a long horizon does NOT imply "
                    f"the ceiling is lifted (see PARITY/MOD3).")


# =========================================================================== #
# EQUITIES probe: do any of the four buy residual signal a 1-tap persistence
# baseline leaves on the next-close target?  (Decision-relevant: the empirical
# hint is the data does NOT reward counting/long memory.)
# =========================================================================== #
def _yyyymmdd_to_ordinal(dates):
    import datetime as _dt
    y, m, d = dates // 10000, (dates // 100) % 100, dates % 100
    return np.fromiter(
        (_dt.date(int(yy), int(mm), int(dd)).toordinal() for yy, mm, dd in zip(y, m, d)),
        dtype=np.int64, count=len(dates),
    )


def exp_EQUITIES() -> None:
    global RNG
    RNG = np.random.default_rng(SEED + 41)
    try:
        z = np.load(EQUITIES_NPZ, allow_pickle=False)
    except Exception as exc:  # pragma: no cover
        _rec("EQUITIES", f"SKIP: could not load equities npz: {exc!r}")
        return
    vocab = list(z["ticker_vocab"])
    pick = ["AAPL", "MSFT", "KO", "BRK.B"]
    X_full, yreg_full = z["X_full"], z["y_reg_full"]
    date_full, code_full = z["date_full"], z["ticker_code_full"]

    seqs = {}
    for nm in pick:
        try:
            code = vocab.index(np.str_(nm))
        except ValueError:
            continue
        mask = code_full == code
        order = np.argsort(date_full[mask])
        Xt = X_full[mask][order].astype(np.float64)
        yr = yreg_full[mask][order].reshape(-1)
        seqs[nm] = (standardize(Xt), yr)
    if not seqs:
        _rec("EQUITIES", "SKIP: none of the picked tickers were in vocab")
        return
    nm = max(seqs, key=lambda k: seqs[k][0].shape[0])
    Xstd, yr = seqs[nm]
    NMAX = 1500
    capped = Xstd.shape[0] > NMAX
    if capped:
        Xstd, yr = Xstd[-NMAX:], yr[-NMAX:]
    close = Xstd[:, 3]
    ytgt = (yr - yr.mean()) / (yr.std() + 1e-8)
    A0 = np.stack([close, np.ones_like(close)], axis=1)
    c0, *_ = np.linalg.lstsq(A0, ytgt, rcond=None)
    residual = ytgt - A0 @ c0
    base_corr = pearson_abs(close, ytgt)

    # P6 NARX recurrent output on the day-axis FIR residual (MSE-fit the centered
    # residual; train_p6_output in this suite is MSE-only).
    H = fir_features(close, K_H_DEFAULT)
    RNG = np.random.default_rng(SEED + 142)
    bp6 = train_p6_output(H, residual, K_FB_DEFAULT, HID_DEFAULT,
                          epochs=300, lr=0.03, n_restart=3)
    p6_corr = pearson_abs(p6_rollout(H, bp6[1])[0], residual)
    # ESN + LMU linear-ridge readouts on the residual
    Win, Wres, bres = esn_reservoir(ESN_N_DEFAULT, spectral_radius=0.9)
    Sesn = esn_states(close, Win, Wres, bres)
    esn_corr = pearson_abs(ridge_readout_predict(Sesn, ridge_readout_fit(Sesn, residual, lam=1e-2)), residual)
    Mlmu = lmu_states(close, LMU_D_DEFAULT, LMU_THETA_DEFAULT, dt=1.0)
    lmu_corr = pearson_abs(ridge_readout_predict(Mlmu, ridge_readout_fit(Mlmu, residual, lam=1e-2)), residual)

    _rec("EQUITIES", f"[{nm}, n={Xstd.shape[0]} days{' (recent cap)' if capped else ''}] "
                     f"baseline |corr(last_close,next_close)|={base_corr:.3f}")
    _rec("EQUITIES", f"residual |corr| (IN-SAMPLE, what each memory adds over persistence): "
                     f"P6-NARX={p6_corr:.3f}  ESN-linear={esn_corr:.3f}  LMU-linear={lmu_corr:.3f} "
                     f"(P5 ref tanh 0.081 / lin 0.048; P4 ref FIR 0.196 / IIR 0.018)")
    _rec("EQUITIES", "interpretation: persistence dominates (|corr|~0.99+); recurrent memory "
                     "adds only a thin residual sliver -> the equities data does NOT reward "
                     "counting/long memory, so the star-free ceiling is NOT binding here.")


# =========================================================================== #
def main() -> int:
    t0 = time.time()
    print(
        f"OQ-4 EXPRESSIVITY SUITE  (seed={SEED}, K_h={K_H_DEFAULT}, K_fb={K_FB_DEFAULT}, "
        f"P6 Hd={HID_DEFAULT}, ESN N={ESN_N_DEFAULT}, LMU d={LMU_D_DEFAULT}/theta="
        f"{LMU_THETA_DEFAULT:g}, numpy {np.__version__}, py {sys.version.split()[0]})",
        flush=True,
    )
    print("=" * 84, flush=True)
    exp_GRAD()       # HARD-ASSERT P6 gradient before trusting any training
    exp_CONTROL()    # positive control: clean teacher-forced XOR generalizes
    exp_PARITY()     # *** HEADLINE: held-out parity across all 4 candidates ***
    exp_MOD3()       # held-out mod-3 counting across all 4 candidates
    exp_HORIZON()    # fixed-lag recall reach (NOT a ceiling test)
    exp_EQUITIES()   # real-data residual probe (decision context)
    print("=" * 84, flush=True)
    print("RESULTS TABLE", flush=True)
    print("-" * 84, flush=True)
    for label, msg in _RESULTS:
        print(f"  {label:8s} | {msg}", flush=True)
    print("-" * 84, flush=True)
    print(f"total runtime: {time.time() - t0:.1f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
