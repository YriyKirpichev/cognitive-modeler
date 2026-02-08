<template>
  <div class="scenario-editor">
    <div v-if="isLoading" class="loading-container">
      <el-skeleton :rows="8" animated />
    </div>

    <div v-else-if="scenario" class="editor-container">

      <!-- Scenario Info Panel -->
      <el-card class="info-panel">
        <template #header>
          <div class="panel-header">
            <span class="scenario-title">{{ scenario.params.name }}</span>
            <el-tag v-if="scenario.result" type="success" :icon="CircleCheck">Completed</el-tag>
          </div>
        </template>

        <div class="info-content">
          <div v-if="scenario.params.description" class="description">
            <el-text type="info">{{ scenario.params.description }}</el-text>
          </div>

          <div class="params-grid">
            <div class="param-item">
              <label>Activation Function:</label>
              <span>{{ scenario.params.activation_type }}</span>
            </div>
            <div class="param-item">
              <label>Use Confidence:</label>
              <span>{{ scenario.params.use_confidence ? 'Yes' : 'No' }}</span>
            </div>
            <div class="param-item">
              <label>Iteration Mode:</label>
              <span>{{ scenario.params.iteration_mode === 'fixed' ? 'Fixed' : 'Auto Convergence' }}</span>
            </div>
            <div class="param-item">
              <label>Max Iterations:</label>
              <span>{{ scenario.params.max_iterations }}</span>
            </div>
            <div v-if="scenario.params.iteration_mode === 'auto'" class="param-item">
              <label>Convergence Threshold:</label>
              <span>{{ scenario.params.convergence_threshold }}</span>
            </div>
          </div>

          <div v-if="scenario.result" class="result-summary">
            <el-divider />
            <el-descriptions title="Simulation Results" :column="3" border>
              <el-descriptions-item label="Iterations">
                {{ scenario.result.iterations_count }}
              </el-descriptions-item>
              <el-descriptions-item label="Converged">
                <el-tag :type="scenario.result.converged ? 'success' : 'warning'">
                  {{ scenario.result.converged ? 'Yes' : 'No' }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="Timestamp">
                {{ formatTimestamp(scenario.result.timestamp) }}
              </el-descriptions-item>
            </el-descriptions>
          </div>
          <div class="editor-header">
            <div class="header-actions">
              <el-button :icon="Edit" @click="showEditDialog = true">Edit Parameters</el-button>
              <el-button
                type="primary"
                :icon="VideoPlay"
                @click="handleRunSimulation"
                :loading="isRunning"
                :disabled="!canRunSimulation"
              >
                Run Simulation
              </el-button>
            </div>
          </div>

        </div>
      </el-card>

      <!-- Initial States Table -->
      <el-card class="initial-states-panel">
        <template #header>
          <span>Initial Node States</span>
        </template>
        <el-table :data="initialStatesTableData" stripe max-height="300">
          <el-table-column prop="label" label="Node" min-width="150" />
          <el-table-column label="Initial Value" width="200" align="center">
            <template #default="scope">
              <el-input-number
                v-model="scope.row.value"
                :min="stateRange[0]"
                :max="stateRange[1]"
                :step="0.1"
                :precision="2"
                size="small"
                @change="handleInitialStateChange"
              />
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- Results Visualization -->
      <ScenarioGraphs 
        v-if="simulationResultWithHistory" 
        :result="simulationResultWithHistory" 
        :nodes="projectStore.nodes" 
      />
    </div>

    <!-- Edit Parameters Dialog -->
    <el-dialog v-model="showEditDialog" title="Edit Scenario Parameters" width="500px">
      <el-form :model="editForm" label-width="140px" label-position="left">
        <el-form-item label="Name" required>
          <el-input v-model="editForm.name" placeholder="Scenario name" />
        </el-form-item>
        <el-form-item label="Description">
          <el-input
            v-model="editForm.description"
            type="textarea"
            :rows="2"
            placeholder="Optional description"
          />
        </el-form-item>
        <el-form-item label="Activation Type" required>
          <el-select v-model="editForm.activation_type">
            <el-option label="Sigmoid" value="sigmoid" />
            <el-option label="Tanh" value="tanh" />
          </el-select>
        </el-form-item>
        <el-form-item label="Use Confidence">
          <el-switch v-model="editForm.use_confidence" />
        </el-form-item>
        <el-form-item label="Iteration Mode" required>
          <el-select v-model="editForm.iteration_mode">
            <el-option label="Fixed Iterations" value="fixed" />
            <el-option label="Auto Convergence" value="auto" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="editForm.iteration_mode === 'fixed'" label="Max Iterations">
          <el-input-number v-model="editForm.max_iterations" :min="1" :max="1000" />
        </el-form-item>
        <el-form-item v-if="editForm.iteration_mode === 'auto'" label="Threshold">
          <el-input-number
            v-model="editForm.convergence_threshold"
            :min="0.0001"
            :max="1"
            :step="0.001"
            :precision="4"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">Cancel</el-button>
        <el-button type="primary" @click="handleUpdateScenario" :loading="isSaving">Update</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { Edit, VideoPlay, CircleCheck } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { scenariosApi } from '@/services/scenariosApi'
import { useProjectStore } from '@/stores/project'
import ScenarioGraphs from './ScenarioGraphs.vue'
import type { Scenario, ScenarioParams } from '@/types/cognitive_map_models'
import { AxiosError } from 'axios'

const props = defineProps<{
  scenarioId: string
}>()

const emit = defineEmits<{
  (e: 'back'): void
  (e: 'scenario-updated'): void
}>()

const projectStore = useProjectStore()

const scenario = ref<Scenario | null>(null)
const isLoading = ref(false)
const isRunning = ref(false)
const isSaving = ref(false)
const showEditDialog = ref(false)

// Get simulation result from store
const simulationResultWithHistory = computed(() => {
  return projectStore.getSimulationResult(props.scenarioId)
})

interface EditForm {
  name: string
  description: string
  activation_type: 'sigmoid' | 'tanh'
  use_confidence: boolean
  iteration_mode: 'fixed' | 'auto'
  max_iterations: number
  convergence_threshold: number
}

const editForm = ref<EditForm>({
  name: '',
  description: '',
  activation_type: 'sigmoid',
  use_confidence: false,
  iteration_mode: 'fixed',
  max_iterations: 100,
  convergence_threshold: 0.001,
})

const stateRange = computed(() => projectStore.fcm?.state_range || [-1, 1])

const canRunSimulation = computed(() => {
  return projectStore.nodes.length > 0 && projectStore.edges.length > 0
})

interface InitialStateRow {
  nodeId: string
  label: string
  value: number
}

const initialStatesTableData = computed<InitialStateRow[]>(() => {
  if (!scenario.value) return []

  return projectStore.nodes.map((node) => ({
    nodeId: node.id,
    label: node.label || node.id,
    value: scenario.value!.params.initial_states[node.id] || 0,
  }))
})

async function loadScenario() {
  isLoading.value = true
  try {
    scenario.value = await scenariosApi.getScenario(props.scenarioId)
  } catch (error) {
    console.error('Failed to load scenario:', error)
    ElMessage.error('Failed to load scenario')
    emit('back')
  } finally {
    isLoading.value = false
  }
}

async function handleRunSimulation() {
  if (!scenario.value) return

  if (!canRunSimulation.value) {
    ElMessage.warning('Cannot run simulation: graph must have nodes and edges')
    return
  }

  isRunning.value = true
  try {
    const result = await scenariosApi.runScenario(props.scenarioId)
    
    projectStore.setSimulationResult(props.scenarioId, result)
    await loadScenario()
    await projectStore.refreshScenarios()
    emit('scenario-updated')
    
    ElMessage.success(
      `Simulation completed: ${result.iterations_count} iterations, converged: ${result.converged ? 'Yes' : 'No'}`
    )
  } catch (error) {
    console.error('Failed to run simulation:', error)
    
    let errorMessage = 'Failed to run simulation'
    if (error instanceof AxiosError) {
      errorMessage = error.response?.data?.detail || errorMessage
    }
    
    ElMessage.error(errorMessage)
  } finally {
    isRunning.value = false
  }
}

function handleInitialStateChange() {
  if (!scenario.value) return

  // Update scenario params with new initial states
  const updatedInitialStates: Record<string, number> = {}
  initialStatesTableData.value.forEach((row) => {
    updatedInitialStates[row.nodeId] = row.value
  })

  const updatedParams: ScenarioParams = {
    ...scenario.value.params,
    initial_states: updatedInitialStates,
  }

  // Save updated params
  saveScenarioParams(updatedParams)
}

async function saveScenarioParams(params: ScenarioParams) {
  try {
    await scenariosApi.updateScenario(props.scenarioId, params)
    scenario.value!.params = params
    // Refresh scenarios in store
    await projectStore.refreshScenarios()
  } catch (error) {
    console.error('Failed to save scenario params:', error)
    ElMessage.error('Failed to save changes')
  }
}

function handleUpdateScenario() {
  if (!editForm.value.name.trim()) {
    ElMessage.warning('Please enter a scenario name')
    return
  }

  if (!scenario.value) return

  const updatedParams: ScenarioParams = {
    ...scenario.value.params,
    name: editForm.value.name,
    description: editForm.value.description,
    activation_type: editForm.value.activation_type,
    use_confidence: editForm.value.use_confidence,
    iteration_mode: editForm.value.iteration_mode,
    max_iterations: editForm.value.max_iterations,
    convergence_threshold: editForm.value.convergence_threshold,
  }

  isSaving.value = true
  scenariosApi
    .updateScenario(props.scenarioId, updatedParams)
    .then(async () => {
      ElMessage.success('Scenario updated successfully')
      showEditDialog.value = false
      await loadScenario()
      // Refresh scenarios in store
      await projectStore.refreshScenarios()
      // Emit event to update scenarios panel
      emit('scenario-updated')
    })
    .catch((error) => {
      console.error('Failed to update scenario:', error)
      ElMessage.error('Failed to update scenario')
    })
    .finally(() => {
      isSaving.value = false
    })
}

function formatTimestamp(timestamp: string): string {
  return new Date(timestamp).toLocaleString()
}

watch(
  () => props.scenarioId,
  () => {
    loadScenario()
  }
)

watch(showEditDialog, (value) => {
  if (value && scenario.value) {
    editForm.value = {
      name: scenario.value.params.name,
      description: scenario.value.params.description || '',
      activation_type: scenario.value.params.activation_type,
      use_confidence: scenario.value.params.use_confidence,
      iteration_mode: scenario.value.params.iteration_mode,
      max_iterations: scenario.value.params.max_iterations,
      convergence_threshold: scenario.value.params.convergence_threshold || 0.001,
    }
  }
})

onMounted(() => {
  loadScenario()
})
</script>

<style scoped>
.scenario-editor {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 16px;
  overflow: hidden;
}

.loading-container {
  padding: 24px;
}

.editor-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
  overflow-y: auto;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.info-panel {
  flex-shrink: 0;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.scenario-title {
  font-size: 18px;
  font-weight: 600;
}

.info-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.description {
  padding: 8px 0;
}

.params-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.param-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.param-item label {
  font-weight: 500;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.param-item span {
  font-size: 14px;
}

.result-summary {
  margin-top: 8px;
}

.initial-states-panel {
  flex-shrink: 0;
}
</style>
