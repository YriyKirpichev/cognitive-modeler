<template>
  <el-card class="graphs-panel">
    <template #header>
      <span>Simulation Results</span>
    </template>
    <div class="graphs-container">
      <!-- Bar Chart for Final States -->
      <div class="chart-section">
        <h3>Final Node States</h3>
        <div ref="chartRef" class="chart" style="width: 100%; height: 400px"></div>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import * as echarts from 'echarts'
import type { Scenario, Node } from '@/types/cognitive_map_models'

const props = defineProps<{
  scenario: Scenario
  nodes: Node[]
}>()

const chartRef = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null

function renderChart() {
  if (!chartRef.value || !props.scenario.result) return

  // Dispose old chart instance if exists
  if (chartInstance) {
    chartInstance.dispose()
  }

  // Create new chart instance
  chartInstance = echarts.init(chartRef.value)

  // Prepare data
  const nodeLabels: string[] = []
  const finalValues: number[] = []
  const colors: string[] = []

  // Create a map of node id to label
  const nodeMap = new Map<string, Node>()
  props.nodes.forEach((node) => {
    nodeMap.set(node.id, node)
  })

  // Sort by node label for better visualization
  const sortedEntries = Object.entries(props.scenario.result.final_states).sort((a, b) => {
    const nodeA = nodeMap.get(a[0])
    const nodeB = nodeMap.get(b[0])
    const labelA = nodeA?.label || a[0]
    const labelB = nodeB?.label || b[0]
    return labelA.localeCompare(labelB)
  })

  sortedEntries.forEach(([nodeId, value]) => {
    const node = nodeMap.get(nodeId)
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
      formatter: (params: any) => {
        const data = params[0]
        return `${data.name}<br/>Final State: ${data.value.toFixed(4)}`
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
          color: (params: any) => {
            return colors[params.dataIndex] || '#909399'
          },
        },
        label: {
          show: true,
          position: 'top',
          formatter: (params: any) => {
            return params.value.toFixed(2)
          },
          fontSize: 11,
        },
        barMaxWidth: 60,
      },
    ],
  }

  chartInstance.setOption(option)
}

// Handle window resize
function handleResize() {
  if (chartInstance) {
    chartInstance.resize()
  }
}

watch(
  () => props.scenario.result,
  () => {
    renderChart()
  },
  { deep: true }
)

onMounted(() => {
  renderChart()
  window.addEventListener('resize', handleResize)
})

// Cleanup on unmount
import { onBeforeUnmount } from 'vue'

onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.dispose()
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
  gap: 24px;
}

.chart-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
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
