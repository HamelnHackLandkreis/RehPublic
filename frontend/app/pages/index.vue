<script setup lang="ts">
const route = useRoute()
navigateTo({
  path: '/map',
  query: route.query
})
</script>

<template>
  <div></div>
</template>
