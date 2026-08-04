#!/usr/bin/env bash
########################################################################################################################################################################################################
# Headless Assuan pinentry stub for scripted GnuPG smartcard testing (answers from env vars).
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
# - THROWAWAY-CREDENTIAL TESTING ONLY. This defeats the entire purpose of pinentry (interactive secret entry) and must never be pointed at a real keyring or a live-provisioned card.
# - It answers gpg-agent's pinentry protocol from:
#
#   - TEST_ADMIN_PIN   — returned when the prompt mentions "Admin"
#   - TEST_USER_PIN    — returned when the prompt mentions the card PIN / "unlock the card"
#   - TEST_PASSPHRASE  — returned for everything else (key passphrase)
#   - PINENTRY_STUB_LOG — optional path; prompt classes (never secrets) are appended
#
########################################################################################################################################################################################################
set -u

LOG="${PINENTRY_STUB_LOG:-}"
log() { if [[ -n "$LOG" ]]; then printf '%s %s\n' "$(date +%H:%M:%S)" "$*" >>"$LOG"; fi; }

desc=""
prompt=""

printf 'Pleased to meet you !\n'
log "started (args: $*)"

while IFS= read -r line; do
    line="${line%$'\r'}"
    case "$line" in
        SETDESC\ *)
            desc="${line#SETDESC }"
            log "SETDESC: $desc"
            printf 'OK\n'
            ;;
        SETPROMPT\ *)
            prompt="${line#SETPROMPT }"
            log "SETPROMPT: $prompt"
            printf 'OK\n'
            ;;
        GETPIN)
            ctx="$desc $prompt"
            if [[ "$ctx" == *Admin* ]]; then
                log "GETPIN -> admin-pin"
                secret="${TEST_ADMIN_PIN:-}"
            elif [[ "$ctx" == *"unlock the card"* || "$ctx" == *PIN* ]]; then
                log "GETPIN -> user-pin"
                secret="${TEST_USER_PIN:-}"
            else
                log "GETPIN -> passphrase"
                secret="${TEST_PASSPHRASE:-}"
            fi
            printf 'D %s\n' "$secret"
            printf 'OK\n'
            ;;
        GETINFO\ pid)
            printf 'D %s\n' "$$"
            printf 'OK\n'
            ;;
        GETINFO\ *)
            printf 'D stub\n'
            printf 'OK\n'
            ;;
        CONFIRM*|MESSAGE*)
            log "$line -> OK"
            printf 'OK\n'
            ;;
        BYE)
            log "BYE"
            printf 'Closing connection...\n'
            exit 0
            ;;
        *)
            printf 'OK\n'
            ;;
    esac
done

exit 0
