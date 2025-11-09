<script setup lang="ts">
import { computed } from 'vue'

const route = useRoute()

const isCameraPage = computed(() => {
  return route.path.startsWith('/camera')
})
</script>

<template>
  <nav class="fixed bottom-0 left-0 right-0 z-50 bg-slate-900 border-t border-slate-700 shadow-2xl">
    <ul class="flex items-center justify-around list-none p-0 m-0 max-w-screen-xl mx-auto">
      <li>
        <NuxtLink to="/map"
          class="flex flex-col items-center gap-1 py-4 px-6 no-underline text-slate-400 transition-all hover:text-white [&.router-link-active]:text-indigo-400 group">
          <Icon name="mdi:map-marker" class="text-2xl" />
          <span class="text-xs font-medium">Map</span>
        </NuxtLink>
      </li>
      <li>
        <NuxtLink
          to="/camera"
          :class="[
            'flex flex-col items-center gap-1 py-4 px-6 no-underline text-slate-400 transition-all hover:text-white group',
            isCameraPage && 'text-indigo-400'
          ]"
        >
          <Icon name="mdi:camera" class="text-2xl" />
          <span class="text-xs font-medium">Cams</span>
        </NuxtLink>
      </li>
      <li>
        <NuxtLink to="/statistics"
          class="flex flex-col items-center gap-1 py-4 px-6 no-underline text-slate-400 transition-all hover:text-white [&.router-link-active]:text-indigo-400 group">
          <Icon name="mdi:chart-bar" class="text-2xl" />
          <span class="text-xs font-medium">Statistics</span>
        </NuxtLink>
      </li>
      <li>
        <NuxtLink
          to="/match"
          class="flex flex-col items-center gap-1 py-4 px-6 no-underline text-slate-400 transition-all hover:text-white [&.router-link-active]:text-indigo-400 group"
        >
          <Icon name="mdi:image-search" class="text-2xl" />
          <span class="text-xs font-medium">Match</span>
        </NuxtLink>
      </li>
    </ul>
  </nav>
</template>
