<template>
  <div class="flex flex-grow px-4 py-6 overflow-x-hidden overflow-y-auto">
    <!-- Loading State -->
    <div v-if="loading" class="flex flex-col items-center justify-center flex-1 gap-4">
      <LoadingSpinner size="lg" />
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="flex flex-col items-center justify-center flex-1 gap-4 text-red-600">
      <p>{{ error }}</p>
      <button @click="fetchCameraData"
        class="px-6 py-2.5 bg-secondary text-white rounded-lg font-medium transition-colors hover:bg-secondary-dark">
        Retry
      </button>
    </div>

    <!-- Content -->
    <div v-else-if="location" class="max-w-6xl mx-auto w-full">
      <!-- Map Section -->
      <div class="bg-white p-8 md:p-5 rounded-xl shadow-sm border border-gray-200 mb-6">
        <div class="relative h-[30vh] min-h-[250px] mb-4 rounded-xl overflow-hidden border-2 border-gray-300">
          <WildlifeMap v-if="location" ref="mapRef" height="100%" :auto-center="false" :default-zoom="20"
            :default-latitude="location.latitude" :default-longitude="location.longitude" :no-marker-popup="true" />
        </div>
        <h1 class="text-3xl md:text-2xl font-bold text-gray-800 mb-3">{{ location.name }}</h1>
        <p v-if="location.description" class="text-base text-gray-600 mb-4 leading-relaxed">{{
          location.description }}
        </p>
        <div class="flex flex-wrap items-center gap-3">
          <button @click="goToCameraList"
            class="inline-flex items-center gap-2 px-4 py-2 bg-white border-2 border-gray-200 rounded-lg text-sm font-medium text-gray-600 transition-all hover:border-secondary hover:text-secondary hover:bg-secondary/5">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" stroke-width="2">
              <path d="M19 12H5M12 19l-7-7 7-7" />
            </svg>
            Go to Camera List
          </button>
          <button @click="revealOnMap"
            class="inline-flex items-center gap-2 px-6 py-2.5 bg-white border-2 border-gray-300 rounded-lg text-sm font-medium text-gray-700 transition-all hover:border-gray-400 hover:bg-gray-50">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" stroke-width="2">
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
              <circle cx="12" cy="10" r="3"></circle>
            </svg>
            Reveal on Map
          </button>
          <button @click="openEditModal"
            class="inline-flex items-center gap-2 px-6 py-2.5 bg-white border-2 border-amber-300 rounded-lg text-sm font-medium text-amber-700 transition-all hover:border-amber-400 hover:bg-amber-50">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" stroke-width="2">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
            </svg>
            Edit Location
          </button>
          <button @click="openDeleteModal"
            class="inline-flex items-center gap-2 px-6 py-2.5 bg-white border-2 border-red-300 rounded-lg text-sm font-medium text-red-700 transition-all hover:border-red-400 hover:bg-red-50">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" stroke-width="2">
              <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
              <line x1="10" y1="11" x2="10" y2="17"></line>
              <line x1="14" y1="11" x2="14" y2="17"></line>
            </svg>
            Delete Camera
          </button>
        </div>
      </div>

      <!-- Tabs Navigation -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 mb-6">
        <div class="flex border-b border-gray-200">
          <button @click="activeTab = 'overview'" :class="[
            'px-6 py-4 text-sm font-medium transition-colors border-b-2',
            activeTab === 'overview'
              ? 'border-secondary text-secondary'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
          ]">
            Overview
          </button>
          <button @click="activeTab = 'upload'" :class="[
            'px-6 py-4 text-sm font-medium transition-colors border-b-2',
            activeTab === 'upload'
              ? 'border-secondary text-secondary'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
          ]">
            Upload
          </button>
          <button @click="activeTab = 'integration'" :class="[
            'px-6 py-4 text-sm font-medium transition-colors border-b-2',
            activeTab === 'integration'
              ? 'border-secondary text-secondary'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
          ]">
            Integration
          </button>
        </div>

        <!-- Tab Content -->
        <div>
          <!-- Overview Tab -->
          <div v-if="activeTab === 'overview'" class="p-8 md:p-5">
            <!-- Statistics Section -->
            <div class="mb-8">
              <h2 class="text-2xl font-bold text-gray-900 mb-6">Statistics</h2>
              <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                <div class="p-6 rounded-xl text-center text-white shadow-lg" style="background: linear-gradient(135deg, var(--color-primary), var(--color-primary-dark))">
                  <div class="text-4xl font-bold mb-2">{{ totalImages }}</div>
                  <div class="text-sm opacity-90 uppercase tracking-wide">Total Images</div>
                </div>
                <div class="p-6 rounded-xl text-center text-white shadow-lg" style="background: linear-gradient(135deg, var(--color-primary), var(--color-primary-dark))">
                  <div class="text-4xl font-bold mb-2">{{ location?.total_unique_species ?? uniqueSpecies.size }}</div>
                  <div class="text-sm opacity-90 uppercase tracking-wide">Unique Species</div>
                </div>
                <div class="p-6 rounded-xl text-center text-white shadow-lg" style="background: linear-gradient(135deg, var(--color-primary), var(--color-primary-dark))">
                  <div class="text-4xl font-bold mb-2">{{ totalDetections }}</div>
                  <div class="text-sm opacity-90 uppercase tracking-wide">Total Detections</div>
                  <div class="text-xs opacity-75 mt-1">({{ imagesWithDetections }} images)</div>
                </div>
              </div>

              <!-- Species Breakdown -->
              <div v-if="speciesBreakdown.length > 0" class="mt-8 pt-8 border-t border-gray-200">
                <h3 class="text-xl font-bold text-gray-900 mb-4">Species Breakdown</h3>
                <div class="flex flex-col gap-4">
                  <div v-for="species in speciesBreakdown" :key="species.name" class="flex flex-col gap-2">
                    <div class="flex justify-between items-center">
                      <span class="font-semibold text-gray-900">{{ species.name }}</span>
                      <span class="text-sm text-gray-500">{{ species.count }} detection{{ species.count !== 1 ? 's' : ''
                        }}</span>
                    </div>
                    <div class="h-2 bg-gray-200 rounded overflow-hidden">
                      <div
                        class="h-full rounded transition-all duration-300 ease-out"
                        :style="{
                          width: `${(species.count / totalDetections) * 100}%`,
                          background: 'linear-gradient(90deg, var(--color-primary), var(--color-primary-dark))'
                        }"></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Images Section -->
            <div>
              <h2 class="text-2xl font-bold text-gray-900 mb-6">Images ({{ location.images?.length || 0 }})</h2>
              <div v-if="location.images && location.images.length > 0"
                class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 md:gap-4">
                <div v-for="image in location.images" :key="image.image_id" class="flex flex-col gap-3">
                  <div @click="() => router.push(`/match/${image.image_id}`)"
                    class="group block relative rounded-lg overflow-hidden border-2 border-transparent transition-all hover:border-secondary hover:-translate-y-0.5 hover:shadow-lg cursor-pointer">
                    <div class="relative w-full aspect-[4/3] overflow-hidden bg-gray-100">
                      <img :src="imageUrls.get(image.image_id) || `${apiUrl}/images/${image.image_id}/base64`"
                        :alt="`Image from ${new Date(image.upload_timestamp).toLocaleString()}`"
                        class="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                        @error="handleImageError" />
                      <div
                        class="absolute inset-0 bg-black/60 flex flex-col items-center justify-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none">
                        <svg class="w-10 h-10 text-white stroke-[2.5]" xmlns="http://www.w3.org/2000/svg"
                          viewBox="0 0 24 24" fill="none" stroke="currentColor">
                          <path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7" />
                        </svg>
                        <span class="text-white text-sm font-semibold drop-shadow-lg">Click to match</span>
                      </div>
                    </div>
                  </div>
                  <div class="flex justify-between items-center gap-2">
                    <small class="text-xs text-gray-500">{{ new Date(image.upload_timestamp).toLocaleString() }}</small>
                    <div class="flex gap-2">
                      <!-- Has detections -->
                      <div v-if="image.detections && image.detections.length > 0"
                        @click="() => router.push(`/match/${image.image_id}`)"
                        class="bg-red-500 text-white px-3 py-1 rounded-full text-xs font-semibold transition-opacity hover:opacity-85 cursor-pointer">
                        {{ image.detections.length }} detection{{ image.detections.length !== 1 ? 's' : '' }}
                      </div>
                      <!-- Processing/Pending -->
                      <span v-else-if="!image.processed || image.processing_status === 'detecting' || image.processing_status === 'uploading'"
                        class="bg-secondary text-white px-3 py-1 rounded-full text-xs font-semibold animate-pulse">
                        Pending
                      </span>
                      <!-- Failed -->
                      <span v-else-if="image.processing_status === 'failed'"
                        class="bg-red-600 text-white px-3 py-1 rounded-full text-xs font-semibold">
                        Processing failed
                      </span>
                      <!-- No detections (completed but empty) -->
                      <span v-else class="bg-gray-500 text-white px-3 py-1 rounded-full text-xs font-semibold">
                        No detection
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              <div v-else class="text-center py-12 text-gray-500">
                <p>No images available for this camera.</p>
              </div>
            </div>
          </div>

          <!-- Upload Tab -->
          <div v-if="activeTab === 'upload'" class="p-8 md:p-5">
            <!-- Drop Zone -->
            <div
              class="flex-shrink-0 bg-gray-50 border-2 border-dashed rounded-xl py-6 px-8 text-center cursor-pointer transition-all duration-300 mb-6"
              :class="{
                'border-gray-400 bg-gray-100': isDragging,
                'hover:border-gray-400 hover:bg-gray-100': !isDragging
              }" @click="triggerFileInput" @drop.prevent="handleDrop" @dragover.prevent="isDragging = true"
              @dragleave.prevent="isDragging = false">
              <svg class="text-gray-400 mb-2 mx-auto" width="24" height="24" viewBox="0 0 24 24" fill="none">
                <path
                  d="M12 15V3M12 3L8 7M12 3L16 7M2 17L2 19C2 20.1046 2.89543 21 4 21L20 21C21.1046 21 22 20.1046 22 19V17"
                  stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
              <p class="text-gray-700 text-sm mb-1">
                Drop files here or <span class="text-gray-900 underline">browse files</span> to add
              </p>
              <p class="text-gray-500 text-xs">Supported: JPG, PNG, GIF (max 10 MB)</p>
              <input ref="fileInput" type="file" multiple accept=".jpg,.jpeg,.png,.gif" @change="handleFileInput"
                class="hidden" />
            </div>

            <!-- Upload Lists Container -->
            <div class="space-y-6">
              <!-- Uploading Files -->
              <div v-if="uploadingFiles.length > 0">
                <div class="flex items-center gap-2 text-xs font-semibold tracking-wider text-gray-500 mb-4">
                  <span>UPLOADING</span>
                </div>
                <div v-for="file in uploadingFiles" :key="file.id"
                  class="bg-white border border-gray-200 rounded-lg p-4 flex items-center gap-4 mb-3 shadow-sm">
                  <div class="text-2xl flex-shrink-0">📄</div>
                  <div class="flex-1 min-w-0">
                    <div class="flex justify-between items-center mb-2">
                      <span class="text-gray-900 text-sm truncate">{{ file.name }}</span>
                      <span class="text-gray-500 text-sm ml-4 flex-shrink-0">{{ file.progress }}%</span>
                    </div>
                    <div class="h-1 bg-gray-200 rounded-full overflow-hidden">
                      <div class="h-full bg-gray-400 transition-all duration-300"
                        :style="{ width: file.progress + '%' }"></div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Finished Files -->
              <div v-if="finishedFiles.length > 0">
                <div class="flex items-center gap-2 text-sm font-bold tracking-wider text-green-600 mb-4">
                  <svg class="text-green-500" width="24" height="24" viewBox="0 0 24 24" fill="none">
                    <path d="M20 6L9 17L4 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                      stroke-linejoin="round" />
                  </svg>
                  <span>FINISHED UPLOADS</span>
                </div>
                <div v-for="file in finishedFiles" :key="file.id"
                  class="bg-white border-2 border-green-200 rounded-xl p-5 mb-4 shadow-lg hover:shadow-xl transition-shadow">
                  <div class="flex items-start gap-4">
                    <div class="text-3xl flex-shrink-0">📄</div>
                    <div class="flex-1 min-w-0">
                      <div class="flex justify-between items-center mb-3">
                        <span class="text-gray-900 text-base font-semibold truncate">{{ file.name }}</span>
                        <span
                          class="text-green-600 text-sm font-bold ml-4 flex-shrink-0 bg-green-100 px-3 py-1 rounded-full">{{
                            file.progress }}%</span>
                      </div>
                      <div class="h-2 bg-gray-200 rounded-full overflow-hidden mb-4">
                        <div class="h-full bg-gradient-to-r from-green-400 to-green-600 transition-all duration-300"
                          :style="{ width: file.progress + '%' }"></div>
                      </div>

                      <!-- Detected Species -->
                      <div v-if="file.detectedSpecies && file.detectedSpecies.length > 0"
                        class="flex flex-wrap gap-3 mt-4">
                        <span v-for="(species, idx) in file.detectedSpecies" :key="idx"
                          class="inline-block bg-gradient-to-r from-green-500 to-green-600 text-white text-base font-bold px-5 py-2.5 rounded-lg shadow-md hover:shadow-lg transition-shadow">
                          {{ species }}
                        </span>
                      </div>

                      <div
                        v-if="file.detectionCount === 0 || (file.detectedSpecies && file.detectedSpecies.length === 0)"
                        class="text-base text-gray-600 italic bg-gray-50 p-4 rounded-lg mt-4">
                        No animals detected in this image
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Failed Files -->
            <div v-if="failedFiles.length > 0">
              <div class="flex items-center gap-2 text-sm font-bold tracking-wider text-red-600 mb-4">
                <svg class="text-red-500" width="24" height="24" viewBox="0 0 24 24" fill="none">
                  <path d="M12 8V12M12 16H12.01M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <span>FAILED</span>
              </div>
              <div v-for="file in failedFiles" :key="file.id" class="bg-white border-2 border-red-200 rounded-xl p-5 mb-4 shadow-lg">
                <div class="flex items-start gap-4">
                  <div class="text-3xl flex-shrink-0">❌</div>
                  <div class="flex-1 min-w-0">
                    <div class="flex justify-between items-center mb-3">
                      <span class="text-gray-900 text-base font-semibold truncate">{{ file.name }}</span>
                      <span class="text-red-600 text-sm font-bold ml-4 flex-shrink-0 bg-red-100 px-3 py-1 rounded-full">Failed</span>
                    </div>
                    <p class="text-sm text-red-600 bg-red-50 p-3 rounded-lg">{{ file.errorMessage || 'Processing failed' }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Integration Tab -->
          <div v-if="activeTab === 'integration'" class="p-8 md:p-5">
            <div class="max-w-2xl">
              <h2 class="text-2xl font-bold text-gray-900 mb-4">External Image Source Integration</h2>
              <p class="text-gray-600 mb-8">
                Configure an external image source that will be automatically polled every hour.
                Images will be downloaded and processed through the same wildlife detection pipeline as manual uploads.
              </p>

              <!-- Existing Integration Display -->
              <div v-if="existingIntegration" class="mb-8 rounded-xl p-6 border-2 shadow-lg" style="background: linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(22, 163, 74, 0.1)); border-color: var(--color-primary);">
                <div class="flex items-start justify-between mb-4">
                  <div>
                    <h3 class="text-lg font-bold text-gray-900 mb-2">Active Integration</h3>
                    <p class="text-sm font-medium text-primary">{{ existingIntegration.name }}</p>
                  </div>
                  <span class="inline-flex items-center gap-2 px-3 py-1 text-white text-xs font-bold rounded-full" :style="{ background: existingIntegration.is_active ? 'var(--color-primary)' : 'var(--color-gray-500)' }">
                    <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                    </svg>
                    {{ existingIntegration.is_active ? 'Active' : 'Inactive' }}
                  </span>
                </div>

                <div class="space-y-3 mb-4">
                  <div class="flex items-start gap-3">
                    <span class="text-sm font-semibold text-gray-900 min-w-[120px]">Base URL:</span>
                    <span class="text-sm text-gray-700 break-all">{{ existingIntegration.base_url }}</span>
                  </div>
                  <div class="flex items-start gap-3">
                    <span class="text-sm font-semibold text-gray-900 min-w-[120px]">Auth Type:</span>
                    <span class="text-sm text-gray-700">{{ existingIntegration.auth_type }}</span>
                  </div>
                  <div v-if="existingIntegration.last_pulled_filename" class="flex items-start gap-3">
                    <span class="text-sm font-semibold text-gray-900 min-w-[120px]">Last Pulled:</span>
                    <span class="text-sm text-gray-700">{{ existingIntegration.last_pulled_filename }}</span>
                  </div>
                  <div v-if="existingIntegration.last_pull_timestamp" class="flex items-start gap-3">
                    <span class="text-sm font-semibold text-gray-900 min-w-[120px]">Last Pull Time:</span>
                    <span class="text-sm text-gray-700">{{ new Date(existingIntegration.last_pull_timestamp).toLocaleString() }}</span>
                  </div>
                </div>

                <div class="flex gap-3">
                  <button @click="toggleIntegration" :disabled="integrationLoading"
                    class="px-4 py-2 bg-yellow-500 text-white rounded-lg font-medium transition-colors hover:bg-yellow-600 disabled:opacity-50 disabled:cursor-not-allowed">
                    {{ existingIntegration.is_active ? 'Deactivate' : 'Activate' }}
                  </button>
                  <button @click="testIntegration" :disabled="integrationLoading"
                    class="px-4 py-2 bg-secondary text-white rounded-lg font-medium transition-colors hover:bg-secondary-dark disabled:opacity-50 disabled:cursor-not-allowed">
                    Test Pull (2 files)
                  </button>
                  <button @click="deleteIntegration"
                    class="px-4 py-2 bg-error text-white rounded-lg font-medium transition-colors hover:bg-error-dark">
                    Delete
                  </button>
                </div>
              </div>

              <!-- Integration Form -->
              <div v-if="!existingIntegration" class="bg-gray-50 rounded-xl p-6 border border-gray-200">
                <form @submit.prevent="createIntegration" class="space-y-6">
                  <div>
                    <label for="integration-name" class="block text-sm font-semibold text-gray-700 mb-2">
                      Integration Name
                    </label>
                    <input
                      id="integration-name"
                      v-model="integrationForm.name"
                      type="text"
                      required
                      placeholder="e.g., Hameln-Pyrmont Camera Feed"
                      class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-secondary focus:border-secondary transition-colors"
                    />
                  </div>

                  <div>
                    <label for="integration-url" class="block text-sm font-semibold text-gray-700 mb-2">
                      Base URL
                    </label>
                    <input
                      id="integration-url"
                      v-model="integrationForm.baseUrl"
                      type="url"
                      required
                      placeholder="https://assets.hameln-pyrmont.digital/image-api/"
                      class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-secondary focus:border-secondary transition-colors"
                    />
                    <p class="text-xs text-gray-500 mt-1">
                      URL to the directory listing containing images
                    </p>
                  </div>

                  <div>
                    <label for="integration-username" class="block text-sm font-semibold text-gray-700 mb-2">
                      Username
                    </label>
                    <input
                      id="integration-username"
                      v-model="integrationForm.username"
                      type="text"
                      placeholder="mitwirker"
                      class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-secondary focus:border-secondary transition-colors"
                    />
                  </div>

                  <div>
                    <label for="integration-password" class="block text-sm font-semibold text-gray-700 mb-2">
                      Password
                    </label>
                    <input
                      id="integration-password"
                      v-model="integrationForm.password"
                      type="password"
                      placeholder="••••••••"
                      class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-secondary focus:border-secondary transition-colors"
                    />
                    <p class="text-xs text-gray-500 mt-1">
                      Leave empty if no authentication is required
                    </p>
                  </div>

                  <div v-if="integrationError" class="bg-red-50 border border-red-200 rounded-lg p-4">
                    <p class="text-sm text-red-700">{{ integrationError }}</p>
                  </div>

                  <div v-if="integrationSuccess" class="bg-green-50 border border-green-200 rounded-lg p-4">
                    <p class="text-sm text-green-700">{{ integrationSuccess }}</p>
                  </div>

                  <div class="flex gap-3 pt-4">
                    <button
                      type="submit"
                      :disabled="integrationLoading"
                      class="px-6 py-2.5 bg-green-500 text-white rounded-lg font-medium transition-all hover:bg-green-600 hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:scale-105"
                    >
                      {{ integrationLoading ? 'Creating...' : 'Create Integration' }}
                    </button>
                  </div>
                </form>
              </div>

              <!-- Information Section -->
              <div class="mt-8 bg-secondary/10 border border-secondary/20 rounded-xl p-6">
                <h4 class="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
                  </svg>
                  How it works
                </h4>
                <ul class="text-sm text-gray-700 space-y-2">
                  <li>• Images are automatically pulled from the configured URL every hour</li>
                  <li>• Each image is processed through the wildlife detection system</li>
                  <li>• Detected animals appear in the Overview tab like manual uploads</li>
                  <li>• The system tracks which files have been processed to avoid duplicates</li>
                  <li>• Up to 10 new images are processed per hour by default</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Edit Location Modal -->
    <div v-if="showEditModal" class="fixed inset-0 flex items-center justify-center p-4" style="z-index: 10000;">
      <!-- Backdrop -->
      <div class="absolute inset-0 bg-black/50" @click="closeEditModal"></div>

      <!-- Modal Content -->
      <div class="relative bg-white rounded-2xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div class="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <h2 class="text-xl font-bold text-gray-900">Edit Camera Location</h2>
          <button @click="closeEditModal" class="p-2 text-gray-400 hover:text-gray-600 transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" stroke-width="2">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="p-6 space-y-6">
          <!-- Map for Location Selection -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Update Location on Map
              <span class="text-gray-400 font-normal">(click to change location)</span>
            </label>
            <div class="relative h-[300px] rounded-xl overflow-hidden border-2 border-gray-200">
              <div ref="editMapContainer" class="w-full h-full"></div>
            </div>
            <p v-if="editLocation.latitude && editLocation.longitude" class="mt-2 text-sm text-green-600">
              📍 Location: {{ editLocation.latitude.toFixed(6) }}, {{ editLocation.longitude.toFixed(6) }}
            </p>
          </div>

          <!-- Name Input -->
          <div>
            <label for="edit-camera-name" class="block text-sm font-medium text-gray-700 mb-2">
              Camera Name <span class="text-red-500">*</span>
            </label>
            <input id="edit-camera-name" v-model="editLocation.name" type="text" placeholder="e.g., Forest Camera North"
              class="w-full px-4 py-2.5 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-blue-500 transition-colors" />
          </div>

          <!-- Description Input -->
          <div>
            <label for="edit-camera-description" class="block text-sm font-medium text-gray-700 mb-2">
              Description <span class="text-gray-400 font-normal">(optional)</span>
            </label>
            <textarea id="edit-camera-description" v-model="editLocation.description" rows="3"
              placeholder="Describe the camera location..."
              class="w-full px-4 py-2.5 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-blue-500 transition-colors resize-none"></textarea>
          </div>

          <!-- Coordinates (Manual Entry) -->
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label for="edit-camera-lat" class="block text-sm font-medium text-gray-700 mb-2">Latitude</label>
              <input id="edit-camera-lat" v-model.number="editLocation.latitude" type="number" step="0.000001"
                placeholder="52.101813"
                class="w-full px-4 py-2.5 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-blue-500 transition-colors" />
            </div>
            <div>
              <label for="edit-camera-lng" class="block text-sm font-medium text-gray-700 mb-2">Longitude</label>
              <input id="edit-camera-lng" v-model.number="editLocation.longitude" type="number" step="0.000001"
                placeholder="9.375444"
                class="w-full px-4 py-2.5 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-blue-500 transition-colors" />
            </div>
          </div>

          <!-- Error Message -->
          <p v-if="editError" class="text-red-500 text-sm">{{ editError }}</p>
        </div>

        <div class="sticky bottom-0 bg-gray-50 border-t border-gray-200 px-6 py-4 flex justify-end gap-3">
          <button @click="closeEditModal"
            class="px-5 py-2.5 border-2 border-gray-200 rounded-lg font-medium text-gray-600 hover:bg-gray-100 transition-colors">
            Cancel
          </button>
          <button @click="saveLocationEdit" :disabled="!canSaveEdit || saving"
            class="px-5 py-2.5 bg-amber-500 text-white rounded-lg font-medium hover:bg-amber-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2">
            <LoadingSpinner v-if="saving" size="sm" />
            {{ saving ? 'Saving...' : 'Save Changes' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Delete Camera Modal -->
    <div v-if="showDeleteModal" class="fixed inset-0 flex items-center justify-center p-4" style="z-index: 10000;">
      <!-- Backdrop -->
      <div class="absolute inset-0 bg-black/50" @click="closeDeleteModal"></div>

      <!-- Modal Content -->
      <div class="relative bg-white rounded-2xl shadow-xl w-full max-w-md">
        <div class="p-6">
          <div class="flex items-center justify-center w-12 h-12 mx-auto mb-4 bg-red-100 rounded-full">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" stroke-width="2" class="text-red-600">
              <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
              <line x1="10" y1="11" x2="10" y2="17"></line>
              <line x1="14" y1="11" x2="14" y2="17"></line>
            </svg>
          </div>
          <h2 class="text-xl font-bold text-gray-900 text-center mb-2">Delete Camera</h2>
          <p class="text-gray-600 text-center mb-2">
            Are you sure you want to delete <strong class="text-gray-900">{{ location?.name }}</strong>?
          </p>

          <!-- Image Count Warning -->
          <div v-if="loadingImageCount" class="flex justify-center mb-4">
            <LoadingSpinner size="sm" />
          </div>
          <div v-else-if="deleteImageCount > 0" class="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
            <p class="text-red-700 text-sm text-center font-medium">
              ⚠️ This will also delete <strong>{{ deleteImageCount }}</strong> image{{ deleteImageCount !== 1 ? 's' : '' }} and all associated detections.
            </p>
          </div>
          <p class="text-gray-500 text-sm text-center mb-6">
            This action cannot be undone.
          </p>

          <!-- Confirmation Input -->
          <div class="mb-6">
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Type <strong class="text-red-600">{{ location?.name }}</strong> to confirm:
            </label>
            <input v-model="deleteConfirmation" type="text" :placeholder="location?.name"
              class="w-full px-4 py-2.5 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-red-500 transition-colors"
              @keyup.enter="deleteCamera" />
          </div>

          <!-- Error Message -->
          <p v-if="deleteError" class="text-red-500 text-sm mb-4 text-center">{{ deleteError }}</p>

          <div class="flex gap-3">
            <button @click="closeDeleteModal"
              class="flex-1 px-5 py-2.5 border-2 border-gray-200 rounded-lg font-medium text-gray-600 hover:bg-gray-100 transition-colors">
              Cancel
            </button>
            <button @click="deleteCamera" :disabled="!canDelete || deleting"
              class="flex-1 px-5 py-2.5 bg-red-500 text-white rounded-lg font-medium hover:bg-red-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2">
              <LoadingSpinner v-if="deleting" size="sm" />
              {{ deleting ? 'Deleting...' : 'Delete' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'

const apiUrl = useApiUrl()
const route = useRoute()
const router = useRouter()
const { fetchWithAuth } = useAuthenticatedApi()
const { getToken } = useAuth()

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
  processingStatus?: string
  taskId?: string
  errorMessage?: string
}

interface ImageDetection {
  image_id: string
  location_id: string
  upload_timestamp: string
  processing_status?: string  // uploading, detecting, completed, failed
  processed?: boolean
  detections: Array<{
    species: string
    confidence: number
    bounding_box: any
    classification_model: string
    is_uncertain: boolean
  }>
}

interface Location {
  id: string
  name: string
  longitude: number
  latitude: number
  description: string
  images?: ImageDetection[]
  total_images?: number
  total_unique_species?: number
  total_spottings?: number
  total_images_with_animals?: number
}

const location = ref<Location | null>(null)
const statistics = ref<any[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const activeTab = ref<'overview' | 'upload' | 'integration'>('overview')
const isDragging = ref(false)
const uploadingFiles = ref<UploadFile[]>([])
const processingFiles = ref<UploadFile[]>([])
const finishedFiles = ref<UploadFile[]>([])
const failedFiles = ref<UploadFile[]>([])
const fileInput = ref<HTMLInputElement | null>(null)
const mapRef = ref<any>(null)
const pollingIntervals = ref<Map<string, number>>(new Map())
const imageUrls = ref<Map<string, string>>(new Map())

// Integration state
const existingIntegration = ref<any>(null)
const integrationLoading = ref(false)
const integrationError = ref<string | null>(null)
const integrationSuccess = ref<string | null>(null)
const integrationForm = ref({
  name: '',
  baseUrl: '',
  username: '',
  password: ''
})

// Edit modal state
const showEditModal = ref(false)
const saving = ref(false)
const editError = ref<string | null>(null)
const editMapContainer = ref<HTMLElement | null>(null)
let editMap: any = null
let editMarker: any = null

const editLocation = ref({
  name: '',
  description: '',
  latitude: null as number | null,
  longitude: null as number | null
})

const canSaveEdit = computed(() => {
  return editLocation.value.name.trim() !== '' &&
    editLocation.value.latitude !== null &&
    editLocation.value.longitude !== null
})

// Delete modal state
const showDeleteModal = ref(false)
const deleting = ref(false)
const deleteError = ref<string | null>(null)
const deleteConfirmation = ref('')
const deleteImageCount = ref(0)
const loadingImageCount = ref(false)

const canDelete = computed(() => {
  return location.value && deleteConfirmation.value === location.value.name
})

const cameraId = computed(() => route.params.id as string)

const totalImages = computed(() => location.value?.total_images ?? location.value?.images?.length ?? 0)

const totalDetections = computed(() => {
  // Use API value if available, otherwise compute from images
  if (location.value?.total_spottings !== undefined) {
    return location.value.total_spottings
  }
  if (!location.value?.images) return 0
  return location.value.images.reduce((sum, img) => sum + (img.detections?.length || 0), 0)
})

const imagesWithDetections = computed(() => {
  // Use API value if available, otherwise compute from images
  if (location.value?.total_images_with_animals !== undefined) {
    return location.value.total_images_with_animals
  }
  if (!location.value?.images) return 0
  return location.value.images.filter(img => img.detections && img.detections.length > 0).length
})

const uniqueSpecies = computed(() => {
  // Use API value if available, otherwise compute from images
  if (location.value?.total_unique_species !== undefined) {
    return new Set<string>() // Return empty set, size will be taken from total_unique_species
  }
  const species = new Set<string>()
  if (location.value?.images) {
    location.value.images.forEach(img => {
      img.detections?.forEach(detection => {
        species.add(detection.species)
      })
    })
  }
  return species
})

const speciesBreakdown = computed(() => {
  // Use statistics from API if available (complete data)
  if (statistics.value.length > 0) {
    const speciesMap = new Map<string, number>()

    statistics.value.forEach(stat => {
      stat.species.forEach((s: { name: string; count: number }) => {
        const currentCount = speciesMap.get(s.name) || 0
        speciesMap.set(s.name, currentCount + s.count)
      })
    })

    return Array.from(speciesMap.entries())
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count)
  }

  // Fallback to calculating from images (limited data)
  const speciesMap = new Map<string, number>()

  if (location.value?.images) {
    location.value.images.forEach(img => {
      img.detections?.forEach(detection => {
        const count = speciesMap.get(detection.species) || 0
        speciesMap.set(detection.species, count + 1)
      })
    })
  }

  return Array.from(speciesMap.entries())
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
})

const fetchCameraData = async () => {
  loading.value = true
  error.value = null

  try {
    const params = new URLSearchParams({
      latitude: '52.10181392588904',
      longitude: '9.37544441225413',
      distance_range: '100000000000'
    })

    const response = await fetchWithAuth(`/locations?${params.toString()}`)

    if (!response.ok) {
      if (response.status === 401) {
        return
      }
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()
    const foundLocation = data.locations.find((loc: Location) => loc.id === cameraId.value)

    if (!foundLocation) {
      throw new Error('Camera location not found')
    }

    location.value = foundLocation

    // Pre-fetch image URLs with authentication
    if (foundLocation.images && foundLocation.images.length > 0) {
      const token = await getToken()
      if (token) {
        await Promise.all(
          foundLocation.images.map(async (img: ImageDetection) => {
            try {
              const response = await fetchWithAuth(`/images/${img.image_id}/base64`)
              if (response.ok) {
                const blob = await response.blob()
                const url = URL.createObjectURL(blob)
                imageUrls.value.set(img.image_id, url)
              }
            } catch (err) {
              console.warn(`Failed to fetch image ${img.image_id}:`, err)
            }
          })
        )
      }
    }

    // Fetch statistics for this location to get complete species breakdown
    try {
      const statsParams = new URLSearchParams({
        period: 'year',
        granularity: 'daily',
        location_id: cameraId.value
      })
      const statsResponse = await fetchWithAuth(`/statistics?${statsParams.toString()}`)

      if (statsResponse.ok) {
        const statsData = await statsResponse.json()
        statistics.value = statsData.statistics || []
      }
    } catch (statsErr) {
      console.warn('Failed to fetch statistics:', statsErr)
      // Continue without statistics - will use fallback from images
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to fetch camera data'
    console.error('Error fetching camera data:', err)
  } finally {
    loading.value = false
  }
}

// Note: We don't need to refetch camera data after upload
// The completed files are shown in the upload tab with detection results
// If user wants to see them in the overview, they can switch tabs manually

const goToCameraList = () => {
  router.push('/camera')
}

const revealOnMap = () => {
  if (location.value) {
    router.push({
      path: '/map',
      query: {
        camera: location.value.id,
        lat: location.value.latitude.toString(),
        lng: location.value.longitude.toString()
      }
    })
  }
}

// Edit modal functions
const openEditModal = async () => {
  if (!location.value) return

  showEditModal.value = true
  editError.value = null

  // Populate form with current values
  editLocation.value = {
    name: location.value.name,
    description: location.value.description || '',
    latitude: location.value.latitude,
    longitude: location.value.longitude
  }

  // Wait for modal to render, then initialize map
  await nextTick()
  initEditMap()
}

const closeEditModal = () => {
  showEditModal.value = false
  if (editMap) {
    editMap.remove()
    editMap = null
  }
  editMarker = null
}

const initEditMap = async () => {
  if (!editMapContainer.value) return

  const L = await import('leaflet')
  await import('leaflet/dist/leaflet.css')

  // Fix for default marker icons
  delete (L.Icon.Default.prototype as any)._getIconUrl
  L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
  })

  // Use current location as center
  const center: [number, number] = [
    editLocation.value.latitude || 52.10181392588904,
    editLocation.value.longitude || 9.37544441225413
  ]

  editMap = L.map(editMapContainer.value).setView(center, 15)

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19,
  }).addTo(editMap)

  // Add marker at current location
  if (editLocation.value.latitude && editLocation.value.longitude) {
    editMarker = L.marker([editLocation.value.latitude, editLocation.value.longitude]).addTo(editMap)
  }

  // Add click handler for location selection
  editMap.on('click', (e: any) => {
    const { lat, lng } = e.latlng
    editLocation.value.latitude = lat
    editLocation.value.longitude = lng

    // Update or create marker
    if (editMarker) {
      editMarker.setLatLng([lat, lng])
    } else if (editMap) {
      editMarker = L.marker([lat, lng]).addTo(editMap)
    }
  })
}

// Watch for manual coordinate changes in edit modal and update marker
watch(
  () => [editLocation.value.latitude, editLocation.value.longitude],
  ([lat, lng]) => {
    if (editMap && lat !== null && lng !== null && showEditModal.value) {
      const L = (window as any).L
      if (editMarker) {
        editMarker.setLatLng([lat, lng])
      } else if (L) {
        editMarker = L.marker([lat, lng]).addTo(editMap)
      }
      editMap.setView([lat, lng], editMap.getZoom())
    }
  }
)

const saveLocationEdit = async () => {
  if (!canSaveEdit.value || !location.value) return

  saving.value = true
  editError.value = null

  try {
    const response = await fetchWithAuth(`/locations/${location.value.id}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        name: editLocation.value.name.trim(),
        description: editLocation.value.description.trim() || null,
        latitude: editLocation.value.latitude,
        longitude: editLocation.value.longitude
      })
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
    }

    // Update local location data
    location.value.name = editLocation.value.name.trim()
    location.value.description = editLocation.value.description.trim() || ''
    location.value.latitude = editLocation.value.latitude!
    location.value.longitude = editLocation.value.longitude!

    // Close modal
    closeEditModal()
  } catch (err) {
    editError.value = err instanceof Error ? err.message : 'Failed to update location'
    console.error('Error updating location:', err)
  } finally {
    saving.value = false
  }
}

// Delete modal functions
const openDeleteModal = async () => {
  if (!location.value) return

  deleteConfirmation.value = ''
  deleteError.value = null
  deleteImageCount.value = 0
  loadingImageCount.value = true
  showDeleteModal.value = true

  // Fetch the image count for this camera
  try {
    const response = await fetchWithAuth(`/locations/${location.value.id}/image-count`)
    if (response.ok) {
      const data = await response.json()
      deleteImageCount.value = data.image_count || 0
    }
  } catch (err) {
    console.error('Error fetching image count:', err)
  } finally {
    loadingImageCount.value = false
  }
}

const closeDeleteModal = () => {
  showDeleteModal.value = false
  deleteConfirmation.value = ''
  deleteError.value = null
  deleteImageCount.value = 0
  loadingImageCount.value = false
}

const deleteCamera = async () => {
  if (!canDelete.value || !location.value) return

  deleting.value = true
  deleteError.value = null

  try {
    const response = await fetchWithAuth(`/locations/${location.value.id}`, {
      method: 'DELETE'
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
    }

    // Close modal and navigate back to camera list
    closeDeleteModal()
    router.push('/camera')
  } catch (err) {
    deleteError.value = err instanceof Error ? err.message : 'Failed to delete camera'
    console.error('Error deleting camera:', err)
  } finally {
    deleting.value = false
  }
}

const goBack = () => {
  router.push('/camera')
}

const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.src = '/fallback.JPG'
}

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
  if (!location.value) {
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
  if (!location.value) {
    return
  }

  const formData = new FormData()
  formData.append('file', uploadFile.file)

  try {
    const token = await getToken()
    if (!token) {
      handleUploadError(uploadFile, 'Authentication required')
      return
    }

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
          console.log('Upload response:', response)

          uploadFile.progress = 100
          uploadFile.imageId = response.image_id
          uploadFile.locationId = response.location_id
          uploadFile.uploadTimestamp = response.upload_timestamp
          uploadFile.processingStatus = response.processing_status
          uploadFile.taskId = response.task_id

          // Remove from uploading list
          const index = uploadingFiles.value.findIndex(f => f.id === uploadFile.id)
          if (index > -1) {
            uploadingFiles.value.splice(index, 1)
          }

          // Check processing status
          if (response.processing_status === 'detecting' || response.task_id) {
            console.log('Starting async processing for task:', response.task_id)
            processingFiles.value.push(uploadFile)
            startPollingStatus(uploadFile)
          } else if (response.processing_status === 'completed') {
            console.log('Sync processing complete, detections:', response.detections_count)
            uploadFile.detectionCount = response.detections_count
            uploadFile.detectedSpecies = response.detected_species || []
            uploadFile.processingStatus = 'completed'
            finishedFiles.value.push(uploadFile)
          } else {
            console.log('Unknown response format, starting polling')
            processingFiles.value.push(uploadFile)
            startPollingStatus(uploadFile)
          }
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
    xhr.open('POST', `${apiUrl}/locations/${location.value.id}/image`)
    xhr.setRequestHeader('Authorization', `Bearer ${token}`)
    xhr.send(formData)

  } catch (error) {
    console.error('Upload error:', error)
    handleUploadError(uploadFile, 'Failed to upload file')
  }
}

const startPollingStatus = (uploadFile: UploadFile) => {
  if (!uploadFile.imageId) {
    console.error('Cannot poll: no image ID')
    return
  }

  console.log('Starting polling for image:', uploadFile.imageId)

  const pollStatus = async () => {
    try {
      const response = await fetchWithAuth(`/images/${uploadFile.imageId}`)
      if (response.ok) {
        const data = await response.json()
        console.log('Poll response for', uploadFile.name, ':', data)

        uploadFile.processingStatus = data.processing_status || 'detecting'

        const detections = data.detections || []
        uploadFile.detectionCount = detections.length
        uploadFile.detectedSpecies = detections.map((d: any) => d.species).filter((s: string) => s)

        const isComplete = data.processing_status === 'completed' || data.processed === true
        const isFailed = data.processing_status === 'failed'

        if (isComplete) {
          console.log('Processing complete for', uploadFile.name, 'with', detections.length, 'detections')
          stopPolling(uploadFile.id)
          moveToFinished(uploadFile)
        } else if (isFailed) {
          console.log('Processing failed for', uploadFile.name)
          stopPolling(uploadFile.id)
          uploadFile.errorMessage = 'Image processing failed'
          moveToFailed(uploadFile)
        } else {
          console.log('Still processing:', uploadFile.name, 'status:', data.processing_status)
        }
      } else {
        console.error('Poll request failed:', response.status)
      }
    } catch (error) {
      console.error('Failed to poll status:', error)
    }
  }

  const intervalId = window.setInterval(pollStatus, 2000)
  pollingIntervals.value.set(uploadFile.id, intervalId)
  pollStatus()
}

const stopPolling = (fileId: string) => {
  const intervalId = pollingIntervals.value.get(fileId)
  if (intervalId) {
    clearInterval(intervalId)
    pollingIntervals.value.delete(fileId)
  }
}

const moveToFinished = (uploadFile: UploadFile) => {
  const index = processingFiles.value.findIndex(f => f.id === uploadFile.id)
  if (index > -1) {
    processingFiles.value.splice(index, 1)
    finishedFiles.value.push(uploadFile)
  }
}

const moveToFailed = (uploadFile: UploadFile) => {
  const index = processingFiles.value.findIndex(f => f.id === uploadFile.id)
  if (index > -1) {
    processingFiles.value.splice(index, 1)
    failedFiles.value.push(uploadFile)
  }
}

const handleUploadError = (uploadFile: UploadFile, message: string) => {
  console.error(message, uploadFile.name)
  uploadFile.errorMessage = message

  const index = uploadingFiles.value.findIndex(f => f.id === uploadFile.id)
  if (index > -1) {
    uploadingFiles.value.splice(index, 1)
  }

  failedFiles.value.push(uploadFile)
}

// Integration functions
const fetchExistingIntegration = async () => {
  if (!cameraId.value) {
    return
  }

  try {
    const response = await fetchWithAuth('/image-pull-sources/')
    if (response.ok) {
      const data = await response.json()
      // Find integration for this location
      const integration = data.find((source: any) => source.location_id === cameraId.value)
      if (integration) {
        existingIntegration.value = integration
      }
    }
  } catch (err) {
    console.error('Failed to fetch existing integration:', err)
  }
}

const createIntegration = async () => {
  if (!cameraId.value) {
    return
  }

  integrationLoading.value = true
  integrationError.value = null
  integrationSuccess.value = null

  try {
    const payload: any = {
      name: integrationForm.value.name,
      location_id: cameraId.value,
      base_url: integrationForm.value.baseUrl,
      auth_type: 'basic',
      is_active: true
    }

    if (integrationForm.value.username && integrationForm.value.password) {
      payload.auth_username = integrationForm.value.username
      payload.auth_password = integrationForm.value.password
    } else {
      payload.auth_type = 'none'
    }

    const response = await fetchWithAuth('/image-pull-sources/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `Failed to create integration: ${response.status}`)
    }

    const data = await response.json()
    existingIntegration.value = data
    integrationSuccess.value = 'Integration created successfully! Images will be pulled hourly.'

    // Reset form
    integrationForm.value = {
      name: '',
      baseUrl: '',
      username: '',
      password: ''
    }

  } catch (err) {
    integrationError.value = err instanceof Error ? err.message : 'Failed to create integration'
    console.error('Error creating integration:', err)
  } finally {
    integrationLoading.value = false
  }
}

const toggleIntegration = async () => {
  if (!existingIntegration.value) {
    return
  }

  integrationLoading.value = true
  integrationError.value = null

  try {
    const newStatus = !existingIntegration.value.is_active
    const response = await fetchWithAuth(
      `/image-pull-sources/${existingIntegration.value.id}/toggle?is_active=${newStatus}`,
      {
        method: 'PATCH'
      }
    )

    if (!response.ok) {
      throw new Error(`Failed to toggle integration: ${response.status}`)
    }

    const data = await response.json()
    existingIntegration.value = data
    integrationSuccess.value = `Integration ${newStatus ? 'activated' : 'deactivated'} successfully`
    setTimeout(() => {
      integrationSuccess.value = null
    }, 3000)

  } catch (err) {
    integrationError.value = err instanceof Error ? err.message : 'Failed to toggle integration'
    console.error('Error toggling integration:', err)
  } finally {
    integrationLoading.value = false
  }
}

const testIntegration = async () => {
  if (!existingIntegration.value) {
    return
  }

  integrationLoading.value = true
  integrationError.value = null
  integrationSuccess.value = null

  try {
    const response = await fetchWithAuth(
      `/image-pull-sources/${existingIntegration.value.id}/process?max_files=2`,
      {
        method: 'POST'
      }
    )

    if (!response.ok) {
      throw new Error(`Failed to test integration: ${response.status}`)
    }

    const data = await response.json()
    integrationSuccess.value = `Test successful! Processed ${data.processed_count} file(s). Check the Overview tab to see the results.`

    // Refresh camera data to show new images
    setTimeout(() => {
      fetchCameraData()
    }, 2000)

  } catch (err) {
    integrationError.value = err instanceof Error ? err.message : 'Failed to test integration'
    console.error('Error testing integration:', err)
  } finally {
    integrationLoading.value = false
  }
}

const deleteIntegration = async () => {
  if (!existingIntegration.value) {
    return
  }

  if (!confirm('Are you sure you want to delete this integration? This cannot be undone.')) {
    return
  }

  integrationLoading.value = true
  integrationError.value = null

  try {
    // Note: Delete endpoint not implemented in backend yet, so we'll deactivate instead
    const response = await fetchWithAuth(
      `/image-pull-sources/${existingIntegration.value.id}/toggle?is_active=false`,
      {
        method: 'PATCH'
      }
    )

    if (!response.ok) {
      throw new Error(`Failed to delete integration: ${response.status}`)
    }

    existingIntegration.value = null
    integrationSuccess.value = 'Integration deleted successfully'

  } catch (err) {
    integrationError.value = err instanceof Error ? err.message : 'Failed to delete integration'
    console.error('Error deleting integration:', err)
  } finally {
    integrationLoading.value = false
  }
}

onMounted(() => {
  fetchCameraData()
  fetchExistingIntegration()
})

onUnmounted(() => {
  pollingIntervals.value.forEach(intervalId => clearInterval(intervalId))
  pollingIntervals.value.clear()
  // Clean up object URLs
  imageUrls.value.forEach(url => URL.revokeObjectURL(url))
  imageUrls.value.clear()
})
</script>
