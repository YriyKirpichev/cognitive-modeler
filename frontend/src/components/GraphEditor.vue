<template>
  <div class="graph-editor">
    <VueFlow 
      v-model:nodes="nodes" 
      v-model:edges="edges" 
      :default-viewport="{ zoom: 1 }" 
      :min-zoom="0.2" 
      :max-zoom="4"
      :nodes-draggable="!isConnectMode"
      @nodes-change="onNodesChange" 
      @edges-change="onEdgesChange" 
      @node-click="onNodeClick" 
      @edge-click="onEdgeClick"
      @pane-click="onPaneClick"
      @node-drag-stop="onNodeDragStop">
      <Background pattern-color="#aaa" :gap="16" />
      <Controls />
      
      <template #node-simple="nodeProps">
        <SimpleNode v-bind="nodeProps" />
      </template>
    </VueFlow>

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
        <el-button :icon="Delete" :disabled="!selectedNode && !selectedEdge" @click="deleteSelected">
          Delete
        </el-button>
      </el-button-group>
    </div>

    <!-- Connect mode overlay -->
    <div v-if="isConnectMode" class="connect-overlay">
      <div class="connect-hint">
        <el-icon class="hint-icon"><InfoFilled /></el-icon>
        <span>
          {{ connectSourceNode ? 'Now click on the target node' : 'Click on the source node first' }}
        </span>
      </div>
    </div>

    <!-- Node properties panel -->
    <el-drawer v-model="showNodeDrawer" title="Node Properties" direction="rtl" size="300px">
      <div v-if="selectedNode" class="properties-panel">
        <el-form label-position="top">
          <el-form-item label="Name">
            <el-input v-model="selectedNode.data.label" @change="updateNodeLabel" />
          </el-form-item>
          <el-form-item label="Color">
            <el-color-picker v-model="selectedNode.data.ui.color" @change="updateNodeColor" />
          </el-form-item>
        </el-form>
      </div>
    </el-drawer>

    <!-- Edge properties panel -->
    <el-drawer v-model="showEdgeDrawer" title="Edge Properties" direction="rtl" size="300px">
      <div v-if="selectedEdge" class="properties-panel">
        <el-form label-position="top">
          <el-form-item label="Weight">
            <el-slider v-model="selectedEdge.data.weight" :min="-1" :max="1" :step="0.1" show-input
              @change="updateEdgeWeight" />
          </el-form-item>
          <el-form-item label="Confidence">
            <el-slider v-model="selectedEdge.data.confidence" :min="0" :max="1" :step="0.1" show-input
              @change="updateEdgeConfidence" />
          </el-form-item>
        </el-form>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { VueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { Plus, Connection, Delete, InfoFilled } from '@element-plus/icons-vue'
import SimpleNode from './SimpleNode.vue'
import { useProjectStore } from '@/stores/project'
import { ElMessage } from 'element-plus'
import type {
  Node as FlowNode,
  Edge as FlowEdge,
} from '@vue-flow/core'
import type { Node, Edge } from '@/types/cognitive_map_models'

const projectStore = useProjectStore()

const nodes = ref<FlowNode[]>([])
const edges = ref<FlowEdge[]>([])
const selectedNode = ref<FlowNode | null>(null)
const selectedEdge = ref<FlowEdge | null>(null)
const showNodeDrawer = ref(false)
const showEdgeDrawer = ref(false)
const isConnectMode = ref(false)
const connectSourceNode = ref<string | null>(null)

const draggedNodes = ref<Map<string, { x: number; y: number }>>(new Map())

// Convert store nodes to VueFlow nodes
function convertToFlowNodes(storeNodes: Node[]): FlowNode[] {
  return storeNodes.map((node) => ({
    id: node.id,
    type: 'simple',
    position: { x: node.ui.x, y: node.ui.y },
    draggable: true,
    data: {
      label: node.label || node.id,
      ...node,
    },
  }))
}

// Convert store edges to VueFlow edges
function convertToFlowEdges(storeEdges: Edge[]): FlowEdge[] {
  return storeEdges.map((edge) => ({
    id: `${edge.source}-${edge.target}`,
    source: edge.source,
    target: edge.target,
    type: 'default',
    animated: edge.weight !== 0,
    markerEnd: {
      type: 'arrowclosed',
      width: 20,
      height: 20,
    },
    style: {
      stroke: edge.weight > 0 ? '#67C23A' : edge.weight < 0 ? '#F56C6C' : '#909399',
      strokeWidth: Math.abs(edge.weight) * 3 + 1,
    },
    label: edge.weight.toFixed(2),
    data: edge,
  }))
}

watch(
  () => projectStore.nodes,
  (newNodes) => {
    nodes.value = convertToFlowNodes(newNodes)
  },
  { immediate: true },
)

watch(
  () => projectStore.edges,
  (newEdges) => {
    edges.value = convertToFlowEdges(newEdges)
  },
  { immediate: true },
)

function onNodesChange(changes: any[]) {
  changes.forEach((change) => {
    if (change.type === 'position' && change.position) {
      const node = nodes.value.find((n) => n.id === change.id)
      if (node) {
        node.position = { ...change.position }
        if (change.dragging) {
          draggedNodes.value.set(change.id, change.position)
        }
      }
    } else if (change.type === 'remove') {
      projectStore.removeNode(change.id)
    }
  })
}


async function onNodeDragStop(event: { node: FlowNode }) {
  const nodeId = event.node.id
  const position = event.node.position

  if (position) {
    const node = nodes.value.find((n) => n.id === nodeId)
    if (node) {
      await projectStore.updateNode(nodeId, {
        ui: {
          x: position.x,
          y: position.y,
          color: node.data.ui.color,
        },
      })
    }
    draggedNodes.value.delete(nodeId)
  }
}

function onEdgesChange(changes: any[]) {
  changes.forEach((change) => {
    if (change.type === 'remove') {
      const edge = edges.value.find((e) => e.id === change.id)
      if (edge) {
        projectStore.removeEdge(edge.source, edge.target)
      }
    } else if (change.type === 'select') {
      const edge = edges.value.find((e) => e.id === change.id)
      if (edge) {
        const baseColor =
          edge.data.weight > 0 ? '#67C23A' : edge.data.weight < 0 ? '#F56C6C' : '#909399'
        edge.style = {
          ...edge.style,
          stroke: change.selected ? 'var(--el-color-primary)' : baseColor,
          strokeWidth: change.selected
            ? Math.abs(edge.data.weight) * 3 + 3
            : Math.abs(edge.data.weight) * 3 + 1,
          filter: change.selected ? 'drop-shadow(0 0 4px var(--el-color-primary))' : 'none',
        }
      }
    }
  })
}

function onNodeClick(event: { node: FlowNode; event: MouseEvent }) {
  if (isConnectMode.value) {
    handleConnectModeClick(event.node.id)
    return
  }

  selectedNode.value = event.node
  selectedEdge.value = null
  showNodeDrawer.value = true
  showEdgeDrawer.value = false
}

async function handleConnectModeClick(nodeId: string) {
  if (!connectSourceNode.value) {
    connectSourceNode.value = nodeId
    const node = nodes.value.find(n => n.id === nodeId)
    if (node) {
      ElMessage.info(`Source: ${node.data.label}. Now click target node.`)
    }
  } else {
    const sourceId = connectSourceNode.value
    const targetId = nodeId

    if (sourceId === targetId) {
      ElMessage.warning('Cannot create a connection from a node to itself')
      connectSourceNode.value = null
      return
    }

    const exists = edges.value.some((e) => e.source === sourceId && e.target === targetId)
    if (exists) {
      ElMessage.warning('Connection between these nodes already exists')
      connectSourceNode.value = null
      return
    }

    const newEdge: Edge = {
      source: sourceId,
      target: targetId,
      weight: 0.5,
      confidence: 1.0,
    }

    try {
      await projectStore.addEdge(newEdge)
      ElMessage.success('Connection created')
      connectSourceNode.value = null
      isConnectMode.value = false
    } catch (error) {
      ElMessage.error('Failed to create connection')
      console.error('Failed to add edge:', error)
      connectSourceNode.value = null
    }
  }
}

function onEdgeClick(event: { edge: FlowEdge }) {
  if (isConnectMode.value) return
  
  selectedEdge.value = event.edge
  selectedNode.value = null
  showEdgeDrawer.value = true
  showNodeDrawer.value = false
}

function onPaneClick() {
  if (isConnectMode.value) {
    connectSourceNode.value = null
  }
  selectedNode.value = null
  selectedEdge.value = null
}

function toggleConnectMode() {
  isConnectMode.value = !isConnectMode.value
  connectSourceNode.value = null
  
  if (isConnectMode.value) {
    ElMessage.info('Click on the source node, then click on the target node')
  }
}

async function addNode() {
  const id = `node-${Date.now()}`
  const newNode: Node = {
    id,
    label: `Node ${projectStore.nodes.length + 1}`,
    ui: {
      x: Math.random() * 400,
      y: Math.random() * 400,
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
  if (selectedNode.value) {
    try {
      await projectStore.removeNode(selectedNode.value.id)
      selectedNode.value = null
      showNodeDrawer.value = false
      ElMessage.success('Node deleted')
    } catch (error) {
      ElMessage.error('Failed to delete node')
      console.error('Failed to remove node:', error)
    }
  } else if (selectedEdge.value) {
    try {
      await projectStore.removeEdge(selectedEdge.value.source, selectedEdge.value.target)
      selectedEdge.value = null
      showEdgeDrawer.value = false
      ElMessage.success('Connection deleted')
    } catch (error) {
      ElMessage.error('Failed to delete connection')
      console.error('Failed to remove edge:', error)
    }
  }
}

function updateNodeLabel() {
  if (selectedNode.value) {
    projectStore.updateNode(selectedNode.value.id, {
      label: selectedNode.value.data.label,
    })
  }
}

function updateNodeColor() {
  if (selectedNode.value) {
    projectStore.updateNode(selectedNode.value.id, {
      ui: {
        ...selectedNode.value.data.ui,
        color: selectedNode.value.data.ui.color,
      },
    })
  }
}

function updateEdgeWeight() {
  if (selectedEdge.value) {
    projectStore.updateEdge(selectedEdge.value.source, selectedEdge.value.target, {
      weight: selectedEdge.value.data.weight,
    })
  }
}

function updateEdgeConfidence() {
  if (selectedEdge.value) {
    projectStore.updateEdge(selectedEdge.value.source, selectedEdge.value.target, {
      confidence: selectedEdge.value.data.confidence,
    })
  }
}
</script>

<style scoped>
.graph-editor {
  position: relative;
  width: 100%;
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

.properties-panel {
  padding: 16px;
}

:deep(.vue-flow__edge-path) {
  stroke-width: 2;
}

:deep(.vue-flow__edge.selected .vue-flow__edge-path) {
  stroke: var(--el-color-primary) !important;
  stroke-width: 4 !important;
  filter: drop-shadow(0 0 4px var(--el-color-primary));
}

:deep(.vue-flow__edge.selected .vue-flow__edge-text) {
  fill: var(--el-color-primary);
  font-weight: bold;
}
</style>