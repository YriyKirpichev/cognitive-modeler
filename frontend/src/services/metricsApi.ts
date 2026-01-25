import apiClient from './api'
import type { MetricsResponse } from '@/types/cognitive_map_models'

export const metricsApi = {
  async getMetrics(): Promise<MetricsResponse> {
    const response = await apiClient.get<MetricsResponse>('/metrics')
    return response.data
  }
}
