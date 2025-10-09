from packaging import version

__version__ = "0.84.1.dev"
safe_version = __version__

try:
    from aider._version import __version__
except Exception:
    __version__ = safe_version + "+import"

if type(__version__) is not str:
    __version__ = safe_version + "+type"
else:
    try:
        if version.parse(__version__) < version.parse(safe_version):
            __version__ = safe_version + "+less"
    except Exception:
        __version__ = safe_version + "+parse"

__all__ = [__version__]

# --------------------------------------------------------------------------- #
# Announce TEAMWORK_API (if present)
# --------------------------------------------------------------------------- #
#
# Load variables from a local `.env` (if any) and print TEAMWORK_API so that the
# user immediately knows it has been detected when they invoke the `aider` CLI.
# Doing this work here in ``__init__`` guarantees it runs for both the console
# entry-point and ``python -m aider``.
import os as _os
from pathlib import Path as _Path


def _load_dotenv() -> None:
    """
    Manually load key=value pairs from a local ``.env`` file (if present) into
    the process environment.  Lines beginning with ``#`` are ignored. Existing
    environment variables are left untouched.
    """
    env_file = (_Path(__file__).resolve().parent.parent / ".env").expanduser()
    if not env_file.is_file():
        return

    for raw_line in env_file.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        # Do not override an explicit environment variable
        _os.environ.setdefault(key, val)


# Ensure .env variables are available early in startup
_load_dotenv()

_teamwork_api = _os.getenv("TEAMWORK_API")
if _teamwork_api:
    print(f"TEAMWORK_API={_teamwork_api}")
