import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { projectApi } from '@/services/projectApi'
import type { CognitiveMap, Node, Edge, HistoryInfo } from '@/types/cognitive_map_models'

export const useProjectStore = defineStore('project', () => {
  // State
  const currentMap = ref<CognitiveMap | null>(null)
  const historyInfo = ref<HistoryInfo | null>(null)
  const currentFilePath = ref<string | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const nodes = computed(() => currentMap.value?.nodes ?? [])
  const edges = computed(() => currentMap.value?.edges ?? [])
  const fcm = computed(() => currentMap.value?.fcm)
  const canUndo = computed(() => historyInfo.value?.can_undo ?? false)
  const canRedo = computed(() => historyInfo.value?.can_redo ?? false)
  const hasUnsavedChanges = computed(() => {
    return historyInfo.value ? historyInfo.value.current_index > 0 : false
  })

  // Actions
  async function loadMap() {
    isLoading.value = true
    error.value = null
    try {
      currentMap.value = await projectApi.getMap()
      await updateHistoryInfo()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load map'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function updateMap(map: CognitiveMap) {
    isLoading.value = true
    error.value = null
    try {
      currentMap.value = await projectApi.putMap(map)
      await updateHistoryInfo()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to update map'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function addNode(node: Node) {
    if (!currentMap.value) return

    const updatedMap: CognitiveMap = {
      ...currentMap.value,
      nodes: [...currentMap.value.nodes, node],
    }
    await updateMap(updatedMap)
  }

  async function updateNode(nodeId: string, updates: Partial<Node>) {
    if (!currentMap.value) return

    const updatedMap: CognitiveMap = {
      ...currentMap.value,
      nodes: currentMap.value.nodes.map((n) => (n.id === nodeId ? { ...n, ...updates } : n)),
    }
    await updateMap(updatedMap)
  }

  async function removeNode(nodeId: string) {
    if (!currentMap.value) return

    const updatedMap: CognitiveMap = {
      ...currentMap.value,
      nodes: currentMap.value.nodes.filter((n) => n.id !== nodeId),
      edges: currentMap.value.edges.filter((e) => e.source !== nodeId && e.target !== nodeId),
    }
    await updateMap(updatedMap)
  }

  async function addEdge(edge: Edge) {
    if (!currentMap.value) return

    const updatedMap: CognitiveMap = {
      ...currentMap.value,
      edges: [...currentMap.value.edges, edge],
    }
    await updateMap(updatedMap)
  }

  async function updateEdge(source: string, target: string, updates: Partial<Edge>) {
    if (!currentMap.value) return

    const updatedMap: CognitiveMap = {
      ...currentMap.value,
      edges: currentMap.value.edges.map((e) =>
        e.source === source && e.target === target ? { ...e, ...updates } : e,
      ),
    }
    await updateMap(updatedMap)
  }

  async function removeEdge(source: string, target: string) {
    if (!currentMap.value) return

    const updatedMap: CognitiveMap = {
      ...currentMap.value,
      edges: currentMap.value.edges.filter((e) => !(e.source === source && e.target === target)),
    }
    await updateMap(updatedMap)
  }

  async function undo() {
    isLoading.value = true
    error.value = null
    try {
      currentMap.value = await projectApi.undo()
      await updateHistoryInfo()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to undo'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function redo() {
    isLoading.value = true
    error.value = null
    try {
      currentMap.value = await projectApi.redo()
      await updateHistoryInfo()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to redo'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function saveToFile() {
    isLoading.value = true
    error.value = null
    try {
      await projectApi.saveToFile()
      await updateHistoryInfo()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to save'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function updateHistoryInfo() {
    try {
      historyInfo.value = await projectApi.getHistory()
    } catch (err) {
      console.error('Failed to update history info:', err)
    }
  }

  function createNewProject() {
    const newMap: CognitiveMap = {
      version: 1,
      nodes: [],
      edges: [],
      fcm: {
        state_range: [-1.0, 1.0],
        activation: {
          type: 'tanh',
          lambda: 1.0,
        },
      },
    }
    currentFilePath.value = null
    updateMap(newMap)
  }

  async function openProject(filePath: string) {
    try {
      currentFilePath.value = filePath
      await loadMap()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to open project'
      throw err
    }
  }

  async function saveProject() {
    if (!currentFilePath.value) {
      throw new Error('No file path specified. Use "Save As" instead.')
    }
    await saveToFile()
  }

  async function saveProjectAs(filePath: string) {
    currentFilePath.value = filePath
    await saveToFile()
  }

  return {
    // State
    currentMap,
    historyInfo,
    currentFilePath,
    isLoading,
    error,

    // Getters
    nodes,
    edges,
    fcm,
    canUndo,
    canRedo,
    hasUnsavedChanges,

    // Actions
    loadMap,
    updateMap,
    addNode,
    updateNode,
    removeNode,
    addEdge,
    updateEdge,
    removeEdge,
    undo,
    redo,
    save: saveToFile,
    createNewProject,
    openProject,
    saveProject,
    saveProjectAs,
  }
})
