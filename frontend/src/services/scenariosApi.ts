import apiClient from './api'
import type { Scenario, ScenarioParams, ScenarioResult } from '@/types/cognitive_map_models'

export const scenariosApi = {
  async getScenarios(): Promise<Scenario[]> {
    const response = await apiClient.get('/scenarios')
    return response.data
  },

  async getScenario(scenarioId: string): Promise<Scenario> {
    const response = await apiClient.get(`/scenarios/${scenarioId}`)
    return response.data
  },

  async createScenario(params: ScenarioParams): Promise<Scenario> {
    const response = await apiClient.post('/scenarios', params)
    return response.data
  },

  async updateScenario(scenarioId: string, params: ScenarioParams): Promise<Scenario> {
    const response = await apiClient.put(`/scenarios/${scenarioId}`, params)
    return response.data
  },

  async deleteScenario(scenarioId: string): Promise<void> {
    await apiClient.delete(`/scenarios/${scenarioId}`)
  },

  async runScenario(scenarioId: string): Promise<ScenarioResult> {
    const response = await apiClient.post(`/scenarios/${scenarioId}/run`)
    return response.data
  },
}
