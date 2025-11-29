<script setup lang="ts">
import { computed } from 'vue'
import LoginButton from './LoginButton.vue'

const route = useRoute()
const { isAuthenticated, isLoading, user } = useAuth()

const isMapPage = computed(() => route.path.startsWith('/map'))
const isCameraPage = computed(() => route.path.startsWith('/camera'))
const isStatisticsPage = computed(() => route.path.startsWith('/statistics'))
const isMatchPage = computed(() => route.path.startsWith('/match'))
const isProfilePage = computed(() => route.path.startsWith('/profile'))

const placeholderImage = `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100' viewBox='0 0 100 100'%3E%3Ccircle cx='50' cy='50' r='50' fill='%2363b3ed'/%3E%3Cpath d='M50 45c7.5 0 13.64-6.14 13.64-13.64S57.5 17.72 50 17.72s-13.64 6.14-13.64 13.64S42.5 45 50 45zm0 6.82c-9.09 0-27.28 4.56-27.28 13.64v3.41c0 1.88 1.53 3.41 3.41 3.41h47.74c1.88 0 3.41-1.53 3.41-3.41v-3.41c0-9.08-18.19-13.64-27.28-13.64z' fill='%23fff'/%3E%3C/svg%3E`

const userInitial = computed(() => {
  if (user.value?.name) {
    return user.value.name.charAt(0).toUpperCase()
  }
  if (user.value?.email) {
    return user.value.email.charAt(0).toUpperCase()
  }
  return 'U'
})
</script>

<template>
  <nav
    class="fixed bottom-0 left-0 right-0 z-50 bg-slate-900 border-t border-slate-700 shadow-2xl md:top-0 md:bottom-auto md:right-auto md:w-auto md:h-screen md:border-t-0 md:border-r">
    <ul
      class="flex items-center justify-around md:flex-col md:justify-center md:gap-1 md:pt-0 list-none p-0 m-0 max-w-screen-xl md:max-w-none mx-auto md:h-full">
      <li>
        <NuxtLink to="/map" :class="[
          'flex flex-col items-center gap-1 py-4 px-6 md:py-3 md:px-3 md:rounded-lg no-underline transition-all group md:w-16',
          isMapPage ? 'text-indigo-400 bg-slate-800' : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
        ]">
          <Icon name="mdi:map-marker" class="text-2xl" />
          <span class="text-xs font-medium">Map</span>
        </NuxtLink>
      </li>
      <li>
        <NuxtLink to="/camera" :class="[
          'flex flex-col items-center gap-1 py-4 px-6 md:py-3 md:px-3 md:rounded-lg no-underline transition-all group md:w-16',
          isCameraPage ? 'text-indigo-400 bg-slate-800' : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
        ]">
          <Icon name="mdi:camera" class="text-2xl" />
          <span class="text-xs font-medium">Cams</span>
        </NuxtLink>
      </li>
      <li>
        <NuxtLink to="/statistics" :class="[
          'flex flex-col items-center gap-1 py-4 px-6 md:py-3 md:px-3 md:rounded-lg no-underline transition-all group md:w-16',
          isStatisticsPage ? 'text-indigo-400 bg-slate-800' : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
        ]">
          <Icon name="mdi:chart-bar" class="text-2xl" />
          <span class="text-xs font-medium">Statistics</span>
        </NuxtLink>
      </li>
      <li>
        <NuxtLink to="/match" :class="[
          'flex flex-col items-center gap-1 py-4 px-6 md:py-3 md:px-3 md:rounded-lg no-underline transition-all group md:w-16',
          isMatchPage ? 'text-indigo-400 bg-slate-800' : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
        ]">
          <Icon name="mdi:image-search" class="text-2xl" />
          <span class="text-xs font-medium">Match</span>
        </NuxtLink>
      </li>
      <li class="md:mt-auto md:border-t md:border-slate-700 md:pt-2">
        <ClientOnly>
          <div v-if="isLoading" class="flex flex-col items-center gap-1 py-4 px-6 md:py-3 md:px-3">
            <div class="w-8 h-8 rounded-full bg-slate-700 animate-pulse"></div>
          </div>
          <NuxtLink v-else-if="isAuthenticated" to="/profile" :class="[
            'flex flex-col items-center gap-1 py-4 px-6 md:py-3 md:px-3 md:rounded-lg no-underline transition-all group md:w-16',
            isProfilePage ? 'text-indigo-400 bg-slate-800' : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
          ]">
            <div v-if="user?.picture" class="w-8 h-8 rounded-full overflow-hidden border-2 border-current">
              <img
                :src="user.picture"
                :alt="user?.name || 'User'"
                class="w-full h-full object-cover"
              />
            </div>
            <div v-else class="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center border-2 border-current">
              <span class="text-sm font-bold">{{ userInitial }}</span>
            </div>
            <span class="text-xs font-medium">Profile</span>
          </NuxtLink>
        </ClientOnly>
      </li>
    </ul>
  </nav>
</template>
