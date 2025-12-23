<template>
  <div class="fixed inset-0 w-screen h-screen bg-slate-900 text-white overflow-y-auto pb-20 md:pb-0">
    <div class="max-w-4xl mx-auto p-6 md:p-8">
      <!-- Header with Profile Picture -->
      <div class="mb-8">
        <div class="bg-slate-800 rounded-lg p-8 border border-slate-700">
          <div class="flex flex-col md:flex-row items-center md:items-start gap-6">
            <div class="flex-shrink-0">
              <div v-if="user?.picture" class="w-24 h-24 md:w-32 md:h-32 rounded-full overflow-hidden border-2 border-slate-600 bg-slate-700">
                <img
                  :src="user.picture"
                  :alt="user?.name || 'User'"
                  class="w-full h-full object-cover rounded-full"
                  @error="handleImageError"
                />
              </div>
              <div v-else class="w-24 h-24 md:w-32 md:h-32 rounded-full bg-primary flex items-center justify-center border-2 border-slate-600">
                <span class="text-4xl md:text-5xl font-bold text-white">{{ userInitial }}</span>
              </div>
            </div>
            <div class="flex-1 text-center md:text-left">
              <h1 class="text-3xl md:text-4xl font-bold mb-2 text-white">
                {{ user?.name || 'User' }}
              </h1>
              <p class="text-lg text-slate-300 mb-3">{{ user?.email || 'No email' }}</p>
              <div v-if="user?.email_verified" class="inline-flex items-center gap-2 px-3 py-1.5 bg-slate-700 border border-slate-600 rounded-full">
                <div class="w-2 h-2 bg-green-400 rounded-full"></div>
                <span class="text-sm text-slate-300">Email Verified</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Privacy Settings Card -->
      <div class="mb-6">
        <div class="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <div class="flex items-center gap-3 mb-4">
            <div class="w-10 h-10 rounded-lg bg-slate-700 flex items-center justify-center">
              <Icon name="mdi:shield-account" class="text-2xl text-primary" />
            </div>
            <h2 class="text-2xl font-bold">Privacy Settings</h2>
          </div>

          <div class="flex items-center justify-between p-4 bg-slate-900 rounded-lg border border-slate-700 hover:border-primary transition-colors">
            <div class="flex items-center gap-4">
              <div class="w-12 h-12 rounded-lg bg-slate-700 flex items-center justify-center">
                <Icon name="mdi:image-multiple" class="text-2xl text-primary" />
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
              <div class="w-14 h-7 bg-slate-700 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/50 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-600 after:border after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-primary peer-disabled:opacity-50 peer-disabled:cursor-not-allowed"></div>
            </label>
          </div>

          <!-- Success/Error Messages -->
          <div v-if="saveSuccess" class="mt-4 p-3 bg-slate-700 border border-slate-600 rounded-lg">
            <p class="text-sm text-success">✓ Privacy setting updated successfully</p>
          </div>
          <div v-if="saveError" class="mt-4 p-3 bg-slate-700 border border-slate-600 rounded-lg">
            <p class="text-sm text-error">✗ {{ saveError }}</p>
          </div>
          <div v-if="loading" class="mt-4 p-3 bg-slate-700 rounded-lg">
            <p class="text-sm text-slate-300">Loading privacy settings...</p>
          </div>
        </div>
      </div>

      <!-- Logout Button -->
      <div>
        <button
          @click="handleLogout"
          class="w-full bg-error hover:bg-error-dark text-white font-semibold py-4 px-6 rounded-lg transition-colors border border-error-dark"
        >
          <div class="flex items-center justify-center gap-3">
            <Icon name="mdi:logout" class="text-xl" />
            <span class="text-base">Log Out</span>
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
