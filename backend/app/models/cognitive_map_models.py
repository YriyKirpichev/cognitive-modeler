from __future__ import annotations
from typing import List, Optional, Tuple, Literal
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
    type: Literal["tanh", "identity"] = "tanh"
    lambda_: float = Field(default=1.0, alias="lambda", gt=0.0)


class FCMModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    state_range: Tuple[float, float] = (-1.0, 1.0)
    activation: ActivationModel = Field(default_factory=ActivationModel)


class CognitiveMapModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: int = 1
    nodes: List[NodeModel] = Field(default_factory=list)
    edges: List[EdgeModel] = Field(default_factory=list)
    fcm: FCMModel = Field(default_factory=FCMModel)
