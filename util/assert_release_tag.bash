#!/usr/bin/env bash
# Assert a publish run is building the ref it claims, and that the built
# artifact's version matches the release tag.
#
# Project:     juniper-ml
# Sub-Project: release tooling
# Author:      Paul Calnon
# License:     MIT License
#
# Closes the two surviving asks of juniper-ml#357 / #358 that the environment
# tag policy does not cover:
#
#   1. REF SHAPE -- a publish must run from a tag, never a branch. The
#      environment ref policy already refuses a branch at the deployment gate,
#      but that happens AFTER the build job has run and only protects the
#      publish jobs. Asserting here fails earlier, names the reason, and keeps
#      the invariant visible in the repository rather than only in settings.
#
#   2. TAG <-> VERSION -- nothing previously checked that the tag being
#      published matches the version actually built. A `v0.7.2` release cut
#      from a tree still declaring 0.7.1 would publish 0.7.1 under a 0.7.2
#      release with no error anywhere.
#
# The built version is read from the WHEEL FILENAME, not from pyproject.toml.
# That is deliberate: it is the version that will actually be uploaded, and it
# works identically for static and dynamic (setuptools-scm / hatch) version
# backends, where parsing pyproject would report nothing useful.
#
# This is defense in depth, NOT the control. Anyone who can edit the workflow
# can delete this step; the environment tag policy is what survives that. See
# notes/JUNIPER_2026-08-17_JUNIPER-ECOSYSTEM_PUBLISH-PATH-AUTHORIZATION-DESIGN.md
# §6 Option B.
#
# Usage:
#   util/assert_release_tag.bash --ref refs/tags/v0.7.1 \
#       --dist-dir dist --expect-prefix v
#
# The ref is taken as the FULLY-FORMED `github.ref`, not `github.ref_name` plus
# a separate `github.ref_type`. GitHub documents `github.ref` as
# `refs/tags/<tag_name>` for a `release` event, so `refs/tags/` is an
# unambiguous, documented discriminator. `ref_type` would work too, but its
# value on a release event is far less clearly specified -- and an assumption
# that is wrong here does not fail safe, it fails EVERY publish.
#
# Exit 0 all assertions hold · 1 an assertion failed · 2 misuse.
set -uo pipefail

REF=""
DIST_DIR="dist"
EXPECT_PREFIX=""

die() {
  echo "::error::$*" >&2
  exit 1
}

usage() {
  echo "usage: $0 --ref <refs/tags/...> --dist-dir <dir> --expect-prefix <prefix>" >&2
  exit 2
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --ref) REF="${2:-}"; shift 2 ;;
    --dist-dir) DIST_DIR="${2:-}"; shift 2 ;;
    --expect-prefix) EXPECT_PREFIX="${2:-}"; shift 2 ;;
    -h|--help) usage ;;
    *) echo "unknown argument: $1" >&2; usage ;;
  esac
done

[ -n "${REF}" ] || usage
[ -n "${EXPECT_PREFIX}" ] || usage

# ── 1. Ref shape ─────────────────────────────────────────────────────────────
case "${REF}" in
  refs/tags/*) : ;;
  *) die "publish must run from a tag, but ref is '${REF}'. Re-run with --ref <tag>; publishing from a branch is refused by design." ;;
esac

REF_NAME="${REF#refs/tags/}"
[ -n "${REF_NAME}" ] || die "ref '${REF}' has no tag name after 'refs/tags/'."

case "${REF_NAME}" in
  "${EXPECT_PREFIX}"*) : ;;
  *) die "tag '${REF_NAME}' does not start with the expected prefix '${EXPECT_PREFIX}' for this package." ;;
esac

# ── 2. Extract the version the tag claims ────────────────────────────────────
# Strip the package prefix, then a single leading 'v'. Done as two steps rather
# than "everything up to the last v" so a package name containing 'v' (e.g. a
# hypothetical juniper-observability-v...) cannot eat part of the version.
TAG_VERSION="${REF_NAME#"${EXPECT_PREFIX}"}"
TAG_VERSION="${TAG_VERSION#v}"
[ -n "${TAG_VERSION}" ] || die "tag '${REF_NAME}' carries no version after the prefix '${EXPECT_PREFIX}'."

# ── 3. Extract the version actually built ────────────────────────────────────
[ -d "${DIST_DIR}" ] || die "dist directory '${DIST_DIR}' does not exist -- run the build before this check."

WHEEL=""
for candidate in "${DIST_DIR}"/*.whl; do
  [ -e "${candidate}" ] || continue
  WHEEL="${candidate}"
  break
done
[ -n "${WHEEL}" ] || die "no wheel found in '${DIST_DIR}' -- cannot verify the built version."

# Wheel filenames are {distribution}-{version}-{python}-{abi}-{platform}.whl
WHEEL_BASE="$(basename "${WHEEL}" .whl)"
BUILT_VERSION="$(printf '%s' "${WHEEL_BASE}" | cut -d- -f2)"
[ -n "${BUILT_VERSION}" ] || die "could not parse a version out of wheel filename '${WHEEL_BASE}'."

# ── 4. Compare, PEP 440-normalized ───────────────────────────────────────────
# A tag may spell a pre-release as 1.0.0-rc1 while the wheel normalizes it to
# 1.0.0rc1; compare with separators removed and case folded so that agrees.
#
# `--` before the SET is load-bearing: some `tr` implementations (notably the
# Rust coreutils rewrite) parse a leading-dash SET like '-_' as an option and
# exit non-zero. Without it BOTH sides normalize to the empty string, the
# comparison becomes "" != "" and the mismatch check passes VACUOUSLY -- a
# check that silently succeeds when its own machinery breaks. The empty-result
# guard below is the belt to that braces.
normalize() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | tr -d -- '-_'
}

NORM_TAG="$(normalize "${TAG_VERSION}")"
NORM_BUILT="$(normalize "${BUILT_VERSION}")"
if [ -z "${NORM_TAG}" ] || [ -z "${NORM_BUILT}" ]; then
  die "version normalization produced an empty result (tag '${TAG_VERSION}' -> '${NORM_TAG}', built '${BUILT_VERSION}' -> '${NORM_BUILT}'). Refusing to compare; this would pass vacuously."
fi

if [ "${NORM_TAG}" != "${NORM_BUILT}" ]; then
  die "tag/version mismatch: tag '${REF_NAME}' claims version '${TAG_VERSION}' but the built wheel is '${BUILT_VERSION}' (${WHEEL_BASE}). Bump the package version to match the tag, or cut the release against the correct tag."
fi

echo "Release tag check passed: ref_type=tag, tag='${REF_NAME}', built version='${BUILT_VERSION}'."
