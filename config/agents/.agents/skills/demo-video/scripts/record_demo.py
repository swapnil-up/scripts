"""Template: record a continuous walkthrough video of a running web app.

Adapt the CONFIG block and the SEGMENTS in main() to your app. Everything else
(caption chips, smooth scrolling, console-error capture, video finalising) is
generic. Uses Python Playwright + Chromium.

Run:  python3 record_demo.py
Then: bash repair_and_verify.sh <raw.webm> <out.mp4>   # ALWAYS repair first
"""

import glob
import os
import time

from playwright.sync_api import sync_playwright

# ----------------------------------------------------------------- CONFIG
BASE = "http://localhost:5173"          # your app
OUT_DIR = "video"                        # put this in .gitignore
VIEWPORT = {"width": 1440, "height": 900}
CAPTIONS = True                          # floating caption chips


def log(*a):
    print(f"[{time.strftime('%H:%M:%S')}]", *a, flush=True)


# ----------------------------------------------------------------- helpers
def caption(page, text):
    """Show/swap/hide a floating caption chip. Survives SPA nav (lives on body)."""
    if not CAPTIONS:
        return
    if text is None:
        page.evaluate("() => { const c=document.getElementById('demo-caption');"
                      " if (c) c.style.opacity='0'; }")
        return
    page.evaluate(
        """(text) => {
        let c = document.getElementById('demo-caption');
        if (!c) {
            c = document.createElement('div');
            c.id = 'demo-caption';
            c.style.cssText = 'position:fixed;left:28px;bottom:28px;z-index:2147483647;'
              + 'display:flex;align-items:center;gap:10px;pointer-events:none;'
              + 'font-family:Georgia,serif;font-size:15px;color:#f2f0ec;'
              + 'background:rgba(17,16,15,.87);border:1px solid rgba(242,240,236,.16);'
              + 'padding:10px 18px;border-radius:999px;backdrop-filter:blur(8px);'
              + 'opacity:0;transition:opacity .45s ease;';
            const dot = document.createElement('span');
            dot.style.cssText = 'width:7px;height:7px;border-radius:50%;background:#67b8b8;'
              + 'flex:none;';
            const label = document.createElement('span');
            label.id = 'demo-caption-text';
            c.append(dot, label);
            document.body.appendChild(c);
        }
        const label = document.getElementById('demo-caption-text');
        if (label.textContent !== text) {
            c.style.opacity = '0';
            setTimeout(() => { label.textContent = text; c.style.opacity = '1'; }, 450);
        } else { c.style.opacity = '1'; }
    }""", text)
    page.wait_for_timeout(750)


def scroll_by(page, dy, steps=30, step_ms=32):
    """Smooth wheel scroll (looks natural in the recording)."""
    per = dy / steps
    for _ in range(steps):
        page.mouse.wheel(0, round(per))
        page.wait_for_timeout(step_ms)


def scroll_to(page, y, step_ms=30):
    cur = page.evaluate("window.scrollY")
    dy = y - cur
    scroll_by(page, dy, steps=max(8, min(60, int(abs(dy) / 22))), step_ms=step_ms)


# ----------------------------------------------------------------- main
def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for f in glob.glob(os.path.join(OUT_DIR, "*.webm")):  # clear partial takes
        os.remove(f)

    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox"])
        ctx = browser.new_context(
            viewport=VIEWPORT,
            record_video_dir=OUT_DIR,
            record_video_size=VIEWPORT,
            color_scheme="light",
            locale="en-US",
        )
        page = ctx.new_page()
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("dialog", lambda d: d.accept())        # auto-accept JS dialogs
        page.mouse.move(VIEWPORT["width"] // 2, VIEWPORT["height"] // 2)

        # ------- SEGMENTS: drive the flow on this one page -----------------
        log("home")
        page.goto(f"{BASE}/", wait_until="networkidle", timeout=45000)
        caption(page, "Design tour")
        page.wait_for_timeout(3200)                    # let hero animations settle

        # Pause at each section below the hero, then keep going.
        tops = page.evaluate(
            "() => Array.from(document.querySelectorAll('.section'))"
            ".map(e => e.getBoundingClientRect().top + window.scrollY - 90)")
        for y in tops[1:5]:
            scroll_to(page, y)
            page.wait_for_timeout(1000)

        log("second route")
        page.goto(f"{BASE}/gallery", wait_until="networkidle", timeout=45000)
        page.wait_for_timeout(1600)
        thumbs = page.locator("main li > button")      # PROBE these first!
        if thumbs.count():
            thumbs.first.hover()
            page.wait_for_timeout(800)
            thumbs.first.click()
            page.wait_for_timeout(1500)
            page.keyboard.press("Escape")
            page.wait_for_timeout(800)

        # ... add more routes/segments here ...

        caption(page, None)
        page.wait_for_timeout(700)
        video_path = page.video.path()
        ctx.close()
        browser.close()

    final = os.path.join(OUT_DIR, "demo.webm")
    os.replace(video_path, final)
    log("raw video:", final, os.path.getsize(final), "bytes")
    log("console errors:", len(errors))
    for e in errors[:8]:
        log("  ERR:", e[:200])
    log("NEXT: bash repair_and_verify.sh", final, "video/demo.mp4")


if __name__ == "__main__":
    main()
