"""Claim router: dispatch analysis sites to feature-owned claim modules."""

from __future__ import annotations

from rextio.config.schema import RextioConfig
from rextio.plugins.api import ClaimResult, ClaimSite, NotCovered

from rextio_networkx.claim import components, traversal

__all__ = ["claim"]


def claim(site: ClaimSite, config: RextioConfig) -> ClaimResult:
    """Decide, at analysis time, whether this plugin lowers the site.

    Deterministic by contract: the decision is a pure function of
    ``(site.kind, site.target, site.operand_types, site.keywords)``. The covered
    component and traversal adapter shapes are :class:`Claimed`; recognized
    traversal misses are :class:`Rejected`; unrelated targets are
    :class:`NotCovered`.
    """
    del config
    result = traversal.try_claim(site)
    if result is not None:
        return result
    result = components.try_claim(site)
    if result is not None:
        return result
    return NotCovered()
