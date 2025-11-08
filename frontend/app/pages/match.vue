<template>
  <div class="min-h-screen bg-gradient-to-b from-gray-50 to-gray-200">
    <!-- Full Size Image - Border to Border -->
    <div class="w-full h-[60vh] overflow-hidden mb-12">
      <img 
        src="/fallback.JPG" 
        alt="Main Wildlife Image" 
        class="w-full h-full object-cover"
      />
    </div>

    <!-- Swipeable Carousel with Placeholders -->
    <div class="max-w-6xl mx-auto px-8 pb-8">
      <h2 class="text-center text-3xl font-semibold mb-6 text-gray-800">Related Images</h2>
      <div class="relative">
        <div 
          class="overflow-hidden rounded-xl cursor-grab active:cursor-grabbing select-none"
          @touchstart="handleTouchStart"
          @touchmove="handleTouchMove"
          @touchend="handleTouchEnd"
          @mousedown="handleMouseDown"
          @mousemove="handleMouseMove"
          @mouseup="handleMouseEnd"
          @mouseleave="handleMouseEnd"
        >
          <div 
            class="flex transition-transform duration-500 ease-in-out" 
          >
            <div 
              v-for="(image, index) in placeholderImages" 
              :key="index" 
              class="min-w-full px-2"
            >
              <div class="aspect-video bg-gradient-to-br from-purple-500 to-purple-700 rounded-xl flex items-center justify-center shadow-lg">
                <span class="text-white text-4xl font-semibold drop-shadow-md">Image {{ index + 1 }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Carousel Indicators -->
      <div class="flex justify-center gap-2 mt-6">
        <button 
          v-for="(image, index) in placeholderImages" 
          :key="index"
          class="w-3 h-3 rounded-full border-0 transition-all duration-300 hover:scale-110"
          :class="currentSlide === index ? 'bg-purple-600 scale-125' : 'bg-gray-300 hover:bg-gray-400'"
          @click="goToSlide(index)"
        ></button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const currentSlide = ref(0)
const placeholderImages = ref([1, 2, 3, 4, 5])

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
@media (max-width: 768px) {
  .h-\[60vh\] {
    height: 50vh;
  }
}
</style>
