#!/usr/bin/env python3
"""Quick anti-detect smoke test for the built Chromium v151 Stealth binary.

Usage:
    python test_stealth.py --binary /path/to/chrome[.exe]

Drives the freshly built binary through the public detector pages and dumps
screenshots + a small JSON verdict so you can eyeball webdriver / WebGL /
canvas / isTrusted after each build.
"""
import argparse
import asyncio
import json
import os
import sys

try:
    from playwright.async_api import async_playwright
except ImportError:
    sys.exit("Install Playwright first:  pip install playwright")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36")


async def run(binary: str, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path=binary,
            headless=False,
            args=[
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        ctx = await browser.new_context(
            user_agent=UA,
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
            timezone_id="America/New_York",
        )
        page = await ctx.new_page()

        # 1) In-page probes for the exact signals the 5 patches target.
        await page.goto("about:blank")
        probe = await page.evaluate(
            """() => {
                const g = document.createElement('canvas').getContext('webgl');
                const ext = g && g.getExtension('WEBGL_debug_renderer_info');
                const ev = new Event('x');  // page-made event: real browser => isTrusted false
                return {
                    webdriver: navigator.webdriver,
                    webglVendor: ext ? g.getParameter(ext.UNMASKED_VENDOR_WEBGL) : null,
                    webglRenderer: ext ? g.getParameter(ext.UNMASKED_RENDERER_WEBGL) : null,
                    syntheticEventIsTrusted: ev.isTrusted,
                };
            }"""
        )

        # 2) Canvas hash: two reads should differ from a vanilla render if noise is on.
        canvas_hash = await page.evaluate(
            """() => {
                const c = document.createElement('canvas');
                c.width = 200; c.height = 50;
                const x = c.getContext('2d');
                x.textBaseline = 'top'; x.font = '14px Arial';
                x.fillStyle = '#f60'; x.fillRect(0, 0, 200, 50);
                x.fillStyle = '#069'; x.fillText('stealth-canvas-☢', 2, 2);
                return c.toDataURL().slice(-32);
            }"""
        )

        verdict = {"probe": probe, "canvasTail": canvas_hash}
        print(json.dumps(verdict, indent=2))
        with open(os.path.join(out_dir, "verdict.json"), "w", encoding="utf-8") as fh:
            json.dump(verdict, fh, indent=2)

        # 3) Visual detectors.
        for name, url in [
            ("sannysoft", "https://bot.sannysoft.com/"),
            ("webgl", "https://browserleaks.com/webgl"),
            ("canvas", "https://browserleaks.com/canvas"),
        ]:
            try:
                await page.goto(url, wait_until="networkidle", timeout=60000)
                await page.screenshot(
                    path=os.path.join(out_dir, f"{name}.png"), full_page=True)
                print(f"[ok] {name} -> {name}.png")
            except Exception as e:  # noqa: BLE001
                print(f"[warn] {name}: {e}")

        await browser.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--binary", required=True, help="path to built chrome / chrome.exe")
    ap.add_argument("--out", default="stealth_test_out", help="screenshot output dir")
    args = ap.parse_args()
    if not os.path.exists(args.binary):
        sys.exit(f"Binary not found: {args.binary}")
    asyncio.run(run(args.binary, args.out))
