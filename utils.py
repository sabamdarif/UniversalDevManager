"""
utils.py — Utility functions for Universal Dev Environment Manager.

Provides OS detection, internet connectivity checks, PATH manipulation,
command execution helpers, and logging configuration.
"""

import os
import sys
import platform
import subprocess
import logging
import socket
import json
import glob
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════
#  Logging
# ═══════════════════════════════════════════════════════════════════════════
if getattr(sys, "frozen", False):
    LOG_FILE = Path(sys.executable).parent / "installer.log"
else:
    LOG_FILE = Path(__file__).parent / "installer.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("UniversalDevManager")


# ═══════════════════════════════════════════════════════════════════════════
#  Config loader
# ═══════════════════════════════════════════════════════════════════════════
def _get_base_dir() -> Path:
    """Return the base directory — sys._MEIPASS when frozen by PyInstaller."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).parent

TOOLS_JSON_PATH = _get_base_dir() / "tools.json"


def load_tools() -> list[dict]:
    """Load and return the tools list from tools.json."""
    try:
        with open(TOOLS_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"Loaded {len(data)} tools from tools.json")
        return data
    except Exception as e:
        logger.error(f"Failed to load tools.json: {e}")
        return []


def get_categories(tools: list[dict]) -> list[str]:
    """Return a sorted list of unique category names."""
    cats = sorted({t.get("category", "Other") for t in tools})
    return cats


# ═══════════════════════════════════════════════════════════════════════════
#  OS Detection
# ═══════════════════════════════════════════════════════════════════════════
def detect_os() -> str:
    """Return 'Windows', 'Linux', or 'Darwin' (macOS)."""
    return platform.system()


def is_windows() -> bool:
    return detect_os() == "Windows"


def is_linux() -> bool:
    return detect_os() == "Linux"


def is_mac() -> bool:
    return detect_os() == "Darwin"


def os_label() -> str:
    mapping = {"Windows": "Windows", "Linux": "Linux", "Darwin": "macOS"}
    return mapping.get(detect_os(), detect_os())


# ═══════════════════════════════════════════════════════════════════════════
#  Internet Check
# ═══════════════════════════════════════════════════════════════════════════
def check_internet(host: str = "8.8.8.8", port: int = 53, timeout: int = 5) -> bool:
    """Return True if there is an active internet connection."""
    try:
        socket.setdefaulttimeout(timeout)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.close()
        logger.info("Internet connection verified.")
        return True
    except OSError:
        logger.warning("No internet connection detected.")
        return False


# ═══════════════════════════════════════════════════════════════════════════
#  Command Execution
# ═══════════════════════════════════════════════════════════════════════════
def run_command(
    cmd: str,
    shell: bool = True,
    timeout: int = 900,
) -> tuple[int, str, str]:
    """
    Run a shell command and return (returncode, stdout, stderr).
    On Windows, CREATE_NO_WINDOW prevents console flashes.
    """
    kwargs: dict = dict(
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=shell,
        timeout=timeout,
    )
    if is_windows():
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

    try:
        proc = subprocess.run(cmd, **kwargs)
        return (
            proc.returncode,
            proc.stdout.decode(errors="replace"),
            proc.stderr.decode(errors="replace"),
        )
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out: {cmd}")
        return -1, "", "Command timed out"
    except Exception as e:
        logger.error(f"Command failed: {cmd} — {e}")
        return -1, "", str(e)


def command_exists(cmd: str) -> bool:
    """Check whether *cmd* is available on PATH."""
    try:
        if is_windows():
            result = subprocess.run(
                ["where", cmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        else:
            result = subprocess.run(
                ["which", cmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        return result.returncode == 0
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════════════════════
#  PATH Utilities
# ═══════════════════════════════════════════════════════════════════════════
def _resolve_env_path(p: str) -> str:
    """Expand environment variables and resolve glob patterns."""
    expanded = os.path.expandvars(p)
    expanded = os.path.expanduser(expanded)
    # Handle glob patterns (e.g. jdk-21.*)
    if "*" in expanded:
        matches = glob.glob(expanded)
        if matches:
            return os.path.normpath(sorted(matches)[-1])  # take latest
    return os.path.normpath(expanded)


def _windows_get_user_path() -> str:
    """Read the current user PATH from the registry."""
    import winreg
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_READ
        ) as key:
            value, _ = winreg.QueryValueEx(key, "Path")
            return value
    except FileNotFoundError:
        return ""


def _windows_set_user_path(new_path: str) -> bool:
    """Write *new_path* to the user PATH in the registry and broadcast."""
    import winreg
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
        # Broadcast WM_SETTINGCHANGE
        import ctypes
        HWND_BROADCAST = 0xFFFF
        WM_SETTINGCHANGE = 0x001A
        SMTO_ABORTIFHUNG = 0x0002
        ctypes.windll.user32.SendMessageTimeoutW(
            HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment",
            SMTO_ABORTIFHUNG, 5000, None,
        )
        logger.info("Windows user PATH updated and change broadcasted.")
        return True
    except Exception as e:
        logger.error(f"Failed to set Windows PATH: {e}")
        return False


def add_to_path(directory: str) -> bool:
    """
    Add *directory* to the user PATH if it is not already present.
    Returns True on success.
    """
    directory = _resolve_env_path(directory)

    if is_windows():
        current = _windows_get_user_path()
        entries = [e.strip() for e in current.split(";") if e.strip()]
        normalized = [os.path.normpath(e) for e in entries]
        if directory in normalized:
            logger.info(f"PATH already contains {directory}")
            return True
        if not os.path.isdir(directory):
            logger.warning(f"Directory does not exist (yet): {directory}")
        entries.append(directory)
        return _windows_set_user_path(";".join(entries))

    elif is_linux():
        rc_file = Path.home() / ".bashrc"
        export_line = f'\nexport PATH="$PATH:{directory}"\n'
        try:
            content = rc_file.read_text(encoding="utf-8") if rc_file.exists() else ""
            if directory in content:
                logger.info(f"PATH already contains {directory}")
                return True
            with open(rc_file, "a", encoding="utf-8") as f:
                f.write(export_line)
            logger.info(f"Appended {directory} to ~/.bashrc")
            return True
        except Exception as e:
            logger.error(f"Failed to update ~/.bashrc: {e}")
            return False

    elif is_mac():
        rc_file = Path.home() / ".zshrc"
        export_line = f'\nexport PATH="$PATH:{directory}"\n'
        try:
            content = rc_file.read_text(encoding="utf-8") if rc_file.exists() else ""
            if directory in content:
                logger.info(f"PATH already contains {directory}")
                return True
            with open(rc_file, "a", encoding="utf-8") as f:
                f.write(export_line)
            logger.info(f"Appended {directory} to ~/.zshrc")
            return True
        except Exception as e:
            logger.error(f"Failed to update ~/.zshrc: {e}")
            return False

    return False


# ═══════════════════════════════════════════════════════════════════════════
#  Admin / Privilege Helpers
# ═══════════════════════════════════════════════════════════════════════════
def is_admin() -> bool:
    """Return True if the process has elevated privileges."""
    if is_windows():
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    else:
        return os.geteuid() == 0


def request_admin():
    """Relaunch the current script with admin / root privileges."""
    if is_windows():
        import ctypes
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit(0)
