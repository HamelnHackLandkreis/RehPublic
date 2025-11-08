<template>
  <nav class="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-lg md:top-0 md:left-0 md:bottom-0 md:right-auto md:w-20 md:border-t-0 md:border-r z-50">
    <ul class="flex justify-around md:flex-col md:h-full md:py-4">
      <li v-for="item in navItems" :key="item.name" class="flex-1 md:flex-none">
        <router-link
          :to="item.path"
          class="flex flex-col items-center justify-center h-16 transition-colors"
          :class="[
            $route.path === item.path 
              ? 'text-blue-600' 
              : 'text-gray-600 hover:text-blue-500'
          ]"
        >
          <span class="text-2xl">{{ item.icon }}</span>
          <span class="text-xs mt-1">{{ item.label }}</span>
        </router-link>
      </li>
    </ul>
  </nav>
</template>

<script setup lang="ts">
const navItems = [
  { name: 'map', path: '/', icon: '📍', label: 'Map' },
  { name: 'upload', path: '/upload', icon: '📤', label: 'Upload' },
  { name: 'gallery', path: '/gallery', icon: '🏷️', label: 'Gallery' },
  { name: 'statistics', path: '/statistics', icon: '📊', label: 'Stats' }
]
</script>
