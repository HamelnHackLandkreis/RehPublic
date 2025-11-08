<template>
  <nav class="w-64 bg-white border-r border-gray-200 shadow-lg z-50 flex flex-col">
    <!-- Header -->
    <div class="p-6 border-b border-gray-200">
      <h1 class="text-xl font-bold text-gray-800">RehPublic</h1>
      <p class="text-xs text-gray-500 mt-1">Wildlife Tracking</p>
    </div>
    
    <!-- Navigation Items -->
    <ul class="flex-1 py-4">
      <li v-for="item in navItems" :key="item.name">
        <router-link
          :to="item.path"
          class="flex items-center px-6 py-4 transition-colors group"
          :class="[
            $route.path === item.path 
              ? 'bg-blue-50 text-blue-600 border-r-4 border-blue-600' 
              : 'text-gray-700 hover:bg-gray-50 hover:text-blue-600'
          ]"
        >
          <span class="text-2xl mr-4">{{ item.icon }}</span>
          <span class="font-medium">{{ item.label }}</span>
        </router-link>
      </li>
    </ul>
    
    <!-- Footer (optional) -->
    <div class="p-4 border-t border-gray-200 text-center">
      <p class="text-xs text-gray-400">© 2025 RehPublic</p>
    </div>
  </nav>
</template>

<script setup lang="ts">
const navItems = [
  { name: 'map', path: '/', icon: '📍', label: 'Map & Locations' },
  { name: 'upload', path: '/upload', icon: '📤', label: 'Upload' },
  { name: 'gallery', path: '/gallery', icon: '🏷️', label: 'Gallery' },
  { name: 'statistics', path: '/statistics', icon: '📊', label: 'Statistics' }
]
</script>
