from typing import Optional
from app.models.cognitive_map_models import CognitiveMapModel, EdgeModel


class MatrixService:

    @staticmethod
    def build_matrix(cognitive_map: CognitiveMapModel) -> dict:
        """
        Returns:
            {
                "nodes_order": List[str],  # Node IDs in order
                "matrix": List[List[Optional[float]]],  # Weight matrix
                "confidence": List[List[Optional[float]]]  # Confidence matrix
            }
        """
        nodes_order = [n.id for n in cognitive_map.nodes]
        n = len(nodes_order)

        matrix: list[list[Optional[float]]] = [
            [None for _ in range(n)] for _ in range(n)
        ]
        confidence_matrix: list[list[Optional[float]]] = [
            [None for _ in range(n)] for _ in range(n)
        ]

        node_index = {node_id: i for i, node_id in enumerate(nodes_order)}

        for edge in cognitive_map.edges:
            source_idx = node_index.get(edge.source)
            target_idx = node_index.get(edge.target)
            if source_idx is not None and target_idx is not None:
                matrix[source_idx][target_idx] = edge.weight
                confidence_matrix[source_idx][target_idx] = edge.confidence

        return {
            "nodes_order": nodes_order,
            "matrix": matrix,
            "confidence": confidence_matrix,
        }

    @staticmethod
    def update_cell(
        cognitive_map: CognitiveMapModel,
        source_index: int,
        target_index: int,
        weight: Optional[float],
        confidence: Optional[float] = None,
    ) -> CognitiveMapModel:
        nodes = cognitive_map.nodes
        if source_index >= len(nodes) or target_index >= len(nodes):
            raise ValueError("Invalid node index")

        if source_index < 0 or target_index < 0:
            raise ValueError("Invalid node index")

        if source_index == target_index:
            raise ValueError("Cannot create self-loop (diagonal cells are locked)")

        source_id = nodes[source_index].id
        target_id = nodes[target_index].id

        existing_edge_idx = None
        for i, edge in enumerate(cognitive_map.edges):
            if edge.source == source_id and edge.target == target_id:
                existing_edge_idx = i
                break

        if weight is None:
            if existing_edge_idx is not None:
                cognitive_map.edges.pop(existing_edge_idx)
        else:
            if weight < -1.0 or weight > 1.0:
                raise ValueError("Weight must be in range [-1.0, 1.0]")

            if confidence is not None and (confidence < 0.0 or confidence > 1.0):
                raise ValueError("Confidence must be in range [0.0, 1.0]")

            if existing_edge_idx is not None:
                edge = cognitive_map.edges[existing_edge_idx]
                edge.weight = weight
                if confidence is not None:
                    edge.confidence = confidence
            else:
                new_edge = EdgeModel(
                    source=source_id,
                    target=target_id,
                    weight=weight,
                    confidence=confidence if confidence is not None else 1.0,
                )
                cognitive_map.edges.append(new_edge)

        return cognitive_map
