<template>
  <div class="min-h-screen bg-white text-gray-900 p-8 flex justify-center pt-16">
    <div class="w-full max-w-lg">
      <!-- Drop Zone -->
      <div
        class="bg-gray-50 border-2 border-dashed border-gray-300 rounded-xl p-12 text-center cursor-pointer transition-all duration-300 hover:border-gray-400 hover:bg-gray-100"
        :class="{ 'border-gray-400 bg-gray-100': isDragging }"
        @click="triggerFileInput"
        @drop.prevent="handleDrop"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
      >
        <svg class="text-gray-400 mb-4 mx-auto" width="24" height="24" viewBox="0 0 24 24" fill="none">
          <path d="M12 15V3M12 3L8 7M12 3L16 7M2 17L2 19C2 20.1046 2.89543 21 4 21L20 21C21.1046 21 22 20.1046 22 19V17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <p class="text-gray-700 text-base mb-2">
          Drop files here or <span class="text-gray-900 underline">browse files</span> to add
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

      <!-- Uploading Files -->
      <div v-if="uploadingFiles.length > 0" class="mt-8">
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
      <div v-if="finishedFiles.length > 0" class="mt-8">
        <div class="flex items-center gap-2 text-xs font-semibold tracking-wider text-gray-500 mb-4">
          <svg class="text-green-500" width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M20 6L9 17L4 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span>FINISHED</span>
        </div>
        <div v-for="file in finishedFiles" :key="file.id" class="bg-white border border-gray-200 rounded-lg p-4 flex items-center gap-4 mb-3 shadow-sm">
          <div class="text-2xl flex-shrink-0">📄</div>
          <div class="flex-1 min-w-0">
            <div class="flex justify-between items-center mb-2">
              <span class="text-gray-900 text-sm truncate">{{ file.name }}</span>
              <span class="text-gray-500 text-sm ml-4 flex-shrink-0">{{ file.progress }}%</span>
            </div>
            <div class="h-1 bg-gray-200 rounded-full overflow-hidden">
              <div class="h-full bg-green-500 transition-all duration-300" :style="{ width: file.progress + '%' }"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface UploadFile {
  id: string
  name: string
  progress: number
  file: File
}

const isDragging = ref(false)
const uploadingFiles = ref<UploadFile[]>([])
const finishedFiles = ref<UploadFile[]>([])
const fileInput = ref<HTMLInputElement | null>(null)

const triggerFileInput = () => {
  fileInput.value?.click()
}

const handleFileInput = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files) {
    handleFiles(Array.from(target.files))
  }
}

const handleDrop = (event: DragEvent) => {
  isDragging.value = false
  if (event.dataTransfer?.files) {
    handleFiles(Array.from(event.dataTransfer.files))
  }
}

const handleFiles = (files: File[]) => {
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
    simulateUpload(uploadFile)
  })
}

const simulateUpload = (uploadFile: UploadFile) => {
  const interval = setInterval(() => {
    uploadFile.progress += Math.random() * 15
    if (uploadFile.progress >= 100) {
      uploadFile.progress = 100
      clearInterval(interval)
      // Move to finished after a short delay
      setTimeout(() => {
        const index = uploadingFiles.value.findIndex(f => f.id === uploadFile.id)
        if (index > -1) {
          uploadingFiles.value.splice(index, 1)
          finishedFiles.value.push(uploadFile)
        }
      }, 300)
    }
  }, 200)
}
</script>
