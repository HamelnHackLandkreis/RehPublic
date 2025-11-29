<template>
  <div class="fixed inset-0 w-screen h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white overflow-y-auto pb-20 md:pb-0">
    <div class="max-w-4xl mx-auto p-6 md:p-8">
      <!-- Header with Profile Picture -->
      <div class="relative mb-8">
        <div class="absolute inset-0 bg-gradient-to-r from-indigo-500/20 to-purple-500/20 rounded-2xl blur-xl"></div>
        <div class="relative bg-slate-800/50 backdrop-blur-sm rounded-2xl p-8 border border-slate-700/50">
          <div class="flex flex-col md:flex-row items-center md:items-start gap-6">
            <div class="relative">
              <div class="absolute inset-0 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-full blur-md opacity-50"></div>
              <div v-if="user?.picture" class="relative w-24 h-24 md:w-32 md:h-32 rounded-full overflow-hidden border-4 border-indigo-500 shadow-2xl">
                <img
                  :src="user.picture"
                  :alt="user?.name || 'User'"
                  class="w-full h-full object-cover"
                  @error="handleImageError"
                />
              </div>
              <div v-else class="relative w-24 h-24 md:w-32 md:h-32 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center border-4 border-indigo-500 shadow-2xl">
                <span class="text-4xl md:text-5xl font-bold text-white">{{ userInitial }}</span>
              </div>
            </div>
            <div class="flex-1 text-center md:text-left">
              <h1 class="text-3xl md:text-4xl font-bold mb-2 bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
                {{ user?.name || 'User' }}
              </h1>
              <p class="text-lg text-slate-300 mb-3">{{ user?.email || 'No email' }}</p>
              <div class="inline-flex items-center gap-2 px-4 py-2 bg-green-500/20 border border-green-500/30 rounded-full">
                <div class="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span class="text-sm text-green-300">{{ user?.email_verified ? 'Email Verified' : 'Email Not Verified' }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Privacy Settings Card -->
      <div class="relative mb-6">
        <div class="absolute inset-0 bg-gradient-to-r from-blue-500/10 to-cyan-500/10 rounded-2xl blur-xl"></div>
        <div class="relative bg-slate-800/50 backdrop-blur-sm rounded-2xl p-6 border border-slate-700/50">
          <div class="flex items-center gap-3 mb-4">
            <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
              <Icon name="mdi:shield-account" class="text-2xl text-white" />
            </div>
            <h2 class="text-2xl font-bold">Privacy Settings</h2>
          </div>

          <div class="flex items-center justify-between p-4 bg-slate-900/50 rounded-xl border border-slate-700/30 hover:border-indigo-500/50 transition-colors">
            <div class="flex items-center gap-4">
              <div class="w-12 h-12 rounded-lg bg-indigo-500/20 flex items-center justify-center">
                <Icon name="mdi:image-multiple" class="text-2xl text-indigo-400" />
              </div>
              <div>
                <p class="font-semibold text-lg">Public Images</p>
                <p class="text-sm text-slate-400">Allow others to see your uploaded images</p>
              </div>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                v-model="isPublic"
                @change="updatePrivacy"
                class="sr-only peer"
              />
              <div class="w-14 h-7 bg-slate-700 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-800 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-gradient-to-r peer-checked:from-indigo-600 peer-checked:to-purple-600"></div>
            </label>
          </div>
        </div>
      </div>

      <!-- Logout Button -->
      <div class="relative">
        <div class="absolute inset-0 bg-gradient-to-r from-red-500/10 to-pink-500/10 rounded-2xl blur-xl"></div>
        <button
          @click="handleLogout"
          class="relative w-full bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 text-white font-bold py-4 px-6 rounded-2xl transition-all transform hover:scale-[1.02] active:scale-[0.98] shadow-lg hover:shadow-red-500/50 border border-red-500/30"
        >
          <div class="flex items-center justify-center gap-3">
            <Icon name="mdi:logout" class="text-2xl" />
            <span class="text-lg">Log Out</span>
          </div>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const { user, logout } = useAuth()
const isPublic = ref(false)

const userInitial = computed(() => {
  if (user.value?.name) {
    return user.value.name.charAt(0).toUpperCase()
  }
  if (user.value?.email) {
    return user.value.email.charAt(0).toUpperCase()
  }
  return 'U'
})

const handleImageError = (e: Event) => {
  // Hide the image element if it fails to load
  const target = e.target as HTMLImageElement
  target.style.display = 'none'
}

// TODO: Load user's privacy setting from backend
onMounted(async () => {
  // Fetch user privacy setting from API
  // isPublic.value = await fetchUserPrivacy()
})

const updatePrivacy = async () => {
  // TODO: Update privacy setting in backend
  console.log('Privacy updated:', isPublic.value)
  // await updateUserPrivacy(isPublic.value)
}

const handleLogout = () => {
  logout()
}
</script>
