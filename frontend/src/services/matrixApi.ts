import api from './api'
import type { CognitiveMap } from '@/types/cognitive_map_models'

export interface MatrixData {
  nodes_order: string[]
  matrix: (number | null)[][]
  confidence: (number | null)[][]
}

export const matrixApi = {
  async getMatrix(): Promise<MatrixData> {
    const response = await api.get<MatrixData>('/matrix')
    return response.data
  },

  async updateCell(
    sourceIndex: number,
    targetIndex: number,
    weight: number | null,
    confidence: number | null = null
  ): Promise<CognitiveMap> {
    const response = await api.put<CognitiveMap>('/matrix/cell', {
      source_index: sourceIndex,
      target_index: targetIndex,
      weight,
      confidence
    })
    return response.data
  }
}
