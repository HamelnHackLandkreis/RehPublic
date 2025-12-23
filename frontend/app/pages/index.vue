<script setup lang="ts">
definePageMeta({
  middleware: (to) => {
    // Only redirect if we're actually on the index page
    if (to.path === '/' || to.path === '') {
      return navigateTo({
        path: '/map',
        query: to.query
      })
    }
  }
})
</script>

<template>
  <div></div>
</template>
