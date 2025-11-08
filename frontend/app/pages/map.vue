<template>
  <div class="map-page">
    <h1 class="text-2xl font-bold mb-4">Wildlife Map</h1>
    <WildlifeMap 
      api-url="http://localhost:8000/locations"
      height=".5vh"
      :auto-center="true"
      :default-zoom="10"
    />
  </div>
</template>

<style scoped>
.map-page {
  padding: 20px;
  height: 100vh;
}
</style>
