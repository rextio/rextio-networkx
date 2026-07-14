"""The rule records and coverage rextio-networkx describes to Rextio core.

L2 rule records per the Rextio tooling contract, plus the coverage declaration.
The set covers the single implemented native construction route (a typed
undirected signed-i64 edge list converted once to an immutable local
``petgraph`` graph, with connected components computed in Rust) and the explicit
exclusions around it. See :mod:`rextio_networkx.rules.records` for the record
semantics and :mod:`rextio_networkx.rules.coverage` for the coverage surface.
"""

from __future__ import annotations

from rextio_networkx.rules.coverage import COVERAGE
from rextio_networkx.rules.records import networkx_rule_records

__all__ = ["COVERAGE", "networkx_rule_records"]
