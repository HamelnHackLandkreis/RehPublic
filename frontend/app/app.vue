<script setup>
// Main app layout
useHead({
  title: 'RehPublic',
  titleTemplate: '%s - Wildlife Monitoring'
})
</script>

<template>
  <div class="min-h-screen flex flex-col md:flex-row justify-between pb-20 md:pb-0">
    <Sidebar class="flex-shrink-0" />
    <main class="flex flex-grow flex-shrink w-full md:ml-20 lg:ml-20">
      <div class="w-full flex flex-grow lg:max-w-7xl lg:mx-auto lg:px-6">
        <NuxtPage />
      </div>
    </main>
  </div>
</template>
