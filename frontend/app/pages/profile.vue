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
                :disabled="saving || loading"
                class="sr-only peer"
              />
              <div class="w-14 h-7 bg-slate-700 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-800 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-gradient-to-r peer-checked:from-indigo-600 peer-checked:to-purple-600 peer-disabled:opacity-50 peer-disabled:cursor-not-allowed"></div>
            </label>
          </div>

          <!-- Success/Error Messages -->
          <div v-if="saveSuccess" class="mt-4 p-3 bg-green-500/20 border border-green-500/30 rounded-lg">
            <p class="text-sm text-green-300">✓ Privacy setting updated successfully</p>
          </div>
          <div v-if="saveError" class="mt-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg">
            <p class="text-sm text-red-300">✗ {{ saveError }}</p>
          </div>
          <div v-if="loading" class="mt-4 p-3 bg-slate-700/50 rounded-lg">
            <p class="text-sm text-slate-300">Loading privacy settings...</p>
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
interface UserProfile {
  id: string
  email: string | null
  name: string | null
  privacy_public: boolean
  created_at: string
  updated_at: string
}

const { user: auth0User, logout } = useAuth()
const { fetchWithAuth } = useAuthenticatedApi()

const userProfile = ref<UserProfile | null>(null)
const isPublic = ref(false)
const loading = ref(true)
const saving = ref(false)
const saveSuccess = ref(false)
const saveError = ref<string | null>(null)

const user = computed(() => {
  const auth0 = auth0User.value
  const profile = userProfile.value

  if (!auth0 && !profile) {
    return null
  }

  return {
    ...auth0,
    ...profile,
    email: auth0?.email || profile?.email || null,
    name: auth0?.name || profile?.name || null,
    picture: auth0?.picture || null,
    email_verified: auth0?.email_verified || false
  }
})

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
  const target = e.target as HTMLImageElement
  target.style.display = 'none'
}

const fetchUserProfile = async () => {
  loading.value = true
  saveError.value = null

  try {
    const response = await fetchWithAuth('/users/me')

    if (!response.ok) {
      throw new Error(`Failed to fetch profile: ${response.status}`)
    }

    const data: UserProfile = await response.json()
    userProfile.value = data
    isPublic.value = data.privacy_public
  } catch (error) {
    console.error('Failed to fetch user profile:', error)
    saveError.value = error instanceof Error ? error.message : 'Failed to load profile'
  } finally {
    loading.value = false
  }
}

const updatePrivacy = async () => {
  saving.value = true
  saveSuccess.value = false
  saveError.value = null

  const previousValue = !isPublic.value

  try {
    const response = await fetchWithAuth('/users/me/privacy', {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        privacy_public: isPublic.value
      })
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(errorData.detail || `Failed to update privacy: ${response.status}`)
    }

    const updatedProfile: UserProfile = await response.json()
    userProfile.value = updatedProfile
    isPublic.value = updatedProfile.privacy_public
    saveSuccess.value = true

    setTimeout(() => {
      saveSuccess.value = false
    }, 3000)
  } catch (error) {
    console.error('Failed to update privacy setting:', error)
    isPublic.value = previousValue
    saveError.value = error instanceof Error ? error.message : 'Failed to update privacy setting'

    setTimeout(() => {
      saveError.value = null
    }, 5000)
  } finally {
    saving.value = false
  }
}

const handleLogout = () => {
  logout()
}

onMounted(async () => {
  await fetchUserProfile()
})
</script>
