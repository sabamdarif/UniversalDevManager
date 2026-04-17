"""
installer.py — Core installation engine for Universal Dev Environment Manager.

Provides:
  • detect_tool()  — check whether a tool is already installed
  • install_tool() — run the platform-appropriate install command
  • setup_path()   — add required directories to PATH
  • install_selected() — orchestrate a batch of installs with progress callbacks
"""

import os
import platform

from utils import (
    logger,
    is_windows,
    is_linux,
    is_mac,
    run_command,
    command_exists,
    add_to_path,
    check_internet,
    _resolve_env_path,
)

# ═══════════════════════════════════════════════════════════════════════════
#  Callbacks — set by the GUI for live updates
# ═══════════════════════════════════════════════════════════════════════════
_progress_cb = None        # (tool_name, status_text, percent_int) → None
_log_cb = None             # (message_str) → None


def set_progress_callback(cb):
    global _progress_cb
    _progress_cb = cb


def set_log_callback(cb):
    global _log_cb
    _log_cb = cb


def _notify(tool: str, status: str, pct: int):
    if _progress_cb:
        _progress_cb(tool, status, pct)


def _log(msg: str):
    logger.info(msg)
    if _log_cb:
        _log_cb(msg)


# ═══════════════════════════════════════════════════════════════════════════
#  Install-command resolver
# ═══════════════════════════════════════════════════════════════════════════
def _get_install_cmd(tool: dict) -> str:
    """Return the install command for the current platform, or '' if none."""
    if is_windows():
        return tool.get("install_command_windows", "")
    elif is_linux():
        return tool.get("install_command_linux", "")
    elif is_mac():
        return tool.get("install_command_mac", "")
    return ""


# ═══════════════════════════════════════════════════════════════════════════
#  Detection
# ═══════════════════════════════════════════════════════════════════════════
def detect_tool(tool: dict) -> bool:
    """Return True if the tool is already present on the system."""
    detect_cmd = tool.get("detect_cmd", "")
    if not detect_cmd:
        return False
    rc, out, _ = run_command(detect_cmd, timeout=15)
    if rc == 0:
        return True
    # Try alternate detect command if provided
    alt = tool.get("detect_cmd_alt", "")
    if alt:
        rc2, _, _ = run_command(alt, timeout=15)
        if rc2 == 0:
            return True
    return False


# ═══════════════════════════════════════════════════════════════════════════
#  Installation
# ═══════════════════════════════════════════════════════════════════════════
def _ensure_homebrew():
    """On macOS, install Homebrew if it is not present."""
    if is_mac() and not command_exists("brew"):
        _log("  Homebrew not found — installing…")
        cmd = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
        rc, out, err = run_command(cmd, timeout=300)
        if rc != 0:
            _log(f"  ⚠ Homebrew install failed: {err[:200]}")
        else:
            _log("  ✓ Homebrew installed.")


def _ensure_apt_updated():
    """Run `sudo apt-get update` once per session on Linux."""
    if not hasattr(_ensure_apt_updated, "_done"):
        _log("  Updating apt package index…")
        run_command("sudo apt-get update -y", timeout=120)
        _ensure_apt_updated._done = True


def install_tool(tool: dict) -> bool:
    """
    Install a single tool using the platform install command.
    Returns True on success.
    """
    name = tool.get("name", "Unknown")
    cmd = _get_install_cmd(tool)

    if not cmd:
        _log(f"  ⚠ No install command for {name} on {platform.system()}")
        return False

    # Platform pre-requisites
    if is_mac():
        _ensure_homebrew()
    if is_linux() and cmd.startswith("sudo apt"):
        _ensure_apt_updated()

    _log(f"  Running: {cmd}")
    rc, out, err = run_command(cmd, timeout=900)

    # winget/apt sometimes returns 0=-success, or contain helpful text
    combined = (out + err).lower()
    if rc == 0:
        return True
    if "already installed" in combined or "no upgrade" in combined or "is already the newest" in combined:
        _log(f"  {name} appears already installed (package manager says so).")
        return True

    _log(f"  stdout: {out.strip()[:300]}")
    _log(f"  stderr: {err.strip()[:300]}")
    return False


# ═══════════════════════════════════════════════════════════════════════════
#  PATH Setup
# ═══════════════════════════════════════════════════════════════════════════
def setup_path(tool: dict) -> bool:
    """Add required directories to PATH for the given tool."""
    if not tool.get("path_required", False):
        return True

    dirs = tool.get("path_dirs_windows" if is_windows() else "path_dirs_linux" if is_linux() else "path_dirs_mac", [])
    if not dirs:
        return True

    ok = True
    for d in dirs:
        resolved = _resolve_env_path(d)
        _log(f"  PATH → {resolved}")
        if not add_to_path(resolved):
            _log(f"  ⚠ Could not add {resolved} to PATH")
            ok = False
    return ok


# ═══════════════════════════════════════════════════════════════════════════
#  Batch Installer (orchestrator)
# ═══════════════════════════════════════════════════════════════════════════
def install_selected(tools: list[dict], on_complete=None) -> dict[str, str]:
    """
    Install all tools in *tools* sequentially, calling _notify / _log
    for live GUI updates. Returns a dict {tool_key: result_str}.
    """
    results: dict[str, str] = {}
    total = len(tools)

    _log("═══════════════════════════════════════════════════════")
    _log(f"  Starting installation of {total} tool(s)…")
    _log("═══════════════════════════════════════════════════════")

    for idx, tool in enumerate(tools, start=1):
        key = tool.get("key", tool["name"])
        name = tool.get("name", key)
        pct = int((idx - 1) / total * 100)

        _notify(name, "Checking…", pct)
        _log(f"\n── {name} ({idx}/{total}) ─────────────────────")

        # 1. Detection
        if detect_tool(tool):
            _log(f"  ✓ {name} is already installed. Skipping.")
            results[key] = "already_installed"
            _notify(name, "Already installed  ✓", int(idx / total * 100))
            continue

        # 2. Installation
        _notify(name, "Installing…", pct)
        _log(f"  Installing {name}…")
        try:
            success = install_tool(tool)
        except Exception as e:
            _log(f"  ✗ Exception during install: {e}")
            success = False

        if not success:
            _log(f"  ✗ Failed to install {name}.")
            results[key] = "failed"
            _notify(name, "Failed  ✗", int(idx / total * 100))
            continue

        # 3. PATH
        if tool.get("path_required", False):
            _notify(name, "Configuring PATH…", pct)
            _log(f"  Configuring PATH for {name}…")
            try:
                setup_path(tool)
            except Exception as e:
                _log(f"  ⚠ PATH error: {e}")

        _log(f"  ✓ {name} installed successfully.")
        results[key] = "installed"
        _notify(name, "Installed  ✓", int(idx / total * 100))

    _notify("Done", "All tasks complete", 100)
    _log("\n═══════════════════════════════════════════════════════")
    _log("  Installation batch complete.")
    _log("═══════════════════════════════════════════════════════\n")

    if on_complete:
        on_complete(results)

    return results
