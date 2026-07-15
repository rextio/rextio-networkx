"""The rule records and coverage rextio-networkx describes to Rextio core.

L2 rule records per the Rextio tooling contract, plus the coverage declaration.
The set covers connected components plus exact API-1.3 resident graph
constructor/BFS/Dijkstra chains and their explicit exclusions. See
:mod:`rextio_networkx.rules.records` for semantics and
:mod:`rextio_networkx.rules.coverage` for the declared surface.
"""

from __future__ import annotations

from rextio_networkx.rules.coverage import COVERAGE
from rextio_networkx.rules.records import networkx_rule_records

__all__ = ["COVERAGE", "networkx_rule_records"]
