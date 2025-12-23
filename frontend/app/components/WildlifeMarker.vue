<template>
  <div class="wildlife-marker">
    <div class="marker-icon">
      <svg 
        xmlns="http://www.w3.org/2000/svg" 
        viewBox="0 0 24 24" 
        fill="currentColor"
        class="camera-icon"
      >
        <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
      </svg>
      <div class="camera-badge">
        <svg 
          xmlns="http://www.w3.org/2000/svg" 
          viewBox="0 0 24 24" 
          fill="white"
          class="badge-icon"
        >
          <path d="M9 2L7.17 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2h-3.17L15 2H9zm3 15c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5z"/>
        </svg>
      </div>
    </div>
    <div class="marker-label" v-if="label">{{ label }}</div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  label?: string
  color?: string
}

withDefaults(defineProps<Props>(), {
  color: '#ef4444'
})
</script>

<style scoped>
.wildlife-marker {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
}

.marker-icon {
  position: relative;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
}

.camera-icon {
  width: 40px;
  height: 40px;
  color: v-bind(color);
  transition: transform 0.2s;
}

.wildlife-marker:hover .camera-icon {
  transform: scale(1.1);
}

.camera-badge {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 16px;
  height: 16px;
  background-color: #2563eb;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid white;
}

.badge-icon {
  width: 10px;
  height: 10px;
}

.marker-label {
  margin-top: 4px;
  padding: 2px 6px;
  background-color: rgba(0, 0, 0, 0.75);
  color: white;
  font-size: 11px;
  font-weight: 600;
  border-radius: 3px;
  white-space: nowrap;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}
</style>
