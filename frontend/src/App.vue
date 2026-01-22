<template>
  <div class="app-container">
    <TopBar />

    <div class="main-content">
      <SidePanel @tab-change="handleTabChange">
        <template #default="{ activeTab }">
          <div v-if="activeTab === 'graph'">
          </div>
        </template>
      </SidePanel>

      <div class="workspace">
        <GraphEditor v-if="currentTab === 'graph'" />
        <MatrixEditor v-else-if="currentTab === 'matrix'" />
        <div v-else-if="currentTab === 'metrics'" class="placeholder">
          <el-empty description="Metrics will be here" />
        </div>
        <div v-else-if="currentTab === 'scenarios'" class="placeholder">
          <el-empty description="Scenarios will be here" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import TopBar from './components/TopBar.vue'
import SidePanel from './components/SidePanel.vue'
import GraphEditor from './components/GraphEditor.vue'
import MatrixEditor from './components/MatrixEditor.vue'
import { useProjectStore } from './stores/project'
import { useElectronMenu } from './composables/useElectronMenu'

const projectStore = useProjectStore()
const currentTab = ref('graph')

useElectronMenu()

function handleTabChange(tab: string) {
  currentTab.value = tab
}

onMounted(async () => {
  try {
    await projectStore.loadMap()
  } catch (error) {
    console.error('Failed to load initial map:', error)
  }
})
</script>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

.main-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.workspace {
  flex: 1;
  overflow: hidden;
  background-color: var(--el-bg-color-page);
}

.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}
</style>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
    sans-serif;
}

#app {
  height: 100vh;
}
</style>