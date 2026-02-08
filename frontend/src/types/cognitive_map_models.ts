export interface NodeUI {
  x: number
  y: number
  color: string
}

export interface Node {
  id: string
  label: string
  ui: NodeUI
  preferred_state?: 'increase' | 'decrease'
}

export interface Edge {
  source: string
  target: string
  weight: number
  confidence?: number
}

export type ActivationType = 'tanh' | 'sigmoid'

export interface Activation {
  type: ActivationType
  lambda: number
}

// Scenario types
export type ScenarioActivationType = 'sigmoid' | 'tanh'
export type IterationMode = 'fixed' | 'auto'

export interface ScenarioParams {
  name: string
  description?: string
  activation_type: ScenarioActivationType
  use_confidence: boolean
  iteration_mode: IterationMode
  max_iterations: number
  convergence_threshold?: number
  initial_states: Record<string, number>
}

export interface ScenarioResult {
  final_states: Record<string, number>
  iterations_count: number
  converged: boolean
  timestamp: string
  history?: Array<Record<string, number>>
}

export interface Scenario {
  id: string
  params: ScenarioParams
  result?: ScenarioResult
  created_at: string
  updated_at: string
}

export interface FCM {
  state_range: [number, number]
  activation: Activation
  scenarios: Scenario[]
}

export interface CognitiveMap {
  version: number
  nodes: Node[]
  edges: Edge[]
  fcm: FCM
}

export interface HistoryInfo {
  current_index: number
  history_length: number
  can_undo: boolean
  can_redo: boolean
}

export type NodeType = 'driver' | 'receiver' | 'mediator' | 'isolated'

export interface NodeMetrics {
  node_id: string
  indegree: number
  outdegree: number
  centrality: number
  type: NodeType
}

export interface MetricsStatistics {
  drivers: number
  receivers: number
  mediators: number
  isolated: number
}

export interface MetricsResponse {
  metrics: NodeMetrics[]
  statistics: MetricsStatistics
}