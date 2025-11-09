<template>
  <div class="flex flex-grow bg-gradient-to-b from-gray-50 to-white px-4 sm:px-6 lg:px-8 py-6 overflow-x-hidden w-full overflow-y-auto">
    <!-- Loading State -->
    <div v-if="loading" class="flex flex-col items-center justify-center flex-1 gap-4">
      <LoadingSpinner size="lg" />
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="flex flex-col items-center justify-center flex-1 gap-4 text-red-600">
      <p>{{ error }}</p>
      <button @click="fetchCameras" class="px-6 py-2.5 bg-blue-500 text-white rounded-lg font-medium transition-colors hover:bg-blue-600">
        Retry
      </button>
    </div>

    <!-- Content -->
    <div v-else class="w-full max-w-7xl mx-auto">
      <div class="mb-8">
        <h1 class="text-3xl md:text-4xl font-bold text-gray-900 mb-2">All Locations</h1>
        <p class="text-base text-gray-500">Choose a camera to view its details, statistics, and images</p>
      </div>

      <div v-if="cameras.length === 0" class="text-center py-12 text-gray-500 text-base">
        <p>No cameras found</p>
      </div>

      <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-5 w-full">
        <button
          v-for="camera in cameras"
          :key="camera.id"
          @click="selectCamera(camera.id)"
          class="group flex items-center gap-3 sm:gap-4 p-4 sm:p-5 bg-white border-2 border-gray-200 rounded-xl cursor-pointer transition-all text-left w-full hover:border-blue-500 hover:shadow-lg hover:-translate-y-0.5"
        >
          <div class="flex-shrink-0 w-20 h-20 sm:w-24 sm:h-24 rounded-xl overflow-hidden border-2 border-gray-200 bg-gray-100">
            <img
              v-if="camera.images && camera.images.length > 0 && camera.images[0]"
              :src="`${apiUrl}/images/${camera.images[0].image_id}/base64`"
              :alt="camera.name"
              class="w-full h-full object-cover"
              @error="handleImageError"
            />
            <div v-else class="w-full h-full flex items-center justify-center bg-gradient-to-br from-blue-500 to-blue-600">
              <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-8 h-8 sm:w-10 sm:h-10 text-white">
                <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
                <circle cx="12" cy="13" r="4"></circle>
              </svg>
            </div>
          </div>
          <div class="flex-1 min-w-0 overflow-hidden">
            <h3 class="text-base sm:text-lg font-semibold text-gray-900 mb-1 truncate">{{ camera.name }}</h3>
            <p v-if="camera.description" class="text-xs sm:text-sm text-gray-500 mb-2 leading-snug line-clamp-2">{{ camera.description }}</p>
            <div class="flex items-center gap-1.5 text-xs text-gray-400 font-mono">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="flex-shrink-0">
                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                <circle cx="12" cy="10" r="3"></circle>
              </svg>
              <span class="truncate">{{ camera.latitude.toFixed(4) }}, {{ camera.longitude.toFixed(4) }}</span>
            </div>
          </div>
          <div class="flex-shrink-0 text-gray-400 transition-all group-hover:text-blue-500 group-hover:translate-x-1">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M5 12h14M12 5l7 7-7 7"></path>
            </svg>
          </div>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface CameraLocation {
  id: string
  name: string
  longitude: number
  latitude: number
  description: string
  images?: Array<{
    image_id: string
    location_id: string
    upload_timestamp: string
    detections?: any[]
  }>
}

const apiUrl = useApiUrl()
const router = useRouter()

const cameras = ref<CameraLocation[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

const fetchCameras = async () => {
  loading.value = true
  error.value = null

  try {
    const params = new URLSearchParams({
      latitude: '52.10181392588904',
      longitude: '9.37544441225413',
      distance_range: '100000000000'
    })

    const response = await fetch(`${apiUrl}/spottings?${params.toString()}`)

    if (!response.ok) {
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

onMounted(() => {
  fetchCameras()
})
</script>

