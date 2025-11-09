<template>
  <div class="flex flex-grow bg-gradient-to-b from-gray-50 to-white px-4 py-6 overflow-x-hidden overflow-y-auto">
    <!-- Loading State -->
    <div v-if="loading" class="flex flex-col items-center justify-center flex-1 gap-4">
      <LoadingSpinner size="lg" />
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="flex flex-col items-center justify-center flex-1 gap-4 text-red-600">
      <p>{{ error }}</p>
      <button @click="fetchCameraData" class="px-6 py-2.5 bg-blue-500 text-white rounded-lg font-medium transition-colors hover:bg-blue-600">
        Retry
      </button>
    </div>

    <!-- Content -->
    <div v-else-if="location" class="max-w-6xl mx-auto w-full">
      <!-- Header Section -->
      <div class="bg-white p-8 md:p-5 rounded-xl shadow-sm border border-gray-200 mb-6">
        <div class="flex flex-wrap items-center gap-3 mb-6">
          <button @click="goToCameraList" class="inline-flex items-center gap-2 px-4 py-2 bg-white border-2 border-gray-200 rounded-lg text-sm font-medium text-gray-600 transition-all hover:border-blue-500 hover:text-blue-500 hover:bg-blue-50">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M19 12H5M12 19l-7-7 7-7"/>
            </svg>
            Go to Camera List
          </button>
          <button @click="revealOnMap" class="inline-flex items-center gap-2 px-6 py-2.5 bg-white border-2 border-gray-300 rounded-lg text-sm font-medium text-gray-700 transition-all hover:border-gray-400 hover:bg-gray-50">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
              <circle cx="12" cy="10" r="3"></circle>
            </svg>
            Reveal on Map
          </button>
        </div>
        <h1 class="text-3xl md:text-2xl font-bold text-gray-900 mb-3">{{ location.name }}</h1>
        <p v-if="location.description" class="text-base text-gray-600 mb-4 leading-relaxed">{{ location.description }}</p>
        <div class="flex items-center gap-3">
          <span class="text-sm text-gray-500 font-mono">
            📍 {{ location.latitude.toFixed(6) }}, {{ location.longitude.toFixed(6) }}
          </span>
        </div>
      </div>

      <!-- Statistics Section -->
      <div class="bg-white p-8 md:p-5 rounded-xl shadow-sm border border-gray-200 mb-6">
        <h2 class="text-2xl font-bold text-gray-900 mb-6">Statistics</h2>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div class="bg-gradient-to-br from-blue-500 to-blue-600 p-6 rounded-xl text-center text-white">
            <div class="text-4xl font-bold mb-2">{{ totalImages }}</div>
            <div class="text-sm opacity-90 uppercase tracking-wide">Total Images</div>
          </div>
          <div class="bg-gradient-to-br from-blue-500 to-blue-600 p-6 rounded-xl text-center text-white">
            <div class="text-4xl font-bold mb-2">{{ uniqueSpecies.size }}</div>
            <div class="text-sm opacity-90 uppercase tracking-wide">Unique Species</div>
          </div>
          <div class="bg-gradient-to-br from-blue-500 to-blue-600 p-6 rounded-xl text-center text-white">
            <div class="text-4xl font-bold mb-2">{{ totalDetections }}</div>
            <div class="text-sm opacity-90 uppercase tracking-wide">Total Detections</div>
          </div>
          <div class="bg-gradient-to-br from-blue-500 to-blue-600 p-6 rounded-xl text-center text-white">
            <div class="text-4xl font-bold mb-2">{{ imagesWithDetections }}</div>
            <div class="text-sm opacity-90 uppercase tracking-wide">Images with Detections</div>
          </div>
        </div>

        <!-- Species Breakdown -->
        <div v-if="speciesBreakdown.length > 0" class="mt-8 pt-8 border-t border-gray-200">
          <h3 class="text-xl font-bold text-gray-900 mb-4">Species Breakdown</h3>
          <div class="flex flex-col gap-4">
            <div v-for="species in speciesBreakdown" :key="species.name" class="flex flex-col gap-2">
              <div class="flex justify-between items-center">
                <span class="font-semibold text-gray-900">{{ species.name }}</span>
                <span class="text-sm text-gray-500">{{ species.count }} detection{{ species.count !== 1 ? 's' : '' }}</span>
              </div>
              <div class="h-2 bg-gray-200 rounded overflow-hidden">
                <div class="h-full bg-gradient-to-r from-blue-500 to-blue-600 rounded transition-all duration-300 ease-out" :style="{ width: `${(species.count / totalDetections) * 100}%` }"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Images Section -->
      <div class="bg-white p-8 md:p-5 rounded-xl shadow-sm border border-gray-200">
        <h2 class="text-2xl font-bold text-gray-900 mb-6">Images ({{ location.images?.length || 0 }})</h2>
        <div v-if="location.images && location.images.length > 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 md:gap-4">
          <div v-for="image in location.images" :key="image.image_id" class="flex flex-col gap-3">
            <a :href="`/match/${image.image_id}`" class="group block relative rounded-lg overflow-hidden border-2 border-transparent transition-all hover:border-blue-500 hover:-translate-y-0.5 hover:shadow-lg">
              <div class="relative w-full aspect-[4/3] overflow-hidden bg-gray-100">
                <img 
                  :src="`${apiUrl}/images/${image.image_id}/base64`" 
                  :alt="`Image from ${new Date(image.upload_timestamp).toLocaleString()}`"
                  class="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                  @error="handleImageError"
                />
                <div class="absolute inset-0 bg-black/60 flex flex-col items-center justify-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none">
                  <svg class="w-10 h-10 text-white stroke-[2.5]" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/>
                  </svg>
                  <span class="text-white text-sm font-semibold drop-shadow-lg">Click to match</span>
                </div>
              </div>
            </a>
            <div class="flex justify-between items-center gap-2">
              <small class="text-xs text-gray-500">{{ new Date(image.upload_timestamp).toLocaleString() }}</small>
              <div class="flex gap-2">
                <a 
                  v-if="image.detections && image.detections.length > 0"
                  :href="`/match/${image.image_id}`"
                  class="bg-red-500 text-white px-3 py-1 rounded-full text-xs font-semibold transition-opacity hover:opacity-85"
                >
                  {{ image.detections.length }} detection{{ image.detections.length !== 1 ? 's' : '' }}
                </a>
                <span v-else class="bg-gray-500 text-white px-3 py-1 rounded-full text-xs font-semibold">No detection</span>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="text-center py-12 text-gray-500">
          <p>No images available for this camera.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

const apiUrl = useApiUrl()
const route = useRoute()
const router = useRouter()

interface ImageDetection {
  image_id: string
  location_id: string
  upload_timestamp: string
  detections: Array<{
    species: string
    confidence: number
    bounding_box: any
    classification_model: string
    is_uncertain: boolean
  }>
}

interface Location {
  id: string
  name: string
  longitude: number
  latitude: number
  description: string
  images?: ImageDetection[]
}

const location = ref<Location | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

const cameraId = computed(() => route.params.id as string)

const totalImages = computed(() => location.value?.images?.length || 0)

const totalDetections = computed(() => {
  if (!location.value?.images) return 0
  return location.value.images.reduce((sum, img) => sum + (img.detections?.length || 0), 0)
})

const imagesWithDetections = computed(() => {
  if (!location.value?.images) return 0
  return location.value.images.filter(img => img.detections && img.detections.length > 0).length
})

const uniqueSpecies = computed(() => {
  const species = new Set<string>()
  if (location.value?.images) {
    location.value.images.forEach(img => {
      img.detections?.forEach(detection => {
        species.add(detection.species)
      })
    })
  }
  return species
})

const speciesBreakdown = computed(() => {
  const speciesMap = new Map<string, number>()
  
  if (location.value?.images) {
    location.value.images.forEach(img => {
      img.detections?.forEach(detection => {
        const count = speciesMap.get(detection.species) || 0
        speciesMap.set(detection.species, count + 1)
      })
    })
  }
  
  return Array.from(speciesMap.entries())
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
})

const fetchCameraData = async () => {
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
    const foundLocation = data.locations.find((loc: Location) => loc.id === cameraId.value)

    if (!foundLocation) {
      throw new Error('Camera location not found')
    }

    location.value = foundLocation
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to fetch camera data'
    console.error('Error fetching camera data:', err)
  } finally {
    loading.value = false
  }
}

const goToCameraList = () => {
  router.push('/camera')
}

const revealOnMap = () => {
  if (location.value) {
    router.push({
      path: '/map',
      query: {
        camera: location.value.id,
        lat: location.value.latitude.toString(),
        lng: location.value.longitude.toString()
      }
    })
  }
}

const goBack = () => {
  router.push('/camera')
}

const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.src = '/fallback.JPG'
}

onMounted(() => {
  fetchCameraData()
})
</script>
