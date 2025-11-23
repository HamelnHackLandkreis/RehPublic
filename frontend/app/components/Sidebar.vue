<script setup lang="ts">
import { computed } from 'vue'
import LoginButton from './LoginButton.vue'
import LogoutButton from './LogoutButton.vue'
import UserProfile from './UserProfile.vue'

const route = useRoute()
const { isAuthenticated, isLoading } = useAuth()

const isMapPage = computed(() => route.path.startsWith('/map'))
const isCameraPage = computed(() => route.path.startsWith('/camera'))
const isStatisticsPage = computed(() => route.path.startsWith('/statistics'))
const isMatchPage = computed(() => route.path.startsWith('/match'))
const isSettingsPage = computed(() => route.path.startsWith('/settings'))
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
      <li>
        <NuxtLink to="/settings" :class="[
          'flex flex-col items-center gap-1 py-4 px-6 md:py-3 md:px-3 md:rounded-lg no-underline transition-all group md:w-16',
          isSettingsPage ? 'text-indigo-400 bg-slate-800' : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
        ]">
          <Icon name="mdi:cog" class="text-2xl" />
          <span class="text-xs font-medium">Settings</span>
        </NuxtLink>
      </li>
      <li class="md:mt-auto md:border-t md:border-slate-700 md:pt-2">
        <div v-if="isLoading" class="flex flex-col items-center gap-2 py-4 px-6 md:py-3 md:px-3">
          <div class="text-slate-400 text-xs">Loading...</div>
        </div>
        <div v-else-if="isAuthenticated" class="flex flex-col items-center gap-2 py-4 px-6 md:py-3 md:px-3 w-full">
          <div class="w-full px-2">
            <UserProfile />
          </div>
          <div class="w-full px-2">
            <LogoutButton />
          </div>
        </div>
        <div v-else class="flex flex-col items-center gap-2 py-4 px-6 md:py-3 md:px-3 w-full">
          <div class="w-full px-2">
            <LoginButton />
          </div>
        </div>
      </li>
    </ul>
  </nav>
</template>
