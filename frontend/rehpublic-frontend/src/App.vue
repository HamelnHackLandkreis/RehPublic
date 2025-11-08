<script setup lang="ts">
import Sidebar from '@/components/Sidebar.vue'
</script>

<template>
  <div class="h-screen flex flex-col md:flex-row overflow-hidden">
    <!-- Sidebar Navigation -->
    <Sidebar />
    
    <!-- Main Content Area -->
    <main class="flex-1 overflow-auto pb-16 md:pb-0 md:ml-20 bg-gray-50">
      <router-view />
    </main>
  </div>
</template>

<style scoped></style>
