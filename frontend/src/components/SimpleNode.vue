<template>
  <div 
    class="simple-node" 
    :style="nodeStyle"
  >
    <div class="node-label">{{ data.label }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { NodeProps } from '@vue-flow/core'

const props = defineProps<NodeProps>()

const nodeStyle = computed(() => ({
  backgroundColor: props.data.ui?.color || '#64748b',
  color: '#fff',
  borderRadius: '8px',
  padding: '12px 16px',
  border: props.selected ? '2px solid var(--el-color-primary)' : '2px solid transparent',
  boxShadow: props.selected ? '0 0 0 4px rgba(64, 158, 255, 0.2)' : 'none',
  cursor: 'grab',
  userSelect: 'none',
  minWidth: '80px',
  textAlign: 'center',
  transition: 'all 0.2s ease',
}))
</script>

<style scoped>
.simple-node {
  position: relative;
}

.simple-node:active {
  cursor: grabbing;
}

.simple-node:hover {
  transform: scale(1.05);
  filter: brightness(1.1);
}

.node-label {
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  pointer-events: none; /* Позволяет кликам проходить через текст к родительскому элементу */
}
</style>