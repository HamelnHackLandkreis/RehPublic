<script setup>
// Main app layout with global auth check
const { isAuthenticated, isLoading, login } = useAuth()
const route = useRoute()

// Global auth protection
watch([isAuthenticated, isLoading], ([authenticated, loading]) => {
  // Skip callback page
  if (route.path === '/callback') {
    return
  }

  // Wait for auth to initialize
  if (loading) {
    return
  }

  // Redirect to login if not authenticated
  if (!authenticated) {
    login()
  }
}, { immediate: true })

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
