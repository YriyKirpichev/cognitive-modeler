export interface NodeUI {
  x: number
  y: number
  color: string
}

export interface Node {
  id: string
  label: string
  ui: NodeUI
}

export interface Edge {
  source: string
  target: string
  weight: number
  confidence?: number
}

export type ActivationType = 'tanh' | 'identity'

export interface Activation {
  type: ActivationType
  lambda: number
}

export interface FCM {
  state_range: [number, number]
  activation: Activation
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