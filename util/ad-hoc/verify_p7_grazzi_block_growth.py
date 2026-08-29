"""
Numpy-only PoC: P7 -- can cascor's CORRELATION-with-residual objective GROW a
Grazzi negative-eigenvalue input-dependent linear-RNN block that does parity
(held-out), or does ONLY ordinary task-loss gradient descent train it?

THE DECISIVE QUESTION (Paul, 2026-06-13).  The merged OQ-4 exhaustive
reevaluation (notes/JUNIPER_2026-06-12_JUNIPER-RECURRENCE_RECURSE-OQ4-EXHAUSTIVE-REEVALUATION.md)
settled that the entire star-free family (RCC / P4-FIR / P5 / P6 / ESN / LMU /
vanilla-SSM) does NOT break the star-free / no-count ceiling, and that the only
general+trainable ceiling-breaker is a NEGATIVE-EIGENVALUE INPUT-DEPENDENT
LINEAR-RNN (Grazzi, Siems, Zela, Franke, Hutter & Pontil, ICLR 2025 Oral,
arXiv:2411.12537, "Unlocking State-Tracking in Linear RNNs through Negative
Eigenvalues").  Grazzi trains that block HOLISTICALLY on a TASK LOSS by gradient
descent.  cascor grows by GREEDY, SINGLE-UNIT, FROZEN-ON-TENURE maximization of
|corr(scalar_activation, residual)| (Fahlman; candidate_unit.py:957/:1044-1045).
A correlation-compatible growth recipe for a negative-eigenvalue recurrent block
is UNSOLVED.  This PoC isolates sub-problem (1): does |corr|-with-residual
SUPERVISE the negative-eigenvalue dynamics?

THE BLOCK (single diagonal Grazzi block, the Mamba/diagonal case of the paper).
For a binary input symbol x(t) in {0,1} (here mapped to the cascor +/-1 stream),
the input-dependent diagonal transition and input drive use a small per-symbol
TABLE (the cheapest input-dependent parameterization; the paper's diagonal
realization is A_diag-(x) = Diag(2*s(x)-1), s in [0,1]^n, web-verified from the
full text):

    a(x) = 2*sigmoid(alpha[x]) - 1        # in (-1, 1); CAN reach negative   (NEG regime)
    a(x) =   sigmoid(alpha[x])            # in ( 0, 1); positive-only        (POS ablation)
    b(x) = beta[x]                         # input-dependent ADDITIVE drive (unconstrained)
    h(t) = a(x_t) (.) h(t-1) + b(x_t)                  # literal paper/prompt recurrence
    o(t) = w . h(t) + c                                # linear readout

State dim d in {1,4,8}.  This is EXACTLY the prompt's intuition
h(t)=a(x_t)h(t-1)+b(x_t) with a(x) input-dependent and reaching -1: set a(1)~=-1,
a(0)~=+1 -> h(t)=(-1)^(#1s)=running parity.  The block carries its OWN recurrent
state (NOT output-state-blind), which is why -- unlike P5/P6 -- it CAN in
principle track parity; the open question is whether the correlation objective
trains it to.

THREE REGIMES on the SAME block, all by analytic BPTT (gradient hard-gated vs
central finite differences first), each evaluated on HELD-OUT running parity +
mod-3 (train one Bernoulli stream, FREEZE, eval a DISJOINT stream; floor-relative
held-out accuracy is the headline):
  (i)   GD-on-task (the Grazzi baseline): minimize task MSE by BPTT.  EXPECT:
        learns parity held-out -> confirms the block + negative eigenvalues CAN
        do it and ARE trainable by ordinary GD.
  (ii)  POS-eigenvalue ablation: clamp a(x) to [0,1] (a(x)=sigmoid), GD-on-task.
        EXPECT: FAILS parity -> confirms the NEGATIVE eigenvalue is the mechanism
        (Grazzi Thm 1: positive-eigenvalue LRNNs provably cannot do parity).
  (iii) CORRELATION-trained (the P7 recipe test): maximize |corr(o, residual)|
        over the window by BPTT (the cascor objective).  DOES IT learn parity
        held-out?  This is the decisive cell.

For EACH regime we report held-out parity & mod-3 acc vs floor AND the LEARNED
per-symbol eigenvalues a(0), a(1) (does the regime drive a(1) -> negative?).

HEADLINE INTERPRETATION:
  (iii) ~= (i) success  => the correlation recipe WORKS (the open problem is
        solvable via direct correlation-BPTT; cascor could grow this block as-is).
  (iii) fails while (i) works => the open problem is REAL (correlation does not
        supervise the negative-eigenvalue dynamics; a hybrid recipe is needed).
Report which.

ANTI-HALLUCINATION.  numpy-only, manual gradients, seed-fixed, deterministic.
This PoC MEASURES learn-and-generalize-or-not (held-out parity/mod-3 accuracy +
whether a(x) learns the sign flip); it does NOT prove impossibility/possibility
-- the impossibility of positive-eigenvalue parity and the possibility of
negative-eigenvalue regular-language recognition are the LITERATURE's (Grazzi
Thms 1-4, web-verified in the OQ-4 docs).  The diagonal block buys PARITY ONLY;
mod-3 / general regular languages provably need the NON-DIAGONAL DeltaNet/GH form
(Grazzi Thm 2, web-verified) -- so the mod-3 cells are EXPECTED to fail for ALL
three regimes here (a diagonal block, even with negatives, cannot count mod-3);
they are reported as a control, not as a P7 failure.  Cascor code claims cite
file:line against the live tree.  Reused machinery: the |corr|+analytic-BPTT
recipe and the held-out parity/mod-3 protocol from
util/ad-hoc/verify_p5_recurrent_output_eval.py /
util/ad-hoc/verify_oq4_expressivity_suite.py.

Project:    Juniper ML Research Platform -- juniper-recurse (P7 design eval PoC)
Sub-Project: recurrent Cascade-Correlation -- P7 (Grazzi neg-eigenvalue block growth)
Application: ad-hoc design-evaluation harness
Author:     Paul Calnon
Version:    0.1.0
License:    MIT License
Created:    2026-06-13
Status:     ad-hoc - investigation (P7: does correlation-BPTT train a neg-eigenvalue
            linear-RNN block to do parity, held-out?  decisive cell = regime iii)
Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: the P7 design decision is ratified; measured numbers folded into the
            P7 design doc (do NOT edit notes/JUNIPER_RECURSE_* from here).
Related: util/ad-hoc/verify_p5_recurrent_output_eval.py (|corr|+BPTT helpers reused),
         util/ad-hoc/verify_oq4_expressivity_suite.py  (held-out protocol reused),
         util/ad-hoc/verify_p6_narx_mlp_output_eval.py  (NARX BPTT precedent),
         notes/JUNIPER_2026-06-12_JUNIPER-RECURRENCE_RECURSE-OQ4-EXHAUSTIVE-REEVALUATION.md,
         arXiv:2411.12537 (Grazzi et al., ICLR 2025 -- the negative-eigenvalue block)
"""

from __future__ import annotations

import sys
import time

import numpy as np

# --------------------------------------------------------------------------- #
SEED = 20260613
RNG = np.random.default_rng(SEED)

_RESULTS: list[tuple[str, str]] = []  # (label, one-line measured result)


def _rec(label: str, msg: str) -> None:
    _RESULTS.append((label, msg))
    print(f"[{label}] {msg}", flush=True)


# --------------------------------------------------------------------------- #
# Correlation objective (Fahlman |Pearson|) + helpers -- reused verbatim from the
# P5/OQ-4 PoCs so the contrast is apples-to-apples with the prior suites.
# --------------------------------------------------------------------------- #
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


def binary_accuracy(pred: np.ndarray, target_pm1: np.ndarray) -> float:
    return float(np.mean(np.sign(pred) == np.sign(target_pm1)))


def _sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))


# --------------------------------------------------------------------------- #
# Task builders (running parity / mod-3 count) -- identical semantics to the
# P5/OQ-4 PoCs (parity is +/-1; mod-3 is the mean-centered Z_3 code).
# --------------------------------------------------------------------------- #
def running_parity(bits: np.ndarray) -> np.ndarray:
    """o(t)=XOR over all bits up to t == o(t)=XOR(x(t),o(t-1)). The crux task."""
    return (np.cumsum(bits) % 2) * 2.0 - 1.0


def mod3_count(bits: np.ndarray) -> np.ndarray:
    """Unbounded mod-3 running count of 1-bits, mean-centered (a Z_3 task)."""
    cnt = (np.cumsum(bits) % 3).astype(np.float64)
    return cnt - cnt.mean()


def mod3_classacc(pred: np.ndarray, bits: np.ndarray) -> float:
    """3-class accuracy for mod-3: round centered prediction back to {0,1,2} via
    nearest of the three centered class codes."""
    true_cls = (np.cumsum(bits) % 3).astype(int)
    centers = np.array([0.0, 1.0, 2.0]) - 1.0  # centered codes (-1, 0, +1)
    d = np.abs(pred[:, None] - centers[None, :])
    return float(np.mean(d.argmin(axis=1) == true_cls))


def _floor_pm1(target_pm1: np.ndarray) -> float:
    p_pos = float(np.mean(target_pm1 > 0))
    return max(p_pos, 1.0 - p_pos)


def _floor_mod3(bits: np.ndarray) -> float:
    true_cls = (np.cumsum(bits) % 3).astype(int)
    _v, cnts = np.unique(true_cls, return_counts=True)
    return float(cnts.max() / true_cls.size)


# =========================================================================== #
# THE GRAZZI DIAGONAL BLOCK (input-dependent, negative-eigenvalue-capable).
#   symbols: x(t) in {0,1} chooses the per-symbol transition a[x] AND the
#            per-symbol additive input drive b[x] (the symbol carries the input;
#            the +/-1 cascor stream u is retained in call signatures for API parity
#            with the P5/P6 trainers but is NOT used by this additive-drive block).
#   raw params:  alpha:(2,d)  per-symbol transition logits
#                beta :(2,d)  per-symbol ADDITIVE input drive b[x]
#                w    :(d,)    readout weights
#                c    : scalar readout bias
#   transition map:  eig='neg' -> a = 2*sigmoid(alpha)-1  in (-1,1)  (Grazzi)
#                    eig='pos' -> a =   sigmoid(alpha)     in ( 0,1)  (ablation)
#   recurrence:  h(t) = a[x_t] (.) h(t-1) + b[x_t],  h(-1)=0  (literal paper form)
#   readout:     o(t) = w . h(t) + c
# This is the diagonal/Mamba case of arXiv:2411.12537 (web-verified mechanism):
# A_diag-(x)=Diag(2*s(x)-1).  A NEGATIVE diagonal eigenvalue is the 2-cycle parity
# needs.  Per Grazzi Thm 2 the diagonal block is PARITY-ONLY (cannot count mod-3).
# =========================================================================== #
class GrazziParams:
    __slots__ = ("alpha", "beta", "w", "c")

    def __init__(self, alpha, beta, w, c):
        self.alpha = alpha  # (2, d)
        self.beta = beta    # (2, d)
        self.w = w          # (d,)
        self.c = float(c)

    def copy(self) -> "GrazziParams":
        return GrazziParams(self.alpha.copy(), self.beta.copy(), self.w.copy(), self.c)


def grazzi_init(d: int, *, a_scale: float = 0.5, b_scale: float = 0.5) -> GrazziParams:
    alpha = RNG.standard_normal((2, d)) * a_scale
    beta = RNG.standard_normal((2, d)) * b_scale
    w = RNG.standard_normal(d) * (1.0 / np.sqrt(d))
    return GrazziParams(alpha, beta, w, 0.0)


def _amap(alpha: np.ndarray, eig: str) -> np.ndarray:
    """Per-symbol diagonal eigenvalues a:(2,d). eig='neg' -> (-1,1); 'pos' -> (0,1)."""
    s = _sigmoid(alpha)
    return (2.0 * s - 1.0) if eig == "neg" else s


def _amap_grad(alpha: np.ndarray, eig: str) -> np.ndarray:
    """da/dalpha given the transition map. d(2s-1)/dalpha = 2 s(1-s);
    d(s)/dalpha = s(1-s)."""
    s = _sigmoid(alpha)
    sp = s * (1.0 - s)
    return (2.0 * sp) if eig == "neg" else sp


def grazzi_rollout(symbols: np.ndarray, u: np.ndarray, p: GrazziParams, eig: str):
    """Forward rollout of the diagonal Grazzi block. symbols:(T,) in {0,1} selects
    the per-symbol transition a[x] AND the per-symbol additive input drive b[x].
    Returns (o:(T,), Hs:(T,d)) where Hs[t]=h(t).

    Drive form is the LITERAL paper / prompt recurrence h(t)=a(x_t)(.)h(t-1)+b(x_t)
    (arXiv:2411.12537 diagonal case; the prompt's intuition h=a(x)h(t-1)+b(x) with
    a(x) input-dependent and reaching -1). b[x] is an input-DEPENDENT ADDITIVE bias
    (not multiplied by a separate u): with a(0)=+1,a(1)=-1,b(1)!=0,b(0)=0 the state
    flips sign on every 1-bit and holds on 0-bits -> h(t)=(-1)^(#1s)=running parity.
    `u` is retained in the signature for API parity with the P5/P6 trainers but is
    NOT used by this additive-drive block (the symbol already carries the input)."""
    T = symbols.shape[0]
    d = p.w.shape[0]
    a_tab = _amap(p.alpha, eig)  # (2, d)
    o = np.zeros(T)
    Hs = np.zeros((T, d))
    h = np.zeros(d)
    for t in range(T):
        sx = int(symbols[t])
        h = a_tab[sx] * h + p.beta[sx]
        Hs[t] = h
        o[t] = float(p.w @ h + p.c)
    return o, Hs


def _grazzi_bptt(symbols, u, p: GrazziParams, eig: str, dL_do_direct: np.ndarray):
    """Shared reverse-mode BPTT core for the diagonal Grazzi block. Given the
    DIRECT dL/do(t) (loss's explicit dependence on each output, NOT through the
    recurrence), returns gradients (gAlpha, gBeta, gW, gc).

    Forward:  h(t)   = a[x_t] (.) h(t-1) + b[x_t];  o(t)=w.h(t)+c.
    Adjoints (lam(t) := dL/dh(t)):
      lam(t) = w * dL_do_direct(t) + a[x_{t+1}] (.) lam(t+1)     (t<T-1; else just w*...)
      a[x_t] / b[x_t] contribute via h(t)=a[x_t]*h(t-1)+b[x_t]:
        dL/da[x_t] += lam(t) (.) h(t-1)
        dL/db[x_t] += lam(t)
      a[x] enters through a=map(alpha) -> dL/dalpha[x] = (dL/da[x]) * (da/dalpha)[x].
      readout:  dL/dw += sum_t dL_do_direct(t) * h(t);  dL/dc += sum_t dL_do_direct(t).
    """
    d = p.w.shape[0]
    a_tab = _amap(p.alpha, eig)  # (2, d)
    o, Hs = grazzi_rollout(symbols, u, p, eig)

    gA_lin = np.zeros((2, d))  # accumulates dL/da[symbol]
    gBeta = np.zeros((2, d))   # accumulates dL/db[symbol] (additive drive)
    gW = np.zeros(d)
    gc = 0.0

    lam = np.zeros(d)  # dL/dh(t+1) carried backward; starts at 0 for t=T-1's future
    for t in range(symbols.shape[0] - 1, -1, -1):
        sx = int(symbols[t])
        # dL/dh(t): direct readout term + recurrence term already folded into lam
        # (lam currently holds a[x_{t+1}] (.) dL/dh(t+1) accumulated below).
        lam_t = p.w * dL_do_direct[t] + lam
        h_prev = Hs[t - 1] if t - 1 >= 0 else np.zeros(d)
        gA_lin[sx] += lam_t * h_prev
        gBeta[sx] += lam_t  # additive drive: d h(t)/d b[x_t] = 1
        # readout grads (direct dependence of o(t) on w, c)
        gW += dL_do_direct[t] * Hs[t]
        gc += dL_do_direct[t]
        # propagate to h(t-1):  d h(t)/d h(t-1) = diag(a[x_t]) -> lam for next iter
        lam = a_tab[sx] * lam_t
    gAlpha = gA_lin * _amap_grad(p.alpha, eig)  # chain through a=map(alpha)
    return o, (gAlpha, gBeta, gW, float(gc))


def grazzi_mse_loss_and_bptt(symbols, u, target, p: GrazziParams, eig: str):
    """Task-loss training: L = mean (o(t)-target(t))^2 + analytic BPTT
    (the Grazzi regime -- ordinary GD on a task loss)."""
    T = symbols.shape[0]
    o, _Hs = grazzi_rollout(symbols, u, p, eig)
    diff = o - target
    L = float(np.mean(diff * diff))
    dL_do_direct = (2.0 / T) * diff
    _o, grads = _grazzi_bptt(symbols, u, p, eig, dL_do_direct)
    return L, grads


def grazzi_corr_loss_and_bptt(symbols, u, residual, p: GrazziParams, eig: str):
    """Cascor objective: L = -|corr(o, residual)| + analytic BPTT (the P7 recipe
    test). Only the DIRECT dL/do term differs from the MSE variant; the recurrence
    adjoint is shared. Mirrors p5_corr_loss_and_bptt
    (verify_p5_recurrent_output_eval.py:243)."""
    o, _Hs = grazzi_rollout(symbols, u, p, eig)
    r = signed_pearson(o, residual)
    L = -abs(r)
    oc = o - o.mean()
    e = residual - residual.mean()
    no = np.linalg.norm(oc) + 1e-12
    ne = np.linalg.norm(e) + 1e-12
    dabs = 1.0 if r >= 0 else -1.0
    dr_do = dabs * ((e / (no * ne)) - (oc * (oc @ e)) / (no**3 * ne))
    dL_do_direct = -dr_do
    _o, grads = _grazzi_bptt(symbols, u, p, eig, dL_do_direct)
    return L, grads


def _flatten(grads):
    gAlpha, gBeta, gW, gc = grads
    return np.concatenate([gAlpha.ravel(), gBeta.ravel(), gW.ravel(), [gc]])


class _Adam:
    """Minimal Adam (the optimizer the Grazzi paper actually uses -- 'plain
    gradient descent (Adam), no architecture-specific tricks', web-verified). A
    single global SGD step cannot simultaneously drive alpha[1] far negative
    through the sign-flip recurrence's vanishing-gradient region AND keep the
    readout stable; Adam's per-parameter adaptive step is what makes the
    negative-eigenvalue solution reachable by ordinary GD. Used for ALL THREE
    regimes so the (i) vs (iii) contrast is fair (same optimizer, only the LOSS
    differs)."""

    def __init__(self, beta1=0.9, beta2=0.999, eps=1e-8):
        self.b1, self.b2, self.eps = beta1, beta2, eps
        self.m = None
        self.v = None
        self.t = 0

    def step(self, theta, grad, lr):
        if self.m is None:
            self.m = np.zeros_like(theta)
            self.v = np.zeros_like(theta)
        self.t += 1
        self.m = self.b1 * self.m + (1 - self.b1) * grad
        self.v = self.b2 * self.v + (1 - self.b2) * (grad * grad)
        mhat = self.m / (1 - self.b1 ** self.t)
        vhat = self.v / (1 - self.b2 ** self.t)
        return theta - lr * mhat / (np.sqrt(vhat) + self.eps)


def _pack(p: GrazziParams):
    return np.concatenate([p.alpha.ravel(), p.beta.ravel(), p.w.ravel(), [p.c]])


def _unpack(theta, d) -> GrazziParams:
    i = 0
    alpha = theta[i:i + 2 * d].reshape(2, d); i += 2 * d
    beta = theta[i:i + 2 * d].reshape(2, d); i += 2 * d
    w = theta[i:i + d]; i += d
    c = float(theta[i])
    return GrazziParams(alpha.copy(), beta.copy(), w.copy(), c)


def train_grazzi(symbols, u, target, d, *, eig="neg", mode="mse",
                 epochs=400, lr=0.05, n_restart=6, grad_clip=5.0):
    """Train the diagonal Grazzi block by BPTT + Adam. mode='mse' fits target by
    MSE (Grazzi task-loss regime); mode='corr' maximizes |corr(o,target)| (cascor
    objective). eig='neg' allows a in (-1,1); eig='pos' clamps to (0,1).
    Multi-restart; returns (score=|corr|, params, a0_vec, a1_vec) for the BEST
    restart, where 'best' tracks the params with the highest in-sample |corr| seen
    at ANY epoch (the sign-flip recurrence can drift, so we keep the running best,
    not the final, params). GENEROUS budget so any parity failure is a
    recipe/representational finding, not under-fitting."""
    best = None  # (score, GrazziParams)
    for _ in range(n_restart):
        p = grazzi_init(d)
        opt = _Adam()
        theta = _pack(p)
        for _ep in range(epochs):
            pc = _unpack(theta, d)
            if mode == "mse":
                _L, grads = grazzi_mse_loss_and_bptt(symbols, u, target, pc, eig)
            else:
                _L, grads = grazzi_corr_loss_and_bptt(symbols, u, target, pc, eig)
            g = _flatten(grads)
            gn = float(np.linalg.norm(g))
            if gn > grad_clip:
                g = g * (grad_clip / (gn + 1e-12))
            theta = opt.step(theta, g, lr)
            # track running-best by in-sample |corr| every few epochs (the sign-flip
            # recurrence can drift, so keep the running best, not the final params;
            # sampled every 10 epochs to bound the extra-rollout cost).
            if (_ep % 10 == 0) or (_ep == epochs - 1):
                o, _Hs = grazzi_rollout(symbols, u, _unpack(theta, d), eig)
                ac = pearson_abs(o, target)
                if best is None or ac > best[0]:
                    best = (ac, _unpack(theta, d))
    a_tab = _amap(best[1].alpha, eig)  # (2, d) learned per-symbol eigenvalues
    return best[0], best[1], a_tab[0], a_tab[1]


# --------------------------------------------------------------------------- #
# Stream + readout-rescale helpers for held-out evaluation.
#   The block is trained on stream A, frozen, then rolled out on a DISJOINT
#   stream B. Because parity (+/-1) and the block's readout scale can differ, we
#   pick the held-out decision by SIGN of (o - median) [parity is a 2-class sign
#   decision]; for mod-3 we nearest-centroid the held-out output onto {-1,0,+1}
#   after an affine fit of (in-sample o -> centered code) so the 3 levels line up.
# --------------------------------------------------------------------------- #
def _bits_pm1(bits):
    return bits * 2.0 - 1.0


def _make_streams(T):
    """Train + DISJOINT test Bernoulli streams (same seed pair for every regime
    so the contrast is fair). Mirrors _make_streams in the OQ-4 suite."""
    rng = np.random.default_rng(SEED)
    bits_tr = rng.integers(0, 2, size=T).astype(np.float64)
    bits_te = rng.integers(0, 2, size=T).astype(np.float64)
    return bits_tr, bits_te


def _parity_acc_signed(o: np.ndarray, tgt_pm1: np.ndarray) -> float:
    """Held-out parity accuracy that is invariant to the readout's overall SIGN
    and OFFSET: threshold at the median, then take the better of {pred, -pred}
    (a frozen linear readout may encode parity up to a global sign)."""
    centered = o - np.median(o)
    a1 = float(np.mean(np.sign(centered) == np.sign(tgt_pm1)))
    a2 = float(np.mean(np.sign(-centered) == np.sign(tgt_pm1)))
    return max(a1, a2)


def _mod3_acc_affine(o_tr, bits_tr, o_te, bits_te) -> float:
    """Held-out mod-3 accuracy: fit affine (o_tr -> centered code) on the TRAIN
    stream, apply to the TEST stream, nearest-centroid onto {-1,0,+1}. Isolates
    'are there 3 separable levels tracking the count' from readout scale."""
    code_tr = (np.cumsum(bits_tr) % 3).astype(np.float64) - 1.0  # centered {-1,0,1}
    A = np.stack([o_tr, np.ones_like(o_tr)], axis=1)
    coef, *_ = np.linalg.lstsq(A, code_tr, rcond=None)
    pred_te = np.stack([o_te, np.ones_like(o_te)], axis=1) @ coef
    centers = np.array([-1.0, 0.0, 1.0])
    pred_cls = np.abs(pred_te[:, None] - centers[None, :]).argmin(axis=1)
    true_cls = (np.cumsum(bits_te) % 3).astype(int)
    return float(np.mean(pred_cls == true_cls))


# =========================================================================== #
# GRADIENT GATE -- Grazzi BPTT vs central finite differences (HARD ASSERT).
# Runs FIRST; if it fails the suite aborts before trusting any training number.
# Checks BOTH transition maps (neg / pos) and BOTH losses (mse / corr).
# =========================================================================== #
def exp_GRAD() -> None:
    global RNG
    RNG = np.random.default_rng(SEED + 7)
    T, d = 40, 4
    bits = RNG.integers(0, 2, size=T).astype(np.float64)
    symbols = bits
    u = _bits_pm1(bits)
    target = running_parity(bits)
    residual = target - target.mean()  # a parity-encoding residual for the corr check

    eps = 1e-6
    overall_max = 0.0
    detail = []
    for eig in ("neg", "pos"):
        for mode in ("mse", "corr"):
            p = grazzi_init(d)
            if mode == "mse":
                _L, grads = grazzi_mse_loss_and_bptt(symbols, u, target, p, eig)

                def _Lonly(pp):
                    o, _ = grazzi_rollout(symbols, u, pp, eig)
                    dd = o - target
                    return float(np.mean(dd * dd))
            else:
                _L, grads = grazzi_corr_loss_and_bptt(symbols, u, residual, p, eig)

                def _Lonly(pp):
                    o, _ = grazzi_rollout(symbols, u, pp, eig)
                    return -abs(signed_pearson(o, residual))

            flat = _flatten(grads)
            theta = np.concatenate([p.alpha.ravel(), p.beta.ravel(), p.w.ravel(), [p.c]])
            shapes = [p.alpha.shape, p.beta.shape, p.w.shape, (1,)]
            sizes = [int(np.prod(s)) for s in shapes]

            def _set(vec):
                i = 0
                mats = []
                for s, sz in zip(shapes, sizes):
                    mats.append(np.array(vec[i:i + sz]).reshape(s))
                    i += sz
                return GrazziParams(mats[0], mats[1], mats[2], float(mats[3][0]))

            idxs = RNG.choice(theta.size, size=min(28, theta.size), replace=False)
            max_rel = 0.0
            for j in idxs:
                tp = theta.copy(); tp[j] += eps
                tm = theta.copy(); tm[j] -= eps
                fd = (_Lonly(_set(tp)) - _Lonly(_set(tm))) / (2 * eps)
                # Skip coords with no gradient signal: when BOTH analytic and FD
                # are below ~machine-noise (e.g. a dead state dim whose readout
                # weight is ~0), the relative error is dominated by FD rounding,
                # not a gradient bug -- there is nothing to verify there.
                if max(abs(flat[j]), abs(fd)) < 1e-7:
                    continue
                rel = abs(flat[j] - fd) / (max(abs(flat[j]), abs(fd)) + 1e-12)
                max_rel = max(max_rel, rel)
            detail.append(f"{eig}/{mode}={max_rel:.1e}")
            overall_max = max(overall_max, max_rel)
    ok = overall_max < 1e-4
    _rec("GRAD", f"Grazzi BPTT vs central-FD: " + " ".join(detail)
         + f" | max rel err={overall_max:.2e} PASS={ok} (threshold 1e-4)")
    assert ok, f"Grazzi BPTT gradient WRONG (max rel {overall_max:.2e}) -- aborting before training"


# =========================================================================== #
# THE HEADLINE: held-out parity across the THREE regimes x state-dims.
#   (i)   task-MSE,  eig='neg'  (Grazzi baseline)
#   (ii)  task-MSE,  eig='pos'  (positive-eigenvalue ablation)
#   (iii) |corr|,    eig='neg'  (the P7 recipe test)
# For each: held-out parity acc vs floor + learned a(0), a(1) (mean over state dim).
# =========================================================================== #
def _eval_parity_regime(label, d, *, eig, mode, epochs, lr, n_restart, seed_off):
    global RNG
    T = 600
    bits_tr, bits_te = _make_streams(T)
    u_tr, u_te = _bits_pm1(bits_tr), _bits_pm1(bits_te)
    tgt_tr = running_parity(bits_tr)
    tgt_te = running_parity(bits_te)
    if mode == "mse":
        train_target = tgt_tr
    else:
        # cascor grows against a RESIDUAL; here the residual encodes running parity
        # (the centered parity signal is the residual the output layer cannot yet
        # explain). This is the most-favorable residual for the recipe -- if |corr|
        # cannot learn parity even when the residual IS parity, the recipe is dead.
        train_target = tgt_tr - tgt_tr.mean()

    RNG = np.random.default_rng(SEED + seed_off)
    score, p, a0, a1 = train_grazzi(
        bits_tr, u_tr, train_target, d, eig=eig, mode=mode,
        epochs=epochs, lr=lr, n_restart=n_restart,
    )
    o_tr, _ = grazzi_rollout(bits_tr, u_tr, p, eig)
    o_te, _ = grazzi_rollout(bits_te, u_te, p, eig)
    in_acc = _parity_acc_signed(o_tr, tgt_tr)
    te_acc = _parity_acc_signed(o_te, tgt_te)
    te_corr = pearson_abs(o_te, tgt_te)
    floor = _floor_pm1(tgt_te)
    margin = te_acc - floor
    return {
        "in_acc": in_acc, "te_acc": te_acc, "te_corr": te_corr,
        "floor": floor, "margin": margin,
        "a0_mean": float(np.mean(a0)), "a1_mean": float(np.mean(a1)),
        "a0_min": float(np.min(a0)), "a1_min": float(np.min(a1)),
    }


def exp_PARITY() -> None:
    _rec("PARITY", "running-parity o(t)=XOR(x(t),o(t-1)); train one stream, FREEZE, "
                   "test DISJOINT stream (T=600 each). HEADLINE = held-out acc vs floor "
                   "AND learned per-symbol eigenvalues a(0)/a(1).")
    regimes = [
        ("i.task-MSE/neg ", dict(eig="neg", mode="mse", epochs=300, lr=0.05, n_restart=8, seed_off=11)),
        ("ii.task-MSE/POS", dict(eig="pos", mode="mse", epochs=300, lr=0.05, n_restart=8, seed_off=23)),
        ("iii.|corr|/neg ", dict(eig="neg", mode="corr", epochs=300, lr=0.05, n_restart=8, seed_off=37)),
    ]
    summary = {}
    for rlabel, cfg in regimes:
        for d in (1, 4, 8):
            r = _eval_parity_regime(rlabel, d, **cfg)
            lifts = r["margin"] > 0.05
            summary.setdefault(rlabel, []).append((d, r, lifts))
            _rec("PARITY",
                 f"{rlabel} d={d}: IN acc={r['in_acc']:.3f} | HELD-OUT acc={r['te_acc']:.3f} "
                 f"|corr|={r['te_corr']:.3f} (floor={r['floor']:.3f}, margin={r['margin']:+.3f})"
                 f"{'  <-- LIFTS' if lifts else ''} | learned a(0)~{r['a0_mean']:+.2f} "
                 f"a(1)~{r['a1_mean']:+.2f} [min a(1)={r['a1_min']:+.2f}]")
    return summary


# =========================================================================== #
# MOD-3 control: the diagonal block is PARITY-ONLY (Grazzi Thm 2: counting mod-m
# for m not a power of 2 needs NON-diagonal transitions). EXPECT all three regimes
# to FAIL mod-3 held-out -- reported as a control confirming the diagonal limit,
# NOT as a P7 recipe failure. (A DeltaNet/GH block would be needed; out of scope
# for a single greedy cascor candidate -- that is sub-problem 2.)
# =========================================================================== #
def exp_MOD3() -> None:
    global RNG
    _rec("MOD3", "mod-3 running count (Z_3); same held-out protocol (T=600). DIAGONAL "
                 "block is parity-only (Grazzi Thm 2) -> EXPECT all regimes fail; CONTROL.")
    T = 600
    bits_tr, bits_te = _make_streams(T)
    u_tr, u_te = _bits_pm1(bits_tr), _bits_pm1(bits_te)
    code_tr = mod3_count(bits_tr)
    floor3 = _floor_mod3(bits_te)
    regimes = [
        ("i.task-MSE/neg ", dict(eig="neg", mode="mse", seed_off=51)),
        ("ii.task-MSE/POS", dict(eig="pos", mode="mse", seed_off=53)),
        ("iii.|corr|/neg ", dict(eig="neg", mode="corr", seed_off=57)),
    ]
    for rlabel, cfg in regimes:
        d = 8  # give the diagonal block its largest tested width for the control
        train_target = code_tr if cfg["mode"] == "mse" else (code_tr - code_tr.mean())
        RNG = np.random.default_rng(SEED + cfg["seed_off"])
        _score, p, a0, a1 = train_grazzi(
            bits_tr, u_tr, train_target, d, eig=cfg["eig"], mode=cfg["mode"],
            epochs=250, lr=0.05, n_restart=4,
        )
        o_tr, _ = grazzi_rollout(bits_tr, u_tr, p, cfg["eig"])
        o_te, _ = grazzi_rollout(bits_te, u_te, p, cfg["eig"])
        te_acc = _mod3_acc_affine(o_tr, bits_tr, o_te, bits_te)
        in_acc = mod3_classacc(o_tr, bits_tr)  # rough in-sample 3-level read
        margin = te_acc - floor3
        lifts = margin > 0.05
        _rec("MOD3",
             f"{rlabel} d={d}: IN acc~{in_acc:.3f} | HELD-OUT acc={te_acc:.3f} "
             f"(floor={floor3:.3f}, margin={margin:+.3f}){'  <-- LIFTS' if lifts else ''} | "
             f"learned a(0)~{np.mean(a0):+.2f} a(1)~{np.mean(a1):+.2f}")


# =========================================================================== #
# POSITIVE CONTROL (optional, per prompt): a HAND-SET negative-eigenvalue block.
# Set a(1)=-1, a(0)=+1, b=1, readout w=1,c=0 -> h(t)=(-1)^(#1s)=parity EXACTLY.
# Confirms the block FAMILY can REPRESENT parity (so a learning failure is about
# the OBJECTIVE/optimization, not representational capacity). No training.
# =========================================================================== #
def exp_CONTROL() -> None:
    T = 1000
    _bits_tr, bits_te = _make_streams(T)
    u_te = _bits_pm1(bits_te)
    tgt_te = running_parity(bits_te)
    d = 1
    # Hand-set RAW params so the 'neg' map yields a(0)=+1, a(1)=-1 (approx via large
    # logits: 2*sigmoid(+big)-1 ~ +1 ; 2*sigmoid(-big)-1 ~ -1), with the ADDITIVE
    # input drive b(1)=1, b(0)=0. Then h(t)=a(x_t)h(t-1)+b(x_t): a 0-bit holds
    # (h unchanged), a 1-bit does h <- -h + 1 which toggles h between {0,1} in lock
    # step with running parity (#1s even -> 0, odd -> 1). readout w=1,c=0.
    BIG = 12.0
    alpha = np.array([[+BIG], [-BIG]])   # symbol 0 -> a=+1, symbol 1 -> a=-1
    beta = np.array([[0.0], [1.0]])      # additive drive: inject only on 1-bits
    p = GrazziParams(alpha, beta, np.array([1.0]), 0.0)
    o, _Hs = grazzi_rollout(bits_te, u_te, p, "neg")
    acc = _parity_acc_signed(o, tgt_te)
    a_tab = _amap(alpha, "neg")
    _rec("CONTROL", f"HAND-SET neg-eigenvalue block a(0)={float(a_tab[0,0]):+.3f} "
                    f"a(1)={float(a_tab[1,0]):+.3f}, additive b(0)=0 b(1)=1: held-out "
                    f"parity acc={acc:.3f} (floor={_floor_pm1(tgt_te):.3f}) -- if ~1.0, the "
                    f"diagonal Grazzi block FAMILY CAN REPRESENT parity; any learning "
                    f"failure below is about the OBJECTIVE/optimization, not capacity.")


# =========================================================================== #
def _verdict(summary) -> None:
    """Compare regime (iii) |corr| against regime (i) task-MSE on best held-out
    parity margin across state dims; print the headline interpretation."""
    def best_margin(rlabel):
        rows = summary.get(rlabel, [])
        return max((r["margin"] for _d, r, _l in rows), default=float("nan"))

    m_i = best_margin("i.task-MSE/neg ")
    m_ii = best_margin("ii.task-MSE/POS")
    m_iii = best_margin("iii.|corr|/neg ")
    i_works = m_i > 0.05
    ii_fails = m_ii <= 0.05
    iii_works = m_iii > 0.05
    _rec("VERDICT", f"best held-out parity MARGIN over floor: (i)task-MSE/neg={m_i:+.3f}  "
                    f"(ii)task-MSE/POS={m_ii:+.3f}  (iii)|corr|/neg={m_iii:+.3f}")
    _rec("VERDICT", f"(i) neg-eig block trainable by task-loss GD = {i_works}; "
                    f"(ii) POS-eig ablation FAILS parity (mechanism = negative eig) = {ii_fails}")
    if iii_works and i_works:
        _rec("VERDICT", "HEADLINE: (iii)|corr| LEARNS held-out parity AND (i) does too => the "
                        "CORRELATION recipe WORKS. Sub-problem (1) is SOLVABLE via direct "
                        "correlation-BPTT: |corr|-with-residual DOES supervise the "
                        "negative-eigenvalue dynamics. cascor could grow this diagonal block "
                        "as-is for PARITY (mod-3+ still needs non-diagonal -> sub-problem 2).")
    elif i_works and not iii_works:
        _rec("VERDICT", "HEADLINE: (i) task-loss GD learns held-out parity but (iii)|corr| does "
                        "NOT => the OPEN PROBLEM IS REAL. The correlation objective does not "
                        "supervise the negative-eigenvalue state-tracking; a hybrid growth "
                        "recipe (e.g. task-loss inner training of the block under a "
                        "correlation-gated install) is needed. This is the decisive P7 finding.")
    elif iii_works and not i_works:
        _rec("VERDICT", "HEADLINE: (iii)|corr| LEARNS held-out parity (a(1)->-1) while (i) "
                        "task-MSE did NOT clear it at this seed/budget => the CORRELATION recipe "
                        "WORKS for parity -- |corr|-with-residual DOES supervise the negative "
                        "eigenvalue. (That task-MSE under-performed at THIS seed is an "
                        "optimization-landscape note, NOT evidence against the recipe: the "
                        "hand-set CONTROL confirms capacity, and |corr| is the cell that "
                        "matters for P7.) Sub-problem (1) SOLVABLE for parity; mod-3+ still "
                        "needs a non-diagonal block (sub-problem 2).")
    else:
        _rec("VERDICT", "INCONCLUSIVE: NEITHER (i) task-loss NOR (iii)|corr| cleared held-out "
                        "parity at this budget -- raise n_restart/epochs. (CONTROL confirms the "
                        "block CAN represent parity, so this is an optimization-budget issue, "
                        "not a capacity or recipe verdict.)")


def main() -> int:
    t0 = time.time()
    print(
        f"P7 Grazzi negative-eigenvalue block-growth PoC  (seed={SEED}, "
        f"numpy {np.__version__}, py {sys.version.split()[0]})",
        flush=True,
    )
    print("=" * 88, flush=True)
    exp_GRAD()      # HARD-ASSERT Grazzi BPTT (neg/pos x mse/corr) before trusting training
    exp_CONTROL()   # hand-set neg-eig block REPRESENTS parity (capacity check)
    summary = exp_PARITY()   # *** HEADLINE: held-out parity across 3 regimes x state-dims ***
    exp_MOD3()      # diagonal-block mod-3 control (expected fail; Grazzi Thm 2)
    _verdict(summary)
    print("=" * 88, flush=True)
    print("RESULTS TABLE", flush=True)
    print("-" * 88, flush=True)
    for label, msg in _RESULTS:
        print(f"  {label:8s} | {msg}", flush=True)
    print("-" * 88, flush=True)
    print(f"total runtime: {time.time() - t0:.1f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
