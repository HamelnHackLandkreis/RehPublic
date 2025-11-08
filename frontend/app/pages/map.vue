<template>
  <div class="map-page">
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
  height: 100vh;
}
</style>
