<template>
  <div class="wildlife-map-container">
    <LeafletMap ref="mapRef" :center="mapCenter" :zoom="zoom" :height="height" :width="width"
      :markers="markers" @marker-click="handleMarkerClick" />
    <div v-if="loading" class="loading-overlay">
      <LoadingSpinner size="md" />
    </div>
    <div v-if="error" class="error-message">
      <p>Error loading locations: {{ error }}</p>
      <button @click="() => fetchLocations()" class="retry-button">Retry</button>
    </div>

    <!-- Filter Panel -->
    <div class="filter-panel" :class="{ expanded: filterExpanded }">
      <button @click="filterExpanded = !filterExpanded" class="filter-toggle-button">
        <Icon name="mdi:filter" class="text-xl" />
        <span v-if="filterExpanded" class="ml-2">Filters</span>
      </button>

      <div v-if="filterExpanded" class="filter-content">
        <!-- Privacy Filter -->
        <div class="filter-section">
          <label class="filter-checkbox">
            <input type="checkbox" v-model="showOnlyMyImages" @change="applyFilters" />
            <span>Show only my images</span>
          </label>
        </div>

        <!-- Species Filter -->
        <div class="filter-section">
          <h3 class="filter-title">Species</h3>
          <div v-if="loadingSpecies" class="filter-loading">
            <LoadingSpinner size="sm" />
          </div>
          <div v-else class="species-list">
            <label v-for="species in availableSpecies" :key="species" class="filter-checkbox">
              <input
                type="checkbox"
                :value="species"
                v-model="selectedSpecies"
                @change="applyFilters"
              />
              <span>{{ species }}</span>
            </label>
            <p v-if="availableSpecies.length === 0" class="filter-empty">No species found</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'

const route = useRoute()
const { isAuthenticated: authIsAuthenticated, isLoading: authIsLoading, getToken } = useAuth()

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
  noMarkerPopup?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  defaultLatitude: 52.10181392588904,
  defaultLongitude: 9.37544441225413,
  defaultDistanceRange: 100000000000,
  height: '100%',
  width: '100%',
  autoCenter: true,
  defaultZoom: 10,
  noMarkerPopup: false
})

const apiUrl = useApiUrl()
const { fetchWithAuth } = useAuthenticatedApi()

const locations = ref<Location[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const zoom = ref(props.defaultZoom)
const mapRef = ref()
const markersWithIcons = ref<any[]>([])
const seenImageIds = ref<Set<string>>(new Set())
const locationsWithNewImages = ref<Set<string>>(new Set())
const isPolling = ref(false)
const imageUrls = ref<Map<string, string>>(new Map())
let pollingInterval: ReturnType<typeof setInterval> | null = null

// Filter state
const filterExpanded = ref(false)
const showOnlyMyImages = ref(false)
const selectedSpecies = ref<string[]>([])
const availableSpecies = ref<string[]>([])
const loadingSpecies = ref(false)
const defaultsApplied = ref(false)

// Define emits for parent components
const emit = defineEmits<{
  locationSelected: [location: Location]
}>()

const createCustomIcon = async (name: string, imageId?: string, hasNewImages: boolean = false) => {
  const L = await import('leaflet')

  const imageSrc = imageId && imageUrls.value.has(imageId)
    ? imageUrls.value.get(imageId)!
    : '/fallback.JPG'

  const wrapperClass = hasNewImages ? 'avatar-wrapper has-new-images' : 'avatar-wrapper'

  const iconHtml = `
    <div class="avatar-marker">
      <div class="${wrapperClass}">
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

const handleMarkerClick = (markerData: any) => {
  // Clear notification for this location when clicked
  if (markerData.location) {
    if (locationsWithNewImages.value.has(markerData.location.id)) {
      // Create a new Set to trigger reactivity
      const updatedSet = new Set(locationsWithNewImages.value)
      updatedSet.delete(markerData.location.id)
      locationsWithNewImages.value = updatedSet
      updateMarkers()
    }
  }

  if (props.noMarkerPopup && markerData.location) {
    // In noMarkerPopup mode, emit the location and center the map
    emit('locationSelected', markerData.location)

    // Center the map on the clicked location
    if (mapRef.value?.setCenter) {
      mapRef.value.setCenter([markerData.location.latitude, markerData.location.longitude], 15)
    }
  }
  // If noMarkerPopup is false, the default popup behavior will happen
}

const updateMarkers = async () => {
  if (locations.value.length === 0) {
    markersWithIcons.value = []
    return
  }

  const newMarkers = await Promise.all(
    locations.value.map(async (location) => {
      // Get the first image ID if available
      const firstImageId = location.images && location.images.length > 0 && location.images[0]
        ? location.images[0].image_id
        : undefined

      const imageCount = location.images?.length || 0
      const hasNewImages = locationsWithNewImages.value.has(location.id)

      // Create image gallery HTML (only if popups are enabled)
      let imagesHtml = ''
      if (!props.noMarkerPopup && location.images && location.images.length > 0) {
        imagesHtml = `
          <div class="popup-images">
            ${location.images.map(img => {
              const hasDetections = img.detections && img.detections.length > 0
              const imageSrc = imageUrls.value.has(img.image_id)
                ? imageUrls.value.get(img.image_id)!
                : '/fallback.JPG'
              const imageContent = `
                <div class="image-container">
                  <img
                    src="${imageSrc}"
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
                <a href="#" data-nuxt-link="/match/${img.image_id}" class="image-link nuxt-link">${imageContent}</a>
                <div class="image-info">
                  <small>${new Date(img.upload_timestamp).toLocaleString()}</small>
                  ${hasDetections ?
            `<a href="#" data-nuxt-link="/match/${img.image_id}" class="detection-badge-link nuxt-link">
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
        popup: props.noMarkerPopup ? undefined : `
          <div class="marker-popup w-75">
            <div class="popup-header">
              <h3><strong>${location.name}</strong></h3>
              <a href="#" data-nuxt-link="/camera/${location.id}" class="camera-detail-button-inline nuxt-link">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                  <circle cx="12" cy="10" r="3"></circle>
                </svg>
                Details
              </a>
            </div>
            ${imagesHtml}
          </div>
        `,
        icon: await createCustomIcon(location.name, firstImageId, hasNewImages),
        zIndexOffset: hasNewImages ? 1000 : 0,
        data: {
          location: location
        }
      }
    })
  )

  // Sort markers so that ones with new images are added last (appear on top)
  newMarkers.sort((a, b) => {
    const aHasNew = locationsWithNewImages.value.has(a.data?.location?.id)
    const bHasNew = locationsWithNewImages.value.has(b.data?.location?.id)
    if (aHasNew && !bHasNew) return 1 // a comes after b
    if (!aHasNew && bHasNew) return -1 // a comes before b
    return 0 // keep original order
  })

  markersWithIcons.value = newMarkers
}

const markers = computed(() => markersWithIcons.value)

// Watch for location changes and create custom icons
watch(() => locations.value, () => {
  // Don't auto-update during polling if we're tracking new images
  // The polling logic will handle marker updates
  if (!isPolling.value || locationsWithNewImages.value.size === 0) {
    updateMarkers()
  }
}, { deep: true })

// Watch for new images and update markers
watch(() => locationsWithNewImages.value.size, () => {
  updateMarkers()
})

const mapCenter = computed((): [number, number] => {
  // Check for lat/lng query parameters (from revealOnMap)
  if (route.query.lat && route.query.lng) {
    const lat = parseFloat(route.query.lat as string)
    const lng = parseFloat(route.query.lng as string)
    if (!isNaN(lat) && !isNaN(lng)) {
      return [lat, lng]
    }
  }

  if (!props.autoCenter || locations.value.length === 0) {
    return [props.defaultLatitude, props.defaultLongitude]
  }

  // Calculate center from all locations
  const latSum = locations.value.reduce((sum, loc) => sum + loc.latitude, 0)
  const lonSum = locations.value.reduce((sum, loc) => sum + loc.longitude, 0)

  return [
    latSum / locations.value.length,
    lonSum / locations.value.length
  ]
})

const fetchLocations = async (isPollingCall: boolean = false) => {
  if (authIsLoading.value) {
    return
  }

  if (!authIsAuthenticated.value) {
    if (!isPollingCall) {
      loading.value = false
    }
    return
  }

  isPolling.value = isPollingCall
  if (!isPollingCall) {
    loading.value = true
  }
  error.value = null

  try {
    // Build base URL with required parameters
    const params = new URLSearchParams({
      latitude: props.defaultLatitude.toString(),
      longitude: props.defaultLongitude.toString(),
      distance_range: props.defaultDistanceRange.toString()
    })

    // Add species filter if selected
    if (selectedSpecies.value.length > 0 && selectedSpecies.value[0]) {
      // Use the first selected species (API only supports single species filter)
      params.set('species', selectedSpecies.value[0])
    } else if (route.query.species && typeof route.query.species === 'string') {
      // Fallback to route query parameter
      params.set('species', route.query.species)
    }

    // Add only_my_images filter if enabled
    if (showOnlyMyImages.value) {
      params.set('only_my_images', 'true')
    }

    // Add optional time_start parameter from route
    if (route.query.time_start && typeof route.query.time_start === 'string') {
      params.set('time_start', route.query.time_start)
    }

    // Add optional time_end parameter from route
    if (route.query.time_end && typeof route.query.time_end === 'string') {
      params.set('time_end', route.query.time_end)
    }

    const spottingsUrl = `/locations?${params.toString()}`
    const response = await fetchWithAuth(spottingsUrl)

    if (!response.ok) {
      if (response.status === 401) {
        return
      }
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data: LocationsResponse = await response.json()
    let newLocations = data.locations

    // Filter out locations without images (backend already filters by privacy/ownership)
    // This ensures we don't show empty locations
    newLocations = newLocations.filter(loc => loc.images && loc.images.length > 0)

    let hasNewImages = false

    // Check for new images if polling
    if (isPollingCall && seenImageIds.value.size > 0) {
      const newImageIds = new Set<string>()
      const newLocationsWithImages = new Set<string>()

      newLocations.forEach(location => {
        if (location.images) {
          location.images.forEach(img => {
            if (!seenImageIds.value.has(img.image_id)) {
              newImageIds.add(img.image_id)
              newLocationsWithImages.add(location.id)
            }
          })
        }
      })

      // Update locations with new images BEFORE updating locations.value
      if (newLocationsWithImages.size > 0) {
        hasNewImages = true
        // Create a new Set to trigger reactivity
        const updatedSet = new Set(locationsWithNewImages.value)
        newLocationsWithImages.forEach(locId => {
          updatedSet.add(locId)
        })
        locationsWithNewImages.value = updatedSet
      }

      // Add new image IDs to seen set
      newImageIds.forEach(id => seenImageIds.value.add(id))
    } else {
      // Initial load - mark all images as seen
      newLocations.forEach(location => {
        if (location.images) {
          location.images.forEach(img => {
            seenImageIds.value.add(img.image_id)
          })
        }
      })
    }

    // Update locations AFTER we've set the new images flags
    locations.value = newLocations

    // Fetch authenticated image URLs for all images
    if (!isPollingCall) {
      await fetchImageUrls(newLocations)
    }

    // Auto-adjust zoom based on number of locations
    if (!isPollingCall && props.autoCenter && locations.value.length > 1) {
      zoom.value = calculateZoomLevel()
    }

    // If lat/lng query params are present, center on that location with appropriate zoom
    if (!isPollingCall && route.query.lat && route.query.lng) {
      const lat = parseFloat(route.query.lat as string)
      const lng = parseFloat(route.query.lng as string)
      if (!isNaN(lat) && !isNaN(lng)) {
        // Set zoom to a close level (15) to show the location clearly
        zoom.value = 15
        // Center the map on the location after a short delay to ensure map is ready
        setTimeout(() => {
          if (mapRef.value?.setCenter) {
            mapRef.value.setCenter([lat, lng], 15)
          }
        }, 100)
      }
    }

    // Update markers with custom icons
    if (!isPollingCall) {
      await updateMarkers()
    } else if (hasNewImages) {
      // If polling and we have new images, update markers to show notifications
      await updateMarkers()
    }
  } catch (err) {
    if (!isPollingCall) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch locations'
      console.error('Error fetching locations:', err)
    }
  } finally {
    if (!isPollingCall) {
      loading.value = false
    }
    isPolling.value = false
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

// Fetch authenticated image URLs and create object URLs
const fetchImageUrls = async (locationsToFetch: Location[]) => {
  const imageIds = new Set<string>()
  locationsToFetch.forEach(location => {
    if (location.images) {
      location.images.forEach(img => {
        imageIds.add(img.image_id)
      })
    }
  })

  // Only fetch images we don't already have
  const imagesToFetch = Array.from(imageIds).filter(id => !imageUrls.value.has(id))

  if (imagesToFetch.length === 0) {
    return
  }

  try {
    const token = await getToken()
    if (!token) {
      return
    }

    await Promise.all(
      imagesToFetch.map(async (imageId) => {
        try {
          const response = await fetchWithAuth(`/images/${imageId}/base64`)
          if (response.ok) {
            const blob = await response.blob()
            const url = URL.createObjectURL(blob)
            imageUrls.value.set(imageId, url)
          }
        } catch (err) {
          console.warn(`Failed to fetch image ${imageId}:`, err)
        }
      })
    )

    // Update markers after fetching images
    await updateMarkers()
  } catch (err) {
    console.error('Error fetching image URLs:', err)
  }
}

// Fetch available species from statistics
const fetchAvailableSpecies = async () => {
  loadingSpecies.value = true
  try {
    const response = await fetchWithAuth('/statistics?period=year&granularity=daily')
    if (response.ok) {
      const data = await response.json()
      const speciesSet = new Set<string>()

      // Collect all unique species from all time periods
      data.statistics.forEach((period: any) => {
        period.species.forEach((s: { name: string; count: number }) => {
          speciesSet.add(s.name)
        })
      })

      availableSpecies.value = Array.from(speciesSet).sort()

      // Apply default: select all species (only once)
      if (!defaultsApplied.value && availableSpecies.value.length > 0) {
        selectedSpecies.value = [...availableSpecies.value]
        defaultsApplied.value = true
        // Apply filters after setting defaults
        applyFilters()
      }
    }
  } catch (err) {
    console.error('Failed to fetch species:', err)
  } finally {
    loadingSpecies.value = false
  }
}

// Apply filters and refetch locations
const applyFilters = () => {
  fetchLocations()
}

// Computed properties for filter UI
const hasActiveFilters = computed(() => {
  return showOnlyMyImages.value || selectedSpecies.value.length > 0
})

const activeFilterCount = computed(() => {
  let count = 0
  if (showOnlyMyImages.value) count++
  if (selectedSpecies.value.length > 0) count++
  return count
})

onMounted(() => {
  watch([authIsAuthenticated, authIsLoading], ([authenticated, loading]) => {
    if (!loading && authenticated) {
      fetchLocations()
      fetchAvailableSpecies()

      // Start polling every 15 seconds
      if (!pollingInterval) {
        pollingInterval = setInterval(() => {
          fetchLocations(true)
        }, 15000)
      }
    }
  }, { immediate: true })
})

onUnmounted(() => {
  if (pollingInterval) {
    clearInterval(pollingInterval)
    pollingInterval = null
  }
  // Clean up object URLs
  imageUrls.value.forEach(url => URL.revokeObjectURL(url))
  imageUrls.value.clear()
})

// Watch for route query changes and refetch
watch(() => route.query, () => {
  if (authIsAuthenticated.value) {
    fetchLocations()
    // If lat/lng query params changed, center on the new location
    if (route.query.lat && route.query.lng) {
      const lat = parseFloat(route.query.lat as string)
      const lng = parseFloat(route.query.lng as string)
      if (!isNaN(lat) && !isNaN(lng)) {
        zoom.value = 15
        setTimeout(() => {
          if (mapRef.value?.setCenter) {
            mapRef.value.setCenter([lat, lng], 15)
          }
        }, 300)
      }
    }
  }
}, { deep: true })

// Expose methods for parent components
defineExpose({
  refresh: fetchLocations,
  getLocations: () => locations.value,
  centerOnLocation: (locationId: string) => {
    const location = locations.value.find(loc => loc.id === locationId)
    if (location && mapRef.value?.setCenter) {
      mapRef.value.setCenter([location.latitude, location.longitude], 15)
    }
  }
})
</script>

<style scoped>
.wildlife-map-container {
  position: relative;
  width: 100%;
  height: 100%;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(2px);
  border-radius: 8px;
  z-index: 1000;
}

.loading-spinner {
  font-size: 18px;
  color: #666;
  padding: 20px;
}

.error-message {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: #fee;
  border-radius: 8px;
  padding: 20px;
  z-index: 1000;
}

.error-message p {
  color: #c33;
  margin-bottom: 16px;
  font-weight: 500;
}

.retry-button {
  padding: 8px 16px;
  background-color: var(--color-secondary);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
}

.retry-button:hover {
  background-color: var(--color-secondary-dark);
}

:deep(.marker-popup) {
  padding: 4px;
}

:deep(.popup-header) {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

:deep(.popup-header h3) {
  margin: 0;
  font-size: 16px;
  color: #1f2937;
  flex: 1;
}

:deep(.camera-detail-button-inline) {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background-color: var(--color-primary);
  color: white;
  text-decoration: none;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  transition: all 0.2s;
  border: none;
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
}

:deep(.camera-detail-button-inline:hover) {
  background-color: var(--color-primary-dark);
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(34, 197, 94, 0.3);
}

:deep(.camera-detail-button-inline svg) {
  width: 14px;
  height: 14px;
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
  border-color: var(--color-secondary);
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

:deep(.avatar-wrapper.has-new-images) {
  border: 5px solid var(--color-secondary);
  animation: pulse-blue-border 1s ease-in-out infinite;
  box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.9), 0 2px 8px rgba(0, 0, 0, 0.3);
}

@keyframes pulse-blue-border {
  0%, 100% {
    border-color: var(--color-secondary);
    box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.9), 0 0 20px rgba(59, 130, 246, 0.8), 0 2px 8px rgba(0, 0, 0, 0.3);
  }
  50% {
    border-color: var(--color-secondary-dark);
    box-shadow: 0 0 0 16px rgba(59, 130, 246, 0), 0 0 30px rgba(59, 130, 246, 1), 0 2px 16px rgba(59, 130, 246, 0.8);
  }
}

:deep(.avatar-image) {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

:deep(.avatar-wrapper) {
  position: relative;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  overflow: hidden;
  border: 2px solid white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  transition: transform 0.2s, box-shadow 0.2s;
  background-color: #f3f4f6;
}

:deep(.avatar-marker:hover .avatar-wrapper) {
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
}

:deep(.camera-badge) {
  position: absolute;
  bottom: -2px;
  right: -2px;
  width: 20px;
  height: 20px;
  background-color: var(--color-secondary-dark);
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

.filter-panel {
  position: absolute;
  bottom: 100px;
  right: 20px;
  z-index: 1001;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1), 0 2px 4px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  transition: all 0.3s ease;
  max-width: 320px;
}

@media (min-width: 768px) {
  .filter-panel {
    bottom: 20px;
  }
}

.filter-toggle-button {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px 16px;
  background: white;
  border: none;
  cursor: pointer;
  font-weight: 500;
  color: #374151;
  width: 100%;
  transition: background-color 0.2s;
  position: relative;
}

.filter-toggle-button:hover {
  background-color: #f9fafb;
}

.filter-content {
  padding: 16px;
  border-top: 1px solid #e5e7eb;
  max-height: 400px;
  overflow-y: auto;
}

.filter-section {
  margin-bottom: 16px;
}

.filter-section:last-child {
  margin-bottom: 0;
}

.filter-title {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 12px;
}

.filter-checkbox {
  display: flex;
  align-items: center;
  padding: 8px 0;
  cursor: pointer;
  user-select: none;
}

.filter-checkbox input[type="checkbox"] {
  margin-right: 8px;
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: var(--color-secondary);
}

.filter-checkbox span {
  font-size: 14px;
  color: #374151;
}

.filter-checkbox:hover span {
  color: #111827;
}

.species-list {
  max-height: 200px;
  overflow-y: auto;
}

.filter-loading {
  display: flex;
  justify-content: center;
  padding: 16px;
}

.filter-empty {
  font-size: 14px;
  color: #6b7280;
  text-align: center;
  padding: 8px 0;
}
</style>
