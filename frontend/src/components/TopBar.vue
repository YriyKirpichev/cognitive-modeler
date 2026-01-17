<template>
  <div class="top-bar">
    <div class="project-info">
      <el-icon class="info-icon">
        <Document />
      </el-icon>
      <span v-if="currentFilePath" class="file-name">{{ fileName }}</span>
      <span v-else class="file-name">New Project</span>
      <el-tag v-if="hasUnsavedChanges" type="warning" size="small" effect="plain">
        Unsaved
      </el-tag>
    </div>
    <div class="meta-info">
      <span class="version">Version: {{ version }}</span>
      <span v-if="lastSaveTime" class="last-save">
        Last saved: {{ formattedLastSaveTime }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { Document } from '@element-plus/icons-vue'
import { useProjectStore } from '@/stores/project'

const projectStore = useProjectStore()

const lastSaveTime = ref<Date | null>(null)
let intervalId: number | null = null

const currentFilePath = computed(() => projectStore.currentFilePath)
const hasUnsavedChanges = computed(() => projectStore.hasUnsavedChanges)
const version = computed(() => projectStore.currentMap?.version ?? 1)

const fileName = computed(() => {
  if (!currentFilePath.value) return ''
  const parts = currentFilePath.value.split(/[/\\]/)
  return parts[parts.length - 1]
})

const timeSinceLastSave = ref<string>('')

const formattedLastSaveTime = computed(() => {
  return timeSinceLastSave.value
})

function updateTimeSinceLastSave() {
  if (!lastSaveTime.value) {
    timeSinceLastSave.value = 'never'
    return
  }

  const now = new Date()
  const diff = now.getTime() - lastSaveTime.value.getTime()
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)

  if (hours > 0) {
    timeSinceLastSave.value = `${hours}h ago`
  } else if (minutes > 0) {
    timeSinceLastSave.value = `${minutes}m ago`
  } else {
    timeSinceLastSave.value = `${seconds}s ago`
  }
}

onMounted(() => {
  updateTimeSinceLastSave()
  intervalId = window.setInterval(updateTimeSinceLastSave, 1000)
})

onUnmounted(() => {
  if (intervalId) {
    clearInterval(intervalId)
  }
})

// Обновляем время сохранения при сохранении проекта
const originalSave = projectStore.save
projectStore.save = async () => {
  await originalSave.call(projectStore)
  lastSaveTime.value = new Date()
}
</script>

<style scoped>
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background-color: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color);
  height: 40px;
}

.project-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-icon {
  font-size: 16px;
  color: var(--el-text-color-secondary);
}

.file-name {
  font-weight: 500;
  font-size: 14px;
}

.meta-info {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.version,
.last-save {
  white-space: nowrap;
}
</style>