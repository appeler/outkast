"""Disclosure-limited aggregate composition lookups from SECC surname groups."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from .secc_composition import (
    get_secc_data_manifest,
    list_supported_states,
    lookup_secc_caste_composition,
)

try:
    __version__ = version("outkast")
except PackageNotFoundError:
    __version__ = "unknown"

__all__ = [
    "get_secc_data_manifest",
    "list_supported_states",
    "lookup_secc_caste_composition",
]
