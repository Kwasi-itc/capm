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
try:
    from dotenv import load_dotenv  # type: ignore
except ImportError:  # pragma: no cover
    load_dotenv = None

import os as _os

if load_dotenv:
    load_dotenv()

_teamwork_api = _os.getenv("TEAMWORK_API")
if _teamwork_api:
    print(f"TEAMWORK_API={_teamwork_api}")
