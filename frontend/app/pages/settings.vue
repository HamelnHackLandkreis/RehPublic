<template>
  <div class="flex flex-grow flex-col overflow-x-hidden">
    <div class="flex-1 flex flex-col max-w-4xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-4 sm:py-6">
      <h1 class="text-3xl font-bold mb-6">Settings</h1>

      <!-- User Profile Section -->
      <div class="bg-white rounded-lg shadow p-6 mb-6">
        <h2 class="text-xl font-semibold mb-4">Profile</h2>
        <div v-if="userProfile" class="space-y-3">
          <div>
            <span class="text-gray-600">Name:</span>
            <span class="ml-2 font-medium">{{ userProfile.name || 'Not set' }}</span>
          </div>
          <div>
            <span class="text-gray-600">Email:</span>
            <span class="ml-2 font-medium">{{ userProfile.email || 'Not set' }}</span>
          </div>
        </div>
        <div v-else class="text-gray-500">Loading profile...</div>
      </div>

      <!-- Privacy Settings Section -->
      <div class="bg-white rounded-lg shadow p-6">
        <h2 class="text-xl font-semibold mb-4">Privacy Settings</h2>

        <div class="space-y-4">
          <div class="flex items-start">
            <div class="flex-1">
              <h3 class="font-medium text-gray-900">Image Visibility</h3>
              <p class="text-sm text-gray-600 mt-1">
                Control whether your uploaded images are visible to other users.
                When disabled, only you can see your images.
              </p>
            </div>
            <div class="ml-4">
              <label class="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  v-model="privacyPublic"
                  @change="handlePrivacyToggle"
                  :disabled="saving"
                  class="sr-only peer"
                />
                <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-green-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-600"></div>
              </label>
            </div>
          </div>

          <div v-if="privacyPublic" class="bg-green-50 border-l-4 border-green-500 p-3">
            <p class="text-sm text-green-700">
              ✓ Your images are visible to all users
            </p>
          </div>
          <div v-else class="bg-gray-50 border-l-4 border-gray-500 p-3">
            <p class="text-sm text-gray-700">
              🔒 Your images are private (only visible to you)
            </p>
          </div>

          <!-- Success/Error Messages -->
          <div v-if="saveSuccess" class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
            Settings saved successfully!
          </div>
          <div v-if="saveError" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            Failed to save settings: {{ saveError }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

definePageMeta({
  middleware: 'auth'
})

interface UserProfile {
  id: string
  email: string | null
  name: string | null
  privacy_public: boolean
}

const { fetchWithAuth } = useAuthenticatedApi()

const userProfile = ref<UserProfile | null>(null)
const privacyPublic = ref(true)
const saving = ref(false)
const saveSuccess = ref(false)
const saveError = ref<string | null>(null)

const fetchUserProfile = async () => {
  try {
    const response = await fetchWithAuth('/users/me')
    if (response.ok) {
      userProfile.value = await response.json()
      privacyPublic.value = userProfile.value?.privacy_public ?? true
    }
  } catch (error) {
    console.error('Failed to fetch user profile:', error)
  }
}

const handlePrivacyToggle = async () => {
  saving.value = true
  saveSuccess.value = false
  saveError.value = null

  try {
    const response = await fetchWithAuth('/users/me/privacy', {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        privacy_public: privacyPublic.value
      })
    })

    if (response.ok) {
      userProfile.value = await response.json()
      saveSuccess.value = true
      setTimeout(() => {
        saveSuccess.value = false
      }, 3000)
    } else {
      const error = await response.json()
      saveError.value = error.detail || 'Unknown error'
      // Revert toggle on error
      privacyPublic.value = !privacyPublic.value
    }
  } catch (error) {
    console.error('Failed to update privacy setting:', error)
    saveError.value = 'Network error'
    // Revert toggle on error
    privacyPublic.value = !privacyPublic.value
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await fetchUserProfile()
})
</script>
