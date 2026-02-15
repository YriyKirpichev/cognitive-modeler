<template>
  <div class="graph-editor">
    <div ref="cytoscapeContainer" class="cytoscape-container" />

    <div class="toolbar">
      <el-button-group>
        <el-button :icon="Plus" @click="addNode">Node</el-button>
        <el-button
          :icon="Connection"
          :type="isConnectMode ? 'primary' : 'default'"
          @click="toggleConnectMode"
        >
          {{ isConnectMode ? 'Cancel' : 'Connect' }}
        </el-button>
        <el-button :icon="Delete" :disabled="!hasSelection" @click="deleteSelected">
          Delete
        </el-button>
      </el-button-group>
    </div>

    <!-- Connect mode overlay -->
    <div v-if="isConnectMode" class="connect-overlay">
      <div class="connect-hint">
        <el-icon class="hint-icon"><InfoFilled /></el-icon>
        <span>Drag from one node to another to create a connection</span>
      </div>
    </div>

    <!-- Tooltip for new edge -->
    <div
      v-if="showEdgeTooltip"
      ref="edgeTooltipRef"
      class="edge-tooltip"
      :style="edgeTooltipStyle"
    >
      <div class="tooltip-header">New Connection</div>
      <el-form label-position="top" size="small">
        <el-form-item label="Weight">
          <el-slider
            v-model="newEdgeWeight"
            :min="-1"
            :max="1"
            :step="0.1"
            show-input
            :input-size="'small'"
          />
        </el-form-item>
        <el-form-item label="Confidence">
          <el-slider
            v-model="newEdgeConfidence"
            :min="0"
            :max="1"
            :step="0.1"
            show-input
            :input-size="'small'"
          />
        </el-form-item>
      </el-form>
      <div class="tooltip-actions">
        <el-button size="small" @click="cancelNewEdge">Cancel</el-button>
        <el-button size="small" type="primary" @click="applyNewEdge">Apply</el-button>
      </div>
    </div>

    <!-- Sidebar with properties panel -->
    <div class="properties-sidebar">
      <div v-if="!selectedNodeData && !selectedEdgeData" class="empty-state">
        <el-icon class="empty-icon"><InfoFilled /></el-icon>
        <p class="empty-text">Select a node or edge to edit properties</p>
      </div>

      <!-- Node properties -->
      <div v-if="selectedNodeData" class="properties-panel">
        <div class="panel-header">
          <h3>Node Properties</h3>
        </div>
        <el-form label-position="top">
          <el-form-item label="Name">
            <el-input v-model="selectedNodeData.label" @change="updateNodeLabel" />
          </el-form-item>
          <el-form-item label="Color">
            <el-color-picker v-model="selectedNodeData.color" @change="updateNodeColor" />
          </el-form-item>
        </el-form>
      </div>

      <!-- Edge properties -->
      <div v-if="selectedEdgeData" class="properties-panel">
        <div class="panel-header">
          <h3>Edge Properties</h3>
        </div>
        <el-form label-position="top">
          <el-form-item label="Weight">
            <el-slider
              v-model="selectedEdgeData.weight"
              :min="-1"
              :max="1"
              :step="0.1"
              show-input
              @change="updateEdgeWeight"
            />
          </el-form-item>
          <el-form-item label="Confidence">
            <el-slider
              v-model="selectedEdgeData.confidence"
              :min="0"
              :max="1"
              :step="0.1"
              show-input
              @change="updateEdgeConfidence"
            />
          </el-form-item>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick, type CSSProperties } from 'vue'
import { Plus, Connection, Delete, InfoFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import cytoscape from 'cytoscape'
import edgehandles, { type EdgeHandlesInstance } from 'cytoscape-edgehandles'
import { useProjectStore } from '@/stores/project'
import type { Node, Edge } from '@/types/cognitive_map_models'
import type { Core, ElementDefinition, NodeSingular, EdgeSingular } from 'cytoscape'

cytoscape.use(edgehandles)

const projectStore = useProjectStore()

const cytoscapeContainer = ref<HTMLElement | null>(null)
const cyInstance = ref<Core | null>(null)
const edgehandlesInstance = ref<EdgeHandlesInstance | null>(null)
  
const isConnectMode = ref(false)
const showEdgeTooltip = ref(false)
const edgeTooltipStyle = ref<CSSProperties>({})
const edgeTooltipRef = ref<HTMLElement | null>(null)

const selectedNodeData = ref<{ id: string; label: string; color: string } | null>(null)
const selectedEdgeData = ref<{ source: string; target: string; weight: number; confidence: number } | null>(null)

const newEdgeWeight = ref(0.5)
const newEdgeConfidence = ref(1.0)
const pendingEdge = ref<{ source: string; target: string } | null>(null)

const hasSelection = computed(() => {
  return selectedNodeData.value !== null || selectedEdgeData.value !== null
})

function convertToCytoscapeElements(nodes: Node[], edges: Edge[]): ElementDefinition[] {
  const elements: ElementDefinition[] = []

  nodes.forEach((node) => {
    elements.push({
      group: 'nodes',
      data: {
        id: node.id,
        label: node.label || node.id,
        color: node.ui?.color || '#64748b',
      },
      position: {
        x: node.ui?.x ?? 0,
        y: node.ui?.y ?? 0,
      },
    })
  })

  edges.forEach((edge) => {
    elements.push({
      group: 'edges',
      data: {
        id: `${edge.source}-${edge.target}`,
        source: edge.source,
        target: edge.target,
        weight: edge.weight ?? 0,
        confidence: edge.confidence ?? 1.0,
      },
    })
  })

  return elements
}

function getEdgeColor(weight: number): string {
  if (weight > 0) return '#67C23A'
  if (weight < 0) return '#F56C6C'
  return '#909399'
}

function getEdgeWidth(weight: number): number {
  return Math.abs(weight) * 3 + 1
}

onMounted(async () => {
  await nextTick()

  if (!cytoscapeContainer.value) return

  cyInstance.value = cytoscape({
    container: cytoscapeContainer.value,
    elements: convertToCytoscapeElements(projectStore.nodes, projectStore.edges),
    style: [
      {
        selector: 'node',
        style: {
          'background-color': (ele: NodeSingular) => ele.data('color') as string || '#64748b',
          'label': 'data(label)',
          'text-valign': 'center',
          'text-halign': 'center',
          'width': 80,
          'height': 40,
          'shape': 'roundrectangle',
          'font-size': '14px',
          'font-weight': 500,
          'color': '#fff',
          'text-outline-color': (ele: NodeSingular) => ele.data('color') as string || '#64748b',
          'text-outline-width': 2,
          'border-width': 2,
          'border-color': 'transparent',
        },
      },
      {
        selector: 'node:selected',
        style: {
          'border-color': '#409EFF',
          'border-width': 3,
        },
      },
      {
        selector: 'edge',
        style: {
          'width': (ele: EdgeSingular) => {
            const weight = ele.data('weight') as number | undefined;
            return weight !== undefined ? getEdgeWidth(weight) : 1;
          },
          'line-color': (ele: EdgeSingular) => {
            const weight = ele.data('weight') as number | undefined;
            return weight !== undefined ? getEdgeColor(weight) : '#909399';
          },
          'target-arrow-shape': 'triangle',
          'target-arrow-color': (ele: EdgeSingular) => {
            const weight = ele.data('weight') as number | undefined;
            return weight !== undefined ? getEdgeColor(weight) : '#909399';
          },
          'curve-style': 'bezier',
          'label': (ele: EdgeSingular) => {
            const weight = ele.data('weight') as number | undefined;
            return weight !== undefined ? weight.toFixed(2) : '0.00';
          },
          'font-size': '12px',
          'text-background-color': '#fff',
          'text-background-opacity': 0.8,
          'text-background-padding': '3px',
          'text-background-shape': 'roundrectangle',
          'color': '#333',
          'text-rotation': 'autorotate',
        },
      },
      {
        selector: 'edge:selected',
        style: {
          'line-color': '#409EFF',
          'target-arrow-color': '#409EFF',
          'width': (ele: EdgeSingular) => {
            const weight = ele.data('weight') as number | undefined;
            return weight !== undefined ? getEdgeWidth(weight) + 2 : 3;
          },
        },
      },
      {
        selector: '.eh-handle',
        style: {
          'background-color': '#409EFF',
          'width': 12,
          'height': 12,
          'shape': 'ellipse',
          'overlay-opacity': 0,
        },
      },
      {
        selector: '.eh-hover',
        style: {
          'background-color': '#67C23A',
        },
      },
      {
        selector: '.eh-source',
        style: {
          'border-width': 3,
          'border-color': '#409EFF',
        },
      },
      {
        selector: '.eh-target',
        style: {
          'border-width': 3,
          'border-color': '#67C23A',
        },
      },
      {
        selector: '.eh-preview, .eh-ghost-edge',
        style: {
          'background-color': '#409EFF',
          'line-color': '#409EFF',
          'target-arrow-color': '#409EFF',
          'source-arrow-color': '#409EFF',
        },
      },
    ],
    layout: {
      name: 'preset',
    },
    minZoom: 0.2,
    maxZoom: 4,
    wheelSensitivity: 0.2,
    boxSelectionEnabled: false,
    selectionType: 'single', 
  })

  edgehandlesInstance.value = cyInstance.value.edgehandles({
    canConnect: (sourceNode: NodeSingular, targetNode: NodeSingular) => {
      return !sourceNode.same(targetNode)
    },
    edgeParams: (sourceNode: NodeSingular, targetNode: NodeSingular) => {
      return {
        data: {
          source: sourceNode.id(),
          target: targetNode.id(),
        },
      }
    },
    hoverDelay: 150,
    snap: true,
    snapThreshold: 50,
    snapFrequency: 15,
    noEdgeEventsInDraw: true,
    disableBrowserGestures: true,
  })

  setupEventListeners()
  setupGridBackground()
})

onBeforeUnmount(() => {
  if (cyInstance.value) {
    cyInstance.value.destroy()
  }
})

function setupGridBackground() {
  if (cytoscapeContainer.value) {
    cytoscapeContainer.value.style.backgroundImage = `
      linear-gradient(rgba(170, 170, 170, 0.3) 1px, transparent 1px),
      linear-gradient(90deg, rgba(170, 170, 170, 0.3) 1px, transparent 1px)
    `
    cytoscapeContainer.value.style.backgroundSize = '16px 16px'
    cytoscapeContainer.value.style.backgroundColor = '#fafafa'
  }
}

function setupEventListeners() {
  if (!cyInstance.value) return

  const cy = cyInstance.value

  cy.on('tap', 'node', (event) => {
    if (isConnectMode.value) return

    const node = event.target as NodeSingular
    const data = node.data()

    selectedNodeData.value = {
      id: data.id as string,
      label: (data.label as string) || (data.id as string),
      color: (data.color as string) || '#64748b',
    }

    selectedEdgeData.value = null
  })

  cy.on('tap', 'edge', (event) => {
    if (isConnectMode.value) return

    const edge = event.target as EdgeSingular
    const data = edge.data()

    selectedEdgeData.value = {
      source: data.source as string,
      target: data.target as string,
      weight: (data.weight as number) ?? 0,
      confidence: (data.confidence as number) ?? 1.0,
    }

    selectedNodeData.value = null
  })

  cy.on('tap', (event) => {
    if (event.target === cy) {
      selectedNodeData.value = null
      selectedEdgeData.value = null
    }
  })

  cy.on('dragfree', 'node', async (event) => {
    const node = event.target as NodeSingular
    const position = node.position()
    const nodeData = projectStore.nodes.find((n) => n.id === node.id())

    if (nodeData) {
      await projectStore.updateNode(node.id(), {
        ui: {
          x: position.x,
          y: position.y,
          color: nodeData.ui?.color || '#64748b',
        },
      })
    }
  })

  cy.on('ehcomplete', async (event, sourceNode: NodeSingular, targetNode: NodeSingular, addedEdge: EdgeSingular) => {
    addedEdge.remove()

    const sourceId = sourceNode.id()
    const targetId = targetNode.id()

    const exists = projectStore.edges.some((e) => e.source === sourceId && e.target === targetId)
    if (exists) {
      ElMessage.warning('Connection between these nodes already exists')
      return
    }

    pendingEdge.value = { source: sourceId, target: targetId }

    await nextTick()
    showEdgeTooltipAtPosition(event.renderedPosition || event.position)
  })
}

function showEdgeTooltipAtPosition(position: { x: number; y: number }) {
  if (!cyInstance.value || !cytoscapeContainer.value) return

  const rect = cytoscapeContainer.value.getBoundingClientRect()

  edgeTooltipStyle.value = {
    left: `${rect.left + position.x}px`,
    top: `${rect.top + position.y}px`,
  }

  showEdgeTooltip.value = true
}

async function applyNewEdge() {
  if (!pendingEdge.value) return

  const newEdge: Edge = {
    source: pendingEdge.value.source,
    target: pendingEdge.value.target,
    weight: newEdgeWeight.value,
    confidence: newEdgeConfidence.value,
  }

  try {
    await projectStore.addEdge(newEdge)
    ElMessage.success('Connection created')

    selectedEdgeData.value = {
      source: newEdge.source,
      target: newEdge.target,
      weight: newEdge.weight,
      confidence: newEdge.confidence ?? 1.0,
    }

    showEdgeTooltip.value = false
    pendingEdge.value = null
  } catch (error) {
    ElMessage.error('Failed to create connection')
    console.error('Failed to add edge:', error)
  }
}

function cancelNewEdge() {
  showEdgeTooltip.value = false
  pendingEdge.value = null
  newEdgeWeight.value = 0.5
  newEdgeConfidence.value = 1.0
}

function toggleConnectMode() {
  isConnectMode.value = !isConnectMode.value

  if (edgehandlesInstance.value) {
    if (isConnectMode.value) {
      edgehandlesInstance.value.enableDrawMode()
      ElMessage.info('Drag from one node to another to create a connection')
    } else {
      edgehandlesInstance.value.disableDrawMode()
    }
  }
}

async function addNode() {
  const id = `node-${Date.now()}`
  const newNode: Node = {
    id,
    label: `Node ${projectStore.nodes.length + 1}`,
    ui: {
      x: 200 + Math.random() * 200,
      y: 200 + Math.random() * 200,
      color: '#64748b',
    },
  }

  try {
    await projectStore.addNode(newNode)
    ElMessage.success('Node added')
  } catch (error) {
    ElMessage.error('Failed to add node')
    console.error('Failed to add node:', error)
  }
}

async function deleteSelected() {
  if (!hasSelection.value) return

  try {
    if (selectedEdgeData.value) {
      await projectStore.removeEdge(selectedEdgeData.value.source, selectedEdgeData.value.target)
      selectedEdgeData.value = null
      ElMessage.success('Edge deleted')
    } else if (selectedNodeData.value) {
      await projectStore.removeNode(selectedNodeData.value.id)
      selectedNodeData.value = null
      ElMessage.success('Node deleted')
    }
  } catch (error) {
    ElMessage.error('Failed to delete element')
    console.error('Failed to delete:', error)
  }
}

function updateNodeLabel() {
  if (!selectedNodeData.value || !cyInstance.value) return

  const node = cyInstance.value.$id(selectedNodeData.value.id)
  if (node.length > 0) {
    node.data('label', selectedNodeData.value.label)

    projectStore.updateNode(selectedNodeData.value.id, {
      label: selectedNodeData.value.label,
    })
  }
}

function updateNodeColor() {
  if (!selectedNodeData.value || !cyInstance.value) return

  const node = cyInstance.value.$id(selectedNodeData.value.id)
  if (node.length > 0) {
    node.data('color', selectedNodeData.value.color)

    const nodeData = projectStore.nodes.find((n) => n.id === selectedNodeData.value!.id)
    if (nodeData) {
      projectStore.updateNode(selectedNodeData.value.id, {
        ui: {
          ...nodeData.ui,
          color: selectedNodeData.value.color,
        },
      })
    }
  }
}

function updateEdgeWeight() {
  if (!selectedEdgeData.value || !cyInstance.value) return

  const edgeId = `${selectedEdgeData.value.source}-${selectedEdgeData.value.target}`
  const edge = cyInstance.value.$id(edgeId)

  if (edge.length > 0) {
    edge.data('weight', selectedEdgeData.value.weight)

    projectStore.updateEdge(selectedEdgeData.value.source, selectedEdgeData.value.target, {
      weight: selectedEdgeData.value.weight,
    })
  }
}

function updateEdgeConfidence() {
  if (!selectedEdgeData.value || !cyInstance.value) return

  const edgeId = `${selectedEdgeData.value.source}-${selectedEdgeData.value.target}`
  const edge = cyInstance.value.$id(edgeId)

  if (edge.length > 0) {
    edge.data('confidence', selectedEdgeData.value.confidence)

    projectStore.updateEdge(selectedEdgeData.value.source, selectedEdgeData.value.target, {
      confidence: selectedEdgeData.value.confidence,
    })
  }
}

watch(
  () => [projectStore.nodes, projectStore.edges],
  () => {
    if (!cyInstance.value) return

    const newElements = convertToCytoscapeElements(projectStore.nodes, projectStore.edges)
    const currentElements = cyInstance.value.elements()

    currentElements.forEach((ele) => {
      const eleId = ele.id()
      const exists = newElements.some((newEle) => newEle.data.id === eleId)
      if (!exists) {
        ele.remove()
      }
    })

    newElements.forEach((newEle) => {
      const eleId = newEle.data.id
      if (!eleId) return

      const existing = cyInstance.value!.$id(eleId)

      if (existing.length === 0) {
        cyInstance.value!.add(newEle)
      } else {
        Object.keys(newEle.data).forEach((key: string) => {
          const value = (newEle.data as Record<string, unknown>)[key]
          if (value !== undefined) {
            existing.data(key, value)
          }
        })

        if (newEle.position && existing.isNode()) {
          const currentPos = existing.position()
          if (currentPos.x !== newEle.position.x || currentPos.y !== newEle.position.y) {
            existing.position(newEle.position)
          }
        }
      }
    })
  },
  { deep: true }
)
</script>

<style scoped>
.graph-editor {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
}

.cytoscape-container {
  flex: 1;
  height: 100%;
}

.toolbar {
  position: absolute;
  top: 16px;
  left: 16px;
  z-index: 10;
  background-color: var(--el-bg-color);
  padding: 8px;
  border-radius: 4px;
  box-shadow: var(--el-box-shadow-light);
}

.connect-overlay {
  position: absolute;
  top: 70px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
}

.connect-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  background-color: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  padding: 12px 20px;
  border-radius: 6px;
  box-shadow: var(--el-box-shadow);
  font-size: 14px;
  font-weight: 500;
}

.hint-icon {
  font-size: 18px;
}

.properties-sidebar {
  width: 320px;
  height: 100%;
  background-color: var(--el-bg-color);
  border-left: 1px solid var(--el-border-color);
  overflow-y: auto;
  flex-shrink: 0;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 32px;
  text-align: center;
  color: var(--el-text-color-secondary);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-text {
  font-size: 14px;
  line-height: 1.5;
}

.properties-panel {
  padding: 24px;
}

.panel-header {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--el-border-color);
}

.panel-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin: 0;
}

.edge-tooltip {
  position: fixed;
  z-index: 1000;
  background-color: #fff;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  box-shadow: var(--el-box-shadow);
  padding: 16px;
  min-width: 300px;
  transform: translate(-50%, -100%) translateY(-20px);
}

.tooltip-header {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
  color: var(--el-text-color-primary);
}

.tooltip-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
}
</style>