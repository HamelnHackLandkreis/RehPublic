<template>
  <div class="fixed inset-0 w-screen h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
    <div class="flex items-center justify-center h-full">
      <div class="flex flex-col items-center gap-4">
        <LoadingSpinner size="md" />
        <p class="text-lg font-medium text-slate-300">Completing login...</p>
      </div>
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
