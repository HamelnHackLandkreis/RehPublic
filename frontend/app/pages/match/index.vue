<template>
  <div class="w-full bg-gradient-to-b overflow-hidden min-h-screen flex items-center justify-center">
    <!-- Loading State -->
    <div class="text-center py-12">
      <LoadingSpinner size="md" />
      <p class="mt-4 text-gray-600">Finding a random image...</p>
    </div>

    <!-- Error State -->
    <div v-if="error" class="text-center py-12 text-red-600">
      <p>{{ error }}</p>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const apiUrl = useApiUrl()
const router = useRouter()

// Types
interface SpottingImage {
  image_id: string
  location_id: string
  upload_timestamp: string
  detections: any[]
}

interface LocationWithImages {
  id: string
  name: string
  longitude: number
  latitude: number
  description: string | null
  images: SpottingImage[]
}

interface SpottingsResponse {
  locations: LocationWithImages[]
  total_unique_species: number
  total_spottings: number
}

// State
const error = ref<string | null>(null)

// Fetch random image and redirect
const fetchRandomImageAndRedirect = async () => {
  try {
    // Fetch spottings with very large distance range to get all images
    const response = await fetch(
      `${apiUrl}/spottings?latitude=50.123&longitude=10.456&distance_range=100000000000`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      }
    )

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data: SpottingsResponse = await response.json()
    
    // Collect all image IDs from all locations
    const allImageIds: string[] = []
    for (const location of data.locations) {
      for (const image of location.images) {
        allImageIds.push(image.image_id)
      }
    }

    if (allImageIds.length === 0) {
      error.value = 'No images found in the database.'
      return
    }

    // Pick a random image ID
    const randomIndex = Math.floor(Math.random() * allImageIds.length)
    const randomImageId = allImageIds[randomIndex]

    console.log(`Redirecting to random image: ${randomImageId}`)

    // Redirect to the match page with the random image ID
    await router.push(`/match/${randomImageId}`)
  } catch (e) {
    console.error('Failed to fetch random image:', e)
    error.value = 'Failed to load images. Please try again later.'
  }
}

// Fetch on mount
onMounted(() => {
  fetchRandomImageAndRedirect()
})
</script>

