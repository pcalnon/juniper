#!/usr/bin/env bash
########################################################################################################################################################################################################
# E2E validation harness: local GPG key generation -> YubiKey keytocard (ed448 repro + ed25519 transfer).
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon (authored via Claude Code)
# Created:    2026-08-03
# Status:     ad-hoc — investigation (YubiKey ed448 keytocard procedure development)
# Retire when: the YubiKey GPG key-to-card procedure doc is finalized and no scripted re-validation is needed
# Related:    notes/JUNIPER_2026-08-03_JUNIPER-ECOSYSTEM_YUBIKEY-GPG-ED448-KEYTOCARD-PROCEDURE.md
#
########################################################################################################################################################################################################
# Notes and Warnings:
#
# - THROWAWAY-CREDENTIAL TESTING ONLY.
#   - Operates exclusively in an isolated GNUPGHOME ($HOME/.gnupg-yktest by default; override with YKTEST_HOME). Never touches ~/.gnupg keyrings.
#   - RESETS the OpenPGP applet of the attached YubiKey (reset-card phase) — wipes on-card OpenPGP keys and restores default PINs 123456/12345678. FIDO/PIV/OATH applets are NOT touched.
#   - All secrets used here are hardcoded throwaway values.
#
# - Phases (run in order):
#   - kill-others  — stop other gpg-agent/scdaemon instances that may hold the card
#   - reset-card   — factory-reset the OpenPGP applet (ykman openpgp reset -f)
#   - gen          — create isolated GNUPGHOME + ed448[C] primary + subkeys:
#                      1: ed25519 [S]   2: ed25519 [A]   3: cv25519 [E]   4: ed448 [S] (repro probe)
#   - repro        — attempt keytocard of the ed448 subkey (expected: KEYTOCARD failed: Invalid value)
#   - transfer     — keytocard subkeys 1/2/3 into card slots Sig/Auth/Enc + save (local -> stubs)
#   - verify       — flush PIN cache, sign+verify and encrypt+decrypt via the card, show counters
#   - status       — print card status + secret key listing
#   - clean        — kill the test home's daemons (leaves $YKTEST_HOME in place for inspection)
########################################################################################################################################################################################################
set -euo pipefail


########################################################################################################################################################################################################
# Define script constants
########################################################################################################################################################################################################
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STUB="${SCRIPT_DIR}/2026-08-03_yubikey_test_pinentry.bash"
TESTHOME="${YKTEST_HOME:-$HOME/.gnupg-yktest}"
MARKER="${TESTHOME}/.yktest-marker"

# Throwaway secrets (deliberately free of shell metacharacters; see the procedure
# doc's warning about $-expansion/quoting when secrets pass through heredocs).
TEST_PASSPHRASE='Throwaway-yktest-passphrase-2026'
TEST_ADMIN_PIN='12345678'   # YubiKey factory default (restored by reset-card)
TEST_USER_PIN='123456'      # YubiKey factory default (restored by reset-card)
TEST_UID='Yubikey Keytocard E2E Test (throwaway) <yktest@invalid.example>'
EXPIRE='2y'

GPG=(gpg --homedir "$TESTHOME")
GPG_BATCH=(gpg --homedir "$TESTHOME" --batch --pinentry-mode loopback --passphrase "$TEST_PASSPHRASE")


########################################################################################################################################################################################################
# Define script Utility functions
########################################################################################################################################################################################################
die() { printf 'FATAL: %s\n' "$*" >&2; exit 1; }
note() { printf '\n==== %s ====\n' "$*"; }

fpr() { cat "${TESTHOME}/fpr.txt"; }

phase_kill_others() {
    note "kill-others: releasing the card from other GnuPG instances"
    gpgconf --kill scdaemon 2>/dev/null || true
    gpgconf --homedir "$HOME/.gnupg/working/yubikey-3c" --kill all 2>/dev/null || true
    pkill -f '^scdaemon --multi-server$' 2>/dev/null || true
    sleep 1
    pgrep -a -f 'scdaemon' || echo "(no scdaemon running)"
}

phase_reset_card() {
    note "reset-card: factory-resetting the OpenPGP applet (throwaway content only)"
    command -v ykman >/dev/null || die "ykman not found"
    ykman openpgp reset -f
    # The isolated GNUPGHOME only exists after the 'gen' phase; skip the status
    # probe on a first-time run (ykman's own output above already confirms the reset).
    if [[ -d "$TESTHOME" ]]; then
        "${GPG[@]}" --card-status | sed -n '1,20p'
    fi
}

phase_gen() {
    note "gen: creating isolated GNUPGHOME at ${TESTHOME}"
    if [[ -e "$TESTHOME" && ! -e "$MARKER" ]]; then
        die "refusing to remove ${TESTHOME}: no ${MARKER} marker (not created by this harness)"
    fi
    rm -rf "$TESTHOME"
    mkdir -m 700 "$TESTHOME"
    touch "$MARKER"

    # 'compliance gnupg' is REQUIRED for Ed448/Curve448 key generation in gpg 2.4.x:
    # without it: "gpg: Cannot create Ed448 or Curve448 key without --compliance=gnupg."
    printf 'keyid-format long\nwith-subkey-fingerprints\ncompliance gnupg\n' > "${TESTHOME}/gpg.conf"
    cat > "${TESTHOME}/gpg-agent.conf" <<EOF
pinentry-program ${TESTHOME}/pinentry-wrapper.bash
allow-loopback-pinentry
default-cache-ttl 60
max-cache-ttl 120
EOF
    cat > "${TESTHOME}/pinentry-wrapper.bash" <<EOF
#!/usr/bin/env bash
export TEST_ADMIN_PIN='${TEST_ADMIN_PIN}'
export TEST_USER_PIN='${TEST_USER_PIN}'
export TEST_PASSPHRASE='${TEST_PASSPHRASE}'
export PINENTRY_STUB_LOG='${TESTHOME}/pinentry-stub.log'
exec '${STUB}' "\$@"
EOF
    chmod 700 "${TESTHOME}/pinentry-wrapper.bash"
    gpgconf --homedir "$TESTHOME" --launch gpg-agent

    note "gen: ed448 certify-only primary"
    "${GPG_BATCH[@]}" --quick-generate-key "$TEST_UID" ed448 cert never

    local f
    f="$("${GPG[@]}" --list-keys --with-colons | awk -F: '/^fpr:/ {print $10; exit}')"
    [[ -n "$f" ]] || die "could not determine primary fingerprint"
    printf '%s\n' "$f" > "${TESTHOME}/fpr.txt"
    echo "primary fingerprint: $f"

    note "gen: subkeys — ed25519[S], ed25519[A], cv25519[E], ed448[S] (repro probe)"
    "${GPG_BATCH[@]}" --quick-add-key "$f" ed25519 sign "$EXPIRE"
    "${GPG_BATCH[@]}" --quick-add-key "$f" ed25519 auth "$EXPIRE"
    "${GPG_BATCH[@]}" --quick-add-key "$f" cv25519 encr "$EXPIRE"
    "${GPG_BATCH[@]}" --quick-add-key "$f" ed448 sign "$EXPIRE"

    "${GPG[@]}" -K
}

phase_repro() {
    note "repro: attempting keytocard of the ed448 subkey (key 4) — expecting 'Invalid value'"
    local out
    out="$(printf 'key 4\nkeytocard\n1\nquit\nn\n' | "${GPG[@]}" --no-tty --command-fd 0 --status-fd 1 --edit-key "$(fpr)" 2>&1 || true)"
    printf '%s\n' "$out"
    if grep -q 'KEYTOCARD failed' <<<"$out"; then
        note "repro: CONFIRMED — ed448 keytocard fails on this card"
    else
        note "repro: NOT REPRODUCED — inspect output above before running 'transfer'"
        return 1
    fi
}

phase_transfer() {
    note "transfer: keytocard 1->Sig(1), 2->Auth(3), 3->Enc(2), then save"
    printf 'key 1\nkeytocard\n1\nkey 1\nkey 2\nkeytocard\n3\nkey 2\nkey 3\nkeytocard\n2\nsave\n' \
        | "${GPG[@]}" --no-tty --command-fd 0 --status-fd 1 --edit-key "$(fpr)" 2>&1 \
        | tee "${TESTHOME}/transfer.log"
    if grep -q 'KEYTOCARD failed' "${TESTHOME}/transfer.log"; then
        die "transfer: a keytocard operation failed — see ${TESTHOME}/transfer.log"
    fi
    local stubs
    stubs="$("${GPG[@]}" -K | grep -c '^ssb>')" || true
    echo "card-backed subkey stubs (ssb>): ${stubs}"
    [[ "$stubs" == "3" ]] || die "expected 3 card-backed subkeys, found ${stubs}"
    note "transfer: SUCCESS — 3 subkeys now live on the card"
}

phase_verify() {
    note "verify: flushing agent PIN cache, then exercising the card"
    gpgconf --homedir "$TESTHOME" --kill gpg-agent 2>/dev/null || true
    sleep 1
    gpgconf --homedir "$TESTHOME" --launch gpg-agent

    note "verify: sign + verify (uses card Sig slot; user PIN via stub)"
    printf 'keytocard e2e test payload\n' > "${TESTHOME}/payload.txt"
    "${GPG[@]}" --batch --yes -u "$(fpr)" --armor --detach-sign -o "${TESTHOME}/payload.sig" "${TESTHOME}/payload.txt"
    "${GPG[@]}" --verify "${TESTHOME}/payload.sig" "${TESTHOME}/payload.txt" 2>&1 | grep -E 'Good signature|using' || die "signature verification failed"

    note "verify: encrypt + decrypt (uses card Enc slot)"
    "${GPG[@]}" --batch --yes -r "$(fpr)" -e -o "${TESTHOME}/payload.gpg" "${TESTHOME}/payload.txt"
    "${GPG[@]}" --batch -d "${TESTHOME}/payload.gpg" > "${TESTHOME}/payload.out" 2>/dev/null
    diff "${TESTHOME}/payload.txt" "${TESTHOME}/payload.out" || die "decrypt roundtrip mismatch"
    echo "decrypt roundtrip: OK"

    note "verify: card status"
    "${GPG[@]}" --card-status | grep -E 'Key attributes|Signature counter|Signature key|Encryption key|Authentication key|created|card-no' || true
    note "verify: ALL CHECKS PASSED"
}

phase_status() {
    "${GPG[@]}" --card-status || true
    "${GPG[@]}" -K || true
}

phase_clean() {
    note "clean: killing test-home daemons (leaving ${TESTHOME} for inspection)"
    gpgconf --homedir "$TESTHOME" --kill all 2>/dev/null || true
}

########################################################################################################################################################################################################
# Main execution
########################################################################################################################################################################################################
case "${1:-}" in
    kill-others) phase_kill_others ;;
    reset-card)  phase_reset_card ;;
    gen)         phase_gen ;;
    repro)       phase_repro ;;
    transfer)    phase_transfer ;;
    verify)      phase_verify ;;
    status)      phase_status ;;
    clean)       phase_clean ;;
    all)         phase_kill_others; phase_reset_card; phase_gen; phase_repro || true; phase_transfer; phase_verify ;;
    *) die "usage: $0 {kill-others|reset-card|gen|repro|transfer|verify|status|clean|all}" ;;
esac
