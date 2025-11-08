<template>
  <div class="min-h-screen bg-gradient-to-b from-gray-50 to-gray-200">
    <!-- Full Size Image - Border to Border -->
    <div class="w-full h-[60vh] overflow-hidden mb-12 relative">
      <img 
        src="/fallback.JPG" 
        alt="Main Wildlife Image" 
        class="w-full h-full object-cover"
      />
      <div class="absolute top-4 left-4 bg-black/60 text-white px-4 py-2 rounded-lg backdrop-blur-sm">
        <p class="text-sm font-medium">What animal do you see?</p>
      </div>
    </div>

    <!-- Animal Match Cards -->
    <div class="max-w-6xl mx-auto px-8 pb-12">
      <div v-if="loading" class="text-center py-12">
        <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
        <p class="mt-4 text-gray-600">Loading animals...</p>
      </div>

      <div v-else-if="error" class="text-center py-12 text-red-600">
        <p>{{ error }}</p>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div 
          v-for="(animal, index) in animals" 
          :key="index"
          @click="selectAnimal(animal)"
          class="bg-white rounded-xl shadow-lg overflow-hidden cursor-pointer transform transition-all duration-300 hover:scale-105 hover:shadow-2xl"
          :class="selectedAnimal?.title === animal.title ? 'ring-4 ring-green-500 scale-105' : ''"
        >
          <!-- Animal Image -->
          <div class="aspect-video bg-gradient-to-br from-green-400 to-blue-500 relative overflow-hidden">
            <img 
              v-if="animal.image_url"
              :src="animal.image_url" 
              :alt="animal.title"
              class="w-full h-full object-cover"
            />
            <div v-else class="w-full h-full flex items-center justify-center text-white text-2xl font-bold">
              {{ animal.title }}
            </div>
            <div 
              v-if="selectedAnimal?.title === animal.title"
              class="absolute inset-0 bg-green-500/20 flex items-center justify-center"
            >
              <div class="bg-green-500 text-white rounded-full p-3">
                <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
                </svg>
              </div>
            </div>
          </div>

          <!-- Animal Info -->
          <div class="p-5">
            <h3 class="text-xl font-bold text-gray-800 mb-3">{{ animal.title }}</h3>
            <p class="text-gray-600 text-sm mb-4 line-clamp-4">
              {{ animal.description }}
            </p>
            <a 
              :href="animal.article_url" 
              target="_blank"
              @click.stop
              class="inline-flex items-center text-purple-600 hover:text-purple-800 font-medium text-sm"
            >
              Learn more on Wikipedia
              <svg class="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/>
              </svg>
            </a>
          </div>
        </div>
      </div>

      <!-- Submit Button -->
      <div v-if="selectedAnimal" class="mt-8 text-center">
        <button 
          @click="submitMatch"
          class="bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-8 rounded-lg shadow-lg transform transition-all duration-200 hover:scale-105"
        >
          Confirm: This is a {{ selectedAnimal.title }}
        </button>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

// Types
interface WikipediaArticle {
  title: string
  description: string
  image_url: string | null
  article_url: string
}

// State
const currentSlide = ref(0)
const placeholderImages = ref([1, 2, 3, 4, 5])
const animals = ref<WikipediaArticle[]>([])
const selectedAnimal = ref<WikipediaArticle | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

// Animals to fetch (you can customize this list based on your detection model)
const animalList = [
  'Red deer',
  'Wild boar',
  'European badger',
  'Red fox',
  'Roe deer',
  'European rabbit'
]

// Fetch animals from backend
const fetchAnimals = async () => {
  try {
    loading.value = true
    error.value = null
    
    const response = await fetch('http://localhost:8000/wikipedia/articles', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        titles: animalList
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

// Select an animal
const selectAnimal = (animal: WikipediaArticle) => {
  selectedAnimal.value = animal
}

// Submit the match
const submitMatch = () => {
  if (selectedAnimal.value) {
    alert(`Great! You identified this as a ${selectedAnimal.value.title}!`)
    // TODO: Send to backend for validation/learning
    console.log('Selected animal:', selectedAnimal.value)
  }
}

// Fetch on mount
onMounted(() => {
  fetchAnimals()
})

// Touch/Swipe handling for carousel
const touchStartX = ref(0)
const touchEndX = ref(0)
const isDragging = ref(false)
const startX = ref(0)

const handleTouchStart = (e: TouchEvent) => {
  if (e.touches[0]) {
    touchStartX.value = e.touches[0].clientX
  }
}

const handleTouchMove = (e: TouchEvent) => {
  if (e.touches[0]) {
    touchEndX.value = e.touches[0].clientX
  }
}

const handleTouchEnd = () => {
  handleSwipe()
}

const handleMouseDown = (e: MouseEvent) => {
  isDragging.value = true
  startX.value = e.clientX
  touchStartX.value = e.clientX
}

const handleMouseMove = (e: MouseEvent) => {
  if (!isDragging.value) return
  touchEndX.value = e.clientX
}

const handleMouseEnd = () => {
  if (!isDragging.value) return
  isDragging.value = false
  handleSwipe()
}

const handleSwipe = () => {
  const swipeThreshold = 50
  const diff = touchStartX.value - touchEndX.value
  
  if (Math.abs(diff) > swipeThreshold) {
    if (diff > 0) {
      nextSlide()
    } else {
      prevSlide()
    }
  }
  
  touchStartX.value = 0
  touchEndX.value = 0
}

const nextSlide = () => {
  currentSlide.value = (currentSlide.value + 1) % placeholderImages.value.length
}

const prevSlide = () => {
  currentSlide.value = currentSlide.value === 0 
    ? placeholderImages.value.length - 1 
    : currentSlide.value - 1
}

const goToSlide = (index: number) => {
  currentSlide.value = index
}
</script>

<style scoped>
.line-clamp-4 {
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

@media (max-width: 768px) {
  .h-\[60vh\] {
    height: 50vh;
  }
}
</style>
