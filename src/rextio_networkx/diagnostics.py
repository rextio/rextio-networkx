"""Shared rejection guidance helpers for rextio-networkx claim decisions.

Holds the plugin type keys and the RXTP-NETWORKX-010 rejection builder used by
the claim router. Guidance text is taken from the matching rule record so the
message/suggestion stay synchronized with the described surface.
"""

from __future__ import annotations

from rextio.analyzer.diagnostics import Diagnostic
from rextio.plugins.api import ClaimResult, ClaimSite, NotCovered, Rejected

from rextio_networkx.rules import networkx_rule_records

#: Plugin type key for the covered undirected signed-i64 edge list input.
EDGELIST_I64 = "rextio-networkx/edgelist-i64"

#: Plugin type key for the ``list[set[int]]`` connected-components output.
COMPONENT_LIST = "rextio-networkx/component-list"

#: All plugin type keys this plugin owns.
TYPE_KEYS: frozenset[str] = frozenset({EDGELIST_I64, COMPONENT_LIST})


def is_edgelist_type(type_key: str | None) -> bool:
    """Report whether ``type_key`` is this plugin's edge-list input type."""
    return type_key == EDGELIST_I64


# The remediation guidance for claim rejections comes from the rule record that
# owns diagnostic code RXTP-NETWORKX-010 (unsupported argument type).
_REJECTION_GUIDANCE = next(
    record.guidance
    for record in networkx_rule_records()
    if record.diagnostic_code == "RXTP-NETWORKX-010"
)


def not_covered_or_rejected(site: ClaimSite) -> ClaimResult:
    """Resolve a covered-target miss: NotCovered when unresolved, else Rejected.

    An unresolved operand (``None``) is :class:`NotCovered` so core reports its
    own diagnostic; a known but unsupported operand type is :class:`Rejected`
    so the plugin's RXTP-NETWORKX-010 guidance is delivered on the function.
    """
    if any(operand is None for operand in site.operand_types):
        return NotCovered()
    named = ", ".join(str(operand) for operand in site.operand_types)
    return Rejected(
        diagnostic=Diagnostic(
            code="RXTP-NETWORKX-010",
            severity="error",
            message=(
                f"rextio-networkx cannot lower {site.target!r}: argument types "
                f"({named}) are outside the supported surface. The covered route "
                f"takes a single rextio_networkx.EdgeListI64 argument "
                f"(list[tuple[int, int]]; key {EDGELIST_I64!r})"
            ),
            file_path="",
            line=0,
            column=0,
            suggestion=_REJECTION_GUIDANCE,
        )
    )
