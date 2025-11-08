<template>
  <div 
    class="avatar" 
    :class="[sizeClass, shapeClass, { 'has-border': border }]"
    :style="{ backgroundColor: bgColor }"
  >
    <img 
      v-if="src" 
      :src="src" 
      :alt="alt"
      class="avatar-image"
      @error="handleImageError"
    />
    <div v-else class="avatar-icon">
      <svg 
        xmlns="http://www.w3.org/2000/svg" 
        viewBox="0 0 24 24" 
        fill="currentColor"
      >
        <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
      </svg>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

type Size = 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl'
type Shape = 'circle' | 'square' | 'rounded'
type BadgePosition = 'top-right' | 'bottom-right' | 'top-left' | 'bottom-left'

interface Props {
  src?: string
  alt?: string
  name?: string
  initials?: string
  size?: Size
  shape?: Shape
  bgColor?: string
  textColor?: string
  border?: boolean
  badge?: string | number
  badgePosition?: BadgePosition
  badgeColor?: string
}

const props = withDefaults(defineProps<Props>(), {
  alt: 'Avatar',
  size: 'md',
  shape: 'circle',
  bgColor: '#3b82f6',
  textColor: '#ffffff',
  border: false,
  badgePosition: 'bottom-right',
  badgeColor: '#22c55e'
})

const imageError = ref(false)

const sizeClass = computed(() => `avatar-${props.size}`)
const shapeClass = computed(() => `avatar-${props.shape}`)
const badgeClass = computed(() => `badge-${props.badgePosition}`)

const handleImageError = () => {
  imageError.value = true
}
</script>

<style scoped>
.avatar {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
  user-select: none;
  color: v-bind(textColor);
  background-color: v-bind(bgColor);
  transition: all 0.2s ease;
}

/* Sizes */
.avatar-xs {
  width: 24px;
  height: 24px;
  font-size: 10px;
}

.avatar-sm {
  width: 32px;
  height: 32px;
  font-size: 12px;
}

.avatar-md {
  width: 40px;
  height: 40px;
  font-size: 14px;
}

.avatar-lg {
  width: 48px;
  height: 48px;
  font-size: 16px;
}

.avatar-xl {
  width: 64px;
  height: 64px;
  font-size: 20px;
}

.avatar-2xl {
  width: 96px;
  height: 96px;
  font-size: 28px;
}

/* Shapes */
.avatar-circle {
  border-radius: 50%;
}

.avatar-rounded {
  border-radius: 8px;
}

.avatar-square {
  border-radius: 0;
}

/* Border */
.avatar.has-border {
  border: 2px solid #ffffff;
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.1);
}

/* Image */
.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* Initials */
.avatar-initials {
  font-weight: 600;
  line-height: 1;
}

/* Icon */
.avatar-icon {
  width: 60%;
  height: 60%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-icon svg {
  width: 100%;
  height: 100%;
}

/* Badge */
.avatar-badge {
  position: absolute;
  min-width: 18px;
  height: 18px;
  padding: 0 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 600;
  color: white;
  background-color: v-bind(badgeColor);
  border: 2px solid white;
  border-radius: 9px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.badge-top-right {
  top: -2px;
  right: -2px;
}

.badge-bottom-right {
  bottom: -2px;
  right: -2px;
}

.badge-top-left {
  top: -2px;
  left: -2px;
}

.badge-bottom-left {
  bottom: -2px;
  left: -2px;
}

/* Hover effect */
.avatar:hover {
  transform: scale(1.05);
}
</style>
