<template>
  <div class="upload-page">
    <div class="upload-container">
      <!-- Camera Selection Section -->
      <div class="camera-section">
        <h2 class="text-2xl font-bold mb-4">Select Camera Location</h2>
        
        <!-- Map for camera selection -->
        <div class="map-container">
          <WildlifeMap 
            ref="mapRef"
            height="100%"
            :auto-center="!selectedLocation"
            :default-zoom="20"
            @marker-click="handleLocationSelect"
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
              {{ location.name }}{{ location.description && location.description !== 'string' ? ' - ' + location.description : '' }}
            </option>
          </select>
        </div>
      </div>

      <!-- Drop Zone -->
      <div
        class="drop-zone"
        :class="{ 
          'drop-zone-active': isDragging,
          'drop-zone-disabled': !selectedLocation
        }"
        @click="selectedLocation ? triggerFileInput() : null"
        @drop.prevent="handleDrop"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
      >
        <svg class="text-gray-400 mb-4 mx-auto" width="24" height="24" viewBox="0 0 24 24" fill="none">
          <path d="M12 15V3M12 3L8 7M12 3L16 7M2 17L2 19C2 20.1046 2.89543 21 4 21L20 21C21.1046 21 22 20.1046 22 19V17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <p class="text-gray-700 text-base mb-2">
          <span v-if="!selectedLocation" class="text-red-500">⚠ Please select a camera location first</span>
          <span v-else>Drop files here or <span class="text-gray-900 underline">browse files</span> to add</span>
        </p>
        <p class="text-gray-500 text-sm">Supported: JPG, PNG, GIF (max 10 MB)</p>
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
      <div class="upload-lists">
        <!-- Uploading Files -->
        <div v-if="uploadingFiles.length > 0" class="upload-section">
          <div class="flex items-center gap-2 text-xs font-semibold tracking-wider text-gray-500 mb-4">
            <svg class="animate-spin" width="20" height="20" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
            </svg>
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
        <div v-if="finishedFiles.length > 0" class="upload-section">
          <div class="flex items-center gap-2 text-xs font-semibold tracking-wider text-gray-500 mb-4">
            <svg class="text-green-500" width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M20 6L9 17L4 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>FINISHED</span>
          </div>
          <div v-for="file in finishedFiles" :key="file.id" class="bg-white border border-gray-200 rounded-lg p-4 mb-3 shadow-sm">
            <div class="flex items-center gap-4">
              <div class="text-2xl flex-shrink-0">📄</div>
              <div class="flex-1 min-w-0">
                <div class="flex justify-between items-center mb-2">
                  <span class="text-gray-900 text-sm truncate">{{ file.name }}</span>
                  <span class="text-gray-500 text-sm ml-4 flex-shrink-0">{{ file.progress }}%</span>
                </div>
                <div class="h-1 bg-gray-200 rounded-full overflow-hidden mb-2">
                  <div class="h-full bg-green-500 transition-all duration-300" :style="{ width: file.progress + '%' }"></div>
                </div>
                <div v-if="file.detectionCount !== undefined" class="text-xs text-green-600 font-semibold">
                  ✓ {{ file.detectionCount }} animal(s) detected
                </div>
                <div v-if="file.imageId" class="text-xs text-gray-500 mt-1">
                  Image ID: {{ file.imageId }}
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
    const response = await fetch(`${API_BASE_URL}/locations`)
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
  
  // Zoom to the selected location
  if (mapRef.value?.zoomToLocation) {
    mapRef.value.zoomToLocation(location.latitude, location.longitude, 15)
  }
}

const handleDropdownSelect = () => {
  const location = cameraLocations.value.find(loc => loc.id === selectedLocationId.value)
  if (location) {
    handleLocationSelect(location)
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
          uploadFile.detectionCount = response.detection_count
          uploadFile.imageId = response.image_id

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
</script>

<style scoped>
.upload-page {
  height: calc(100vh - 4rem); /* Subtract bottom nav bar height */
  background-color: white;
  color: rgb(17 24 39);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.upload-container {
  height: 100%;
  max-width: 80rem;
  margin: 0 auto;
  padding: 2rem;
  width: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.camera-section {
  flex-shrink: 0;
  margin-bottom: 1.5rem;
}

.map-container {
  height: 30vh;
  margin-bottom: 1rem;
  border-radius: 0.75rem;
  overflow: hidden;
  border: 2px solid rgb(209 213 219);
}

.drop-zone {
  flex-shrink: 0;
  background-color: rgb(249 250 251);
  border: 2px dashed rgb(209 213 219);
  border-radius: 0.75rem;
  padding: 3rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 1.5rem;
}

.drop-zone:hover:not(.drop-zone-disabled) {
  border-color: rgb(156 163 175);
  background-color: rgb(243 244 246);
}

.drop-zone-active {
  border-color: rgb(156 163 175);
  background-color: rgb(243 244 246);
}

.drop-zone-disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.upload-lists {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.upload-section {
  margin-bottom: 2rem;
}
</style>
