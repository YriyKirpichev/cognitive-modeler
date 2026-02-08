import logging
from datetime import datetime
from typing import Dict, List, Tuple
import numpy as np

from app.models.cognitive_map_models import (
    CognitiveMapModel,
    ScenarioParams,
    ScenarioResult,
    EdgeModel,
)

logger = logging.getLogger("app")


def sigmoid(x: float, lambda_param: float = 1.0) -> float:
    return 1.0 / (1.0 + np.exp(-lambda_param * x))


def tanh_activation(x: float, lambda_param: float = 1.0) -> float:
    return np.tanh(lambda_param * x)


class ScenarioService:
    """Service for running FCM scenario simulations."""

    @staticmethod
    def validate_initial_states(
        initial_states: Dict[str, float],
        node_ids: List[str],
        state_range: Tuple[float, float],
    ) -> None:
        """
        Validate that initial states are valid.

        Args:
            initial_states: Dictionary of node_id -> initial_value
            node_ids: List of valid node IDs
            state_range: Tuple of (min, max) for state values

        Raises:
            ValueError: If validation fails
        """
        min_val, max_val = state_range

        # Check that all node_ids in initial_states are valid
        for node_id in initial_states.keys():
            if node_id not in node_ids:
                raise ValueError(
                    f"Node ID '{node_id}' in initial_states does not exist in the cognitive map"
                )

        # Check that all initial values are within state_range
        for node_id, value in initial_states.items():
            if not (min_val <= value <= max_val):
                raise ValueError(
                    f"Initial value {value} for node '{node_id}' is outside state_range [{min_val}, {max_val}]"
                )

    @staticmethod
    def get_effective_weight(edge: EdgeModel, use_confidence: bool) -> float:
        """
        Calculate effective weight of an edge.

        Args:
            edge: The edge model
            use_confidence: Whether to apply confidence to weight

        Returns:
            Effective weight (weight * confidence if use_confidence, else weight)
        """
        if use_confidence and edge.confidence is not None:
            return edge.weight * edge.confidence
        return edge.weight

    @staticmethod
    def build_adjacency_matrix(
        cognitive_map: CognitiveMapModel,
        use_confidence: bool,
    ) -> Tuple[np.ndarray, Dict[str, int], Dict[int, str]]:
        """
        Build adjacency matrix from cognitive map.

        Args:
            cognitive_map: The cognitive map model
            use_confidence: Whether to apply confidence to weights

        Returns:
            Tuple of (adjacency_matrix, node_id_to_index, index_to_node_id)
        """
        nodes = cognitive_map.nodes
        edges = cognitive_map.edges

        # Create node ID mappings
        node_id_to_index = {node.id: idx for idx, node in enumerate(nodes)}
        index_to_node_id = {idx: node.id for idx, node in enumerate(nodes)}

        # Initialize adjacency matrix
        n = len(nodes)
        adjacency_matrix = np.zeros((n, n))

        # Fill adjacency matrix with edge weights
        for edge in edges:
            if edge.source in node_id_to_index and edge.target in node_id_to_index:
                source_idx = node_id_to_index[edge.source]
                target_idx = node_id_to_index[edge.target]
                effective_weight = ScenarioService.get_effective_weight(
                    edge, use_confidence
                )
                adjacency_matrix[source_idx, target_idx] = effective_weight

        return adjacency_matrix, node_id_to_index, index_to_node_id

    @staticmethod
    def run_simulation(
        cognitive_map: CognitiveMapModel,
        params: ScenarioParams,
    ) -> ScenarioResult:
        """
        Run FCM simulation with given parameters.

        Args:
            cognitive_map: The cognitive map to simulate
            params: Simulation parameters

        Returns:
            ScenarioResult with final states and metadata

        Raises:
            ValueError: If parameters are invalid
        """
        # Validate inputs
        node_ids = [node.id for node in cognitive_map.nodes]

        if not node_ids:
            raise ValueError("Cannot run simulation on empty cognitive map")

        ScenarioService.validate_initial_states(
            params.initial_states,
            node_ids,
            cognitive_map.fcm.state_range,
        )

        # Check that initial_states contains all nodes
        if len(params.initial_states) != len(node_ids):
            raise ValueError(
                f"initial_states must contain values for all {len(node_ids)} nodes"
            )

        # Build adjacency matrix
        adjacency_matrix, node_id_to_index, index_to_node_id = (
            ScenarioService.build_adjacency_matrix(cognitive_map, params.use_confidence)
        )

        # Initialize state vector
        n = len(node_ids)
        state = np.zeros(n)
        for node_id, value in params.initial_states.items():
            idx = node_id_to_index[node_id]
            state[idx] = value

        # Select activation function
        lambda_param = cognitive_map.fcm.activation.lambda_
        if params.activation_type == "sigmoid":
            activation_fn = lambda x: sigmoid(x, lambda_param)
        else:  # tanh
            activation_fn = lambda x: tanh_activation(x, lambda_param)

        # Run simulation
        converged = False
        iterations_count = 0
        state_range = cognitive_map.fcm.state_range

        # Initialize history list to store states at each iteration
        history: List[Dict[str, float]] = []

        # Store initial state (iteration 0)
        history.append({index_to_node_id[idx]: float(state[idx]) for idx in range(n)})

        for iteration in range(params.max_iterations):
            iterations_count = iteration + 1

            # Calculate new state
            # For each node: new_state = activation(sum of incoming influences)
            new_state = np.zeros(n)

            for target_idx in range(n):
                # Sum of incoming influences from all source nodes
                input_sum = 0.0
                for source_idx in range(n):
                    weight = adjacency_matrix[source_idx, target_idx]
                    if weight != 0.0:
                        input_sum += state[source_idx] * weight

                # Apply activation function
                activated_value = activation_fn(input_sum)

                # Clip to state_range
                new_state[target_idx] = np.clip(
                    activated_value, state_range[0], state_range[1]
                )

            # Store state after this iteration
            history.append(
                {index_to_node_id[idx]: float(new_state[idx]) for idx in range(n)}
            )

            # Check convergence for auto mode
            if params.iteration_mode == "auto":
                max_change = np.max(np.abs(new_state - state))
                if max_change < params.convergence_threshold:
                    converged = True
                    state = new_state
                    break

            state = new_state

        # Auto mode convergence status
        if params.iteration_mode == "auto":
            if not converged:
                logger.warning(
                    f"Simulation did not converge after {params.max_iterations} iterations"
                )
        else:
            # Fixed mode is always considered "converged" after completing iterations
            converged = True

        # Build final states dictionary
        final_states = {index_to_node_id[idx]: float(state[idx]) for idx in range(n)}

        # Create result with history
        result = ScenarioResult(
            final_states=final_states,
            iterations_count=iterations_count,
            converged=converged,
            timestamp=datetime.utcnow().isoformat() + "Z",
            history=history,  # Include iteration history
        )

        logger.info(
            f"Simulation completed: {iterations_count} iterations, "
            f"converged={converged}, history_length={len(history)}"
        )

        return result
