<template>
  <div class="flex-1 bg-gradient-to-b overflow-hidden flex flex-col">
    <!-- Full Size Image - Border to Border -->
    <div class="w-full h-[60vh] overflow-hidden mb-2 relative bg-gray-100 flex-shrink-0">
      <!-- Skeleton loader for main image -->
      <div 
        v-if="!mainImageSrc"
        class="absolute inset-0 bg-gradient-to-br from-gray-200 via-gray-300 to-gray-200 animate-pulse flex items-center justify-center"
      >
        <div class="text-gray-400">
          <svg class="w-16 h-16 mx-auto mb-2" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clip-rule="evenodd" />
          </svg>
        </div>
      </div>
      
      <!-- Actual image -->
      <img 
        v-if="mainImageSrc"
        :src="mainImageSrc" 
        alt="Main Wildlife Image" 
        class="absolute inset-0 w-full h-full object-cover"
      />
      
      <div class="absolute top-4 left-4 bg-black/60 text-white px-4 py-2 rounded-lg backdrop-blur-sm">
        <p class="text-sm font-medium">What animal do you see?</p>
      </div>
    </div>

    <!-- Loading/Error States -->
    <div v-if="loading" class="text-center py-12 flex-1">
      <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      <p class="mt-4 text-gray-600">Loading image data...</p>
    </div>

    <div v-else-if="error" class="text-center py-12 text-red-600 flex-1">
      <p>{{ error }}</p>
    </div>

    <!-- Swipeable Cards Container -->
    <div 
      v-else 
      class="relative flex-1 w-full"
    >
      <!-- Cards -->
      <div class="relative h-full">
        <div 
          v-for="(animal, index) in animals" 
          :key="index"
          class="absolute inset-0 transition-all duration-300 ease-out cursor-grab active:cursor-grabbing"
          :style="getCardStyle(index)"
          @touchstart="handleTouchStart"
          @touchmove="handleTouchMove"
          @touchend="handleTouchEnd"
          @mousedown="handleMouseDown"
          @mousemove="handleMouseMove"
          @mouseup="handleMouseEnd"
          @mouseleave="handleMouseEnd"
        >
          <div 
            class="w-full h-full overflow-hidden relative bg-gray-100"
          >
            <!-- Skeleton loader for animal image -->
            <div 
              v-if="!animal.image_url"
              class="absolute inset-0 bg-gradient-to-br from-gray-200 via-gray-300 to-gray-200 animate-pulse flex items-center justify-center"
            >
              <div class="text-gray-400">
                <svg class="w-16 h-16 mx-auto" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clip-rule="evenodd" />
                </svg>
              </div>
            </div>
            
            <!-- Actual animal image -->
            <img 
              v-if="animal.image_url"
              :src="animal.image_url" 
              :alt="animal.title"
              class="absolute inset-0 w-full h-full object-cover"
            />

            <!-- Overlay Gradient -->
            <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent"></div>

            <!-- Wikipedia Link - Top Right -->
            <a 
              :href="animal.article_url" 
              target="_blank"
              @click.stop
              class="absolute top-4 right-4 bg-white/90 hover:bg-white text-gray-800 p-3 rounded-full shadow-lg transition-all duration-200 hover:scale-110 z-10"
              title="View on Wikipedia"
            >
              <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm0 2c5.523 0 10 4.477 10 10s-4.477 10-10 10S2 17.523 2 12 6.477 2 12 2zm-1 4v2h2V6h-2zm0 4v8h2v-8h-2z"/>
              </svg>
            </a>

            <!-- Text Content - Bottom -->
            <div class="absolute bottom-0 left-0 right-0 p-6 text-white z-10 pointer-events-none">
              <div class="flex items-center gap-3 mb-3">
                <h3 class="text-3xl font-bold drop-shadow-lg">{{ animal.title }}</h3>
                <span 
                  v-if="getUserDetectionCount(animal.title) > 0"
                  class="bg-blue-500/90 text-white text-sm font-semibold px-3 py-1 rounded-full backdrop-blur-sm"
                >
                  {{ getUserDetectionCount(animal.title) }} user{{ getUserDetectionCount(animal.title) !== 1 ? 's' : '' }}
                </span>
              </div>
              <p class="text-white/90 text-base leading-relaxed line-clamp-3 drop-shadow-md">
                {{ animal.description }}
              </p>
            </div>

            <!-- Swipe Up Hint -->
            <div class="absolute bottom-40 left-1/2 -translate-x-1/2 text-white text-center z-10 pointer-events-none">
              <div class="animate-bounce">
                <svg class="w-8 h-8 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18"/>
                </svg>
                <p class="text-sm font-medium drop-shadow-lg">Swipe up to match</p>
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'

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

// Computed property for main image source
const mainImageSrc = computed(() => {
  if (imageData.value?.raw) {
    return `data:image/jpeg;base64,${imageData.value.raw}`
  }
  return null
})

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
    
    // Fetch Wikipedia articles for detected species
    if (detectedSpecies.length > 0) {
      await fetchAnimals(detectedSpecies)
    } else {
      // Fallback to default list if no detections
      await fetchAnimals([
        'Roe deer'
      ])
    }
  } catch (e) {
    console.error('Failed to fetch image data:', e)
    error.value = 'Failed to load image data. Please try again later.'
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

// Submit the match
const submitMatch = async (animal: WikipediaArticle) => {
  try {
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

    // Reload the page to get fresh data (or navigate to next image when random endpoint is ready)
    window.location.reload()
    
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
  const swipeThreshold = 80
  const matchThreshold = -100 // Swipe up threshold
  
  const diffX = dragOffset.value.x
  const diffY = dragOffset.value.y
  
  // Check for swipe up (match)
  if (diffY < matchThreshold && Math.abs(diffX) < swipeThreshold) {
    const currentAnimal = animals.value[currentSlide.value]
    if (currentAnimal) {
      submitMatch(currentAnimal)
    }
    return
  }
  
  // Check for horizontal swipe (navigate)
  if (Math.abs(diffX) > swipeThreshold && Math.abs(diffY) < swipeThreshold) {
    if (diffX < 0) {
      nextSlide()
    } else {
      prevSlide()
    }
  }
}

const nextSlide = () => {
  if (currentSlide.value < animals.value.length - 1) {
    currentSlide.value++
  }
}

const prevSlide = () => {
  if (currentSlide.value > 0) {
    currentSlide.value--
  }
}

const goToSlide = (index: number) => {
  currentSlide.value = index
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
