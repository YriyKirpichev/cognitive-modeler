import apiClient from './api'
import type { CognitiveMap, HistoryInfo } from '@/types/cognitive_map_models'

export const projectApi = {
  async getMap(): Promise<CognitiveMap> {
    const response = await apiClient.get<CognitiveMap>('/project/map')
    return response.data
  },

  async putMap(map: CognitiveMap): Promise<CognitiveMap> {
    const response = await apiClient.put<CognitiveMap>('/project/map', map)
    return response.data
  },

  async undo(): Promise<CognitiveMap> {
    const response = await apiClient.post<CognitiveMap>('/project/undo')
    return response.data
  },

  async redo(): Promise<CognitiveMap> {
    const response = await apiClient.post<CognitiveMap>('/project/redo')
    return response.data
  },

  async getHistory(): Promise<HistoryInfo> {
    const response = await apiClient.get<HistoryInfo>('/project/history')
    return response.data
  },

  async saveToFile(): Promise<{ ok: boolean }> {
    const response = await apiClient.post<{ ok: boolean }>('/project/save-to-file')
    return response.data
  },

  async newProject(filePath: string): Promise<CognitiveMap> {
    const response = await apiClient.post<CognitiveMap>('/project/new', {
      file_path: filePath,
    })
    return response.data
  },

  async openProject(filePath: string): Promise<CognitiveMap> {
    const response = await apiClient.post<CognitiveMap>('/project/open', {
      file_path: filePath,
    })
    return response.data
  },

  async saveAsProject(filePath: string): Promise<CognitiveMap> {
    const response = await apiClient.post<CognitiveMap>('/project/save-as', {
      file_path: filePath,
    })
    return response.data
  },
}
