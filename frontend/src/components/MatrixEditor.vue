<template>
  <div class="matrix-editor">
    <div class="matrix-toolbar">
      <div class="toolbar-left">
        <el-text size="large" tag="b">Adjacency Matrix</el-text>
        <el-text type="info">Size: {{ matrixSize }}x{{ matrixSize }}</el-text>
      </div>
      <div class="toolbar-right">
        <el-button :icon="Refresh" @click="refreshMatrix">Refresh</el-button>
      </div>
    </div>

    <div v-if="matrixSize === 0" class="empty-state">
      <el-empty description="No nodes in the graph. Add nodes in the Graph tab to create a matrix." />
    </div>

    <div v-else class="matrix-container">
      <el-scrollbar>
        <table class="matrix-table">
          <thead>
            <tr>
              <th class="corner-cell"></th>
              <th v-for="(targetId, _colIndex) in nodesOrder" :key="'header-' + targetId" class="header-cell">
                <div class="node-label-header">{{ getNodeLabel(targetId) }}</div>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(sourceId, rowIndex) in nodesOrder" :key="'row-' + sourceId">
              <th class="row-header">
                <div class="node-label-row">{{ getNodeLabel(sourceId) }}</div>
              </th>
              <td v-for="(targetId, colIndex) in nodesOrder" :key="'cell-' + rowIndex + '-' + colIndex">
                <MatrixCell
                  :source-index="rowIndex"
                  :target-index="colIndex"
                  :weight="getCellWeight(rowIndex, colIndex)"
                  :confidence="getCellConfidence(rowIndex, colIndex)"
                  :is-diagonal="rowIndex === colIndex"
                  @update="handleCellUpdate"
                />
              </td>
            </tr>
          </tbody>
        </table>
      </el-scrollbar>
    </div>

    <div v-if="matrixSize > 0" class="matrix-legend">
      <el-text type="info" size="small">Legend:</el-text>
      <div class="legend-items">
        <div class="legend-item">
          <div class="legend-color confidence-high"></div>
          <el-text size="small">High confidence (≥0.8)</el-text>
        </div>
        <div class="legend-item">
          <div class="legend-color confidence-medium"></div>
          <el-text size="small">Medium confidence (0.5-0.8)</el-text>
        </div>
        <div class="legend-item">
          <div class="legend-color confidence-low"></div>
          <el-text size="small">Low confidence (&lt;0.5)</el-text>
        </div>
        <div class="legend-item">
          <el-text size="small" class="weight-positive">Green = positive weight</el-text>
        </div>
        <div class="legend-item">
          <el-text size="small" class="weight-negative">Red = negative weight</el-text>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { useProjectStore } from '@/stores/project'
import MatrixCell from './MatrixCell.vue'
import { matrixApi } from '@/services/matrixApi'
import { ElMessage } from 'element-plus'

const projectStore = useProjectStore()

const nodesOrder = ref<string[]>([])
const matrix = ref<(number | null)[][]>([])
const confidenceMatrix = ref<(number | null)[][]>([])
const isLoading = ref(false)

const matrixSize = computed(() => nodesOrder.value.length)

function getNodeLabel(nodeId: string): string {
  const node = projectStore.nodes.find((n) => n.id === nodeId)
  return node?.label || nodeId
}

function getCellWeight(rowIndex: number, colIndex: number): number | null | undefined {
  return matrix.value[rowIndex]?.[colIndex]
}

function getCellConfidence(rowIndex: number, colIndex: number): number | null | undefined {
  return confidenceMatrix.value[rowIndex]?.[colIndex]
}

async function loadMatrix() {
  isLoading.value = true
  try {
    const data = await matrixApi.getMatrix()
    nodesOrder.value = data.nodes_order
    matrix.value = data.matrix
    confidenceMatrix.value = data.confidence
  } catch (error) {
    console.error('Failed to load matrix:', error)
    ElMessage.error('Failed to load matrix')
  } finally {
    isLoading.value = false
  }
}

async function refreshMatrix() {
  await loadMatrix()
  ElMessage.success('Matrix refreshed')
}

async function handleCellUpdate(event: {
  sourceIndex: number
  targetIndex: number
  weight: number | null
  confidence: number | null
}) {
  try {
    const updatedMap = await matrixApi.updateCell(
      event.sourceIndex,
      event.targetIndex,
      event.weight,
      event.confidence
    )

    await projectStore.updateMap(updatedMap)

    await loadMatrix()

    if (event.weight === null) {
      ElMessage.success('Connection deleted')
    } else {
      ElMessage.success('Connection updated')
    }
  } catch (error) {
    console.error('Failed to update cell:', error)
    ElMessage.error('Failed to update connection')
  }
}

watch(
  () => projectStore.edges,
  () => {
    loadMatrix()
  },
  { deep: true }
)

watch(
  () => projectStore.nodes,
  () => {
    loadMatrix()
  },
  { deep: true }
)

onMounted(() => {
  loadMatrix()
})
</script>

<style scoped>
.matrix-editor {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  background-color: var(--el-bg-color-page);
}

.matrix-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background-color: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color);
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.toolbar-right {
  display: flex;
  gap: 8px;
}

.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.matrix-container {
  flex: 1;
  overflow: hidden;
  padding: 16px;
}

.matrix-table {
  border-collapse: separate;
  border-spacing: 2px;
  width: auto;
  min-width: 100%;
}

.corner-cell {
  background-color: var(--el-fill-color);
  min-width: 120px;
  max-width: 120px;
  width: 120px;
  border: 1px solid var(--el-border-color);
}

.header-cell {
  background-color: var(--el-fill-color-light);
  padding: 8px;
  text-align: center;
  font-weight: 600;
  border: 1px solid var(--el-border-color);
  min-width: 80px;
}

.row-header {
  background-color: var(--el-fill-color-light);
  padding: 8px 12px;
  font-weight: 600;
  text-align: left;
  border: 1px solid var(--el-border-color);
  min-width: 120px;
  max-width: 120px;
  width: 120px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.node-label-header {
  writing-mode: vertical-rl;
  text-orientation: mixed;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-height: 120px;
  margin: 0 auto;
}

.node-label-row {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.matrix-table td {
  padding: 0;
  border: none;
}

.matrix-legend {
  padding: 16px 24px;
  background-color: var(--el-bg-color);
  border-top: 1px solid var(--el-border-color);
}

.legend-items {
  display: flex;
  gap: 24px;
  margin-top: 8px;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-color {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  border: 1px solid var(--el-border-color);
}

.legend-color.confidence-high {
  background-color: rgba(103, 194, 58, 0.3);
}

.legend-color.confidence-medium {
  background-color: rgba(230, 162, 60, 0.3);
}

.legend-color.confidence-low {
  background-color: rgba(245, 108, 108, 0.3);
}

.weight-positive {
  color: #67c23a;
  font-weight: bold;
}

.weight-negative {
  color: #f56c6c;
  font-weight: bold;
}
</style>
