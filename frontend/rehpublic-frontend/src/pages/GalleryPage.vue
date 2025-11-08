<template>
  <div class="flex flex-col h-full">
    <!-- Large Image - 2/3 height -->
    <div class="h-2/3 bg-gray-300 flex items-center justify-center">
      <p class="text-gray-600">Large Image Preview</p>
    </div>
    
    <!-- Grid of 4 images - 1/3 height -->
    <div class="h-1/3 grid grid-cols-2 gap-1 p-1">
      <div class="bg-gray-200 flex items-center justify-center">
        <p class="text-xs text-gray-500">Image 1</p>
      </div>
      <div class="bg-gray-200 flex items-center justify-center">
        <p class="text-xs text-gray-500">Image 2</p>
      </div>
      <div class="bg-gray-200 flex items-center justify-center">
        <p class="text-xs text-gray-500">Image 3</p>
      </div>
      <div class="bg-gray-200 flex items-center justify-center">
        <p class="text-xs text-gray-500">Image 4</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
</script>
