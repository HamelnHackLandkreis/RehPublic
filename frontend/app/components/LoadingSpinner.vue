<template>
  <div :class="['loading-spinner', sizeClass]">
    <div class="logo-container">
      <img 
        src="/RehPublic_Icon.png" 
        alt="Loading" 
        class="logo-image"
        :style="{ width: `${size}px`, height: `${size}px` }"
      />
      <div class="shimmer-overlay"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  size?: 'sm' | 'md' | 'lg' | 'xl'
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md'
})

const sizeMap = {
  sm: 60,
  md: 96,
  lg: 128,
  xl: 160
}

const size = computed(() => sizeMap[props.size])
const sizeClass = computed(() => `size-${props.size}`)
</script>

<style scoped>
.loading-spinner {
  display: inline-block;
  position: relative;
}

.logo-container {
  position: relative;
  display: inline-block;
}

.logo-image {
  position: relative;
  z-index: 2;
  filter: drop-shadow(0 0 12px rgba(34, 197, 94, 0.3));
}

.shimmer-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 3;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(34, 197, 94, 0.4) 20%,
    rgba(22, 163, 74, 0.4) 35%,
    rgba(132, 204, 22, 0.4) 50%,
    rgba(101, 163, 13, 0.4) 65%,
    rgba(120, 53, 15, 0.4) 80%,
    rgba(154, 52, 18, 0.4) 100%,
    transparent 100%
  );
  background-size: 200% 100%;
  animation: shimmer 2s ease-in-out infinite;
  border-radius: 50%;
  pointer-events: none;
}

@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}
</style>

