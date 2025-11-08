<script setup>
// Sidebar component for navigation
</script>

<template>
  <div class="w-64 min-h-screen bg-gray-100 p-5 border-r border-gray-300">
    <nav>
      <ul class="list-none p-0 m-0">
        <li class="mb-2.5">
          <NuxtLink 
            to="/upload" 
            class="block py-2.5 px-4 no-underline text-gray-800 rounded transition-colors hover:bg-gray-200 [&.router-link-active]:bg-blue-600 [&.router-link-active]:text-white"
          >
            Upload
          </NuxtLink>
        </li>
        <li class="mb-2.5">
          <NuxtLink 
            to="/statistics" 
            class="block py-2.5 px-4 no-underline text-gray-800 rounded transition-colors hover:bg-gray-200 [&.router-link-active]:bg-blue-600 [&.router-link-active]:text-white"
          >
            Statistics
          </NuxtLink>
        </li>
        <li class="mb-2.5">
          <NuxtLink 
            to="/map" 
            class="block py-2.5 px-4 no-underline text-gray-800 rounded transition-colors hover:bg-gray-200 [&.router-link-active]:bg-blue-600 [&.router-link-active]:text-white"
          >
            Map
          </NuxtLink>
        </li>
        <li class="mb-2.5">
          <NuxtLink 
            to="/match" 
            class="block py-2.5 px-4 no-underline text-gray-800 rounded transition-colors hover:bg-gray-200 [&.router-link-active]:bg-blue-600 [&.router-link-active]:text-white"
          >
            Match
          </NuxtLink>
        </li>
      </ul>
    </nav>
  </div>
</template>
