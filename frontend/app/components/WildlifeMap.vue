<template>
  <div class="wildlife-map-container">
    <div v-if="loading" class="loading-overlay">
      <div class="loading-spinner">Loading locations...</div>
    </div>
    <div v-else-if="error" class="error-message">
      <p>Error loading locations: {{ error }}</p>
      <button @click="fetchLocations" class="retry-button">Retry</button>
    </div>
    <LeafletMap 
      v-else
      ref="mapRef"
      :center="mapCenter" 
      :zoom="zoom"
      :height="height"
      :width="width"
      :markers="markers"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

interface Location {
  id: string
  name: string
  longitude: number
  latitude: number
  description: string
  image?: string
}

interface Props {
  apiUrl?: string
  height?: string
  width?: string
  autoCenter?: boolean
  defaultZoom?: number
}

const props = withDefaults(defineProps<Props>(), {
  apiUrl: 'http://localhost:8000/locations',
  height: '600px',
  width: '100%',
  autoCenter: true,
  defaultZoom: 10
})

const locations = ref<Location[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const zoom = ref(props.defaultZoom)
const mapRef = ref()
const markersWithIcons = ref<any[]>([])

const createCustomIcon = async (name: string, imageUrl?: string) => {
  const L = await import('leaflet')
  
  const imageSrc = imageUrl || '/fallback.JPG'
  
  const iconHtml = `
    <div class="avatar-marker">
      <div class="avatar-wrapper">
        <img 
          src="${imageSrc}" 
          alt="${name}"
          class="avatar-image"
          onerror="this.src='/fallback.JPG'"
        />
        <div class="camera-badge">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white">
            <path d="M9 2L7.17 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2h-3.17L15 2H9zm3 15c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5z"/>
          </svg>
        </div>
      </div>
      <div class="marker-label">${name}</div>
    </div>
  `
  
  return L.divIcon({
    html: iconHtml,
    className: 'custom-div-icon',
    iconSize: [60, 80],
    iconAnchor: [30, 80],
    popupAnchor: [0, -80]
  })
}

const updateMarkers = async () => {
  if (locations.value.length === 0) {
    markersWithIcons.value = []
    return
  }

  const newMarkers = await Promise.all(
    locations.value.map(async (location) => ({
      position: [location.latitude, location.longitude] as [number, number],
      popup: `
        <div class="marker-popup">
          <h3><strong>${location.name}</strong></h3>
          <p>${location.description}</p>
          <small>Lat: ${location.latitude}, Lon: ${location.longitude}</small>
        </div>
      `,
      icon: await createCustomIcon(location.name, location.image)
    }))
  )
  
  markersWithIcons.value = newMarkers
}

const markers = computed(() => markersWithIcons.value)

// Watch for location changes and create custom icons
watch(() => locations.value, () => {
  updateMarkers()
}, { deep: true })

const mapCenter = computed((): [number, number] => {
  if (!props.autoCenter || locations.value.length === 0) {
    return [51.9244, 9.4305] // Default: Hameln, Germany
  }

  // Calculate center from all locations
  const latSum = locations.value.reduce((sum, loc) => sum + loc.latitude, 0)
  const lonSum = locations.value.reduce((sum, loc) => sum + loc.longitude, 0)
  
  return [
    latSum / locations.value.length,
    lonSum / locations.value.length
  ]
})

const fetchLocations = async () => {
  loading.value = true
  error.value = null
  
  try {
    const response = await fetch(props.apiUrl)
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const data = await response.json()
    locations.value = data
    
    // Auto-adjust zoom based on number of locations
    if (props.autoCenter && locations.value.length > 1) {
      zoom.value = calculateZoomLevel()
    }
    
    // Update markers with custom icons
    await updateMarkers()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to fetch locations'
    console.error('Error fetching locations:', err)
  } finally {
    loading.value = false
  }
}

const calculateZoomLevel = (): number => {
  if (locations.value.length < 2) return props.defaultZoom

  // Calculate bounding box
  const lats = locations.value.map(loc => loc.latitude)
  const lons = locations.value.map(loc => loc.longitude)
  
  const latDiff = Math.max(...lats) - Math.min(...lats)
  const lonDiff = Math.max(...lons) - Math.min(...lons)
  
  const maxDiff = Math.max(latDiff, lonDiff)
  
  // Simple zoom calculation based on coordinate spread
  if (maxDiff > 5) return 6
  if (maxDiff > 2) return 8
  if (maxDiff > 1) return 9
  if (maxDiff > 0.5) return 10
  if (maxDiff > 0.1) return 12
  return 13
}

onMounted(() => {
  fetchLocations()
})

// Expose methods for parent components
defineExpose({
  refresh: fetchLocations,
  getLocations: () => locations.value
})
</script>

<style scoped>
.wildlife-map-container {
  position: relative;
  width: 100%;
}

.loading-overlay {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  background-color: #f5f5f5;
  border-radius: 8px;
}

.loading-spinner {
  font-size: 18px;
  color: #666;
  padding: 20px;
}

.error-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  background-color: #fee;
  border-radius: 8px;
  padding: 20px;
}

.error-message p {
  color: #c33;
  margin-bottom: 16px;
  font-weight: 500;
}

.retry-button {
  padding: 8px 16px;
  background-color: #3b82f6;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
}

.retry-button:hover {
  background-color: #2563eb;
}

:deep(.marker-popup) {
  padding: 4px;
}

:deep(.marker-popup h3) {
  margin: 0 0 8px 0;
  font-size: 16px;
  color: #1f2937;
}

:deep(.marker-popup p) {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #4b5563;
}

:deep(.marker-popup small) {
  font-size: 12px;
  color: #6b7280;
}

/* Custom marker styles */
:deep(.custom-div-icon) {
  background: transparent;
  border: none;
}

:deep(.avatar-marker) {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
}

:deep(.avatar-wrapper) {
  position: relative;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  overflow: hidden;
  border: 3px solid white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  transition: transform 0.2s, box-shadow 0.2s;
  background-color: #f3f4f6;
}

:deep(.avatar-marker:hover .avatar-wrapper) {
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
}

:deep(.avatar-image) {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

:deep(.camera-badge) {
  position: absolute;
  bottom: -2px;
  right: -2px;
  width: 20px;
  height: 20px;
  background-color: #2563eb;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

:deep(.camera-badge svg) {
  width: 12px;
  height: 12px;
}

:deep(.marker-label) {
  margin-top: 4px;
  padding: 4px 10px;
  background-color: rgba(0, 0, 0, 0.85);
  color: white;
  font-size: 12px;
  font-weight: 600;
  border-radius: 4px;
  white-space: nowrap;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}
</style>
