from __future__ import annotations
from typing import List, Optional, Tuple, Literal, Dict
from pydantic import BaseModel, Field, ConfigDict


class NodeUIModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    x: float
    y: float
    color: str = "#64748b"


class NodeModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    label: str = ""
    ui: NodeUIModel
    preferred_state: Optional[Literal["increase", "decrease"]] = None


class EdgeModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source: str
    target: str
    weight: float = Field(..., ge=-1.0, le=1.0)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class ActivationModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["tanh", "sigmoid"] = "tanh"
    lambda_: float = Field(default=1.0, alias="lambda", gt=0.0)


# Scenario Models
class ScenarioParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    description: Optional[str] = ""
    activation_type: Literal["sigmoid", "tanh"] = "sigmoid"
    use_confidence: bool = False
    iteration_mode: Literal["fixed", "auto"] = "fixed"
    max_iterations: int = Field(default=100, ge=1, le=1000)
    convergence_threshold: Optional[float] = Field(default=0.001, gt=0.0)
    initial_states: Dict[str, float] = Field(default_factory=dict)


class ScenarioResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    final_states: Dict[str, float]
    iterations_count: int
    converged: bool
    timestamp: str
    history: Optional[List[Dict[str, float]]] = Field(
        default=None,
        description="State history for each iteration (not persisted to JSON)",
    )


class ScenarioModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    params: ScenarioParams
    result: Optional[ScenarioResult] = None
    created_at: str
    updated_at: str


class FCMModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    state_range: Tuple[float, float] = (-1.0, 1.0)
    activation: ActivationModel = Field(default_factory=ActivationModel)
    scenarios: List[ScenarioModel] = Field(default_factory=list)


class CognitiveMapModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: int = 1
    nodes: List[NodeModel] = Field(default_factory=list)
    edges: List[EdgeModel] = Field(default_factory=list)
    fcm: FCMModel = Field(default_factory=FCMModel)
