<script setup>
// Sidebar component for navigation
const isOpen = ref(false)

const toggleSidebar = () => {
  isOpen.value = !isOpen.value
}

// Close sidebar on route change (mobile)
const route = useRoute()
watch(() => route.path, () => {
  if (window.innerWidth < 768) {
    isOpen.value = false
  }
})
</script>

<template>
  <div>
    <!-- Mobile Toggle Button -->
    <button
      @click="toggleSidebar"
      class="fixed top-4 left-4 z-50 md:hidden bg-blue-600 text-white p-3 rounded-lg shadow-lg hover:bg-blue-700 transition-colors"
      aria-label="Toggle menu"
    >
      <Icon :name="isOpen ? 'mdi:close' : 'mdi:menu'" class="text-2xl" />
    </button>

    <!-- Sidebar -->
    <div
      :class="[
        'fixed md:static inset-y-0 left-0 z-40 w-64 min-h-screen bg-gray-100 p-5 border-r border-gray-300 transition-transform duration-300 ease-in-out',
        isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
      ]"
    >
      <nav class="mt-16 md:mt-0">
        <ul class="list-none p-0 m-0">
          <li class="mb-2.5">
            <NuxtLink
              to="/upload"
              class="flex items-center gap-3 py-2.5 px-4 no-underline text-gray-800 rounded transition-colors hover:bg-gray-200 [&.router-link-active]:bg-blue-600 [&.router-link-active]:text-white"
            >
              <Icon name="mdi:cloud-upload" class="text-xl" />
              <span>Upload</span>
            </NuxtLink>
          </li>
          <li class="mb-2.5">
            <NuxtLink
              to="/statistics"
              class="flex items-center gap-3 py-2.5 px-4 no-underline text-gray-800 rounded transition-colors hover:bg-gray-200 [&.router-link-active]:bg-blue-600 [&.router-link-active]:text-white"
            >
              <Icon name="mdi:chart-bar" class="text-xl" />
              <span>Statistics</span>
            </NuxtLink>
          </li>
          <li class="mb-2.5">
            <NuxtLink
              to="/map"
              class="flex items-center gap-3 py-2.5 px-4 no-underline text-gray-800 rounded transition-colors hover:bg-gray-200 [&.router-link-active]:bg-blue-600 [&.router-link-active]:text-white"
            >
              <Icon name="mdi:map-marker" class="text-xl" />
              <span>Map</span>
            </NuxtLink>
          </li>
          <li class="mb-2.5">
            <NuxtLink
              to="/match"
              class="flex items-center gap-3 py-2.5 px-4 no-underline text-gray-800 rounded transition-colors hover:bg-gray-200 [&.router-link-active]:bg-blue-600 [&.router-link-active]:text-white"
            >
              <Icon name="mdi:image-search" class="text-xl" />
              <span>Match</span>
            </NuxtLink>
          </li>
        </ul>
      </nav>
    </div>
  </div>
</template>
