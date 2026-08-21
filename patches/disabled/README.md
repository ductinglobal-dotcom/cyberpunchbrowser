# Parked patches (NOT applied by CI)

The `Apply stealth patches` step only globs `patches/*.patch`, so anything in
this `disabled/` subfolder is intentionally **not** applied. Kept for record /
future rebase. Verified against Chromium tag **151.0.7922.108** on 2026-08-21.

| Patch | Why parked |
|-------|-----------|
| `0002-strip-cdp-and-custom-v8-tokens.patch` | Target file `chrome/test/chromedriver/chrome/custom_v8_functions.cc` **does not exist** in v151, and it lives in the **ChromeDriver** binary (which this workflow does not build). It is also a **no-op for CDP/Playwright** drivers (they never inject `$cdc_`), which is how CyberPunch drives the browser. Nothing to gain. |
| `0004-canvas-noise-generator.patch` | `getImageData` moved to `BaseRenderingContext2D::getImageDataInternal` in `modules/canvas/canvas2d/base_rendering_context_2d.cc`; the ImageData buffer accessor drifted from the old `data()->View()` API and needs a careful v151 rebase to avoid a `-Werror` compile break 3h into the build. The CyberPunch wrapper already applies **per-profile canvas noise via JS injection**, so this is redundant for now. Rebase later if a native (non-JS) canvas tell is ever needed. |
| `0005-preserve-event-istrusted.patch` | Anchor (`is_trusted_(false)` in `core/dom/events/event.cc`) still exists in v151, so it *would* apply — but flipping the base `Event` ctor makes **page-created** events (`new Event()`, `dispatchEvent`) also report `isTrusted === true`, which real browsers report as `false`. That is itself a **detectable anomaly** (net-negative) and weakens the web security model. The correct approach is to flip trust only on the CDP `Input.dispatch*` path; the CyberPunch wrapper already handles input trust there. |

To re-enable one after a proper v151 rebase, move it back up to `patches/`.
