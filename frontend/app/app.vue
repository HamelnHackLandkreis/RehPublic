<script setup lang="ts">
import { onMounted, ref } from 'vue'

const locations = ref([])
const error = ref(null)

// Test backend connection
onMounted(async () => {
  try {
    const response = await fetch('http://localhost:8000/locations')
    const data = await response.json()
    locations.value = data
    console.log('Backend connection successful:', data)
  } catch (err) {
    error.value = err.message
    console.error('Backend connection failed:', err)
  }
})
</script>

<template>
  <div class="p-8">
    <h1 class="text-2xl font-bold mb-4">Wildlife Camera Dashboard</h1>
    
    <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
      Backend connection failed: {{ error }}
    </div>
    
    <div v-else-if="locations.length > 0" class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
      Backend connected! Found {{ locations.length }} locations.
    </div>
    
    <div v-else class="bg-blue-100 border border-blue-400 text-blue-700 px-4 py-3 rounded mb-4">
      Connecting to backend...
    </div>
    
    <div v-if="locations.length > 0" class="mt-4">
      <h2 class="text-xl font-semibold mb-2">Locations:</h2>
      <ul class="list-disc pl-5">
        <li v-for="location in locations" :key="location.id" class="mb-1">
          {{ location.name }} ({{ location.latitude }}, {{ location.longitude }})
        </li>
      </ul>
    </div>
  </div>
</template>
