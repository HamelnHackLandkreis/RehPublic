<template>
  <div class="map-page">
    <h1 class="text-2xl font-bold mb-4">Wildlife Map</h1>
    <LeafletMap 
      :center="[51.9244, 9.4305]" 
      :zoom="13"
      height="600px"
      :markers="sampleMarkers"
    />
  </div>
</template>

<script setup lang="ts">
// Sample markers for demonstration
const sampleMarkers = ref([
  {
    position: [51.9244, 9.4305],
    popup: 'Hameln City Center'
  },
  {
    position: [51.9344, 9.4405],
    popup: 'Wildlife Sighting 1'
  }
])
</script>

<style scoped>
.map-page {
  padding: 20px;
  height: 100vh;
}
</style>
