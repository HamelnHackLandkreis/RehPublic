<script setup lang="ts">
import Sidebar from '@/components/Sidebar.vue'
</script>

<template>
  <div class="h-screen flex overflow-hidden">
    <!-- Sidebar Navigation -->
    <Sidebar />
    
    <!-- Main Content Area -->
    <main class="flex-1 overflow-auto ml-64 bg-gray-50">
      <router-view />
    </main>
  </div>
</template>

<style scoped></style>
