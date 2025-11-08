<template>
  <div class="map-page">
    <h1 class="text-2xl font-bold mb-4">Wildlife Map</h1>
    <LeafletMap 
      :center="[51.9244, 9.4305]" 
      :zoom="13"
      height="600px"
    />
  </div>
</template>

<style scoped>
.map-page {
  padding: 20px;
  height: 100vh;
}
</style>
