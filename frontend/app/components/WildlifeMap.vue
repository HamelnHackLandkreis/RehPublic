<template>
  <div class="wildlife-map-container">
    <div v-if="loading" class="loading-overlay">
      <div class="loading-spinner">Loading locations...</div>
    </div>
    <div v-else-if="error" class="error-message">
      <p>Error loading locations: {{ error }}</p>
      <button @click="fetchLocations" class="retry-button">Retry</button>
    </div>
    <LeafletMap v-else ref="mapRef" :center="mapCenter" :zoom="zoom" :height="height" :width="width"
      :markers="markers" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

const route = useRoute()

interface ImageDetection {
  image_id: string
  location_id: string
  upload_timestamp: string
  detections: any[]
}

interface Location {
  id: string
  name: string
  longitude: number
  latitude: number
  description: string
  images?: ImageDetection[]
}

interface LocationsResponse {
  locations: Location[]
}

interface Props {
  height?: string
  width?: string
  autoCenter?: boolean
  defaultZoom?: number
  defaultLatitude?: number
  defaultLongitude?: number
  defaultDistanceRange?: number
}

const props = withDefaults(defineProps<Props>(), {
  defaultLatitude: 52.10181392588904,
  defaultLongitude: 9.37544441225413,
  defaultDistanceRange: 100000000000,
  height: '100%',
  width: '100%',
  autoCenter: true,
  defaultZoom: 10
})

const apiUrl = useApiUrl()

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
    locations.value.map(async (location) => {
      // Get the first image if available
      const imageUrl = location.images && location.images.length > 0 && location.images[0]
        ? `${apiUrl}/images/${location.images[0].image_id}/base64`
        : undefined

      const imageCount = location.images?.length || 0

      // Create image gallery HTML
      let imagesHtml = ''
      if (location.images && location.images.length > 0) {
        imagesHtml = `
          <div class="popup-images">
            ${location.images.map(img => {
              const hasDetections = img.detections && img.detections.length > 0
              const imageContent = `
                <div class="image-container">
                  <img 
                    src="${apiUrl}/images/${img.image_id}/base64" 
                    alt="Camera image"
                    class="popup-image"
                    onerror="this.style.display='none'"
                  />
                  <div class="click-overlay">
                    <svg class="click-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/>
                    </svg>
                    <span class="click-text">Click to match</span>
                  </div>
                </div>
              `
              
              return `
              <div class="popup-image-wrapper">
                <a href="/match/${img.image_id}" class="image-link">${imageContent}</a>
                <div class="image-info">
                  <small>${new Date(img.upload_timestamp).toLocaleString()}</small>
                  ${hasDetections ?
            `<a href="/match/${img.image_id}" class="detection-badge-link">
              <span class="detection-badge">${img.detections.length} detection${img.detections.length !== 1 ? 's' : ''}</span>
            </a>`
            : `<span class="no-detection-badge">No detection</span>`}
                </div>
              </div>
            `}).join('')}
          </div>
        `
      }

      return {
        position: [location.latitude, location.longitude] as [number, number],
        popup: `
          <div class="marker-popup w-75">
            <h3><strong>${location.name}</strong></h3>
            ${imagesHtml}
          </div>
        `,
        icon: await createCustomIcon(location.name, imageUrl)
      }
    })
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
    // Build base URL with required parameters
    const params = new URLSearchParams({
      latitude: props.defaultLatitude.toString(),
      longitude: props.defaultLongitude.toString(),
      distance_range: props.defaultDistanceRange.toString()
    })

    // Add optional species parameter from route
    if (route.query.species && typeof route.query.species === 'string') {
      params.set('species', route.query.species)
    }

    // Add optional time_start parameter from route
    if (route.query.time_start && typeof route.query.time_start === 'string') {
      params.set('time_start', route.query.time_start)
    }

    // Add optional time_end parameter from route
    if (route.query.time_end && typeof route.query.time_end === 'string') {
      params.set('time_end', route.query.time_end)
    }

    const spottingsUrl = `${apiUrl}/spottings?${params.toString()}`
    const response = await fetch(spottingsUrl)

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data: LocationsResponse = await response.json()
    locations.value = data.locations

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

// Watch for route query changes and refetch
watch(() => route.query, () => {
  fetchLocations()
}, { deep: true })

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
  min-width: 100%;
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

:deep(.popup-stats) {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #e5e7eb;
  font-size: 13px;
  color: #4b5563;
}

:deep(.popup-stats span) {
  display: inline-block;
  padding: 2px 0;
}

:deep(.popup-images) {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 400px;
  overflow-y: auto;
}

:deep(.popup-image-wrapper) {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

:deep(.image-container) {
  position: relative;
  width: 100%;
  max-width: 300px;
  overflow: hidden;
  border-radius: 6px;
}

:deep(.popup-image) {
  width: 100%;
  height: auto;
  border-radius: 6px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s, filter 0.3s;
  display: block;
  cursor: pointer;
}

:deep(.click-overlay) {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s;
  pointer-events: none;
  gap: 8px;
}

:deep(.click-icon) {
  width: 40px;
  height: 40px;
  color: white;
  stroke-width: 2.5;
}

:deep(.click-text) {
  color: white;
  font-size: 14px;
  font-weight: 600;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
}

:deep(.image-link) {
  display: block;
  text-decoration: none;
  position: relative;
  border-radius: 6px;
  border: 2px solid transparent;
  transition: border-color 0.3s;
}

:deep(.image-link:hover) {
  border-color: #3b82f6;
}

:deep(.image-link:hover .click-overlay) {
  opacity: 1;
}

:deep(.image-link:hover .popup-image) {
  transform: scale(1.05);
}

:deep(.image-info) {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
}

:deep(.image-info small) {
  font-size: 11px;
  color: #6b7280;
}

:deep(.detection-badge) {
  background-color: #ef4444;
  color: white;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
}

:deep(.detection-badge-link) {
  text-decoration: none;
  display: inline-block;
  transition: opacity 0.2s;
}

:deep(.detection-badge-link:hover) {
  opacity: 0.85;
}

:deep(.no-detection-badge) {
  background-color: #6b7280;
  color: white;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
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
