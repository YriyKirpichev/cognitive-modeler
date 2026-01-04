<template>
  <h1>Hello from Electron renderer!</h1>
  <p>👋</p>
  <button @click="sendCountRequest">Get Count from API</button>
  <p>Count: {{ count }}</p>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import apiClient from './services/api'

const count = ref(0)

const sendCountRequest = async () => {
  try {
    const response = await apiClient.get('/count')
    count.value = response.data.count
  } catch (error) {
    console.error('API Error:', error)
  }
}
</script>

<style scoped></style>
