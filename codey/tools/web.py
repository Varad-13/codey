"""
Web browser tool powered by Playwright.

Install once:
    pip install playwright
    playwright install chromium

The browser opens in headed mode by default so the user can watch.
Set CODEY_WEB_HEADLESS=true to run invisibly.
"""

import atexit
import base64
import os
import time
from pathlib import Path

_pw_ctx = None   # playwright instance
_browser = None
_page = None


def _get_page():
    global _pw_ctx, _browser, _page
    if _page is not None:
        return _page
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError(
            "Playwright is not installed.\n"
            "Run: pip install playwright && playwright install chromium"
        )
    headless = os.getenv("CODEY_WEB_HEADLESS", "false").lower() == "true"
    _pw_ctx = sync_playwright().__enter__()
    _browser = _pw_ctx.chromium.launch(headless=headless)
    _page = _browser.new_page()
    atexit.register(_cleanup)
    return _page


def _cleanup():
    global _pw_ctx, _browser, _page
    try:
        if _browser:
            _browser.close()
        if _pw_ctx:
            _pw_ctx.__exit__(None, None, None)
    except Exception:
        pass
    _pw_ctx = _browser = _page = None


# ── Tool result sentinel for images ─────────────────────────────────────────
# chat_runner detects dicts with "__image__" and sends them as multimodal
# content blocks so vision models can actually see the screenshot.

def _img_result(page, label: str) -> dict:
    shots_dir = Path(os.getcwd()) / ".codey_screenshots"
    shots_dir.mkdir(exist_ok=True)
    path = shots_dir / f"screenshot_{int(time.time())}.png"
    page.screenshot(path=str(path), full_page=False)
    b64 = base64.b64encode(path.read_bytes()).decode()
    return {
        "__image__": f"data:image/png;base64,{b64}",
        "text": f"{label} — saved to {path}",
    }


# ── Public tool function ─────────────────────────────────────────────────────

def web(
    action: str,
    url: str = "",
    selector: str = "",
    text: str = "",
    js: str = "",
    direction: str = "down",
    amount: int = 500,
    timeout: int = 10000,
):
    """
    Control a local Chromium browser.

    action=navigate   url=<url>                    → load page, return title
    action=screenshot                               → capture viewport (image)
    action=get_text                                 → visible body text
    action=get_html                                 → full page HTML
    action=click      selector=<css>               → click element
    action=fill       selector=<css>  text=<text>  → type into input
    action=scroll     direction=up|down amount=<px> → scroll
    action=eval       js=<expression>              → run JavaScript, return value
    action=wait       selector=<css>               → wait for element to appear
    action=close                                   → shut down browser
    """
    if action == "close":
        _cleanup()
        return "Browser closed."

    try:
        page = _get_page()
    except RuntimeError as e:
        return str(e)

    try:
        if action == "navigate":
            if not url:
                return "Error: 'url' is required for action=navigate."
            resp = page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            status = resp.status if resp else "unknown"
            return f"Navigated to {url} — HTTP {status}, title: \"{page.title()}\""

        elif action == "screenshot":
            return _img_result(page, f"Screenshot of {page.url}")

        elif action == "get_text":
            return page.inner_text("body")

        elif action == "get_html":
            return page.content()

        elif action == "click":
            if not selector:
                return "Error: 'selector' is required for action=click."
            page.click(selector, timeout=timeout)
            return f"Clicked '{selector}'. Current URL: {page.url}"

        elif action == "fill":
            if not selector:
                return "Error: 'selector' is required for action=fill."
            page.fill(selector, text, timeout=timeout)
            return f"Filled '{selector}' with provided text."

        elif action == "scroll":
            px = amount if direction == "down" else -amount
            page.evaluate(f"window.scrollBy(0, {px})")
            return f"Scrolled {direction} {abs(px)}px."

        elif action == "eval":
            if not js:
                return "Error: 'js' is required for action=eval."
            result = page.evaluate(js)
            return str(result)

        elif action == "wait":
            if not selector:
                return "Error: 'selector' is required for action=wait."
            page.wait_for_selector(selector, timeout=timeout)
            return f"Element '{selector}' is visible."

        else:
            return (
                f"Unknown action '{action}'. "
                "Valid: navigate, screenshot, get_text, get_html, click, fill, scroll, eval, wait, close."
            )

    except Exception as e:
        return f"Browser error ({action}): {e}"


schema = {
    "type": "function",
    "function": {
        "name": "web",
        "description": (
            "Control a local Chromium browser. "
            "Use navigate to open pages, screenshot to see what's on screen, "
            "get_text/get_html to read content, click/fill to interact with forms, "
            "scroll to reveal more content, eval to run JavaScript. "
            "Screenshots are returned as images that you can see directly."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["navigate", "screenshot", "get_text", "get_html",
                             "click", "fill", "scroll", "eval", "wait", "close"],
                    "description": "Operation to perform."
                },
                "url": {
                    "type": "string",
                    "description": "URL to navigate to. Required for action=navigate."
                },
                "selector": {
                    "type": "string",
                    "description": "CSS selector for the target element. Required for click, fill, wait."
                },
                "text": {
                    "type": "string",
                    "description": "Text to type into an input. Used with action=fill."
                },
                "js": {
                    "type": "string",
                    "description": "JavaScript expression to evaluate. Used with action=eval."
                },
                "direction": {
                    "type": "string",
                    "enum": ["up", "down"],
                    "description": "Scroll direction. Default: down."
                },
                "amount": {
                    "type": "number",
                    "description": "Pixels to scroll. Default: 500."
                },
                "timeout": {
                    "type": "number",
                    "description": "Max milliseconds to wait for an element or navigation. Default: 10000."
                }
            },
            "required": ["action"],
            "additionalProperties": False
        }
    }
}
