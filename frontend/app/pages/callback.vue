<template>
  <div class="flex items-center justify-center min-h-screen bg-slate-900 text-white">
    <div class="flex flex-col items-center gap-4">
      <div class="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
      <p class="text-lg font-medium text-slate-300">Completing login...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
const { isAuthenticated, isLoading } = useAuth()
const router = useRouter()

watch([isAuthenticated, isLoading], ([authenticated, loading]) => {
  if (!loading) {
    if (authenticated) {
      router.push('/map')
    } else {
      router.push('/')
    }
  }
}, { immediate: true })
</script>
