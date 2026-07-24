"""Infer caste from Indian last names using SECC data."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from .secc_caste_ln import secc_caste

try:
    __version__ = version("outkast")
except PackageNotFoundError:
    __version__ = "unknown"

__all__ = ["secc_caste"]
