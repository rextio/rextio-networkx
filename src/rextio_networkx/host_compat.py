"""Fail-closed compatibility checks for supported Rextio plugin hosts."""

from __future__ import annotations

import re

_PLUGIN_API_RE = re.compile(r"^(?P<major>[0-9]+)\.(?P<minor>[0-9]+)$")
_REQUIRED_MAJOR = 1
_REQUIRED_MINOR = 3


def supports_plugin_api(version: object) -> bool:
    """Return whether *version* is API 1.3 or a later compatible 1.x API.

    The provider remains an API-1.3 provider.  Hosts that add a later minor API
    retain the API-1.3 extension surface, while other majors and malformed
    versions are deliberately rejected rather than guessed.
    """
    if not isinstance(version, str):
        return False
    match = _PLUGIN_API_RE.fullmatch(version)
    if match is None:
        return False
    return (
        int(match["major"]) == _REQUIRED_MAJOR
        and int(match["minor"]) >= _REQUIRED_MINOR
    )


def require_supported_plugin_api(version: object, *, consumer: str) -> None:
    """Raise a stable error unless a host exposes a compatible plugin API."""
    if not supports_plugin_api(version):
        raise RuntimeError(
            f"{consumer} requires Rextio plugin API 1.3 or a later 1.x minor, found {version!r}"
        )


__all__ = ["require_supported_plugin_api", "supports_plugin_api"]
