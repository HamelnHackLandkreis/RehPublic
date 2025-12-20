<template>
  <div class="flex flex-grow px-4 sm:px-6 lg:px-8 py-6 overflow-x-hidden w-full overflow-y-auto">
    <!-- Loading State -->
    <div v-if="loading" class="flex flex-col items-center justify-center flex-1 gap-4">
      <LoadingSpinner size="lg" />
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="flex flex-col items-center justify-center flex-1 gap-4 text-red-600">
      <p>{{ error }}</p>
      <button @click="fetchCameras"
        class="px-6 py-2.5 bg-secondary text-white rounded-lg font-medium transition-colors hover:bg-secondary-dark">
        Retry
      </button>
    </div>

    <!-- Content -->
    <div v-else class="w-full max-w-7xl mx-auto">
      <div class="mb-8 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 class="text-3xl md:text-4xl font-bold text-white mb-2 drop-shadow-lg">All Locations</h1>
          <p class="text-base text-white/90 drop-shadow">Choose a camera to view its details, statistics, and images</p>
        </div>
        <button @click="openCreateModal"
          class="inline-flex items-center gap-2 px-5 py-2.5 bg-green-500 text-white rounded-lg font-medium transition-all hover:bg-green-600 hover:shadow-lg self-start sm:self-auto">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" stroke-width="2">
            <path d="M12 5v14M5 12h14" />
          </svg>
          New Camera
        </button>
      </div>

      <div v-if="cameras.length === 0" class="text-center py-12 text-white/80 text-base">
        <p>No cameras found</p>
      </div>

      <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-5 w-full">
        <button v-for="camera in cameras" :key="camera.id" @click="selectCamera(camera.id)"
          class="group flex items-center gap-3 sm:gap-4 p-4 sm:p-5 bg-white border-2 border-gray-200 rounded-xl cursor-pointer transition-all text-left w-full hover:border-secondary hover:shadow-lg hover:-translate-y-0.5">
          <div
            class="flex-shrink-0 w-20 h-20 sm:w-24 sm:h-24 rounded-xl overflow-hidden border-2 border-gray-200 bg-gray-100">
            <img v-if="camera.images && camera.images.length > 0 && camera.images[0]"
              :src="`${apiUrl}/images/${camera.images[0].image_id}/base64`" :alt="camera.name"
              class="w-full h-full object-cover" @error="handleImageError" />
            <div v-else
              class="w-full h-full flex items-center justify-center bg-gradient-to-br from-secondary to-secondary-dark">
              <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" stroke-width="2" class="w-8 h-8 sm:w-10 sm:h-10 text-white">
                <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
                <circle cx="12" cy="13" r="4"></circle>
              </svg>
            </div>
          </div>
          <div class="flex-1 min-w-0 overflow-hidden">
            <h3 class="text-base sm:text-lg font-semibold text-gray-900 mb-1 truncate">{{ camera.name }}</h3>
            <p v-if="camera.description" class="text-xs sm:text-sm text-gray-500 mb-2 leading-snug line-clamp-2">{{
              camera.description }}</p>
            <div class="flex items-center gap-3 text-xs text-gray-400">
              <div class="flex items-center gap-1.5 font-mono">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" stroke-width="2" class="flex-shrink-0">
                  <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                  <circle cx="12" cy="10" r="3"></circle>
                </svg>
                <span class="truncate">{{ camera.latitude.toFixed(4) }}, {{ camera.longitude.toFixed(4) }}</span>
              </div>
              <div class="flex items-center gap-1.5 font-medium">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" stroke-width="2" class="flex-shrink-0">
                  <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
                  <circle cx="12" cy="13" r="4"></circle>
                </svg>
              </div>
            </div>
          </div>
          <div class="flex-shrink-0 text-gray-400 transition-all group-hover:text-secondary group-hover:translate-x-1">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" stroke-width="2">
              <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
              <line x1="10" y1="11" x2="10" y2="17"></line>
              <line x1="14" y1="11" x2="14" y2="17"></line>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Create Camera Modal -->
    <div v-if="showCreateModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <!-- Backdrop -->
      <div class="absolute inset-0 bg-black/50" @click="closeCreateModal"></div>

      <!-- Modal Content -->
      <div class="relative bg-white rounded-2xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div class="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <h2 class="text-xl font-bold text-gray-900">Create New Camera Location</h2>
          <button @click="closeCreateModal" class="p-2 text-gray-400 hover:text-gray-600 transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" stroke-width="2">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="p-6 space-y-6">
          <!-- Map for Location Selection -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Pick Location on Map
              <span class="text-gray-400 font-normal">(click to set location)</span>
            </label>
            <div class="relative h-[300px] rounded-xl overflow-hidden border-2 border-gray-200">
              <div ref="createMapContainer" class="w-full h-full"></div>
            </div>
            <p v-if="newCamera.latitude && newCamera.longitude" class="mt-2 text-sm text-green-600">
              📍 Selected: {{ newCamera.latitude.toFixed(6) }}, {{ newCamera.longitude.toFixed(6) }}
            </p>
            <p v-else class="mt-2 text-sm text-gray-500">
              Click on the map to select a location
            </p>
          </div>

          <!-- Name Input -->
          <div>
            <label for="camera-name" class="block text-sm font-medium text-gray-700 mb-2">
              Camera Name <span class="text-red-500">*</span>
            </label>
            <input id="camera-name" v-model="newCamera.name" type="text" placeholder="e.g., Forest Camera North"
              class="w-full px-4 py-2.5 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-blue-500 transition-colors" />
          </div>

          <!-- Description Input -->
          <div>
            <label for="camera-description" class="block text-sm font-medium text-gray-700 mb-2">
              Description <span class="text-gray-400 font-normal">(optional)</span>
            </label>
            <textarea id="camera-description" v-model="newCamera.description" rows="3"
              placeholder="Describe the camera location..."
              class="w-full px-4 py-2.5 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-blue-500 transition-colors resize-none"></textarea>
          </div>

          <!-- Coordinates (Manual Entry) -->
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label for="camera-lat" class="block text-sm font-medium text-gray-700 mb-2">Latitude</label>
              <input id="camera-lat" v-model.number="newCamera.latitude" type="number" step="0.000001"
                placeholder="52.101813"
                class="w-full px-4 py-2.5 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-blue-500 transition-colors" />
            </div>
            <div>
              <label for="camera-lng" class="block text-sm font-medium text-gray-700 mb-2">Longitude</label>
              <input id="camera-lng" v-model.number="newCamera.longitude" type="number" step="0.000001"
                placeholder="9.375444"
                class="w-full px-4 py-2.5 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-blue-500 transition-colors" />
            </div>
          </div>

          <!-- Error Message -->
          <p v-if="createError" class="text-red-500 text-sm">{{ createError }}</p>
        </div>

        <div class="sticky bottom-0 bg-gray-50 border-t border-gray-200 px-6 py-4 flex justify-end gap-3">
          <button @click="closeCreateModal"
            class="px-5 py-2.5 border-2 border-gray-200 rounded-lg font-medium text-gray-600 hover:bg-gray-100 transition-colors">
            Cancel
          </button>
          <button @click="createCamera" :disabled="!canCreate || creating"
            class="px-5 py-2.5 bg-green-500 text-white rounded-lg font-medium hover:bg-green-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2">
            <LoadingSpinner v-if="creating" size="sm" />
            {{ creating ? 'Creating...' : 'Create Camera' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Delete Camera Modal -->
    <div v-if="showDeleteModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <!-- Backdrop -->
      <div class="absolute inset-0 bg-black/50" @click="closeDeleteModal"></div>

      <!-- Modal Content -->
      <div class="relative bg-white rounded-2xl shadow-xl w-full max-w-md">
        <div class="p-6">
          <div class="flex items-center justify-center w-12 h-12 mx-auto mb-4 bg-red-100 rounded-full">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" stroke-width="2" class="text-red-600">
              <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
              <line x1="10" y1="11" x2="10" y2="17"></line>
              <line x1="14" y1="11" x2="14" y2="17"></line>
            </svg>
          </div>
          <h2 class="text-xl font-bold text-gray-900 text-center mb-2">Delete Camera</h2>
          <p class="text-gray-600 text-center mb-2">
            Are you sure you want to delete <strong class="text-gray-900">{{ cameraToDelete?.name }}</strong>?
          </p>

          <!-- Image Count Warning -->
          <div v-if="loadingImageCount" class="flex justify-center mb-4">
            <LoadingSpinner size="sm" />
          </div>
          <div v-else-if="deleteImageCount > 0" class="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
            <p class="text-red-700 text-sm text-center font-medium">
              ⚠️ This will also delete <strong>{{ deleteImageCount }}</strong> image{{ deleteImageCount !== 1 ? 's' : '' }} and all associated detections.
            </p>
          </div>
          <p class="text-gray-500 text-sm text-center mb-6">
            This action cannot be undone.
          </p>

          <!-- Confirmation Input -->
          <div class="mb-6">
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Type <strong class="text-red-600">{{ cameraToDelete?.name }}</strong> to confirm:
            </label>
            <input v-model="deleteConfirmation" type="text" :placeholder="cameraToDelete?.name"
              class="w-full px-4 py-2.5 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-red-500 transition-colors"
              @keyup.enter="deleteCamera" />
          </div>

          <!-- Error Message -->
          <p v-if="deleteError" class="text-red-500 text-sm mb-4 text-center">{{ deleteError }}</p>

          <div class="flex gap-3">
            <button @click="closeDeleteModal"
              class="flex-1 px-5 py-2.5 border-2 border-gray-200 rounded-lg font-medium text-gray-600 hover:bg-gray-100 transition-colors">
              Cancel
            </button>
            <button @click="deleteCamera" :disabled="!canDelete || deleting"
              class="flex-1 px-5 py-2.5 bg-red-500 text-white rounded-lg font-medium hover:bg-red-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2">
              <LoadingSpinner v-if="deleting" size="sm" />
              {{ deleting ? 'Deleting...' : 'Delete' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Map, Marker } from 'leaflet'
import { computed, nextTick, onMounted, ref, watch } from 'vue'

interface CameraLocation {
  id: string
  name: string
  longitude: number
  latitude: number
  description: string
  total_images_with_animals: number
  images?: Array<{
    image_id: string
    location_id: string
    upload_timestamp: string
    detections?: any[]
  }>
}

const apiUrl = useApiUrl()
const router = useRouter()
const { fetchWithAuth } = useAuthenticatedApi()

const cameras = ref<CameraLocation[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

// Create modal state
const showCreateModal = ref(false)
const creating = ref(false)
const createError = ref<string | null>(null)
const createMapContainer = ref<HTMLElement | null>(null)
let createMap: Map | null = null
let createMarker: Marker | null = null

// Delete modal state
const showDeleteModal = ref(false)
const deleting = ref(false)
const deleteError = ref<string | null>(null)
const cameraToDelete = ref<CameraLocation | null>(null)
const deleteConfirmation = ref('')
const deleteImageCount = ref(0)
const loadingImageCount = ref(false)

const canDelete = computed(() => {
  return cameraToDelete.value && deleteConfirmation.value === cameraToDelete.value.name
})

const newCamera = ref({
  name: '',
  description: '',
  latitude: null as number | null,
  longitude: null as number | null
})

const canCreate = computed(() => {
  return newCamera.value.name.trim() !== '' &&
    newCamera.value.latitude !== null &&
    newCamera.value.longitude !== null
})

const openCreateModal = async () => {
  showCreateModal.value = true
  createError.value = null

  // Reset form
  newCamera.value = {
    name: '',
    description: '',
    latitude: null,
    longitude: null
  }

  // Wait for modal to render, then initialize map
  await nextTick()
  initCreateMap()
}

const closeCreateModal = () => {
  showCreateModal.value = false
  if (createMap) {
    createMap.remove()
    createMap = null
  }
  createMarker = null
}

const initCreateMap = async () => {
  if (!createMapContainer.value) return

  const L = await import('leaflet')
  await import('leaflet/dist/leaflet.css')

  // Fix for default marker icons
  delete (L.Icon.Default.prototype as any)._getIconUrl
  L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
  })

  // Default center (Hameln area)
  const defaultCenter: [number, number] = [52.10181392588904, 9.37544441225413]

  createMap = L.map(createMapContainer.value).setView(defaultCenter, 10)

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19,
  }).addTo(createMap)

  // Add click handler for location selection
  createMap.on('click', (e: any) => {
    const { lat, lng } = e.latlng
    newCamera.value.latitude = lat
    newCamera.value.longitude = lng

    // Update or create marker
    if (createMarker) {
      createMarker.setLatLng([lat, lng])
    } else if (createMap) {
      createMarker = L.marker([lat, lng]).addTo(createMap)
    }
  })
}

// Watch for manual coordinate changes and update marker
watch(
  () => [newCamera.value.latitude, newCamera.value.longitude],
  ([lat, lng]) => {
    if (createMap && lat !== null && lat !== undefined && lng !== null && lng !== undefined) {
      const L = (window as any).L
      if (createMarker) {
        createMarker.setLatLng([lat as number, lng as number])
      } else if (L) {
        createMarker = L.marker([lat as number, lng as number]).addTo(createMap)
      }
      createMap.setView([lat as number, lng as number], createMap.getZoom())
    }
  }
)

const createCamera = async () => {
  if (!canCreate.value) return

  creating.value = true
  createError.value = null

  try {
    const response = await fetchWithAuth('/locations', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        name: newCamera.value.name.trim(),
        description: newCamera.value.description.trim() || null,
        latitude: newCamera.value.latitude,
        longitude: newCamera.value.longitude
      })
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
    }

    const createdCamera = await response.json()

    // Close modal and refresh list
    closeCreateModal()
    await fetchCameras()

    // Navigate to the new camera
    router.push(`/camera/${createdCamera.id}`)
  } catch (err) {
    createError.value = err instanceof Error ? err.message : 'Failed to create camera'
    console.error('Error creating camera:', err)
  } finally {
    creating.value = false
  }
}

const fetchCameras = async () => {
  loading.value = true
  error.value = null

  try {
    const params = new URLSearchParams({
      latitude: '52.10181392588904',
      longitude: '9.37544441225413',
      distance_range: '100000000000'
    })

    const response = await fetchWithAuth(`/locations?${params.toString()}`)

    if (!response.ok) {
      if (response.status === 401) {
        return
      }
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()
    cameras.value = data.locations || []
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to fetch cameras'
    console.error('Error fetching cameras:', err)
  } finally {
    loading.value = false
  }
}

const selectCamera = (cameraId: string) => {
  router.push(`/camera/${cameraId}`)
}

const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.src = '/fallback.JPG'
}

// Delete modal functions
const openDeleteModal = async (camera: CameraLocation) => {
  cameraToDelete.value = camera
  deleteConfirmation.value = ''
  deleteError.value = null
  deleteImageCount.value = 0
  loadingImageCount.value = true
  showDeleteModal.value = true

  // Fetch the image count for this camera
  try {
    const response = await fetchWithAuth(`/locations/${camera.id}/image-count`)
    if (response.ok) {
      const data = await response.json()
      deleteImageCount.value = data.image_count || 0
    }
  } catch (err) {
    console.error('Error fetching image count:', err)
  } finally {
    loadingImageCount.value = false
  }
}

const closeDeleteModal = () => {
  showDeleteModal.value = false
  cameraToDelete.value = null
  deleteConfirmation.value = ''
  deleteError.value = null
  deleteImageCount.value = 0
  loadingImageCount.value = false
}

const deleteCamera = async () => {
  if (!canDelete.value || !cameraToDelete.value) return

  deleting.value = true
  deleteError.value = null

  try {
    const response = await fetchWithAuth(`/locations/${cameraToDelete.value.id}`, {
      method: 'DELETE'
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
    }

    // Close modal and refresh list
    closeDeleteModal()
    await fetchCameras()
  } catch (err) {
    deleteError.value = err instanceof Error ? err.message : 'Failed to delete camera'
    console.error('Error deleting camera:', err)
  } finally {
    deleting.value = false
  }
}

onMounted(() => {
  fetchCameras()
})
</script>
