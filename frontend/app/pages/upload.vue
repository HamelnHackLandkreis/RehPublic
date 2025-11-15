<template>
  <div class="flex flex-grow flex-col overflow-x-hidden">
    <div class="flex-1 flex flex-col max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-4 sm:py-6 overflow-y-auto">
      <!-- Camera Selection Section -->
      <div class="mb-4">
        <h2 class="text-2xl font-bold mb-4">Select Camera Location</h2>

        <!-- Map for camera selection -->
        <div class="relative h-[25vh] min-h-[200px] mb-4 rounded-xl overflow-hidden border-2 border-gray-300">
          <WildlifeMap
            ref="mapRef"
            height="100%"
            :auto-center="!selectedLocation"
            :default-zoom="20"
            :no-marker-popup="true"
            @location-selected="handleLocationSelect"
          />
        </div>

        <!-- Selected Location Display -->
        <div v-if="selectedLocation" class="bg-green-50 border-l-4 border-green-500 p-3 mb-4">
          <div class="flex items-center gap-2">
            <svg class="text-green-500" width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M20 6L9 17L4 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span class="font-semibold text-gray-900">Selected: {{ selectedLocation.name }}</span>
            <span class="text-gray-600 text-sm ml-2">{{ selectedLocation.description }}</span>
          </div>
        </div>

        <!-- Location Dropdown (always visible) -->
        <div v-if="cameraLocations.length > 0" class="mb-4">
          <label class="block text-sm font-medium text-gray-700 mb-2">Select Camera:</label>
          <select
            v-model="selectedLocationId"
            @change="handleDropdownSelect"
            class="w-full p-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-gray-400 bg-white"
          >
            <option value="">Choose a camera...</option>
            <option v-for="location in cameraLocations" :key="location.id" :value="location.id">
              {{ location.name }}
            </option>
          </select>
        </div>
      </div>

      <!-- Drop Zone -->
      <div
        class="flex-shrink-0 bg-gray-50 border-2 border-dashed rounded-xl py-6 px-8 text-center cursor-pointer transition-all duration-300 mb-6"
        :class="{
          'border-gray-400 bg-gray-100': isDragging,
          'opacity-50 cursor-not-allowed': !selectedLocation,
          'hover:border-gray-400 hover:bg-gray-100': selectedLocation && !isDragging
        }"
        @click="selectedLocation ? triggerFileInput() : null"
        @drop.prevent="handleDrop"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
      >
        <svg class="text-gray-400 mb-2 mx-auto" width="24" height="24" viewBox="0 0 24 24" fill="none">
          <path d="M12 15V3M12 3L8 7M12 3L16 7M2 17L2 19C2 20.1046 2.89543 21 4 21L20 21C21.1046 21 22 20.1046 22 19V17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <p class="text-gray-700 text-sm mb-1">
          <span v-if="!selectedLocation" class="text-red-500">⚠ Please select a camera location first</span>
          <span v-else>Drop files here or <span class="text-gray-900 underline">browse files</span> to add</span>
        </p>
        <p class="text-gray-500 text-xs">Supported: JPG, PNG, GIF (max 10 MB)</p>
        <input
          ref="fileInput"
          type="file"
          multiple
          accept=".jpg,.jpeg,.png,.gif"
          @change="handleFileInput"
          class="hidden"
        />
      </div>

      <!-- Upload Lists Container -->
      <div class="flex-1 overflow-y-auto min-h-0">
        <!-- Uploading Files -->
        <div v-if="uploadingFiles.length > 0" class="mb-6">
          <div class="flex items-center gap-2 text-xs font-semibold tracking-wider text-gray-500 mb-4">
            <span>UPLOADING</span>
          </div>
          <div v-for="file in uploadingFiles" :key="file.id" class="bg-white border border-gray-200 rounded-lg p-4 flex items-center gap-4 mb-3 shadow-sm">
            <div class="text-2xl flex-shrink-0">📄</div>
            <div class="flex-1 min-w-0">
              <div class="flex justify-between items-center mb-2">
                <span class="text-gray-900 text-sm truncate">{{ file.name }}</span>
                <span class="text-gray-500 text-sm ml-4 flex-shrink-0">{{ file.progress }}%</span>
              </div>
              <div class="h-1 bg-gray-200 rounded-full overflow-hidden">
                <div class="h-full bg-gray-400 transition-all duration-300" :style="{ width: file.progress + '%' }"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Finished Files -->
        <div v-if="finishedFiles.length > 0" class="mb-6">
          <div class="flex items-center gap-2 text-sm font-bold tracking-wider text-green-600 mb-4">
            <svg class="text-green-500" width="24" height="24" viewBox="0 0 24 24" fill="none">
              <path d="M20 6L9 17L4 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>FINISHED UPLOADS</span>
          </div>
          <div v-for="file in finishedFiles" :key="file.id" class="bg-white border-2 border-green-200 rounded-xl p-5 mb-4 shadow-lg hover:shadow-xl transition-shadow">
            <div class="flex items-start gap-4">
              <div class="text-3xl flex-shrink-0">📄</div>
              <div class="flex-1 min-w-0">
                <div class="flex justify-between items-center mb-3">
                  <span class="text-gray-900 text-base font-semibold truncate">{{ file.name }}</span>
                  <span class="text-green-600 text-sm font-bold ml-4 flex-shrink-0 bg-green-100 px-3 py-1 rounded-full">{{ file.progress }}%</span>
                </div>
                <div class="h-2 bg-gray-200 rounded-full overflow-hidden mb-4">
                  <div class="h-full bg-gradient-to-r from-green-400 to-green-600 transition-all duration-300" :style="{ width: file.progress + '%' }"></div>
                </div>

                <!-- Detected Species -->
                <div v-if="file.detectedSpecies && file.detectedSpecies.length > 0" class="flex flex-wrap gap-3 mt-4">
                  <span
                    v-for="(species, idx) in file.detectedSpecies"
                    :key="idx"
                    class="inline-block bg-gradient-to-r from-green-500 to-green-600 text-white text-base font-bold px-5 py-2.5 rounded-lg shadow-md hover:shadow-lg transition-shadow"
                  >
                    {{ species }}
                  </span>
                </div>

                <div v-if="file.detectionCount === 0 || (file.detectedSpecies && file.detectedSpecies.length === 0)" class="text-base text-gray-600 italic bg-gray-50 p-4 rounded-lg mt-4">
                  No animals detected in this image
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface CameraLocation {
  id: string
  name: string
  longitude: number
  latitude: number
  description: string
}

interface UploadFile {
  id: string
  name: string
  progress: number
  file: File
  detectionCount?: number
  imageId?: string
  locationId?: string
  uploadTimestamp?: string
  detectedSpecies?: string[]
}

const API_BASE_URL = useApiUrl()

const isDragging = ref(false)
const uploadingFiles = ref<UploadFile[]>([])
const finishedFiles = ref<UploadFile[]>([])
const fileInput = ref<HTMLInputElement | null>(null)
const mapRef = ref<any>(null)
const cameraLocations = ref<CameraLocation[]>([])
const selectedLocation = ref<CameraLocation | null>(null)
const selectedLocationId = ref<string>('')

// Fetch available camera locations on mount
onMounted(async () => {
  try {
    // Use locations endpoint with wide range to get all locations
    const params = new URLSearchParams({
      latitude: '51.9607',
      longitude: '9.7085',
      distance_range: '1000'
    })
    const response = await fetch(`${API_BASE_URL}/locations?${params.toString()}`)
    if (response.ok) {
      const data = await response.json()
      cameraLocations.value = data.locations || []
    }
  } catch (error) {
    console.error('Failed to fetch camera locations:', error)
  }
})

const handleLocationSelect = (location: CameraLocation) => {
  selectedLocation.value = location
  selectedLocationId.value = location.id
}

const handleDropdownSelect = () => {
  const location = cameraLocations.value.find(loc => loc.id === selectedLocationId.value)
  if (location) {
    selectedLocation.value = location
    // Center the map on the selected location
    if (mapRef.value?.centerOnLocation) {
      mapRef.value.centerOnLocation(location.id)
    }
  }
}

const triggerFileInput = () => {
  if (selectedLocation.value) {
    fileInput.value?.click()
  }
}

const handleFileInput = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files) {
    handleFiles(Array.from(target.files))
  }
}

const handleDrop = (event: DragEvent) => {
  isDragging.value = false
  if (!selectedLocation.value) {
    alert('Please select a camera location first')
    return
  }
  if (event.dataTransfer?.files) {
    handleFiles(Array.from(event.dataTransfer.files))
  }
}

const handleFiles = (files: File[]) => {
  if (!selectedLocation.value) {
    alert('Please select a camera location first')
    return
  }

  const validFiles = files.filter(file => {
    const validTypes = ['image/jpeg', 'image/png', 'image/gif']
    const maxSize = 10 * 1024 * 1024 // 10 MB
    return validTypes.includes(file.type) && file.size <= maxSize
  })

  validFiles.forEach(file => {
    const uploadFile: UploadFile = {
      id: Math.random().toString(36).substr(2, 9),
      name: file.name,
      progress: 0,
      file: file
    }
    uploadingFiles.value.push(uploadFile)
    uploadFileToAPI(uploadFile)
  })
}

const uploadFileToAPI = async (uploadFile: UploadFile) => {
  if (!selectedLocation.value) {
    return
  }

  const formData = new FormData()
  formData.append('file', uploadFile.file)

  try {
    const xhr = new XMLHttpRequest()

    // Track upload progress
    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable) {
        uploadFile.progress = Math.round((e.loaded / e.total) * 100)
      }
    })

    // Handle completion
    xhr.addEventListener('load', () => {
      if (xhr.status <= 300) {
        try {
          const response = JSON.parse(xhr.responseText)
          uploadFile.progress = 100
          uploadFile.detectionCount = response.detections_count
          uploadFile.imageId = response.image_id
          uploadFile.locationId = response.location_id
          uploadFile.uploadTimestamp = response.upload_timestamp
          uploadFile.detectedSpecies = response.detected_species || []

          // Move to finished after a short delay
          setTimeout(() => {
            const index = uploadingFiles.value.findIndex(f => f.id === uploadFile.id)
            if (index > -1) {
              uploadingFiles.value.splice(index, 1)
              finishedFiles.value.push(uploadFile)
            }
          }, 300)
        } catch (e) {
          console.error('Failed to parse response:', e)
          handleUploadError(uploadFile, 'Failed to parse response')
        }
      } else {
        handleUploadError(uploadFile, `Upload failed with status ${xhr.status}`)
      }
    })

    // Handle errors
    xhr.addEventListener('error', () => {
      handleUploadError(uploadFile, 'Network error during upload')
    })

    xhr.addEventListener('abort', () => {
      handleUploadError(uploadFile, 'Upload cancelled')
    })

    // Send the request
    xhr.open('POST', `${API_BASE_URL}/locations/${selectedLocation.value.id}/image`)
    xhr.send(formData)

  } catch (error) {
    console.error('Upload error:', error)
    handleUploadError(uploadFile, 'Failed to upload file')
  }
}

const handleUploadError = (uploadFile: UploadFile, message: string) => {
  console.error(message, uploadFile.name)
  // Remove from uploading list
  const index = uploadingFiles.value.findIndex(f => f.id === uploadFile.id)
  if (index > -1) {
    uploadingFiles.value.splice(index, 1)
  }
  alert(`Failed to upload ${uploadFile.name}: ${message}`)
}

const formatTimestamp = (timestamp: string): string => {
  try {
    const date = new Date(timestamp)
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (e) {
    return timestamp
  }
}
</script>
