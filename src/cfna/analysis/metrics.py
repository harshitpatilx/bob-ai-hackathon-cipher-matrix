from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from cfna.graph import DiGraph
from cfna.models import CaseGraph, EntityType

TRANSFER = "transfer"
CO_OCCUR = "co_occur"

IDENTIFIER_TYPES = {
    EntityType.UPI_ID,
    EntityType.PHONE,
    EntityType.ACCOUNT,
    EntityType.CARD,
}


@dataclass
class NodeMetrics:
    node_id: str
    in_deg: int = 0
    out_deg: int = 0
    flow_in_deg: int = 0
    flow_out_deg: int = 0
    call_out_deg: int = 0
    call_in_deg: int = 0
    degree: int = 0
    in_amount: float = 0.0
    out_amount: float = 0.0
    narrative_loss: float = 0.0
    transfer_count: int = 0
    pass_through: float = 0.0
    pagerank: float = 0.0
    betweenness: float = 0.0
    community: int = -1
    labels: list[str] = field(default_factory=list)
    suspicious_hits: list[str] = field(default_factory=list)

    @property
    def net_amount(self) -> float:
        return self.in_amount - self.out_amount

    @property
    def loss_amount(self) -> float:
        """Largest documented victim loss: transfer outflow or the figure stated in the narrative."""
        return max(self.out_amount, self.narrative_loss)

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "in_deg": self.in_deg,
            "out_deg": self.out_deg,
            "flow_in_deg": self.flow_in_deg,
            "flow_out_deg": self.flow_out_deg,
            "degree": self.degree,
            "in_amount": round(self.in_amount, 2),
            "out_amount": round(self.out_amount, 2),
            "narrative_loss": round(self.narrative_loss, 2),
            "net_amount": round(self.net_amount, 2),
            "transfer_count": self.transfer_count,
            "pass_through": round(self.pass_through, 3),
            "pagerank": round(self.pagerank, 6),
            "betweenness": round(self.betweenness, 3),
            "community": self.community,
            "labels": list(self.labels),
        }


@dataclass
class GraphMetrics:
    flow_graph: DiGraph
    full_graph: DiGraph
    nodes: dict[str, NodeMetrics]
    components: list[set[str]]
    communities: dict[str, int]
    pagerank: dict[str, float]
    betweenness: dict[str, float]
    total_flow: float
    flows: list[tuple[str, str, float]]

    def get(self, node_id: str) -> NodeMetrics:
        if node_id not in self.nodes:
            self.nodes[node_id] = NodeMetrics(node_id=node_id)
        return self.nodes[node_id]

    def top(self, key: str, limit: int = 5) -> list[NodeMetrics]:
        return sorted(self.nodes.values(), key=lambda m: getattr(m, key), reverse=True)[:limit]


def _label_hits(case: CaseGraph, node_id: str) -> list[str]:
    ent = case.entities.get(node_id)
    return list(ent.labels) if ent else []


def compute_metrics(case: CaseGraph) -> GraphMetrics:
    flow_graph = DiGraph()
    full_graph = DiGraph()
    flows: list[tuple[str, str, float]] = []

    for entity in case.entities.values():
        full_graph.add_node(entity.id)

    flow_in: dict[str, set[str]] = {}
    flow_out: dict[str, set[str]] = {}
    call_in: dict[str, set[str]] = {}
    call_out: dict[str, set[str]] = {}

    for rel in case.relation_list():
        full_graph.add_edge(rel.src, rel.dst, rel.weight)
        if rel.rtype == "call":
            call_out.setdefault(rel.src, set()).add(rel.dst)
            call_in.setdefault(rel.dst, set()).add(rel.src)
        if rel.rtype == TRANSFER and rel.amount > 0:
            flow_graph.add_edge(rel.src, rel.dst, rel.amount)
            flows.append((rel.src, rel.dst, rel.amount))
            flow_out.setdefault(rel.src, set()).add(rel.dst)
            flow_in.setdefault(rel.dst, set()).add(rel.src)

    pagerank = full_graph.pagerank()
    betweenness = full_graph.betweenness()
    communities = full_graph.label_communities()
    components = full_graph.connected_components()

    inflow: dict[str, float] = {}
    outflow: dict[str, float] = {}
    for src, dst, amount in flows:
        outflow[src] = outflow.get(src, 0.0) + amount
        inflow[dst] = inflow.get(dst, 0.0) + amount

    transfer_counts: dict[str, int] = {}
    for rel in case.relation_list():
        if rel.rtype == TRANSFER:
            transfer_counts[rel.src] = transfer_counts.get(rel.src, 0) + rel.count
            transfer_counts[rel.dst] = transfer_counts.get(rel.dst, 0) + rel.count

    nodes: dict[str, NodeMetrics] = {}
    for node in full_graph.nodes:
        metric = NodeMetrics(node_id=node)
        metric.in_deg = full_graph.in_degree(node)
        metric.out_deg = full_graph.out_degree(node)
        metric.flow_in_deg = len(flow_in.get(node, ()))
        metric.flow_out_deg = len(flow_out.get(node, ()))
        metric.call_out_deg = len(call_out.get(node, ()))
        metric.call_in_deg = len(call_in.get(node, ()))
        metric.degree = metric.in_deg + metric.out_deg
        metric.in_amount = inflow.get(node, 0.0)
        metric.out_amount = outflow.get(node, 0.0)
        metric.transfer_count = transfer_counts.get(node, 0)
        ent = case.entities.get(node)
        if ent is not None and ent.attrs:
            try:
                metric.narrative_loss = float(ent.attrs.get("loss_amount") or 0.0)
            except (TypeError, ValueError):
                metric.narrative_loss = 0.0
        metric.pass_through = (metric.out_amount / metric.in_amount) if metric.in_amount > 0 else 0.0
        metric.pagerank = pagerank.get(node, 0.0)
        metric.betweenness = betweenness.get(node, 0.0)
        metric.community = communities.get(node, -1)
        metric.labels = _label_hits(case, node)
        nodes[node] = metric

    return GraphMetrics(
        flow_graph=flow_graph,
        full_graph=full_graph,
        nodes=nodes,
        components=components,
        communities=communities,
        pagerank=pagerank,
        betweenness=betweenness,
        total_flow=sum(amount for _, _, amount in flows),
        flows=flows,
    )
