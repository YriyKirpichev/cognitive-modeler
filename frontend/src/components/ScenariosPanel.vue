<template>
  <div class="scenarios-panel">
    <div class="panel-header">
      <el-button type="primary" :icon="Plus" size="small" @click="showCreateDialog = true">
        New Scenario
      </el-button>
      <el-button
        :icon="Delete"
        size="small"
        type="danger"
        :disabled="!selectedScenarioId"
        @click="handleDeleteScenario"
      >
        Delete
      </el-button>
    </div>

    <div v-if="isLoading" class="loading-state">
      <el-skeleton :rows="3" animated />
    </div>

    <div v-else-if="scenarios.length === 0" class="empty-state">
      <el-empty description="No scenarios" :image-size="60" />
    </div>

    <div v-else class="scenarios-list">
      <div
        v-for="scenario in scenarios"
        :key="scenario.id"
        class="scenario-item"
        :class="{ selected: selectedScenarioId === scenario.id }"
        @click="handleSelectScenario(scenario.id)"
      >
        <div class="scenario-name">{{ scenario.params.name }}</div>
        <div class="scenario-meta">
          <el-tag v-if="scenario.result" size="small" type="success" effect="plain">
            <el-icon><CircleCheck /></el-icon>
          </el-tag>
        </div>
      </div>
    </div>

    <!-- Create Dialog -->
    <el-dialog v-model="showCreateDialog" title="Create New Scenario" width="500px">
      <el-form :model="formData" label-width="140px" label-position="left">
        <el-form-item label="Name" required>
          <el-input v-model="formData.name" placeholder="Scenario name" />
        </el-form-item>
        <el-form-item label="Description">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="2"
            placeholder="Optional description"
          />
        </el-form-item>
        <el-form-item label="Activation Type" required>
          <el-select v-model="formData.activation_type">
            <el-option label="Sigmoid" value="sigmoid" />
            <el-option label="Tanh" value="tanh" />
          </el-select>
        </el-form-item>
        <el-form-item label="Use Confidence">
          <el-switch v-model="formData.use_confidence" />
        </el-form-item>
        <el-form-item label="Iteration Mode" required>
          <el-select v-model="formData.iteration_mode">
            <el-option label="Fixed Iterations" value="fixed" />
            <el-option label="Auto Convergence" value="auto" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="formData.iteration_mode === 'fixed'" label="Max Iterations">
          <el-input-number v-model="formData.max_iterations" :min="1" :max="1000" />
        </el-form-item>
        <el-form-item v-if="formData.iteration_mode === 'auto'" label="Threshold">
          <el-input-number
            v-model="formData.convergence_threshold"
            :min="0.0001"
            :max="1"
            :step="0.001"
            :precision="4"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">Cancel</el-button>
        <el-button type="primary" @click="handleCreateScenario" :loading="isSaving">Create</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { Plus, CircleCheck, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { scenariosApi } from '@/services/scenariosApi'
import { useProjectStore } from '@/stores/project'
import type { ScenarioParams } from '@/types/cognitive_map_models'

const props = defineProps<{
  selectedScenarioId: string | null
}>()

const emit = defineEmits<{
  (e: 'select-scenario', scenarioId: string): void
  (e: 'scenarios-updated'): void
}>()

const projectStore = useProjectStore()

const isLoading = ref(false)
const isSaving = ref(false)
const showCreateDialog = ref(false)

// Use scenarios from store
const scenarios = computed(() => projectStore.scenarios)

interface FormData {
  name: string
  description: string
  activation_type: 'sigmoid' | 'tanh'
  use_confidence: boolean
  iteration_mode: 'fixed' | 'auto'
  max_iterations: number
  convergence_threshold: number
}

const formData = ref<FormData>({
  name: '',
  description: '',
  activation_type: 'sigmoid',
  use_confidence: false,
  iteration_mode: 'fixed',
  max_iterations: 100,
  convergence_threshold: 0.001,
})

async function loadScenarios() {
  isLoading.value = true
  try {
    await projectStore.refreshScenarios()
  } catch (error) {
    console.error('Failed to load scenarios:', error)
    ElMessage.error('Failed to load scenarios')
  } finally {
    isLoading.value = false
  }
}

function handleSelectScenario(scenarioId: string) {
  emit('select-scenario', scenarioId)
}

async function handleCreateScenario() {
  if (!formData.value.name.trim()) {
    ElMessage.warning('Please enter a scenario name')
    return
  }

  // Build initial_states with all nodes set to 0
  const initialStates: Record<string, number> = {}
  for (const node of projectStore.nodes) {
    initialStates[node.id] = 0
  }

  const params: ScenarioParams = {
    name: formData.value.name,
    description: formData.value.description,
    activation_type: formData.value.activation_type,
    use_confidence: formData.value.use_confidence,
    iteration_mode: formData.value.iteration_mode,
    max_iterations: formData.value.max_iterations,
    convergence_threshold: formData.value.convergence_threshold,
    initial_states: initialStates,
  }

  isSaving.value = true
  try {
    const newScenario = await scenariosApi.createScenario(params)
    ElMessage.success('Scenario created successfully')
    showCreateDialog.value = false
    resetForm()
    await loadScenarios()
    emit('scenarios-updated')
    // Auto-select newly created scenario
    emit('select-scenario', newScenario.id)
  } catch (error) {
    console.error('Failed to create scenario:', error)
    ElMessage.error('Failed to create scenario')
  } finally {
    isSaving.value = false
  }
}

function resetForm() {
  formData.value = {
    name: '',
    description: '',
    activation_type: 'sigmoid',
    use_confidence: false,
    iteration_mode: 'fixed',
    max_iterations: 100,
    convergence_threshold: 0.001,
  }
}

async function handleDeleteScenario() {
  if (!props.selectedScenarioId) return

  try {
    await ElMessageBox.confirm(
      'This will permanently delete the scenario. Continue?',
      'Warning',
      {
        confirmButtonText: 'Delete',
        cancelButtonText: 'Cancel',
        type: 'warning',
      }
    )

    await scenariosApi.deleteScenario(props.selectedScenarioId)
    ElMessage.success('Scenario deleted successfully')
    
    // Clear selection
    emit('select-scenario', '')
    
    // Reload list
    await loadScenarios()
    emit('scenarios-updated')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete scenario:', error)
      ElMessage.error('Failed to delete scenario')
    }
  }
}

onMounted(() => {
  loadScenarios()
})

// Watch for changes in nodes/edges to reload scenarios
watch(
  () => [projectStore.nodes.length, projectStore.edges.length],
  () => {
    loadScenarios()
  }
)
</script>

<style scoped>
.scenarios-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 12px;
}

.panel-header {
  flex-shrink: 0;
  display: flex;
  gap: 8px;
}

.loading-state {
  padding: 16px;
}

.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.scenarios-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.scenario-item {
  padding: 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid var(--el-border-color-lighter);
  background-color: var(--el-bg-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.scenario-item:hover {
  background-color: var(--el-fill-color-light);
  border-color: var(--el-border-color);
}

.scenario-item.selected {
  background-color: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary);
  color: var(--el-color-primary);
}

.scenario-name {
  font-size: 14px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.scenario-meta {
  flex-shrink: 0;
  margin-left: 8px;
}
</style>
