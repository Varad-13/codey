# codey/update.py
"""
Self-update mechanism for Codey.

Distribution is GitHub Releases only (no PyPI). We poll
https://api.github.com/repos/Varad-13/codey/releases/latest with a short
timeout and a User-Agent header (60 req/hr/IP is fine for unauth use).

All network code swallows every exception: an update check must never
crash the CLI. The CLI can be started with CODEY_NO_UPDATE_CHECK set
to disable checks entirely.

Only stdlib is used at runtime. packaging.version is used if available,
otherwise a tiny tuple-comparison helper handles numeric versions.
"""

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
import urllib.error
from pathlib import Path

# ---------------------------------------------------------------------------
# Current version
# ---------------------------------------------------------------------------
_CURRENT_VERSION_CACHE = None


def _resolve_current_version():
    """Determine the running version. Tries, in order:

    0. codey/__init__.py.__version__  (authoritative for source-tree runs)
    1. importlib.metadata.version("codey")  (works once installed)
    2. Reading version="..." from setup.py sitting next to the installed
       package directory.
    3. Falling back to "0.0.0".
    """
    global _CURRENT_VERSION_CACHE
    if _CURRENT_VERSION_CACHE is not None:
        return _CURRENT_VERSION_CACHE

    # 0. Trust codey/__init__.py.__version__ if the package we're running
    #    from defines it. This keeps editable / source-tree installs honest
    #    even when an older copy is also importable via importlib.metadata.
    try:
        from codey import __version__ as _pkg_version  # type: ignore[import]
        if _pkg_version:
            _CURRENT_VERSION_CACHE = _pkg_version
            return _pkg_version
    except Exception:
        pass

    # 1. importlib.metadata (Python 3.8+ has it; for 3.7, import backport via
    #    importlib.metadata's own shim if present)
    try:
        try:
            from importlib import metadata as importlib_metadata  # py3.8+
        except ImportError:  # pragma: no cover
            import importlib_metadata  # type: ignore[import]
        v = importlib_metadata.version("codey")
        if v:
            _CURRENT_VERSION_CACHE = v
            return v
    except Exception:
        pass

    # 2. Fall back to setup.py next to the installed package directory
    try:
        pkg_file = Path(__file__).resolve()
        setup_py = pkg_file.parent.parent / "setup.py"
        if setup_py.is_file():
            text = setup_py.read_text(encoding="utf-8", errors="ignore")
            for line in text.splitlines():
                line = line.strip()
                if line.startswith("version="):
                    # version='0.4.0',
                    val = line.split("=", 1)[1].strip().rstrip(",")
                    if val.startswith(("'", '"')) and val.endswith(("'", '"')) and len(val) >= 2:
                        val = val[1:-1]
                    if val:
                        _CURRENT_VERSION_CACHE = val
                        return val
    except Exception:
        pass

    # 3. Last resort
    _CURRENT_VERSION_CACHE = "0.0.0"
    return _CURRENT_VERSION_CACHE


CURRENT_VERSION = _resolve_current_version()


# ---------------------------------------------------------------------------
# Cache path
# ---------------------------------------------------------------------------
def _cache_path():
    """Return ~/.cache/codey/update_check.json (or OS-appropriate location).

    Uses platformdirs if it's installed (it isn't a hard dep, but if some
    other dep dragged it in, prefer the proper location).
    """
    try:
        import platformdirs  # type: ignore[import]

        base = Path(platformdirs.user_cache_dir("codey", "codey"))
    except Exception:
        if sys.platform.startswith("win"):
            base = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local")) / "codey"
        else:
            base = Path.home() / ".cache" / "codey"
    p = base / "update_check.json"
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return p


_CACHE_PATH = _cache_path()
CACHE_TTL_SECONDS = 6 * 3600

GITHUB_RELEASES_URL = "https://api.github.com/repos/Varad-13/codey/releases/latest"
GITHUB_RELEASES_PAGE = "https://github.com/Varad-13/codey/releases"


# ---------------------------------------------------------------------------
# Version comparison
# ---------------------------------------------------------------------------
def _parse_version(s):
    """Return a tuple of ints for numeric comparison.

    Splits on '.' and ignores non-numeric suffixes so '0.4.0a1' -> (0, 4, 0).
    Missing components become 0.
    """
    out = []
    for part in str(s).split("."):
        # take leading digits only
        digits = ""
        for ch in part:
            if ch.isdigit():
                digits += ch
            else:
                break
        out.append(int(digits) if digits else 0)
    while len(out) < 3:
        out.append(0)
    return tuple(out)


def _is_newer(remote, current):
    """Return True if `remote` is strictly newer than `current`.

    Uses packaging.version.Version if it's importable, otherwise falls back
    to the simple _parse_version tuple comparison.
    """
    if not remote:
        return False
    if not current:
        return True
    try:
        from packaging.version import Version  # type: ignore[import]

        try:
            return Version(remote) > Version(current)
        except Exception:
            return _parse_version(remote) > _parse_version(current)
    except Exception:
        return _parse_version(remote) > _parse_version(current)


# ---------------------------------------------------------------------------
# stderr helper (notices must not tangle with REPL stdout)
# ---------------------------------------------------------------------------
def _print(*args, **kwargs):
    kwargs.setdefault("file", sys.stderr)
    try:
        print(*args, **kwargs)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------
def _read_cache():
    try:
        with open(_CACHE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception:
        return None
    return None


def _write_cache(payload):
    try:
        _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = str(_CACHE_PATH) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f)
        os.replace(tmp, str(_CACHE_PATH))
    except Exception:
        pass


def _cache_fresh(cached):
    if not cached:
        return False
    checked_at = cached.get("checked_at")
    if not isinstance(checked_at, (int, float)):
        return False
    return (time.time() - float(checked_at)) < CACHE_TTL_SECONDS


def _env_disabled():
    val = os.environ.get("CODEY_NO_UPDATE_CHECK", "")
    if not val:
        return False
    return val.strip().lower() in ("1", "true", "yes", "on")


# ---------------------------------------------------------------------------
# Network: GitHub release lookup
# ---------------------------------------------------------------------------
def _fetch_latest_release():
    """Return parsed JSON dict from the GitHub API or None on any failure."""
    req = urllib.request.Request(
        GITHUB_RELEASES_URL,
        headers={
            "User-Agent": "codey-cli",
            "Accept": "application/vnd.github+json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            raw = resp.read()
        try:
            return json.loads(raw.decode("utf-8", errors="ignore"))
        except Exception:
            return None
    except Exception:
        return None


def _extract_wheel_asset(release):
    """Find the wheel asset for `tag_name` in `release["assets"]`.

    Returns (asset_dict, wheel_filename) or (None, None).
    """
    tag = (release or {}).get("tag_name", "") or ""
    version = tag.lstrip("v").strip()
    if not version:
        return None, None
    expected = "codey-{0}-py3-none-any.whl".format(version)
    for asset in (release.get("assets") or []):
        if (asset.get("name") or "").strip() == expected:
            return asset, expected
    # Fallback: any codey-*py3-none-any.whl
    for asset in (release.get("assets") or []):
        name = asset.get("name") or ""
        if name.startswith("codey-") and name.endswith("-py3-none-any.whl"):
            return asset, name
    return None, None


def _extract_sha256(asset):
    """Pull the sha256 hex digest out of an asset's `digest` field.

    digest format is 'sha256:<hex>'. Returns the hex string or None.
    """
    if not asset:
        return None
    digest = (asset.get("digest") or "").strip()
    if digest.startswith("sha256:"):
        return digest.split(":", 1)[1].strip() or None
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def check_for_update(force=False):
    """Return update info dict if a newer release is available, else None.

    Cache results (including None) for CACHE_TTL_SECONDS unless `force=True`.
    Set CODEY_NO_UPDATE_CHECK to disable network checks entirely.
    """
    if _env_disabled():
        return None

    cached = _read_cache()
    if not force and _cache_fresh(cached):
        cached_info = cached.get("info")
        if cached_info is None:
            return None
        # Validate cached info: if cached version is no longer newer than
        # current, ignore the cached "available" payload.
        if _is_newer(cached_info.get("version", ""), CURRENT_VERSION):
            return cached_info
        # Otherwise fall through to a fresh check.

    release = _fetch_latest_release()
    if not release:
        # Cache the failure so we don't hammer the API
        _write_cache({"checked_at": time.time(), "info": None})
        return None

    tag = (release.get("tag_name") or "").lstrip("v").strip()
    if not tag or not _is_newer(tag, CURRENT_VERSION):
        _write_cache({"checked_at": time.time(), "info": None})
        return None

    asset, wheel_name = _extract_wheel_asset(release)
    if not asset:
        # No wheel for the new version; cache nothing useful but don't claim
        # there's an update either.
        _write_cache({"checked_at": time.time(), "info": None})
        return None

    wheel_url = asset.get("browser_download_url") or ""
    wheel_sha256 = _extract_sha256(asset)
    html_url = release.get("html_url") or (
        "{0}/tag/v{1}".format(GITHUB_RELEASES_PAGE.rstrip("/"), tag)
    )

    info = {
        "version": tag,
        "url": html_url,
        "notes": release.get("body") or "",
        "wheel_url": wheel_url,
        "wheel_sha256": wheel_sha256,
        "published_at": release.get("published_at") or "",
    }
    _write_cache({"checked_at": time.time(), "info": info})
    return info


# ---------------------------------------------------------------------------
# Notice formatting (ONE LINE; stderr; ASCII-safe)
#
# We deliberately use ASCII (->, --) instead of Unicode arrow / em-dash so
# the notice prints cleanly on Windows consoles whose default encoding is
# cp1252. ANSI color codes are still emitted; terminals that don't render
# them will show literal escape sequences, which is harmless.
# ---------------------------------------------------------------------------
_YELLOW = "\033[33m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_RESET = "\033[0m"


def format_update_notice(info):
    """Return a single-line ANSI-colored update notice."""
    new_v = (info or {}).get("version", "?")
    return (
        "{bold}{yellow}Update available: v{cur} -> v{new}{reset}"
        " {dim}-- run 'codey update' to upgrade{reset}"
    ).format(
        bold=_BOLD,
        yellow=_YELLOW,
        cur=CURRENT_VERSION,
        new=new_v,
        reset=_RESET,
        dim=_DIM,
    )


# ---------------------------------------------------------------------------
# Update flow
# ---------------------------------------------------------------------------
def _print_release_notes(info):
    notes = (info or {}).get("notes") or ""
    lines = notes.splitlines()
    head = lines[:15]
    if len(lines) > 15:
        head.append("...")
    _print("")
    _print("Release notes for v{0}:".format(info.get("version", "?")))
    for line in head:
        _print("  {0}".format(line))
    _print("")


def perform_update(info=None):
    """Download and install the latest wheel. Returns (ok: bool, message: str).

    If `info` is None, runs check_for_update(force=True) first. The user is
    prompted to confirm before any pip install is executed.

    `ok` is True for both "updated successfully" and "already up to date"
    (no-op). It is False only for genuine failures (network/SHA/pip errors
    or user cancellation).
    """
    if info is None:
        info = check_for_update(force=True)
    if not info:
        # No newer release -> not a failure, just nothing to do.
        return True, "Already up to date (v{0}).".format(CURRENT_VERSION)

    new_v = info.get("version", "?")
    wheel_url = info.get("wheel_url") or ""
    expected_sha = info.get("wheel_sha256") or ""

    if not wheel_url:
        return False, "Update failed: release has no downloadable wheel."

    _print_release_notes(info)

    try:
        answer = input("Proceed with update to v{0}? [y/N]: ".format(new_v)).strip().lower()
    except (EOFError, KeyboardInterrupt):
        _print("Update cancelled.")
        return False, "Update cancelled."

    if answer not in ("y", "yes"):
        return False, "Update cancelled."

    tmp_path = None
    try:
        # Download to a temp file
        fd, tmp_path_str = tempfile.mkstemp(suffix=".whl", prefix="codey-update-")
        tmp_path = tmp_path_str
        os.close(fd)
        try:
            with urllib.request.urlopen(wheel_url, timeout=30) as resp:
                data = resp.read()
        except Exception as e:
            return False, "Update failed: download error ({0})".format(e)
        try:
            with open(tmp_path, "wb") as f:
                f.write(data)
        except Exception as e:
            return False, "Update failed: could not save wheel ({0})".format(e)

        # Verify SHA256 if we have it
        if expected_sha:
            try:
                h = hashlib.sha256()
                with open(tmp_path, "rb") as f:
                    for chunk in iter(lambda: f.read(64 * 1024), b""):
                        h.update(chunk)
                got = h.hexdigest().lower()
                want = expected_sha.lower()
                if got != want:
                    return False, (
                        "Update failed: SHA256 mismatch "
                        "(expected {0}, got {1})".format(want, got)
                    )
            except Exception as e:
                return False, "Update failed: hash check error ({0})".format(e)

        # pip install --upgrade --force-reinstall
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "--force-reinstall", tmp_path],
                capture_output=True,
                text=True,
            )
        except Exception as e:
            return False, "Update failed: pip could not be invoked ({0})".format(e)

        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout or "").strip().splitlines()
            tail = err[-1] if err else "pip exited with code {0}".format(proc.returncode)
            return False, "Update failed: {0}".format(tail)

        return True, "Updated to v{0}. Restart Codey to use the new version.".format(new_v)
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass