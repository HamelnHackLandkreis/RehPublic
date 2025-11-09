<template>
  <div class="flex-1 bg-gradient-to-b overflow-hidden flex flex-col">
    <!-- Full Size Image - Border to Border -->
    <div class="w-full h-[60vh] overflow-hidden mb-2 relative bg-gray-100 flex-shrink-0">
      <!-- Skeleton loader for main image -->
      <div v-if="!mainImageSrc"
        class="absolute inset-0 bg-gradient-to-br from-gray-200 via-gray-300 to-gray-200 animate-pulse flex items-center justify-center">
        <div class="text-gray-400">
          <svg class="w-16 h-16 mx-auto mb-2" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd"
              d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z"
              clip-rule="evenodd" />
          </svg>
        </div>
      </div>

      <!-- Actual image - Toggle between cropped and full -->
      <img v-if="showCropped && croppedImageSrc" :src="croppedImageSrc" alt="Cropped Wildlife Detection"
        class="absolute inset-0 w-full h-full object-contain" />

      <!-- Fallback: full image if no bounding box or toggle is off -->
      <img v-else-if="mainImageSrc" :src="mainImageSrc" alt="Main Wildlife Image"
        class="absolute inset-0 w-full h-full object-contain" ref="fullImageRef" @load="handleFullImageLoad" />

      <!-- Bounding box overlay when showing full image -->
      <svg v-if="!showCropped && imageData?.detections && imageData.detections.length > 0 && boundingBoxOverlay"
        class="absolute inset-0 w-full h-full pointer-events-none"
        :viewBox="`0 0 ${fullImageDimensions.width} ${fullImageDimensions.height}`" preserveAspectRatio="xMidYMid meet">
        <rect v-for="(detection, index) in imageData.detections" :key="index" :x="detection.bounding_box.x"
          :y="detection.bounding_box.y" :width="detection.bounding_box.width" :height="detection.bounding_box.height"
          fill="none" stroke="#3b82f6" stroke-width="12" stroke-dasharray="18,10" />
        <!-- Label for each detection -->
        <g v-for="(detection, index) in imageData.detections" :key="`label-${index}`">
          <rect :x="detection.bounding_box.x" :y="detection.bounding_box.y - 60"
            :width="detection.species.length * 19 + 40" height="60" fill="#3b82f6" opacity="0.9" />
          <text :x="detection.bounding_box.x + 20" :y="detection.bounding_box.y - 18" fill="white" font-size="38"
            font-weight="bold" font-family="system-ui, sans-serif">
            {{ detection.species }} ({{ Math.round(detection.confidence * 100) }}%)
          </text>
        </g>
      </svg>

      <!-- Toggle button - only show if cropped image is available -->
      <button v-if="croppedImageSrc" @click="showCropped = !showCropped"
        class="absolute top-4 right-4 bg-white/90 hover:bg-white text-gray-800 p-3 rounded-full shadow-lg transition-all duration-200 hover:scale-110 z-10"
        :title="showCropped ? 'Show full image' : 'Show cropped detection'">
        <!-- Expand icon (show when cropped) -->
        <svg v-if="showCropped" class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
        </svg>
        <!-- Crop/Focus icon (show when full) -->
        <svg v-else class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
        </svg>
      </button>

      <div class="bg-black/60 text-white px-4 py-2 rounded-lg backdrop-blur-sm absolute top-4 left-4">
        <p class="text-sm font-medium">What animal do you see?</p>
      </div>

      <button @click="submitUnknown"
        class="hover:bg-white/20 text-white p-1.5 rounded-lg transition-all duration-200 absolute top-4 left-[230px] bg-black/60 backdrop-blur-sm shadow-lg hover:scale-110"
        title="Can't identify the animal">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round"
            d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </button>
    </div>

    <!-- Loading/Error States -->
    <div v-if="loading" class="text-center py-12 flex-1">
      <LoadingSpinner size="md" />
      <p class="mt-4 text-gray-600">Loading image data...</p>
    </div>

    <div v-else-if="error" class="text-center py-12 text-red-600 flex-1">
      <p>{{ error }}</p>
    </div>

    <!-- Swipeable Cards Container -->
    <div v-else class="relative flex-1 w-full">
      <!-- Cards -->
      <div class="relative h-full">
        <div v-for="(animal, index) in animals" :key="index"
          class="absolute inset-0 transition-all duration-300 ease-out cursor-grab active:cursor-grabbing"
          :style="getCardStyle(index)" @touchstart="handleTouchStart" @touchmove="handleTouchMove"
          @touchend="handleTouchEnd" @mousedown="handleMouseDown" @mousemove="handleMouseMove" @mouseup="handleMouseEnd"
          @mouseleave="handleMouseEnd">
          <div class="w-full h-full overflow-hidden relative bg-gray-100">
            <!-- Skeleton loader for animal image -->
            <div v-if="!animal.image_url"
              class="absolute inset-0 bg-gradient-to-br from-gray-200 via-gray-300 to-gray-200 animate-pulse flex items-center justify-center">
              <div class="text-gray-400">
                <svg class="w-16 h-16 mx-auto" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd"
                    d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z"
                    clip-rule="evenodd" />
                </svg>
              </div>
            </div>

            <!-- Actual animal image -->
            <img v-if="animal.image_url" :src="animal.image_url" :alt="animal.title"
              class="absolute inset-0 w-full h-full object-cover" />

            <!-- Overlay Gradient -->
            <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent"></div>

            <!-- Wikipedia Link - Top Right -->
            <a :href="animal.article_url" target="_blank" @click.stop
              class="absolute top-4 right-4 bg-white/90 hover:bg-white text-gray-800 p-3 rounded-full shadow-lg transition-all duration-200 hover:scale-110 z-10"
              title="View on Wikipedia">
              <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                <path
                  d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm0 2c5.523 0 10 4.477 10 10s-4.477 10-10 10S2 17.523 2 12 6.477 2 12 2zm-1 4v2h2V6h-2zm0 4v8h2v-8h-2z" />
              </svg>
            </a>

            <!-- Text Content - Bottom -->
            <div class="absolute bottom-0 left-0 right-0 p-6 text-white z-10 pointer-events-none">
              <h3 class="text-3xl font-bold drop-shadow-lg mb-2">{{ animal.title }}</h3>

              <!-- Badges Row -->
              <div class="flex flex-wrap items-center gap-2 mb-3">
                <!-- AI Confidence Badge -->
                <span v-if="getAIConfidence(animal.title) > 0"
                  class="bg-purple-500/90 text-white text-xs font-semibold px-2.5 py-1 rounded-full backdrop-blur-sm flex items-center gap-1.5 whitespace-nowrap">
                  <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M13 7H7v6h6V7z" />
                    <path fill-rule="evenodd"
                      d="M7 2a1 1 0 012 0v1h2V2a1 1 0 112 0v1h2a2 2 0 012 2v2h1a1 1 0 110 2h-1v2h1a1 1 0 110 2h-1v2a2 2 0 01-2 2h-2v1a1 1 0 11-2 0v-1H9v1a1 1 0 11-2 0v-1H5a2 2 0 01-2-2v-2H2a1 1 0 110-2h1V9H2a1 1 0 010-2h1V5a2 2 0 012-2h2V2zM5 5h10v10H5V5z"
                      clip-rule="evenodd" />
                  </svg>
                  AI: {{ Math.round(getAIConfidence(animal.title) * 100) }}%
                </span>

                <!-- User Detections Badge -->
                <span v-if="getUserDetectionCount(animal.title) > 0"
                  class="bg-blue-500/90 text-white text-xs font-semibold px-2.5 py-1 rounded-full backdrop-blur-sm flex items-center gap-1.5 whitespace-nowrap">
                  <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z" />
                  </svg>
                  {{ getUserDetectionCount(animal.title) }} user{{ getUserDetectionCount(animal.title) !== 1 ? 's' : ''
                  }}
                </span>
              </div>

              <p class="text-white/90 text-base leading-relaxed line-clamp-3 drop-shadow-md">
                {{ animal.description }}
              </p>
            </div>

            <!-- Swipe Hints -->
            <div class="absolute bottom-[11rem] left-0 right-0 flex justify-between px-8 text-white z-10 pointer-events-none">
              <!-- Left: Incorrect -->
              <div class="text-center">
                <div class="animate-pulse">
                  <svg class="w-8 h-8 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  <p class="text-sm font-medium drop-shadow-lg">Swipe left<br />if wrong</p>
                </div>
              </div>

              <!-- Right: Correct -->
              <div class="text-center">
                <div class="animate-pulse">
                  <svg class="w-8 h-8 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                  </svg>
                  <p class="text-sm font-medium drop-shadow-lg">Swipe right<br />if correct</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>

  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

const apiUrl = useApiUrl()
const route = useRoute()

// Types
interface WikipediaArticle {
  title: string
  description: string
  image_url: string | null
  article_url: string
}

interface BoundingBox {
  x: number
  y: number
  width: number
  height: number
}

interface Detection {
  species: string
  confidence: number
  bounding_box: BoundingBox
  classification_model: string
  is_uncertain: boolean
}

interface ImageData {
  image_id: string
  location_id: string
  raw: string // base64 encoded image
  upload_timestamp: string
  detections: Detection[]
}

interface SpeciesCount {
  name: string
  count: number
}

interface UserStats {
  image_id: string
  user_detections: SpeciesCount[]
  total_user_detections: number
  automated_detections: string[]
}

interface TimePeriodStatistics {
  start_time: string
  end_time: string
  species: SpeciesCount[]
  total_spottings: number
}

interface StatisticsResponse {
  statistics: TimePeriodStatistics[]
}

// Get image ID from route parameter (required for this dynamic route)
const imageId = computed(() => {
  return route.params.id as string
})

// State
const currentSlide = ref(0)
const animals = ref<WikipediaArticle[]>([])
const imageData = ref<ImageData | null>(null)
const userStats = ref<UserStats | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const dragOffset = ref({ x: 0, y: 0 })
const showCropped = ref(true) // Default to showing cropped view
const fullImageRef = ref<HTMLImageElement | null>(null)
const fullImageDimensions = ref({ width: 1920, height: 1080 })
const boundingBoxOverlay = ref(false)

// Computed property for main image source
const mainImageSrc = computed(() => {
  if (imageData.value?.raw) {
    return `data:image/jpeg;base64,${imageData.value.raw}`
  }
  return null
})

// Ref for cropped image
const croppedImageSrc = ref<string | null>(null)

// Handle full image load to get dimensions for bounding box overlay
const handleFullImageLoad = (event: Event) => {
  const img = event.target as HTMLImageElement
  if (img.naturalWidth && img.naturalHeight) {
    fullImageDimensions.value = {
      width: img.naturalWidth,
      height: img.naturalHeight
    }
    boundingBoxOverlay.value = true
  }
}

// Create cropped image when detection data is available
const createCroppedImage = async () => {
  // Only crop if we have detections with valid bounding boxes
  if (!imageData.value?.detections || imageData.value.detections.length === 0 || !mainImageSrc.value) {
    croppedImageSrc.value = null
    return
  }

  const detection = imageData.value.detections[0]
  if (!detection?.bounding_box) {
    croppedImageSrc.value = null
    return
  }

  const bbox = detection.bounding_box

  // Validate bounding box has valid dimensions
  if (bbox.width <= 0 || bbox.height <= 0) {
    croppedImageSrc.value = null
    return
  }

  // Create an image element to load the base64 image
  const img = new Image()
  img.src = mainImageSrc.value

  await new Promise((resolve) => {
    img.onload = resolve
  })

  // Add padding around the bounding box (30% on each side)
  const paddingPercent = 0.3
  const paddedX = Math.max(0, bbox.x - bbox.width * paddingPercent)
  const paddedY = Math.max(0, bbox.y - bbox.height * paddingPercent)
  const paddedWidth = Math.min(
    bbox.width * (1 + 2 * paddingPercent),
    img.width - paddedX
  )
  const paddedHeight = Math.min(
    bbox.height * (1 + 2 * paddingPercent),
    img.height - paddedY
  )

  // Create a canvas to crop the image
  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')

  if (!ctx) {
    croppedImageSrc.value = null
    return
  }

  // Set canvas size to the padded bounding box size
  canvas.width = paddedWidth
  canvas.height = paddedHeight

  // Draw the cropped portion with padding
  ctx.drawImage(
    img,
    paddedX, paddedY, paddedWidth, paddedHeight,  // Source rectangle
    0, 0, paddedWidth, paddedHeight                // Destination rectangle
  )

  // Convert canvas to base64
  croppedImageSrc.value = canvas.toDataURL('image/jpeg', 0.95)
}

// Watch for changes in image data to create cropped version
watch([imageData, mainImageSrc], () => {
  createCroppedImage()
}, { immediate: true })

// Get user detection count for a specific species
const getUserDetectionCount = (speciesName: string): number => {
  if (!userStats.value) {
    console.log('getUserDetectionCount: userStats is null')
    return 0
  }

  console.log('getUserDetectionCount called for:', speciesName)
  console.log('Available user detections:', userStats.value.user_detections)

  const detection = userStats.value.user_detections.find(d => d.name === speciesName)
  const count = detection ? detection.count : 0
  console.log('Found count:', count)
  return count
}

// Get AI confidence for a specific species
const getAIConfidence = (speciesName: string): number => {
  console.log("confidence check:", imageData.value?.detections)
  if (!imageData.value?.detections) {
    return 0
  }

  // Find the detection with the highest confidence for this species
  const matchingDetections = imageData.value.detections.filter(d => d.species === speciesName.toLocaleLowerCase())
  console.log("matching detections for", speciesName, ":", matchingDetections)
  if (matchingDetections.length === 0) {
    return 0
  }

  // Return the highest confidence value
  return Math.max(...matchingDetections.map(d => d.confidence))
}

// Fetch image data from backend
const fetchImageData = async () => {
  try {
    const response = await fetch(`${apiUrl}/images/${imageId.value}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()
    imageData.value = data

    // Extract unique species from detections for candidates
    const detectedSpecies = [...new Set(data.detections.map((d: Detection) => d.species))] as string[]

    // Fetch historical species as fallback
    const historicalSpecies = await fetchHistoricalSpecies()

    // Merge detected species with historical, keeping detected ones first and ensuring uniqueness
    const allSpecies = [...new Set([...detectedSpecies, ...historicalSpecies])]

    // Fetch Wikipedia articles for all species
    if (allSpecies.length > 0) {
      await fetchAnimals(allSpecies)
    } else {
      // Ultimate fallback to default list if no detections and no history
      await fetchAnimals(['Roe deer'])
    }
  } catch (e) {
    console.error('Failed to fetch image data:', e)
    error.value = 'Failed to load image data. Please try again later.'
  }
}

// Fetch historical species from statistics endpoint
const fetchHistoricalSpecies = async (): Promise<string[]> => {
  try {
    const response = await fetch(`${apiUrl}/statistics?period=year&granularity=daily`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    })

    if (!response.ok) {
      console.warn('Failed to fetch statistics, using default fallback')
      return []
    }

    const data: StatisticsResponse = await response.json()

    // Collect all unique species from all time periods
    const speciesSet = new Set<string>()
    data.statistics.forEach(period => {
      period.species.forEach(species => {
        speciesSet.add(species.name)
      })
    })

    return Array.from(speciesSet)
  } catch (e) {
    console.error('Failed to fetch historical species:', e)
    return []
  }
}

// Fetch animals from backend
const fetchAnimals = async (speciesList: string[]) => {
  try {
    const response = await fetch(`${apiUrl}/wikipedia/articles`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        titles: speciesList
      })
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()
    animals.value = data
  } catch (e) {
    console.error('Failed to fetch animals:', e)
    error.value = 'Failed to load animal data. Please try again later.'
  } finally {
    loading.value = false
  }
}

// Fetch user detection stats
const fetchUserStats = async () => {
  try {
    console.log('Fetching user stats for image:', imageId.value)
    const response = await fetch(`${apiUrl}/user-detections/${imageId.value}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    })

    console.log('User stats response status:', response.status)

    if (!response.ok) {
      const errorText = await response.text()
      console.error('User stats API error:', response.status, errorText)
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()
    console.log('User stats data received:', data)
    userStats.value = data
  } catch (e) {
    console.error('Failed to fetch user stats:', e)
    // Don't show error to user, stats are optional
  }
}

// Fetch on mount
onMounted(() => {
  fetchImageData()
  fetchUserStats() // Fetch stats automatically when page loads
})

// Touch/Swipe handling for carousel
const getCardStyle = (index: number) => {
  const offset = index - currentSlide.value
  const isActive = offset === 0

  const baseTransform = `translateX(${offset * 100}%)`
  const dragTransform = isActive && isDragging.value
    ? ` translateX(${dragOffset.value.x}px) translateY(${dragOffset.value.y}px) rotate(${dragOffset.value.x * 0.05}deg)`
    : ''

  return {
    transform: `${baseTransform}${dragTransform} scale(${isActive ? 1 : 0.9})`,
    opacity: isActive ? 1 : 0,
    zIndex: isActive ? 10 : 0,
    pointerEvents: (isActive ? 'auto' : 'none') as 'auto' | 'none',
  }
}

// Submit unknown and go back to match
const submitUnknown = async () => {
  try {
    // Submit "unknown" as the species
    const response = await fetch(`${apiUrl}/user-detections`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        image_id: imageId.value,
        species: 'unknown',
        user_session_id: null
      })
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    console.log('User marked as unknown')

    // Redirect to /match to load a random image
    await navigateTo('/match')
  } catch (e) {
    console.error('Failed to submit unknown detection:', e)
    alert('Failed to save your answer. Please try again.')
  }
}

// Submit the match
const submitMatch = async (animal: WikipediaArticle, isCorrect: boolean) => {
  try {
    if (isCorrect) {
      // Submit user detection to backend
      const response = await fetch(`${apiUrl}/user-detections`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          image_id: imageId.value,
          species: animal.title,
          user_session_id: null // Optional: could add session tracking later
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      // Show success feedback
      console.log(`User identified: ${animal.title}`)

      // Redirect to /match to load a random image
      await navigateTo('/match')
    } else {
      // User said this is incorrect - just log it for now
      console.log(`User rejected: ${animal.title}`)

      // Move to next card if available
      if (currentSlide.value < animals.value.length - 1) {
        currentSlide.value++
        return // Don't reload, let them try another option
      }
    }

  } catch (e) {
    console.error('Failed to submit user detection:', e)
    alert('Failed to save your answer. Please try again.')
  }
}

// Touch/Swipe handling for carousel
const touchStartX = ref(0)
const touchStartY = ref(0)
const isDragging = ref(false)

const handleTouchStart = (e: TouchEvent) => {
  if (e.touches[0]) {
    isDragging.value = true
    touchStartX.value = e.touches[0].clientX
    touchStartY.value = e.touches[0].clientY
    dragOffset.value = { x: 0, y: 0 }
  }
}

const handleTouchMove = (e: TouchEvent) => {
  if (!isDragging.value || !e.touches[0]) return

  dragOffset.value = {
    x: e.touches[0].clientX - touchStartX.value,
    y: e.touches[0].clientY - touchStartY.value
  }
}

const handleTouchEnd = () => {
  if (!isDragging.value) return

  handleSwipe()
  isDragging.value = false
  dragOffset.value = { x: 0, y: 0 }
}

const handleMouseDown = (e: MouseEvent) => {
  isDragging.value = true
  touchStartX.value = e.clientX
  touchStartY.value = e.clientY
  dragOffset.value = { x: 0, y: 0 }
}

const handleMouseMove = (e: MouseEvent) => {
  if (!isDragging.value) return

  dragOffset.value = {
    x: e.clientX - touchStartX.value,
    y: e.clientY - touchStartY.value
  }
}

const handleMouseEnd = () => {
  if (!isDragging.value) return

  handleSwipe()
  isDragging.value = false
  dragOffset.value = { x: 0, y: 0 }
}

const handleSwipe = () => {
  const swipeThreshold = 100 // Increased threshold for more deliberate swipes

  const diffX = dragOffset.value.x
  const diffY = dragOffset.value.y

  // Check for horizontal swipe (needs to be primarily horizontal, not diagonal)
  if (Math.abs(diffX) > swipeThreshold && Math.abs(diffY) < Math.abs(diffX) * 0.5) {
    const currentAnimal = animals.value[currentSlide.value]
    if (currentAnimal) {
      if (diffX > 0) {
        // Swipe right = correct match
        submitMatch(currentAnimal, true)
      } else {
        // Swipe left = incorrect/skip
        submitMatch(currentAnimal, false)
      }
    }
  }
}

</script>

<style scoped>
.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

@media (max-width: 768px) {
  .h-\[60vh\] {
    height: 50vh;
  }
}
</style>
