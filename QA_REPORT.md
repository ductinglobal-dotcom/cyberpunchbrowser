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

## LOG LỖI (CI runs)

| Ngày | Lỗi | Nguyên nhân | Cách xử lý | Trạng thái |
|------|-----|-------------|-----------|------------|
| 2026-08-20 | Run #1 chết ở step "Apply stealth patches": `cd /c/c/src: No such file or directory` (exit 1). Fetch 2h54m đã OK, source ở `C:\c\src`. | Chỉ mỗi step này dùng `shell: bash` + path Unix `/c/c/src`; git-bash trên runner windows-2022 không map được đường dẫn đó (các step khác dùng cmd/pwsh + `C:\c\src` nên OK). | Viết lại step sang `shell: pwsh`, `Set-Location C:\c\src` (path native đồng bộ các step khác), thêm `C:\depot_tools` vào PATH cho git, apply theo chuỗi fallback (`--whitespace=fix` → `--recount` → `--3way` → `-C1`) chịu lệch dòng. | ✅ Đã fix ở run #2 |
| 2026-08-20 | Run #2 chết ở step "Apply": `Set-Location: Cannot find path 'C:\c\src' because it does not exist`. Fetch xanh 2h40m nhưng `C:\c\src` KHÔNG tồn tại. | `mkdir C:\c && cd C:\c`: nếu `mkdir` fail thì `&&` chặn `cd` (cmd không fail-fast), `fetch` đổ cây Chromium vào workspace ổ D: chứ không phải `C:\c\src`. Bước Fetch vẫn "xanh" vì cmd chỉ lấy exit code dòng cuối. | (a) Bước Free-up chọn ổ C:/D: nhiều chỗ nhất, ghi `CHROMIUM_ROOT`/`CHROMIUM_SRC` ra `$GITHUB_ENV`; (b) Fetch fail-fast `\|\| exit /b 1` + verify `%CHROMIUM_SRC%\BUILD.gn` (fail ngay, không đợi 3h) + in disk free; (c) Apply/GN/Compile/Package đọc path từ `CHROMIUM_SRC` (bỏ hết `C:\c\src` hardcode); (d) dọn đĩa mạnh hơn. | ✅ Đã fix (xác nhận run #3: đã qua Free-up + path đúng) |
| 2026-08-21 | Run #3 chết ở step "Fetch Chromium source" sau ~1h5m (fail-fast hoạt động): `curl 56 schannel: server closed abruptly (missing close_notify)` → `fetch-pack: unexpected disconnect` → `fatal: early EOF` → `invalid index-pack output`. Xảy ra trong `gclient sync --nohooks --no-history`. | KHÔNG phải lỗi repo/code. Là bug kinh điển của **schannel** (TLS mặc định của git trên Windows) khi tải một mạch nhiều GB: server đóng kết nối đột ngột giữa dòng → git bỏ dở. Workflow cũ tải 1 lần, đứt là chết, không retry. Lỗi transient nhưng lặp lại vì fetch quá lớn. | (a) `git config --global http.sslBackend openssl` (né đúng bug schannel) + `http.version HTTP/1.1` (không HTTP/2 stream-reset); (b) `http.postBuffer 1.5GB` + `lowSpeedLimit 0`/`lowSpeedTime 999999` (không abort khi chậm) + `core.compression 0`; (c) BỎ `fetch`, thay bằng `gclient config --spec $spec` + **vòng lặp retry `gclient sync` 6 lần**; (d) giữ verify `BUILD.gn` + in disk free. | ⚠️ Fix TLS+retry OK nhưng (c) gây lỗi mới ở run #4 (xem dưới) |
| 2026-08-21 | Run #4 chết ngay đầu step "Fetch": `Error: There is a syntax error in .gclient / Line #1, character 37: "solutions = [{ name: src, url: ..., custom_deps: {}, custom_vars: {}, },]"`. Cả 6 retry đều fail theo. | **Regression do fix #3**: viết `.gclient` bằng `gclient config --spec $spec`. Khi PowerShell truyền `$spec` (chứa nháy kép) sang native `gclient.bat`, **nháy kép bị nuốt** → file `.gclient` thành `name: src` (không nháy) → Python parse báo syntax error. File config hỏng nên mọi retry vô nghĩa. Các fix trước (Free-up/path/depot_tools/TLS) vẫn ĐÚNG. | KHÔNG tự viết spec nữa. Dùng lại `fetch --nohooks --no-history chromium` để **nó tự sinh `.gclient` chuẩn** (nháy kép nguyên vẹn), nhưng gọi fetch **đúng 1 lần có canh `Test-Path .gclient`** (tránh lỗi "đã tồn tại" khi re-run) → giữ retry: nếu fetch đứt mạng thì `.gclient` vẫn còn, vòng lặp `gclient sync` 8 lần resume tiếp. Giữ nguyên hardening TLS của fix #3. | ✅ Đã fix (chờ run #5 xác nhận) |
