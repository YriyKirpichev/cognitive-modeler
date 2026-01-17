<template>
  <div class="side-panel" :class="{ collapsed: isCollapsed }">
    <div v-if="!isCollapsed" class="panel-content">
      <div class="tabs-list">
        <div v-for="tab in tabs" :key="tab.name" class="tab-item" :class="{ active: activeTab === tab.name }"
          @click="handleTabChange(tab.name)">
          <el-icon class="tab-icon">
            <component :is="tab.icon" />
          </el-icon>
          <span class="tab-label">{{ tab.label }}</span>
        </div>
      </div>

      <div class="tab-content">
        <slot :active-tab="activeTab"></slot>
      </div>
    </div>

    <div class="resize-handle" @mousedown="startResize"></div>

    <div class="collapse-btn" @click="toggleCollapse">
      <el-icon>
        <DArrowLeft v-if="!isCollapsed" />
        <DArrowRight v-else />
      </el-icon>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Share, Grid, DataAnalysis, VideoPlay, DArrowLeft, DArrowRight } from '@element-plus/icons-vue'

const emit = defineEmits<{
  (e: 'tab-change', tab: string): void
}>()

const tabs = [
  { name: 'graph', label: 'Graph', icon: Share },
  { name: 'matrix', label: 'Matrix', icon: Grid },
  { name: 'metrics', label: 'Metrics', icon: DataAnalysis },
  { name: 'scenarios', label: 'Scenarios', icon: VideoPlay },
]

const activeTab = ref('graph')
const isCollapsed = ref(false)

function handleTabChange(tabName: string) {
  activeTab.value = tabName
  emit('tab-change', tabName)
}

function toggleCollapse() {
  isCollapsed.value = !isCollapsed.value
}

// Resize logic
const isResizing = ref(false)
const panelWidth = ref(280)

function startResize(e: MouseEvent) {
  isResizing.value = true
  const startX = e.clientX
  const startWidth = panelWidth.value

  function onMouseMove(e: MouseEvent) {
    if (!isResizing.value) return
    const diff = e.clientX - startX
    const newWidth = Math.max(200, Math.min(600, startWidth + diff))
    panelWidth.value = newWidth
    document.documentElement.style.setProperty('--side-panel-width', `${newWidth}px`)
  }

  function onMouseUp() {
    isResizing.value = false
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
  }

  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}
</script>

<style scoped>
.side-panel {
  position: relative;
  width: var(--side-panel-width, 280px);
  background-color: var(--el-bg-color);
  border-right: 1px solid var(--el-border-color);
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
}

.side-panel.collapsed {
  width: 40px;
}

.panel-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.tabs-list {
  padding: 8px;
  border-bottom: 1px solid var(--el-border-color);
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  margin-bottom: 4px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;
}

.tab-item:hover {
  background-color: var(--el-fill-color-light);
}

.tab-item.active {
  background-color: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  font-weight: 500;
}

.tab-icon {
  font-size: 18px;
  flex-shrink: 0;
}

.tab-label {
  font-size: 14px;
}

.tab-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.resize-handle {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  cursor: ew-resize;
  background-color: transparent;
  transition: background-color 0.2s;
}

.resize-handle:hover {
  background-color: var(--el-color-primary);
}

.collapse-btn {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  background-color: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.collapse-btn:hover {
  background-color: var(--el-fill-color-light);
}
</style>