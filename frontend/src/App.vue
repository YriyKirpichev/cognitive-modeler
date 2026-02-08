<template>
  <div class="app-container">
    <TopBar />

    <div class="main-content">
      <SidePanel @tab-change="handleTabChange" @select-scenario="handleSelectScenario">
        <template #default="{ activeTab }">
          <div v-if="activeTab === 'graph'">
          </div>
          <ScenariosPanel
            v-else-if="activeTab === 'scenarios'"
            :selected-scenario-id="selectedScenarioId"
            @select-scenario="handleSelectScenario"
            @scenarios-updated="handleScenariosUpdated"
          />
        </template>
      </SidePanel>

      <div class="workspace">
        <GraphEditor v-if="currentTab === 'graph'" />
        <MatrixEditor v-else-if="currentTab === 'matrix'" />
        <MetricsEditor v-else-if="currentTab === 'metrics'" />
        <div v-else-if="currentTab === 'scenarios'" class="scenarios-view">
          <ScenarioEditor
            v-if="selectedScenarioId"
            :scenario-id="selectedScenarioId"
            @back="selectedScenarioId = null"
            @scenario-updated="handleScenariosUpdated"
          />
          <div v-else class="no-selection">
            <el-empty description="Select a scenario from the side panel or create a new one" />
          </div>
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
import MetricsEditor from './components/MetricsEditor.vue'
import ScenariosPanel from './components/ScenariosPanel.vue'
import ScenarioEditor from './components/ScenarioEditor.vue'
import { useProjectStore } from './stores/project'
import { useElectronMenu } from './composables/useElectronMenu'

const projectStore = useProjectStore()
const currentTab = ref('graph')
const selectedScenarioId = ref<string | null>(null)

useElectronMenu()

function handleTabChange(tab: string) {
  currentTab.value = tab
  // Reset selected scenario when switching away from scenarios tab
  if (tab !== 'scenarios') {
    selectedScenarioId.value = null
  }
}

function handleSelectScenario(scenarioId: string) {
  // If empty string is passed (from delete), clear selection
  if (!scenarioId) {
    selectedScenarioId.value = null
    return
  }
  
  selectedScenarioId.value = scenarioId
  // Switch to scenarios tab if not already there
  if (currentTab.value !== 'scenarios') {
    currentTab.value = 'scenarios'
  }
}

function handleScenariosUpdated() {
  // This will trigger re-render of scenarios panel
  // Could be used to reload scenarios list if needed
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

.scenarios-view {
  height: 100%;
  overflow: hidden;
}

.no-selection {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
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