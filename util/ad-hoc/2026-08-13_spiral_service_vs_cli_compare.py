"""Are the service spiral and the direct-CLI spiral the same problem? (R-5 precondition)

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-13
Status: ad-hoc -- one-off
Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: R-5 is closed out in the P4 follow-up write-up.
Related: P4 §7 R-5 (service 0.670 val vs ~0.995 direct CLI).

R-5 reads a service-vs-CLI accuracy gap as if both paths were solving one problem. Before
attributing that gap to the service tier, this checks the premise: it reconstructs the
geometry each path actually generates and reports (a) whether noise makes either dataset
non-separable and (b) how much boundary complexity each one demands.

Both generators are reimplemented here from their sources rather than imported, so the
comparison needs neither a running juniper-data nor a torch-importing cascor:

  juniper-data SpiralGenerator._generate_spiral_coordinates
      (juniper_data/generators/spiral/generator.py:132-141)
  cascor SpiralProblem._make_coords / generate_n_spiral_dataset
      (src/spiral_problem/spiral_problem.py:665, :803 -- both deprecated in favour of the service)

Read-only: generates arrays in memory, prints a report, writes nothing.
"""

import numpy as np

# spiral-baseline.yaml -- what every E-A / E-C service cell actually requests.
SERVICE = {"n_spirals": 2, "n_points_per_spiral": 500, "n_rotations": 3.0, "noise": 0.05, "radius": 10.0, "algorithm": "modern"}
# juniper_data/generators/spiral/defaults.py
DATA_DEFAULT_RADIUS = 10.0
# cascor constants_problem.py: radial sweep is 780 degrees expressed in radians.
CLI_SWEEP_DEGREES = 780.0


def modern(n_points, radius, n_rotations, noise, angle_offset, direction, rng):
    """juniper-data 'modern': linspace radii, linspace theta, NORMAL noise."""
    radii = np.linspace(0, radius, n_points)
    theta = np.linspace(0, 2 * np.pi * n_rotations, n_points) + angle_offset
    x = direction * radii * np.cos(theta) + rng.standard_normal(n_points) * noise
    y = direction * radii * np.sin(theta) + rng.standard_normal(n_points) * noise
    return np.column_stack([x, y])


def legacy_cascor(n_points, radius, noise, angle_offset, direction, rng):
    """juniper-data 'legacy_cascor' / the cascor CLI family: theta IS the radius (r = theta),
    sqrt-distributed radii, UNIFORM noise. n_rotations is not a parameter of this form --
    the sweep is fixed by `radius`, which is the whole point of the comparison."""
    distance = np.sqrt(rng.random(n_points)) * radius
    theta = direction * (distance + angle_offset)
    x = np.cos(theta) * distance + rng.random(n_points) * noise
    y = np.sin(theta) * distance + rng.random(n_points) * noise
    return np.column_stack([x, y])


def two_arm(kind, radius, n_rotations, noise, n_points, seed=20260729):
    # direction comes from the suite-level `clockwise` flag (default True -> +1) and is the
    # SAME for every arm -- arms are separated by angle_offset alone. Alternating it per arm
    # would make offset=pi cancel direction=-1 exactly and collapse both arms onto each other.
    rng = np.random.default_rng(seed)
    direction = 1  # SPIRAL_DEFAULT_CLOCKWISE = True
    arms = []
    for i in range(2):
        offset = 2 * np.pi * i / 2
        if kind == "modern":
            arms.append(modern(n_points, radius, n_rotations, noise, offset, direction, rng))
        else:
            arms.append(legacy_cascor(n_points, radius, noise, offset, direction, rng))
    X = np.vstack(arms)
    y = np.concatenate([np.zeros(n_points, dtype=int), np.ones(n_points, dtype=int)])
    return X, y


def nn1_accuracy(X, y):
    """Leave-one-out 1-NN. A capacity-free separability probe: if this is ~1.0 the classes
    are geometrically distinct and NOISE is not what limits any learner on this dataset."""
    d = np.linalg.norm(X[:, None, :] - X[None, :, :], axis=2)
    np.fill_diagonal(d, np.inf)
    return float((y[np.argmin(d, axis=1)] == y).mean())


def report(label, X, y, turns, note):
    span = float(np.abs(X).max())
    # Half the radial gap between successive turns: how far a point sits from the other arm.
    half_gap = (span / turns) / 2 if turns else float("nan")
    print(f"\n{label}")
    print(f"  rotations (full turns)   : {turns:.2f}")
    print(f"  coordinate span (max |v|): {span:.2f}")
    print(f"  half gap between arms    : {half_gap:.2f}")
    print(f"  1-NN separability        : {nn1_accuracy(X, y):.4f}")
    print(f"  boundary alternations    : ~{2 * turns:.1f} along a radial cut")
    print(f"  {note}")


def main() -> int:
    print("=" * 78)
    print("R-5 precondition: is the service spiral the same problem as the direct-CLI spiral?")
    print("=" * 78)

    Xs, ys = two_arm("modern", SERVICE["radius"], SERVICE["n_rotations"], SERVICE["noise"], SERVICE["n_points_per_spiral"])
    report(
        "SERVICE  (spiral-baseline.yaml -> juniper-data 'modern')",
        Xs,
        ys,
        SERVICE["n_rotations"],
        "n_rotations=3.0 is an explicit knob; radii are linspace and INDEPENDENT of theta.",
    )

    # The CLI sweeps 780 degrees of theta and sets r = theta, so its turn count is fixed by
    # that sweep, not by any n_rotations setting.
    cli_sweep_rad = CLI_SWEEP_DEGREES * np.pi / 180.0
    cli_turns = cli_sweep_rad / (2 * np.pi)
    Xc, yc = two_arm("legacy", cli_sweep_rad, None, SERVICE["noise"], SERVICE["n_points_per_spiral"])
    report(
        "DIRECT CLI (SpiralProblem -> legacy_cascor family)",
        Xc,
        yc,
        cli_turns,
        f"780 deg sweep with r = theta. n_rotations is NOT used by this form.",
    )

    Xl, yl = two_arm("legacy", DATA_DEFAULT_RADIUS, None, SERVICE["noise"], SERVICE["n_points_per_spiral"])
    report(
        "(reference) juniper-data 'legacy_cascor' at its default radius 10",
        Xl,
        yl,
        DATA_DEFAULT_RADIUS / (2 * np.pi),
        "Shows the service COULD produce the CLI-family geometry -- via algorithm, not n_rotations.",
    )

    print("\n" + "=" * 78)
    print("READING")
    print("=" * 78)
    print(
        "\n".join(
            [
                "1. Different generators, not one problem measured twice. The service config selects",
                "   algorithm: modern (linspace radii, theta from n_rotations, NORMAL noise); the CLI",
                "   uses the legacy family (sqrt radii, r = theta, UNIFORM noise).",
                "2. n_rotations is inert in the legacy family. Comparing 'n_rotations: 3.0' against a",
                "   CLI figure is comparing a knob that only one side has.",
                "3. Noise is not the differentiator at 0.05 -- 1-NN is ~1.0 for both, so both datasets",
                "   are geometrically separable and any accuracy shortfall is a CAPACITY/BUDGET result,",
                "   not a noise-floor result.",
                "4. The service spiral demands MORE boundary complexity (3.00 turns vs ~2.17), while the",
                "   service run is capped at 12 units by max_iterations: 12 (R-3). Dataset difficulty and",
                "   budget ceiling move the SAME direction, so both must be controlled before any",
                "   residual gap can be attributed to the service tier.",
            ]
        )
    )
    print("\nCONCLUSION: R-5's premise does not hold as stated. To make the comparison meaningful,")
    print("re-run the CLI on the SAME dataset the service uses (or set algorithm: legacy_cascor")
    print("service-side) and equalise the unit budget -- i.e. land R-3 first, as the register says.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
