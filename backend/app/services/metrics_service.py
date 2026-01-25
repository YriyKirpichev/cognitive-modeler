from typing import Literal
from pydantic import BaseModel
from app.models.cognitive_map_models import CognitiveMapModel


NodeType = Literal["driver", "receiver", "mediator", "isolated"]


class NodeMetrics(BaseModel):
    node_id: str
    indegree: int
    outdegree: int
    centrality: float
    type: NodeType


class MetricsStatistics(BaseModel):
    drivers: int
    receivers: int
    mediators: int
    isolated: int


class MetricsResponse(BaseModel):
    metrics: list[NodeMetrics]
    statistics: MetricsStatistics


class MetricsService:

    @staticmethod
    def calculate_metrics(cognitive_map: CognitiveMapModel) -> MetricsResponse:
        node_metrics_list: list[NodeMetrics] = []

        drivers = 0
        receivers = 0
        mediators = 0
        isolated = 0

        for node in cognitive_map.nodes:
            incoming_edges = [e for e in cognitive_map.edges if e.target == node.id]
            indegree = len(incoming_edges)

            outgoing_edges = [e for e in cognitive_map.edges if e.source == node.id]
            outdegree = len(outgoing_edges)

            weighted_indegree = sum(abs(edge.weight) for edge in incoming_edges)
            weighted_outdegree = sum(abs(edge.weight) for edge in outgoing_edges)
            centrality = weighted_indegree + weighted_outdegree

            node_type = MetricsService._classify_node_type(indegree, outdegree)

            if node_type == "driver":
                drivers += 1
            elif node_type == "receiver":
                receivers += 1
            elif node_type == "mediator":
                mediators += 1
            elif node_type == "isolated":
                isolated += 1

            metrics = NodeMetrics(
                node_id=node.id,
                indegree=indegree,
                outdegree=outdegree,
                centrality=round(centrality, 2),
                type=node_type,
            )
            node_metrics_list.append(metrics)

        statistics = MetricsStatistics(
            drivers=drivers, receivers=receivers, mediators=mediators, isolated=isolated
        )

        return MetricsResponse(metrics=node_metrics_list, statistics=statistics)

    @staticmethod
    def _classify_node_type(indegree: int, outdegree: int) -> NodeType:
        if indegree == 0 and outdegree == 0:
            return "isolated"

        if outdegree > indegree:
            return "driver"

        if indegree > outdegree:
            return "receiver"

        return "mediator"
