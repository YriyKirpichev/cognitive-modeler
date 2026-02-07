<template>
  <div class="scenarios-list">
    <div class="scenarios-header">
      <el-text size="large" tag="b">Scenarios</el-text>
      <el-button type="primary" :icon="Plus" @click="showCreateDialog = true">New Scenario</el-button>
    </div>

    <div v-if="scenarios.length === 0 && !isLoading" class="empty-state">
      <el-empty description="No scenarios yet. Create your first scenario to start simulation." />
    </div>

    <div v-else class="scenarios-container">
      <el-scrollbar>
        <div v-loading="isLoading" class="scenarios-grid">
          <el-card
            v-for="scenario in scenarios"
            :key="scenario.id"
            class="scenario-card"
            shadow="hover"
            @click="handleSelectScenario(scenario.id)"
          >
            <template #header>
              <div class="card-header">
                <span class="scenario-name">{{ scenario.params.name }}</span>
                <div class="card-actions">
                  <el-button
                    :icon="Edit"
                    size="small"
                    text
                    @click.stop="handleEditScenario(scenario)"
                  />
                  <el-button
                    :icon="Delete"
                    size="small"
                    text
                    type="danger"
                    @click.stop="handleDeleteScenario(scenario.id)"
                  />
                </div>
              </div>
            </template>
            <div class="scenario-info">
              <div v-if="scenario.params.description" class="scenario-description">
                {{ scenario.params.description }}
              </div>
              <div class="scenario-meta">
                <el-tag size="small">{{ scenario.params.activation_type }}</el-tag>
                <el-tag size="small" type="info">
                  {{ scenario.params.iteration_mode === 'fixed' ? `${scenario.params.max_iterations} iterations` : 'Auto convergence' }}
                </el-tag>
                <el-tag v-if="scenario.params.use_confidence" size="small" type="warning">
                  Confidence
                </el-tag>
              </div>
              <div v-if="scenario.result" class="scenario-result">
                <el-icon :size="16" color="#67c23a"><CircleCheck /></el-icon>
                <span>Completed: {{ scenario.result.iterations_count }} iterations</span>
              </div>
            </div>
          </el-card>
        </div>
      </el-scrollbar>
    </div>

    <!-- Create/Edit Dialog -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingScenario ? 'Edit Scenario' : 'Create New Scenario'"
      width="500px"
    >
      <el-form :model="formData" label-width="140px" label-position="left">
        <el-form-item label="Name" required>
          <el-input v-model="formData.name" placeholder="Scenario name" />
        </el-form-item>
        <el-form-item label="Description">
          <el-input v-model="formData.description" type="textarea" :rows="2" placeholder="Optional description" />
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
          <el-input-number v-model="formData.convergence_threshold" :min="0.0001" :max="1" :step="0.001" :precision="4" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">Cancel</el-button>
        <el-button type="primary" @click="handleSaveScenario" :loading="isSaving">
          {{ editingScenario ? 'Update' : 'Create' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { Plus, Edit, Delete, CircleCheck } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { scenariosApi } from '@/services/scenariosApi'
import { useProjectStore } from '@/stores/project'
import type { Scenario, ScenarioParams } from '@/types/cognitive_map_models'

const emit = defineEmits<{
  (e: 'select-scenario', scenarioId: string): void
}>()

const projectStore = useProjectStore()

const scenarios = ref<Scenario[]>([])
const isLoading = ref(false)
const isSaving = ref(false)
const showCreateDialog = ref(false)
const editingScenario = ref<Scenario | null>(null)

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
    scenarios.value = await scenariosApi.getScenarios()
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

function handleEditScenario(scenario: Scenario) {
  editingScenario.value = scenario
  formData.value = {
    name: scenario.params.name,
    description: scenario.params.description || '',
    activation_type: scenario.params.activation_type,
    use_confidence: scenario.params.use_confidence,
    iteration_mode: scenario.params.iteration_mode,
    max_iterations: scenario.params.max_iterations,
    convergence_threshold: scenario.params.convergence_threshold || 0.001,
  }
  showCreateDialog.value = true
}

async function handleSaveScenario() {
  if (!formData.value.name.trim()) {
    ElMessage.warning('Please enter a scenario name')
    return
  }

  // Build initial_states with all nodes set to 0 (or default value)
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
    if (editingScenario.value) {
      await scenariosApi.updateScenario(editingScenario.value.id, params)
      ElMessage.success('Scenario updated successfully')
    } else {
      await scenariosApi.createScenario(params)
      ElMessage.success('Scenario created successfully')
    }
    showCreateDialog.value = false
    resetForm()
    await loadScenarios()
  } catch (error) {
    console.error('Failed to save scenario:', error)
    ElMessage.error('Failed to save scenario')
  } finally {
    isSaving.value = false
  }
}

async function handleDeleteScenario(scenarioId: string) {
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

    await scenariosApi.deleteScenario(scenarioId)
    ElMessage.success('Scenario deleted successfully')
    await loadScenarios()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete scenario:', error)
      ElMessage.error('Failed to delete scenario')
    }
  }
}

function resetForm() {
  editingScenario.value = null
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

onMounted(() => {
  loadScenarios()
})
</script>

<style scoped>
.scenarios-list {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 16px;
  overflow: hidden;
}

.scenarios-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.scenarios-container {
  flex: 1;
  overflow: hidden;
}

.scenarios-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  padding-bottom: 16px;
}

.scenario-card {
  cursor: pointer;
  transition: all 0.3s;
}

.scenario-card:hover {
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.scenario-name {
  font-weight: 600;
  font-size: 16px;
}

.card-actions {
  display: flex;
  gap: 4px;
}

.scenario-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.scenario-description {
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.scenario-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.scenario-result {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--el-color-success);
  font-size: 14px;
}
</style>
