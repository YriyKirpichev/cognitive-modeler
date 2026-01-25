<template>
  <div class="metrics-editor">
    <div class="metrics-toolbar">
      <div class="toolbar-left">
        <el-text size="large" tag="b">Node Metrics & State</el-text>
        <div v-if="!isLoading && metricsData" class="statistics">
          <el-tag type="primary" size="small">Drivers: {{ metricsData.statistics.drivers }}</el-tag>
          <el-tag type="success" size="small">Receivers: {{ metricsData.statistics.receivers }}</el-tag>
          <el-tag type="warning" size="small">Mediators: {{ metricsData.statistics.mediators }}</el-tag>
          <el-tag type="info" size="small">Isolated: {{ metricsData.statistics.isolated }}</el-tag>
        </div>
      </div>
      <div class="toolbar-right">
        <el-button :icon="Refresh" @click="refreshMetrics" :loading="isLoading">Refresh</el-button>
      </div>
    </div>

    <div v-if="projectStore.nodes.length === 0" class="empty-state">
      <el-empty description="No nodes in the graph. Add nodes in the Graph tab to see metrics." />
    </div>

    <div v-else class="metrics-container">
      <el-scrollbar>
        <el-table
          :data="tableData"
          stripe
          style="width: 100%"
          v-loading="isLoading"
          default-sort="{ prop: 'label', order: 'ascending' }"
        >
          <el-table-column prop="label" label="Node" sortable min-width="150">
            <template #default="scope">
              <span class="node-label">{{ scope.row.label }}</span>
            </template>
          </el-table-column>

          <el-table-column prop="indegree" label="Indegree" sortable width="120" align="center">
            <template #default="scope">
              <el-text>{{ scope.row.indegree }}</el-text>
            </template>
          </el-table-column>

          <el-table-column prop="outdegree" label="Outdegree" sortable width="120" align="center">
            <template #default="scope">
              <el-text>{{ scope.row.outdegree }}</el-text>
            </template>
          </el-table-column>

          <el-table-column prop="centrality" label="Centrality" sortable width="120" align="center">
            <template #default="scope">
              <el-text>{{ scope.row.centrality.toFixed(2) }}</el-text>
            </template>
          </el-table-column>

          <el-table-column prop="type" label="Type" sortable width="140" align="center">
            <template #default="scope">
              <el-tag :type="getTypeTagType(scope.row.type)" size="small">
                {{ formatType(scope.row.type) }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column prop="preferred_state" label="Preferred State" width="180" align="center">
            <template #default="scope">
              <el-select
                v-model="scope.row.preferred_state"
                placeholder="None"
                size="small"
                clearable
                @change="handlePreferredStateChange(scope.row.node_id, scope.row.preferred_state)"
              >
                <el-option label="Increase" value="increase" />
                <el-option label="Decrease" value="decrease" />
              </el-select>
            </template>
          </el-table-column>
        </el-table>
      </el-scrollbar>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { useProjectStore } from '@/stores/project'
import { metricsApi } from '@/services/metricsApi'
import { ElMessage } from 'element-plus'
import type { MetricsResponse, NodeType } from '@/types/cognitive_map_models'

const projectStore = useProjectStore()

const metricsData = ref<MetricsResponse | null>(null)
const isLoading = ref(false)

interface TableRow {
  node_id: string
  label: string
  indegree: number
  outdegree: number
  centrality: number
  type: NodeType
  preferred_state?: 'increase' | 'decrease'
}

const tableData = computed<TableRow[]>(() => {
  if (!metricsData.value) return []

  const rows: TableRow[] = metricsData.value.metrics.map((metric) => {
    const node = projectStore.nodes.find((n) => n.id === metric.node_id)
    return {
      node_id: metric.node_id,
      label: node?.label || metric.node_id,
      indegree: metric.indegree,
      outdegree: metric.outdegree,
      centrality: metric.centrality,
      type: metric.type,
      preferred_state: node?.preferred_state
    }
  })

  // Sort by label alphabetically
  return rows.sort((a, b) => a.label.localeCompare(b.label))
})

function getTypeTagType(type: NodeType): string {
  switch (type) {
    case 'driver':
      return 'primary'
    case 'receiver':
      return 'success'
    case 'mediator':
      return 'warning'
    case 'isolated':
      return 'info'
    default:
      return ''
  }
}

function formatType(type: NodeType): string {
  return type.charAt(0).toUpperCase() + type.slice(1)
}

async function loadMetrics() {
  isLoading.value = true
  try {
    metricsData.value = await metricsApi.getMetrics()
  } catch (error) {
    console.error('Failed to load metrics:', error)
    ElMessage.error('Failed to load metrics')
  } finally {
    isLoading.value = false
  }
}

async function refreshMetrics() {
  await loadMetrics()
  ElMessage.success('Metrics refreshed')
}

async function handlePreferredStateChange(nodeId: string, newState: 'increase' | 'decrease' | undefined) {
  try {
    const node = projectStore.nodes.find((n) => n.id === nodeId)
    if (!node) {
      ElMessage.error('Node not found')
      return
    }

    if (node.preferred_state === newState) {
      // No change
      return
    }
    
    // Save to backend
    await projectStore.updateNode(nodeId, { preferred_state: newState })

    if (newState) {
      ElMessage.success(`Preferred state set to "${newState}"`)
    } else {
      ElMessage.success('Preferred state cleared')
    }
  } catch (error) {
    console.error('Failed to update preferred state:', error)
    ElMessage.error('Failed to update preferred state')
  }
}

// Watch for changes in nodes or edges to reload metrics
watch(
  () => [projectStore.nodes, projectStore.edges],
  () => {
    loadMetrics()
  },
  { deep: true }
)

onMounted(() => {
  loadMetrics()
})
</script>

<style scoped>
.metrics-editor {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  background-color: var(--el-bg-color-page);
}

.metrics-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background-color: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color);
}

.toolbar-left {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.statistics {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
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

.metrics-container {
  flex: 1;
  overflow: hidden;
  padding: 16px;
}

.node-label {
  font-weight: 500;
}
</style>
