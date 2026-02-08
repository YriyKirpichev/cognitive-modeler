<template>
  <el-card class="graphs-panel">
    <template #header>
      <span>Simulation Results</span>
    </template>
    <div class="graphs-container">
      <!-- Bar Chart for Final States -->
      <div class="chart-section">
        <h3>Final Node States</h3>
        <div ref="barChartRef" class="chart" style="height: 400px"></div>
      </div>

      <!-- Line Chart for Node States Over Time -->
      <div v-if="hasHistory" class="chart-section">
        <div class="chart-header">
          <h3>Node States Over Time</h3>
          <el-text v-if="result.converged && result.iterations_count" type="info" size="small">
            Converged at iteration {{ result.iterations_count }}
          </el-text>
        </div>
        <div ref="lineChartRef" class="chart" style="height: 500px"></div>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import type { ScenarioResult, Node } from '@/types/cognitive_map_models'
import type { 
  CallbackDataParams 
} from 'echarts/types/dist/shared'

const props = defineProps<{
  result: ScenarioResult
  nodes: Node[]
}>()

const barChartRef = ref<HTMLElement>()
const lineChartRef = ref<HTMLElement>()
let barChartInstance: echarts.ECharts | null = null
let lineChartInstance: echarts.ECharts | null = null

const hasHistory = computed(() => 
  props.result?.history && props.result.history.length > 0
)

const nodeMap = computed(() => {
  const map = new Map<string, Node>()
  props.nodes.forEach(node => map.set(node.id, node))
  return map
})

function renderBarChart() {
  if (!barChartRef.value || !props.result) return

  // Dispose old chart instance if exists
  if (barChartInstance) {
    barChartInstance.dispose()
  }

  // Create new chart instance
  barChartInstance = echarts.init(barChartRef.value)

  // Prepare data
  const nodeLabels: string[] = []
  const finalValues: number[] = []
  const colors: string[] = []

  // Sort by node label for better visualization
  const sortedEntries = Object.entries(props.result.final_states).sort((a, b) => {
    const nodeA = nodeMap.value.get(a[0])
    const nodeB = nodeMap.value.get(b[0])
    const labelA = nodeA?.label || a[0]
    const labelB = nodeB?.label || b[0]
    return labelA.localeCompare(labelB)
  })

  sortedEntries.forEach(([nodeId, value]) => {
    const node = nodeMap.value.get(nodeId)
    const label = node?.label || nodeId
    nodeLabels.push(label)
    finalValues.push(value)

    // Color based on value: positive (green), negative (red), near zero (gray)
    if (value > 0.1) {
      colors.push('#67c23a') // green
    } else if (value < -0.1) {
      colors.push('#f56c6c') // red
    } else {
      colors.push('#909399') // gray
    }
  })

  // Chart options
  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow',
      },
      formatter: (params: CallbackDataParams | CallbackDataParams[]) => {
        const data = params ? (Array.isArray(params) ? params[0] : params) : null
        return data ? `${data.name}<br/>Final State: ${(data.value as number).toFixed(4)}` : ''
      },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '10%',
      top: '10%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: nodeLabels,
      axisLabel: {
        interval: 0,
        rotate: nodeLabels.length > 10 ? 45 : 0,
        fontSize: 12,
      },
    },
    yAxis: {
      type: 'value',
      name: 'State Value',
      axisLabel: {
        formatter: '{value}',
      },
    },
    series: [
      {
        name: 'Final State',
        type: 'bar',
        data: finalValues,
        itemStyle: {
          color: (params: CallbackDataParams) => {
            return colors[params.dataIndex] || '#909399'
          },
        },
        label: {
          show: true,
          position: 'top',
          formatter: (params: CallbackDataParams) => {
            return (params.value as number).toFixed(2)
          },
          fontSize: 11,
        },
        barMaxWidth: 60,
      },
    ],
  }

  barChartInstance.setOption(option)
}

function renderLineChart() {
  if (!lineChartRef.value || !hasHistory.value) return

  const history = props.result.history!
  const iterations = history.length

  // Dispose old chart instance if exists
  if (lineChartInstance) {
    lineChartInstance.dispose()
  }

  // Create new chart instance
  lineChartInstance = echarts.init(lineChartRef.value)

  // X-axis data - iteration numbers (0, 1, 2, ...)
  const xAxisData = Array.from({ length: iterations }, (_, i) => i)

  // Create series for each node
  const series = props.nodes.map(node => {
    const hasPreferredState = node.preferred_state !== undefined && node.preferred_state !== null

    // Determine color based on preferred_state
    let color: string | undefined = undefined
    if (hasPreferredState) {
      color = node.preferred_state === 'increase' ? '#67c23a' : '#f56c6c'
    }

    return {
      name: node.label || node.id,
      type: 'line' as const,
      smooth: true,
      data: history.map(state => state[node.id]),
      lineStyle: {
        width: hasPreferredState ? 3 : 2,
        type: 'solid' as const,
      },
      itemStyle: {
        color: color,
      },
      emphasis: {
        focus: 'series' as const,
      },
    }
  })

  // Add convergence marker if converged
  const markLine = props.result.converged && props.result.iterations_count ? {
    silent: false,
    symbol: 'none',
    data: [{
      xAxis: props.result.iterations_count,
      label: {
        formatter: 'Converged',
        position: 'insideEndTop' as const,
      },
      lineStyle: {
        color: '#409eff',
        type: 'dashed' as const,
        width: 2,
      },
    }],
  } : undefined

  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
      },
    },
    legend: {
      data: props.nodes.map(n => n.label || n.id),
      type: 'scroll',
      bottom: 60,
      selected: {}, // All nodes visible by default, user can click to toggle
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '20%',
      top: '10%',
      containLabel: true,
    },
    toolbox: {
      feature: {
        dataZoom: {
          yAxisIndex: 'none', // Zoom only on X axis
        },
        restore: {}, // Reset zoom button
      },
    },
    dataZoom: [
      {
        type: 'inside', // Zoom with mouse wheel
        start: 0,
        end: 100,
      },
      {
        type: 'slider', // Slider at the bottom
        start: 0,
        end: 100,
        height: 20,
        bottom: 30,
      },
    ],
    xAxis: {
      type: 'category',
      data: xAxisData,
      name: 'Iteration',
      nameLocation: 'middle',
      nameGap: 35,
      boundaryGap: false,
    },
    yAxis: {
      type: 'value',
      name: 'State Value',
      nameLocation: 'middle',
      nameGap: 50,
    },
    series: series.map((s) => ({
      ...s,
      type: 'line' as const,
      markLine: markLine,
    })),
  }

  lineChartInstance.setOption(option)
}

// Handle window resize
function handleResize() {
  barChartInstance?.resize()
  lineChartInstance?.resize()
}

watch(
  () => props.result,
  () => {
    renderBarChart()
    renderLineChart()
  },
  { deep: true }
)

onMounted(() => {
  renderBarChart()
  renderLineChart()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  if (barChartInstance) {
    barChartInstance.dispose()
  }
  if (lineChartInstance) {
    lineChartInstance.dispose()
  }
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.graphs-panel {
  flex-shrink: 0;
}

.graphs-container {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.chart-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-section h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.chart {
  min-height: 400px;
}
</style>
