from __future__ import annotations

from importlib.metadata import version, PackageNotFoundError

from .secc_caste_ln import secc_caste

try:
    __version__ = version("outkast")
except PackageNotFoundError:
    __version__ = "unknown"

__all__ = ["secc_caste"]
