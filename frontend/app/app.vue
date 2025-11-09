<script setup>
// Main app layout
useHead({
  title: 'RehPublic',
  titleTemplate: '%s - Wildlife Monitoring'
})
</script>

<template>
   <div class="min-h-screen flex flex-col justify-between pb-20">
    <main class="flex flex-grow flex-shrink">
      <NuxtPage />
    </main>
    <Sidebar class="flex-shrink-0" />
  </div>
</template>
