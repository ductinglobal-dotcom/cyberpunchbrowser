# Chromium v151 Stealth (CloakBrowser alternative)

Self-built anti-detect Chromium — a free alternative to the license-gated
CloakBrowser Pro v151 binary. Instead of buying a Pro key, this repo carries
the C++ source patches and a CI pipeline that compiles a stealth Chromium
from the official v151 source.

## Layout
```
patches/                         5 unified-diff C++ patches (corrected — see QA_REPORT.md)
  0001-hide-navigator-webdriver.patch
  0002-strip-cdp-and-custom-v8-tokens.patch
  0003-spoof-webgl-renderer.patch
  0004-canvas-noise-generator.patch
  0005-preserve-event-istrusted.patch
args.gn                          GN build args (production, no Google telemetry)
.github/workflows/build-stealth-chromium.yml   GitHub Actions build (Linux)
test_stealth.py                  post-build anti-detect smoke test (Playwright)
QA_REPORT.md                     per-patch review + blockers needing your decision
```

## What each patch does
1. `navigator.webdriver` → always false (Blink level)
2. ChromeDriver `$cdc_` marker → benign prefix (chromedriver only)
3. WebGL UNMASKED vendor/renderer → spoofed, never leak SwiftShader
4. Canvas `getImageData` → invisible sub-pixel noise (breaks hash FP)
5. `event.isTrusted` → true for CDP input (see WARNING in QA_REPORT #05)

## How to build (CI — recommended)
1. Push this folder to a GitHub repo.
2. Actions → **Build Chromium v151 Stealth** → Run workflow → tag `151.0.7922.108`.
3. Download the `chromium-v151-stealth` artifact when the (long) build finishes.

> Local build is NOT possible on this machine: no depot_tools/gn/gclient, and a
> full Chromium tree is ~100 GB. See QA_REPORT.md #3.

## After build
```
python test_stealth.py --binary path/to/chrome[.exe]
```
Check `stealth_test_out/verdict.json` + the screenshots against QA_REPORT's
expected results, then point the CyberPunch tool at the binary via
`CLOAKBROWSER_BINARY_PATH` (custom kernel) — no license key needed.

## DECISIONS (phiên 46) — see QA_REPORT.md
- **Target OS = Windows x64** → CI on `windows-2022`, packages `chrome.exe`.
- **Tag = `151.0.7922.108`** (workflow default).
- **WebGL = guarded fallback** (keep real GPU for per-profile spoof; only mask
  software renderers) — v146 parity.
- ⚠️ Windows Chromium build is disk/time-heavy (~100+ GB); hosted runners may
  need to be swapped for a self-hosted/larger runner.
