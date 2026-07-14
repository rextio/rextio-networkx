"""Claim router: dispatch analysis sites to feature-owned claim modules."""

from __future__ import annotations

from rextio.config.schema import RextioConfig
from rextio.plugins.api import ClaimResult, ClaimSite, NotCovered

from rextio_networkx.claim import components

__all__ = ["claim"]


def claim(site: ClaimSite, config: RextioConfig) -> ClaimResult:
    """Decide, at analysis time, whether this plugin lowers the site.

    Deterministic by contract: the decision is a pure function of
    ``(site.kind, site.target, site.operand_types, site.keywords)``. The covered
    adapter call with a typed :data:`~rextio_networkx.EdgeListI64` argument is
    :class:`Claimed`; the same call with a known-but-unsupported argument type is
    :class:`Rejected` with RXTP-NETWORKX-010 guidance; everything else is
    :class:`NotCovered`.
    """
    del config
    result = components.try_claim(site)
    if result is not None:
        return result
    return NotCovered()
