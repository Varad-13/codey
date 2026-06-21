"""
Web browser tool powered by Playwright.

All browser operations run in a dedicated background thread so Playwright's
internal asyncio event loop never touches the main thread — critical for
prompt_toolkit compatibility on Python 3.12+.

The browser opens in headed mode by default so the user can watch.
Set CODEY_WEB_HEADLESS=true to run invisibly.
"""

import atexit
import base64
import concurrent.futures
import os

# Single-threaded executor: all Playwright work happens here, never in main thread
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1, thread_name_prefix="codey-playwright")

# Browser state — owned exclusively by the executor thread
_state: dict = {}


def _ensure_chromium() -> None:
    import subprocess
    import sys
    print("Playwright: Chromium not found — downloading now (one-time ~120 MB)...")
    result = subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "Could not auto-install Chromium.\n"
            "Run manually: playwright install chromium"
        )


def _init_browser() -> None:
    """Initialize Playwright inside the executor thread."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError("Playwright is not installed.\nRun: pip install playwright")

    headless = os.getenv("CODEY_WEB_HEADLESS", "false").lower() == "true"

    def _launch():
        pw = sync_playwright().__enter__()
        browser = pw.chromium.launch(headless=headless)
        page = browser.new_page()
        _state['pw'] = pw
        _state['browser'] = browser
        _state['page'] = page

    try:
        _launch()
    except Exception as exc:
        err = str(exc).lower()
        if any(k in err for k in ("executable", "not found", "install playwright", "browser")):
            _ensure_chromium()
            _launch()
        else:
            raise


def _get_page():
    """Return the live Page; initialize browser on first call. Runs in executor thread."""
    if 'page' not in _state:
        _init_browser()
    return _state['page']


def _cleanup_in_thread() -> None:
    try:
        if _state.get('browser'):
            _state['browser'].close()
        if _state.get('pw'):
            _state['pw'].__exit__(None, None, None)
    except Exception:
        pass
    _state.clear()


def _cleanup() -> None:
    """atexit handler — runs in main thread, delegates to executor."""
    try:
        _executor.submit(_cleanup_in_thread).result(timeout=5)
    except Exception:
        pass
    _executor.shutdown(wait=False)


atexit.register(_cleanup)


# ── Tool result sentinel for images ─────────────────────────────────────────

def _img_result(page, label: str) -> dict:
    png_bytes = page.screenshot(full_page=False)
    b64 = base64.b64encode(png_bytes).decode()
    return {
        "__image__": f"data:image/png;base64,{b64}",
        "text": label,
    }


def _web_action(action, url, selector, text, js, direction, amount, timeout):
    """All browser work runs here — inside the executor thread."""
    if action == "close":
        _cleanup_in_thread()
        return "Browser closed."

    page = _get_page()

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
    try:
        return _executor.submit(
            _web_action, action, url, selector, text, js, direction, amount, timeout
        ).result()
    except RuntimeError as e:
        return str(e)
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
