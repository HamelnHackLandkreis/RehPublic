<template>
  <div ref="mapContainer" class="leaflet-map" :style="{ height: height, width: width }"></div>
</template>

<script setup lang="ts">
import type { LatLngExpression, Map, Marker } from 'leaflet'
import { onMounted, onUnmounted, ref, watch } from 'vue'

interface Props {
  center?: [number, number]
  zoom?: number
  height?: string
  width?: string
  markers?: Array<{
    position: [number, number]
    popup?: string
    icon?: any
  }>
}

const props = withDefaults(defineProps<Props>(), {
  center: () => [51.9244, 9.4305], // Default: Hameln, Germany
  zoom: 13,
  height: '100%',
  width: '100%',
  markers: () => []
})

const mapContainer = ref<HTMLElement | null>(null)
let map: Map | null = null
let markerInstances: Marker[] = []

onMounted(async () => {
  if (!mapContainer.value) return

  // Dynamically import Leaflet to avoid SSR issues
  const L = await import('leaflet')
  
  // Import Leaflet CSS
  await import('leaflet/dist/leaflet.css')

  // Fix for default marker icons in Leaflet
  delete (L.Icon.Default.prototype as any)._getIconUrl
  L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
  })

  // Initialize map
  map = L.map(mapContainer.value).setView(props.center as LatLngExpression, props.zoom)

  // Add OpenStreetMap tile layer
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19,
  }).addTo(map)

  // Add markers if provided
  addMarkers()
})

const addMarkers = async () => {
  if (!map || props.markers.length === 0) return

  const L = await import('leaflet')
  
  // Clear existing markers
  markerInstances.forEach(marker => marker.remove())
  markerInstances = []

  // Add new markers
  props.markers.forEach(markerData => {
    if (!map) return
    
    // Create marker options, only include icon if it's provided
    const markerOptions = markerData.icon ? { icon: markerData.icon } : {}
    
    const marker = L.marker(markerData.position as LatLngExpression, markerOptions).addTo(map)

    if (markerData.popup) {
      marker.bindPopup(markerData.popup)
    }

    markerInstances.push(marker)
  })
}

// Watch for marker changes
watch(() => props.markers, () => {
  addMarkers()
}, { deep: true })

// Watch for center changes
watch(() => props.center, (newCenter) => {
  if (map) {
    map.setView(newCenter as LatLngExpression, props.zoom)
  }
})

onUnmounted(() => {
  if (map) {
    map.remove()
    map = null
  }
})

// Expose map instance for parent components
defineExpose({
  getMap: () => map
})
</script>

<style scoped>
.leaflet-map {
  min-height: 400px;
  border-radius: 8px;
  overflow: hidden;
}
</style>
