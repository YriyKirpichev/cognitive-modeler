<template>
  <div
    class="matrix-cell"
    :class="{
      'is-diagonal': isDiagonal,
      'has-value': weight !== null && weight !== undefined,
      'confidence-high': confidenceLevel === 'high',
      'confidence-medium': confidenceLevel === 'medium',
      'confidence-low': confidenceLevel === 'low',
      'weight-positive': weight !== null && weight > 0,
      'weight-negative': weight !== null && weight < 0
    }"
    @click="openEditDialog"
  >
    <span v-if="weight !== null && weight !== undefined" class="weight-value">
      {{ weight.toFixed(2) }}
    </span>
    <span v-else class="empty-cell">-</span>
  </div>

  <!-- Edit dialog -->
  <el-dialog v-model="showDialog" title="Edit Connection" width="400px">
    <el-form label-position="top">
      <el-form-item label="Weight [-1 to 1]">
        <el-slider v-model="editWeight" :min="-1" :max="1" :step="0.1" show-input />
      </el-form-item>
      <el-form-item label="Confidence [0 to 1]">
        <el-slider v-model="editConfidence" :min="0" :max="1" :step="0.1" show-input />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button
        v-if="weight !== null && weight !== undefined"
        type="danger"
        @click="deleteConnection"
      >
        Delete
      </el-button>
      <el-button @click="showDialog = false">Cancel</el-button>
      <el-button type="primary" @click="saveChanges">Save</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps<{
  sourceIndex: number
  targetIndex: number
  weight: number | null | undefined
  confidence: number | null | undefined
  isDiagonal: boolean
}>()

const emit = defineEmits<{
  update: [event: {
    sourceIndex: number
    targetIndex: number
    weight: number | null
    confidence: number | null
  }]
}>()

const showDialog = ref(false)
const editWeight = ref(0)
const editConfidence = ref(1.0)

const confidenceLevel = computed(() => {
  if (props.confidence === null || props.confidence === undefined) return null
  if (props.confidence >= 0.8) return 'high'
  if (props.confidence >= 0.5) return 'medium'
  return 'low'
})

function openEditDialog() {
  if (props.isDiagonal) {
    ElMessage.warning('Cannot create self-loop (diagonal cells are locked)')
    return
  }

  editWeight.value = props.weight ?? 0
  editConfidence.value = props.confidence ?? 1.0
  showDialog.value = true
}

function saveChanges() {
  emit('update', {
    sourceIndex: props.sourceIndex,
    targetIndex: props.targetIndex,
    weight: editWeight.value,
    confidence: editConfidence.value
  })
  showDialog.value = false
}

function deleteConnection() {
  emit('update', {
    sourceIndex: props.sourceIndex,
    targetIndex: props.targetIndex,
    weight: null,
    confidence: null
  })
  showDialog.value = false
}
</script>

<style scoped>
.matrix-cell {
  padding: 12px;
  cursor: pointer;
  border-radius: 4px;
  text-align: center;
  transition: all 0.2s;
  min-height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  border: 1px solid var(--el-border-color-lighter);
}

.matrix-cell:not(.is-diagonal):hover {
  background-color: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary-light-5);
}

.matrix-cell.is-diagonal {
  background-color: var(--el-fill-color-darker);
  cursor: not-allowed;
  opacity: 0.5;
}

.matrix-cell.has-value {
  font-weight: bold;
}

/* Weight direction visualization */
.matrix-cell.weight-positive {
  color: #67c23a;
}

.matrix-cell.weight-negative {
  color: #f56c6c;
}

/* Confidence level visualization via background color */
.matrix-cell.confidence-high:not(.is-diagonal) {
  background-color: rgba(103, 194, 58, 0.15);
}

.matrix-cell.confidence-medium:not(.is-diagonal) {
  background-color: rgba(230, 162, 60, 0.15);
}

.matrix-cell.confidence-low:not(.is-diagonal) {
  background-color: rgba(245, 108, 108, 0.15);
}

.matrix-cell.confidence-high:not(.is-diagonal):hover {
  background-color: rgba(103, 194, 58, 0.25);
}

.matrix-cell.confidence-medium:not(.is-diagonal):hover {
  background-color: rgba(230, 162, 60, 0.25);
}

.matrix-cell.confidence-low:not(.is-diagonal):hover {
  background-color: rgba(245, 108, 108, 0.25);
}

.empty-cell {
  color: var(--el-text-color-placeholder);
  font-size: 12px;
}

.weight-value {
  font-family: monospace;
}
</style>
