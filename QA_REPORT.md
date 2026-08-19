# QA Report — Patchset review (v151 Stealth)

Review of the 5 C++ patches in `Huong_Dan_Build_Chromium_v151_Stealth.md`
against real Chromium source, done as a Chromium/anti-detect engineer.
The `patches/*.patch` files in this repo are the **corrected** versions.

| # | Patch | Verdict on the doc | Fix applied here |
|---|-------|--------------------|------------------|
| 01 | hide navigator.webdriver | ✅ Correct & minimal | Kept as-is. Context plausible; verify offset on the exact tag. |
| 02 | strip `$cdc_` token | ❌ **Would not compile** | Doc *added* a 2nd `const char kCustomObjectPrefix[]` → C++ redefinition. Rewrote as a single-line value replacement. Also: this file is in **chromedriver**, not chrome.exe — irrelevant to Playwright/CDP. |
| 03 | spoof WebGL renderer | ❌ **No-op + fabricated context** | Doc's `-`/`+` lines were identical (git apply rejects). Real Blink reads the driver via `GetUnmaskedString`, not a hardcoded switch. Rewrote to intercept `GetUnmaskedString`; **needs source verification** of the helper signature on v151. |
| 04 | canvas noise | ⚠️ Works but weak | Doc XORs a constant 0x01 → deterministic hash (does NOT vary per profile as its own checklist claims). Kept + documented how to seed per-profile; flagged the `data()->View()` accessor + `toDataURL` coverage to verify. Moved noise to the blue channel to match the stated intent. |
| 05 | force isTrusted | ⚠️ Over-broad + risky | Setting `is_trusted_=true` in the base `Event` ctor makes **page-created** events also report `isTrusted=true` (real browsers say false) → itself a detectable tell + a security-model change. Also the file path is `core/dom/events/event.cc` (doc said `core/events/event.cc`). Kept with a loud warning; recommend flipping only on the CDP input path instead. |

## DECISIONS TAKEN (phiên 46 — user delegated "tùy ý làm, chuẩn như v146")

1. **Target OS = Windows x64.** `args.gn` now sets `target_os="win"`,
   `target_cpu="x64"`; CI runs on `windows-2022` and packages `chrome.exe` +
   the same runtime file set as the v146 cache.
2. **Tag = `151.0.7922.108`** (the CloakHQ v151 release you linked) — the
   workflow_dispatch default.
3. **WebGL (Patch 03) = guarded fallback, not a hard pin.** For v146 parity the
   real GPU passes through (so the wrapper's per-profile WebGL spoof stays
   authoritative); a discrete GPU is substituted ONLY when the real renderer is
   software (SwiftShader/llvmpipe/Mesa). This keeps per-profile realism.
4. **Runner size caveat.** A from-scratch Windows Chromium build needs ~100+ GB
   and many hours; GitHub-hosted runners give ~85 GB. If the hosted build fails
   on disk, use a self-hosted or larger runner. The workflow shallow-syncs
   (`--no-history`) and frees preinstalled SDKs to buy headroom.

## Original blockers (now resolved above)

1. **Target OS mismatch.** The CI builds a **Linux** `chrome` ELF, but the
   CyberPunch tool runs on **Windows** and needs `chrome.exe`. A Windows
   build needs a `windows-2022` runner + VS 2022 + Windows SDK and
   `target_os="win"`. Confirm which OS you want; I wired the Linux path and
   left the Windows switch commented in `args.gn`.

2. **Exact v151 tag.** The doc's default `151.0.7500.0` is a placeholder.
   The real published tag is **`151.0.7922.108`** (from the CloakHQ release
   you linked). All patch offsets must be verified against that exact tag —
   the `@@` hunks here are best-effort and the CI uses `git apply --3way`
   to absorb small drift, but Patch 03/04 will likely need a manual rebase.

3. **No local Chromium source tree.** NHIỆM VỤ 2 ("apply on local v151 source")
   cannot run on this machine — there is no `depot_tools` / `src/` checkout
   (a full Chromium tree is ~100 GB + hours to sync). The GitHub Actions
   pipeline (NHIỆM VỤ 3) is the viable place to apply/verify offsets. Run it
   with `workflow_dispatch` once this repo is pushed to GitHub.

4. **WebGL GPU string.** Patch 03 hardcodes an RTX 3060 / NVIDIA string.
   Set this to whatever your fleet should look like (ideally matched to the
   fingerprint DB the CyberPunch tool already ships).
