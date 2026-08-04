# YubiKey GPG Provisioning — ed448 `keytocard` Root Cause & Validated Transfer Procedure

**Project**: Juniper — Cascade Correlation Neural Network Research Platform
**Scope**: Ecosystem-wide (GPG code-signing key ceremony on the development host + YubiKey 5C NFC provisioning)
**Author**: Paul Calnon (investigation and validation driven via Claude Code session)
**Date**: 2026-08-03
**Status**: VALIDATED — every command in §4 was executed end-to-end against the live YubiKey on 2026-08-03 with throwaway credentials
**Related**: [`JUNIPER_2026-07-16_JUNIPER-ECOSYSTEM_CODE-SIGNING-KEY-MIGRATION-STATUS.md`](JUNIPER_2026-07-16_JUNIPER-ECOSYSTEM_CODE-SIGNING-KEY-MIGRATION-STATUS.md) (git-signing migration; deferred GitHub-side items), harness scripts [`../util/ad-hoc/2026-08-03_yubikey_curve448_keytocard_e2e.bash`](../util/ad-hoc/2026-08-03_yubikey_curve448_keytocard_e2e.bash) + [`../util/ad-hoc/2026-08-03_yubikey_test_pinentry.bash`](../util/ad-hoc/2026-08-03_yubikey_test_pinentry.bash)

---

## 0. Executive summary

**`gpg: KEYTOCARD failed: Invalid value` is a hardware capability limit, not a procedure error.**
The YubiKey 5 series — including this 5C NFC on the newest firmware line 5.7.x (5.7.4 on the attached key) — **does not implement Ed448 or X448 in its OpenPGP application**.
The card's own Algorithm Information object advertises RSA 2048/3072/4096, NIST P-256/384/521, secp256k1, brainpool 256/384/512, and Curve25519 (ed25519/cv25519) — and nothing else.
`keytocard` fails because gpg must first switch the target slot's algorithm attributes to the key's algorithm, and the card rejects an algorithm it does not support.
No gpg flag, applet reset, or firmware update changes this; Yubico has shipped no firmware with Curve448 OpenPGP support.

**The requirement set is still almost fully satisfiable.**
The certification primary never moves to the card in this design — it lives offline and only manages subkeys.
Only the *subkeys* must be card-compatible.
The validated configuration is:

| Role                                      | Algorithm        | Lives                                        |
|-------------------------------------------|------------------|----------------------------------------------|
| Certify (primary, subkey management only) | **ed448**        | Offline / local ceremony dir — never on card |
| Sign (subkey)                             | ed25519          | YubiKey slot 1                               |
| Encrypt (subkey)                          | cv25519 (X25519) | YubiKey slot 2                               |
| Authenticate (subkey)                     | ed25519          | YubiKey slot 3                               |

This keeps the ed448 requirement where hardware permits (the certification root), keeps distinct per-role subkeys, and was proven live: subkeys transferred, card-backed signing and decryption both verified (§8). If Curve448-on-hardware is a hard requirement, the only known path is a Gnuk 2.2+ token (e.g. Nitrokey Start) — see §3.3.

Two secondary failure classes were also identified in the earlier attempts recorded in `~/.gnupg/notes.txt` and are addressed by this procedure: gpg 2.4.x refuses to *create* Ed448/Curve448 keys without `--compliance=gnupg` (§2.2), and the scripted heredoc transfer attempts corrupted every secret they piped (§2.3).

## 1. Environment and evidence base

| Component | Value                                                                | Checked                            |
|-----------|----------------------------------------------------------------------|------------------------------------|
| GnuPG     | 2.4.8 (libgcrypt 1.11.0)                                             | `gpg --version`                    |
| YubiKey   | 5C NFC, serial 24955323, **firmware 5.7.4**, OpenPGP applet spec 3.4 | `ykman info`, `ykman openpgp info` |
| ykman     | 5.7.2                                                                | `ykman --version`                  |
| pcscd     | active                                                               | `systemctl is-active pcscd`        |

Evidence for the Curve448 verdict (three independent sources):

1. **The card's parsed capability list.** `gpg-connect-agent 'scd getattr KEY-ATTR-INFO' /bye` enumerates, per slot, exactly: `rsa2048 rsa3072 rsa4096 nistp256 nistp384 nistp521 secp256k1 brainpoolP256r1 brainpoolP384r1 brainpoolP512r1` plus `ed25519` (slots 1/3) / `cv25519` (slot 2). No `ed448`, no `cv448`/`x448`.
2. **The raw Algorithm Information DO (tag `0xFA`) from the card itself.** `gpg-connect-agent --hex 'scd apdu 00 ca 00 fa 00' /bye` — the EdDSA entries carry only the Ed25519 OID (`16 2B 06 01 04 01 DA 47 0F 01` = algorithm 22 + 1.3.6.1.4.1.11591.15.1) and the ECDH entries only the X25519 OID (`12 2B 06 01 04 01 97 55 01 05 01`). The Ed448 OID (`2B 65 71` = 1.3.101.113) and X448 OID (`2B 65 6F` = 1.3.101.111) appear nowhere in the response.
3. **Yubico documentation.** The OpenPGP curve support list (firmware 5.2.3+; unchanged through the 5.7 additions of RSA-3072/4096) ends at Curve25519. 5.7's new curve support (Ed25519/X25519) applies to **PIV**, which had lacked them — OpenPGP already had them and gained no Curve448.

Live reproduction (§8) closed the loop: with correct passphrase and Admin PIN supplied, `keytocard` of an ed448 subkey still fails `SC_OP_FAILURE` / `Invalid value`, while the identical procedure with ed25519 succeeds seconds later on the same card.

## 2. Root cause — three layers

### 2.1 Layer 1 (the reported error): the card cannot hold Curve448 keys

When `keytocard` moves a key, gpg/scdaemon must first set the target slot's *algorithm attributes* (OpenPGP card DOs C1/C2/C3) to match the key being written.
The card validates the requested attribute against its Algorithm Information list and rejects unlisted algorithms; scdaemon surfaces the rejection as `GPG_ERR_INV_VALUE` → **`KEYTOCARD failed: Invalid value`**.
This is also why the on-card `generate` path worked: it generates whatever the card supports (default rsa2048) and never has to accept a foreign algorithm.

Consequences:

- The error occurs for **every** ed448/x448 subkey, regardless of slot, PIN correctness, or key-attr pre-setting (`gpg --card-edit` → `admin` → `key-attr` offers no Curve448 entry to select either).
- The 2025-08-29 ed448 key `93E8591643C507FF` (uid comment "yubikey-3", the current git `user.signingkey`) predictably could never have been moved to a YubiKey either — it operates as an on-disk software key.

### 2.2 Layer 2: gpg 2.4.x gates Ed448/Curve448 *creation* behind `--compliance=gnupg`

A fresh GNUPGHOME reproduces:

```text
gpg: Cannot create Ed448 or Curve448 key without --compliance=gnupg.
gpg: Key generation failed: Invalid public key algorithm
```

Ed448/X448 in the v4/v5 packet formats gpg 2.4 emits is a GnuPG/LibrePGP extension (the IETF RFC 9580 "crypto-refresh" encodes these algorithms differently), so gpg requires the explicit compliance opt-in for generation. Add `compliance gnupg` to the ceremony home's `gpg.conf` (covers every invocation) or pass `--compliance=gnupg` per generating command — the notes.txt `--quick-add-key` lines already did the latter.

Related observable: gpg creates ed448 keys in **v5 key format** — the primary's fingerprint is 64 hex chars (32 bytes) instead of the classic v4 40. Many external services cannot parse v5 keys (§6).

### 2.3 Layer 3: the scripted attempts corrupted every secret they piped

The `notes.txt` transfer/PIN-change attempts fed secrets through **unquoted heredocs** (`<<EOF`). Inside an unquoted heredoc, bash performs `$`-expansion, and surrounding single quotes are *not* quoting — they become literal characters:

- `...&6f6#$w%EXm6hLBM...` → `$w` expanded to empty (unset variable) — passphrase silently mangled.
- `...$BxR70^$5#of189...$ZOQ000pRksIFCtf2*fes$UEDdGsS21` → `$BxR70`, `$5`, `$ZOQ000pRksIFCtf2`, `$UEDdGsS21` all expanded — Admin PIN mangled.
- Lines written as `'secret'` delivered a value that *starts and ends with a literal apostrophe*.

Any of these produce wrong-passphrase / wrong-PIN failures that are easy to misread as the Layer-1 error (and wrong Admin PIN attempts decrement the card's retry counter, 3 strikes → admin lockout). Rules adopted by this procedure:

1. Assign secrets once, in **single-quoted shell assignments** (`PASS='...'`), never inside heredocs.
2. Deliver them with `printf '%s' "$PASS" |` + `--passphrase-fd 0`, or `--passphrase-file`, or (best for the transfer step) type interactively / use the pinentry stub harness (§9).
3. Never mix `--pinentry-mode=loopback` with operations that prompt for *both* a passphrase and a PIN in one flow — loopback answers every prompt with the same fd content, so one of the two receives the wrong secret. The card PIN-change attempts in notes.txt had exactly this shape.
4. Prefer secrets without shell metacharacters for throwaway/dev use; for live secrets, treat every `$`, `!`, backtick and quote as a handling hazard.

A fourth environmental hazard observed on this host: **three concurrent GnuPG stacks** (the default `~/.gnupg` supervised agent, a second agent for `~/.gnupg/working/yubikey-3c`, and a stray manually-started `scdaemon --multi-server`) can contend for the card. Kill extras before card ceremonies (§4.0).

## 3. Requirement resolution

### 3.1 Decision matrix

| Option                         | Certify         | Sign / Auth | Encrypt | On YubiKey?                         | Notes                                                                                                                                 |
|--------------------------------|-----------------|-------------|---------|-------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------|
| **A (validated, recommended)** | ed448 (offline) | ed25519     | cv25519 | Subkeys yes, primary no (by design) | Max curve strength where hardware allows; ed25519 signatures are also the *most* interoperable EdDSA (GitHub-verifiable, ssh-ed25519) |
| B                              | ed25519         | ed25519     | cv25519 | Yes                                 | Choose if the v5-format ed448 primary's interop cost (§6) outweighs its strength; whole chain is v4                                   |
| C                              | ed448           | ed448       | x448    | **No** — software-only              | The original spec; works entirely on disk (current state of `93E8591643C507FF`); no hardware isolation                                |
| D                              | ed448           | ed448       | x448    | Gnuk 2.2+ token                     | Gnuk (open firmware; Nitrokey Start) added Ed448/X448 in 2.2; different hardware, lower assurance/performance class than YubiKey      |
| E                              | rsa4096         | rsa4096     | rsa4096 | Yes                                 | Maximum legacy interop; large, slow                                                                                                   |

### 3.2 Why Option A satisfies the intent

- **"Certification key whose only role is related to the subkeys"** — met exactly: the ed448 primary is created certify-only (`[C]`), never touches the card, and is needed only to add/revoke/extend subkeys and certify others' keys.
- **"Distinct sub-key for each of signing, encryption, authentication"** — met: three separate subkeys, one per card slot.
- **"ed448/x448 types"** — met for the primary; *impossible on this hardware* for the card-resident subkeys (§2.1). ed25519/X25519 is the strongest curve family the applet supports and is the same 128-bit-security class used pervasively (SSH, age, signal, minisign).

### 3.3 If Curve448-on-hardware is non-negotiable

Only [Gnuk](https://www.fsij.org/category/gnuk.html) ≥ 2.2 (open-source token firmware; commercially available as Nitrokey Start) is known to implement Ed448/X448 for OpenPGP. YubiKey (all firmware through 5.7.x), Nitrokey 3, and SmartPGP do not. Keep watching Yubico firmware release notes; a future applet could add the two OIDs, at which point this exact procedure works unchanged with `ed448`/`cv448` substituted in §4.3.

## 4. Validated procedure

Everything below was executed successfully on 2026-08-03 (§8). Steps assume the YubiKey is attached and dedicated to this purpose. `<ANGLE>` placeholders are yours to substitute. The scripted form of §4.0–§4.5 is the harness in §9.

### 4.0 Preflight — one GnuPG stack, known card state

```bash
gpg --version | head -1               # want ≥ 2.4  (2.3 minimum for any 448 support)
ykman info                            # confirm the intended serial; firmware note: 5.7.x still has no Curve448
systemctl is-active pcscd             # 'active' expected on this host

# Kill competing daemons so exactly one scdaemon owns the card during the ceremony:
gpgconf --kill scdaemon
gpgconf --homedir ~/.gnupg/working/yubikey-3c --kill all 2>/dev/null || true
pkill -f '^scdaemon --multi-server$' 2>/dev/null || true
```

### 4.1 Card preparation (destructive to on-card OpenPGP content only)

```bash
ykman openpgp reset -f     # wipes OpenPGP applet; restores PIN 123456 / Admin PIN 12345678
```

- Scope: **only** the OpenPGP applet. FIDO2/U2F, PIV, OATH, OTP credentials on the key are untouched.
- Do this for the live run too: it guarantees empty slots (no `Replace existing key?` prompts), default retry counters, and default PINs for the transfer step.
- If a previous provisioning left stubs in your keyring pointing at the now-wiped card (`ssb>` entries whose material no longer exists), they are inert; delete the dead key with `gpg --delete-secret-and-public-key <KEYID>` when convenient.

### 4.2 Ceremony directory and key generation (all local, offline-capable)

Use a dedicated GNUPGHOME so the ceremony is hermetic and portable to an air-gapped machine:

```bash
export GNUPGHOME="$HOME/.gnupg/working/<CARD-NAME>"   # or a ramdisk for a live ceremony
mkdir -m 700 -p "$GNUPGHOME"
printf 'keyid-format long\nwith-subkey-fingerprints\ncompliance gnupg\n' > "$GNUPGHOME/gpg.conf"
```

`compliance gnupg` is **required** for the ed448 primary (§2.2).

```bash
CERTIFY_PASS='<STRONG-PASSPHRASE>'     # single-quoted assignment; never re-type inside heredocs
IDENTITY='Paul Calnon (<COMMENT>) <overtoad.research@gmail.com>'

# Certify-only ed448 primary, no expiry:
printf '%s' "$CERTIFY_PASS" | gpg --batch --pinentry-mode loopback --passphrase-fd 0 \
    --quick-generate-key "$IDENTITY" ed448 cert never

KEYFP=$(gpg --list-keys --with-colons "$IDENTITY" | awk -F: '/^fpr:/ {print $10; exit}')

# Card-compatible subkeys (2y expiry; renewable from the offline primary):
for spec in 'ed25519 sign' 'ed25519 auth' 'cv25519 encr'; do
  printf '%s' "$CERTIFY_PASS" | gpg --batch --pinentry-mode loopback --passphrase-fd 0 \
      --quick-add-key "$KEYFP" $spec 2y
done

gpg -K    # expect: sec ed448 [C]; ssb ed25519 [S]; ssb ed25519 [A]; ssb cv25519 [E]
```

Interactive equivalent for the primary, if preferred: `gpg --expert --full-generate-key` → `(11) ECC (set your own capabilities)` → toggle `S` off (and `A` if offered) so only `Certify` remains → `Q` → choose the curve. Note the earlier interactive run in notes.txt skipped the toggling and produced an `[SCA]` primary — the quick-generate form above cannot make that mistake.

Ordering note: `gpg --edit-key` numbers subkeys by creation order, so the loop above yields `key 1`=[S] ed25519, `key 2`=[A] ed25519, `key 3`=[E] cv25519 — the numbering §4.4 uses.

### 4.3 Backups — mandatory, BEFORE any `keytocard`

`keytocard` + `save` **moves** the key: the on-disk copy becomes a stub. Without prior export you cannot load a second/replacement YubiKey.

```bash
cd "$GNUPGHOME"
printf '%s' "$CERTIFY_PASS" | gpg --batch --pinentry-mode loopback --passphrase-fd 0 \
    --armor --export-secret-keys    -o "$KEYFP-Certify.key"  "$KEYFP"
printf '%s' "$CERTIFY_PASS" | gpg --batch --pinentry-mode loopback --passphrase-fd 0 \
    --armor --export-secret-subkeys -o "$KEYFP-Subkeys.key"  "$KEYFP"
gpg --armor --export -o "$KEYFP-Public.asc" "$KEYFP"
ls openpgp-revocs.d/       # auto-generated revocation certificate — back it up too
```

Store `*.key` + the revocation certificate on ≥ 2 offline media (the LUKS-partition recipe already in notes.txt is good; paperkey optional for the primary). The public `.asc` can go anywhere.

### 4.4 Transfer subkeys to the card

Interactive canonical form (Admin PIN is factory `12345678` right after §4.1; the certify passphrase is also prompted):

```text
gpg --edit-key $KEYFP

gpg> key 1                  ← select ONLY the [S] subkey (ssb* marks selection)
gpg> keytocard
Please select where to store the key:
   (1) Signature key
   (3) Authentication key
Your selection? 1
gpg> key 1                  ← DESELECT before touching the next subkey
gpg> key 2                  ← the [A] subkey
gpg> keytocard
Your selection? 3
gpg> key 2
gpg> key 3                  ← the [E] subkey
gpg> keytocard
Your selection? 2
gpg> save                   ← writes stubs; the move becomes final
```

Rules learned the hard way:

- **Exactly one subkey selected per `keytocard`.** With zero or multiple `ssb*` selections the slot menu/behavior is wrong.
- Slot mapping is by capability: `[S]`→1, `[E]`→2, `[A]`→3. gpg only offers valid slots for the selected key.
- gpg auto-switches each slot's algorithm attribute (rsa2048 → ed25519/cv25519) during `keytocard`; no manual `key-attr` step is needed for card-supported algorithms. (For ed448 this auto-switch is precisely what fails — §2.1.)
- `save` is the point of no return (local key → stub). Quitting without saving after `keytocard` leaves both a card copy and the local key — do **not** rely on that as a backup strategy; use §4.3.
- Scripted transfer: use the §9 harness (`--command-fd` + `--no-tty` + stub pinentry). Do not resurrect the loopback-heredoc pattern (§2.3).

### 4.5 Verify

```bash
gpg --card-status | grep -E 'Key attributes|Signature key|Encryption key|Authentication key|counter'
#   Key attributes ...: ed25519 cv25519 ed25519      ← slots re-attributed
#   + the three subkey fingerprints on their slots

gpg -K "$KEYFP"          # all three subkeys now show 'ssb>' (card-backed) + card-no

echo test > /tmp/t.txt
gpg -u "$KEYFP" --armor --detach-sign -o /tmp/t.sig /tmp/t.txt    # prompts card PIN (123456 until §5)
gpg --verify /tmp/t.sig /tmp/t.txt                                 # 'Good signature'
gpg -r "$KEYFP" -e -o /tmp/t.gpg /tmp/t.txt && gpg -d /tmp/t.gpg   # decrypt via card
gpg --card-status | grep 'Signature counter'                        # incremented
```

### 4.6 Loading a second / replacement YubiKey (later)

Because the local copies became stubs, restore from backup into a scratch home and repeat §4.4 against the new card:

```bash
export GNUPGHOME=$(mktemp -d); chmod 700 "$GNUPGHOME"
printf 'compliance gnupg\n' > "$GNUPGHOME/gpg.conf"
gpg --import <backup>/$KEYFP-Certify.key      # or -Subkeys.key for a subkeys-only load
gpg --edit-key $KEYFP    # → §4.4
```

## 5. Live-run hardening checklist (deltas on top of §4)

Order matters — do these **after** §4.1's reset and **before** handing the key to daily use:

1. *(Optional)* `gpg --card-edit` → `admin` → `kdf-setup` — enable KDF PIN hashing **before** changing PINs, if wanted; some non-gpg tooling mishandles KDF, and it is reasonable to skip.
2. **Change PINs — interactively** (`ykman` prompts; avoids every §2.3 hazard):

   ```bash
   ykman openpgp access change-pin          # user PIN: 6–127 chars (used for sign/decrypt/auth)
   ykman openpgp access change-admin-pin    # admin PIN: 8–127 chars (64 chars verified workable)
   ```

   Do this **before** §4.4 on the live run so the true Admin PIN is what authorizes the transfer. gpg alternative: `gpg --card-edit` → `admin` → `passwd`.
3. Cardholder metadata (optional): `gpg --card-edit` → `admin` → `name` / `login` / `url` / `lang`. Keep `login`/public URL free of information you would not want readable from a lost key (readable without PIN).
4. **Touch policies** (after keys are on the card):

   ```bash
   ykman openpgp keys set-touch sig on      # or 'cached' (15 s grace) for signing bursts
   ykman openpgp keys set-touch dec on
   ykman openpgp keys set-touch aut on
   ```

   `on` = every operation needs a physical touch; recommended at least for `sig`. Note: any touch-required key is **incompatible with unattended/headless use** — see rule 8.
5. Publish/distribute the public key (`$KEYFP-Public.asc`), set owner trust on daily-driver keyrings (`gpg --edit-key … trust` → ultimate on your own machine).
6. Git signing switch-over (when adopting a key produced by this procedure):

   ```bash
   git config --global user.signingkey '<SIGNING-SUBKEY-FPR>!'    # '!' pins the exact subkey
   ```

   The trailing `!` avoids the ambiguous-resolution class documented in the [2026-07-16 migration note §3](JUNIPER_2026-07-16_JUNIPER-ECOSYSTEM_CODE-SIGNING-KEY-MIGRATION-STATUS.md).
7. SSH via the card (a bonus Option A enables — ed25519 auth subkeys are SSH-usable, ed448 never was):

   ```bash
   echo enable-ssh-support >> ~/.gnupg/gpg-agent.conf && gpgconf --kill gpg-agent
   gpg --export-ssh-key "$KEYFP"        # → 'ssh-ed25519 AAAA…' public line for authorized_keys
   # add the auth subkey's keygrip ($GNUPGHOME/private-keys-v1.d name) to ~/.gnupg/sshcontrol
   ```

8. **Standing automation rule is unchanged**: headless/agent sessions must use `git -c commit.gpgsign=false -c tag.gpgSign=false …` — a card-resident key cannot sign without the human (PIN and/or touch).
9. Store the ceremony GNUPGHOME (now containing the offline ed448 primary + stubs) offline per §4.3; remove it from the online host if the threat model calls for a true offline master.

## 6. Interoperability caveats

| Concern | Detail |
| --- | --- |
| **ed448 primary = v5 key format** | gpg emits ed448 keys as v5 (64-hex/32-byte fingerprint — observed live). Many parsers accept only v4. Impact is limited because *verifiers of your commits/artifacts only need the ed25519 signing subkey's signatures*, but any service that must ingest the **whole public key** (key servers, forges) may reject it. |
| **GitHub** | GitHub's GPG support has historically excluded ed448 (the 2026-07-16 note left this as an unconfirmed deferred probe; a Forgejo tracker for curve-448 keys confirms forge-side gaps are the norm). Uploading an Option-A public key (ed448 primary) may be refused even though the signatures themselves are ed25519. If GitHub "Verified" badges are required and the upload fails, fall back to Option B (ed25519 primary) or GitHub SSH-signing. Test before committing to Option A for GitHub-verified work|
| **OpenSSH** | No ed448 key type exists in OpenSSH — another reason the auth subkey is ed25519 (`ssh-ed25519` works everywhere). |
| **RFC 9580 (crypto-refresh) implementations** | gpg's ed448 uses the LibrePGP-lineage encoding behind `--compliance=gnupg`; RFC 9580-only stacks encode Ed448/X448 differently (dedicated v6 algorithm IDs). Cross-stack exchange of the ed448 primary may not round-trip. ed25519/cv25519 v4 material is universally understood. |

## 7. Troubleshooting

| Symptom                                                            | Cause                                                                                                   | Fix                                                                                            |
|--------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| `KEYTOCARD failed: Invalid value`                                  | Key algorithm not in the card's Algorithm Information list (ed448/x448 on any YubiKey)                  | Card-supported algorithm for card-resident subkeys (§3); Gnuk 2.2+ hardware for true 448       |
| `Cannot create Ed448 or Curve448 key without --compliance=gnupg`   | gpg 2.4.x generation gate                                                                               | `compliance gnupg` in gpg.conf or `--compliance=gnupg` on the command (§2.2)                   |
| Wrong-passphrase / `Bad PIN` from scripts that "should" be correct | Heredoc `$`-expansion / literal quotes mangling secrets; loopback answering both prompts with one value | §2.3 rules; interactive entry or the §9 stub                                                   |
| `Bad PIN` interactively; counters dropping                         | Wrong PIN, or PIN state uncertain after failed scripted changes                                         | Check `ykman openpgp info` counters; 0 admin retries = unblockable → `ykman openpgp reset`     |
| `cannot open '/dev/tty'` in scripted `--edit-key`                  | gpg wants a tty                                                                                         | add `--no-tty` with `--command-fd 0 --status-fd 1`                                             |
| `OpenPGP card not available` / card "in use"                       | Competing gpg-agent/scdaemon stacks or pcscd contention                                                 | §4.0 kill-others; replug; `gpgconf --kill scdaemon` then retry                                 |
| `keytocard` silently targets the wrong slot                        | Multiple (or zero) subkeys selected                                                                     | Exactly one `ssb*` per operation; deselect between subkeys (§4.4)                              |
| Old `ssb>` stubs for keys no longer on any card                    | Keyring stubs outlive `ykman openpgp reset`                                                             | `gpg --delete-secret-and-public-key <KEYID>` for retired throwaway ids                         |
| On-card `generate` only makes rsa2048 with combined SC key         | That is the card default and the on-card path's design                                                  | Don't use on-card generate for this design; generate locally + `keytocard` (whole point of §4) |

## 8. Evidence log (2026-08-03 validation run)

Executed via [`../util/ad-hoc/2026-08-03_yubikey_curve448_keytocard_e2e.bash`](../util/ad-hoc/2026-08-03_yubikey_curve448_keytocard_e2e.bash) phases `kill-others → reset-card → gen → repro → transfer → verify`, isolated GNUPGHOME `~/.gnupg-yktest`, throwaway secrets, factory PINs:

1. `reset-card`: applet wiped; defaults restored (`PIN: 123456 / Admin: 12345678`).
2. `gen`: `sec ed448/4E61AF8290580CB9 [C]` (v5, 64-hex fpr) + `ssb ed25519 [S]` + `ssb ed25519 [A]` + `ssb cv25519 [E]` + `ssb ed448 [S]` (repro probe) — required the §2.2 compliance line.
3. `repro`: `keytocard` of the ed448 subkey → pinentry served passphrase + Admin PIN correctly (4 launches) → **`SC_OP_FAILURE` / `gpg: KEYTOCARD failed: Invalid value`** — the reported error, reproduced with provably-correct credentials.
4. `transfer`: three `keytocard` ops + `save` → **success**; card attributes flipped `rsa2048 rsa2048 rsa2048` → `ed25519 cv25519 ed25519`; keyring shows 3 × `ssb>` with `card-no: 0006 24955323`.
5. `verify` (PIN cache flushed first): card-backed detach-sign → `Good signature`; card-backed decrypt roundtrip OK; `Signature counter: 1`.

Residue intentionally left for inspection (all throwaway): the loaded test subkeys on the card, `~/.gnupg-yktest/`, and the dead rsa2048 on-card-generate key `E003DB98C3BE9FD6` stubs in `~/.gnupg`. The live run's §4.1 reset clears the card; the rest cleans up with `rm -rf ~/.gnupg-yktest` and the §7 stub-deletion row.

## 9. Automation harness (for re-validation / CI-style reruns)

- [`../util/ad-hoc/2026-08-03_yubikey_curve448_keytocard_e2e.bash`](../util/ad-hoc/2026-08-03_yubikey_curve448_keytocard_e2e.bash) — phase-structured driver (`kill-others|reset-card|gen|repro|transfer|verify|status|clean|all`). Hermetic to `$YKTEST_HOME` (default `~/.gnupg-yktest`); never touches `~/.gnupg` keyrings; resets only the OpenPGP applet.
- [`../util/ad-hoc/2026-08-03_yubikey_test_pinentry.bash`](../util/ad-hoc/2026-08-03_yubikey_test_pinentry.bash) — Assuan pinentry stub answering Admin-PIN / user-PIN / passphrase prompts from env vars, classified by prompt text. **Throwaway-credential testing only** — it exists to make card ceremonies scriptable; a live key must never be provisioned with a stub pinentry holding real secrets in env/files.
- Scripting pattern that works headless (used by both repro and transfer): `printf '<edit-key answers>\n…' | gpg --no-tty --command-fd 0 --status-fd 1 --edit-key <FPR>` with the stub handling secret prompts. `--pinentry-mode loopback` is used **only** for single-secret operations (generation, export).

## 10. Sources

- Card evidence: `KEY-ATTR-INFO` + raw `00 CA 00 FA` APDU (this host, 2026-08-03) — §1.
- [Yubico — YubiKey 5.2.3 enhancements to OpenPGP 3.4](https://developers.yubico.com/PGP/YubiKey_5.2.3_Enhancements_to_OpenPGP_3.4.html) (curve support list: ends at curve25519).
- [Yubico — YubiKey Technical Manual, firmware overview](https://docs.yubico.com/hardware/yubikey/yk-tech-manual/yk5-firmware-overview.html) (5.7 feature scope).
- [GnuPG T5704 — Ed448/X448 as defined in draft-ietf-openpgp-crypto-refresh](https://dev.gnupg.org/T5704) (encoding/compliance background for §2.2/§6).
- [Forgejo #6268 — feat: add support for curve 448 gpg signing keys](https://codeberg.org/forgejo/forgejo/issues/6268) (forge-side ed448 gaps).
- [Gnuk](https://www.fsij.org/category/gnuk.html) — Ed448/X448-capable open token firmware (≥ 2.2), the §3.3 hardware alternative.
- [drduh YubiKey guide](https://github.com/drduh/YubiKey-Guide) — the ceremony/backup skeleton notes.txt was following; its patterns are preserved where they were sound.
