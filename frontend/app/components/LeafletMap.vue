<template>
  <div ref="mapContainer" class="leaflet-map" :style="{ height: height, width: width }"></div>
</template>

<script setup lang="ts">
import type { LatLngExpression, Map, Marker } from 'leaflet'
import { onMounted, onUnmounted, ref, watch } from 'vue'

const router = useRouter()

interface Props {
  center?: [number, number]
  zoom?: number
  height?: string
  width?: string
  markers?: Array<{
    position: [number, number]
    popup?: string
    icon?: any
    id?: string
    zIndexOffset?: number
    data?: any
  }>
}

const props = withDefaults(defineProps<Props>(), {
  center: () => [51.9244, 9.4305], // Default: Hameln, Germany
  zoom: 13,
  height: '100%',
  width: '100%',
  markers: () => []
})

const emit = defineEmits<{
  markerClick: [data: any]
}>()

const mapContainer = ref<HTMLElement | null>(null)
let map: Map | null = null
let markerInstances: Marker[] = []

onMounted(async () => {
  if (!mapContainer.value) return

  // Dynamically import Leaflet to avoid SSR issues
  const L = await import('leaflet')

  // Import Leaflet CSS
  await import('leaflet/dist/leaflet.css')

  // Fix for default marker icons in Leaflet
  delete (L.Icon.Default.prototype as any)._getIconUrl
  L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
  })

  // Initialize map
  map = L.map(mapContainer.value).setView(props.center as LatLngExpression, props.zoom)

  // Add OpenStreetMap tile layer
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19,
  }).addTo(map)

  // Add markers if provided
  addMarkers()
})

const addMarkers = async () => {
  if (!map || props.markers.length === 0) return

  const L = await import('leaflet')

  // Clear existing markers
  markerInstances.forEach(marker => marker.remove())
  markerInstances = []

  // Add new markers
  props.markers.forEach(markerData => {
    if (!map) return

    // Create marker options, only include icon if it's provided
    const markerOptions: any = {}
    if (markerData.icon) {
      markerOptions.icon = markerData.icon
    }
    if (markerData.zIndexOffset !== undefined) {
      markerOptions.zIndexOffset = markerData.zIndexOffset
    }

    const marker = L.marker(markerData.position as LatLngExpression, markerOptions).addTo(map)

    if (markerData.popup) {
      marker.bindPopup(markerData.popup)
      
      // Add click handler for Nuxt links in popup
      marker.on('popupopen', () => {
        const popup = marker.getPopup()
        if (popup && popup.getElement()) {
          const popupElement = popup.getElement()
          const nuxtLinks = popupElement?.querySelectorAll('.nuxt-link')
          nuxtLinks?.forEach((link: Element) => {
            const anchor = link as HTMLAnchorElement
            const routePath = anchor.getAttribute('data-nuxt-link')
            if (routePath && !anchor.dataset.listenerAdded) {
              anchor.dataset.listenerAdded = 'true'
              anchor.addEventListener('click', (e) => {
                e.preventDefault()
                e.stopPropagation()
                router.push(routePath)
              })
            }
          })
        }
      })
    }

    // Add click event listener
    marker.on('click', (e) => {
      emit('markerClick', markerData.data || markerData)

      // Move the marker to the bottom center of the viewport only if popup is closed
      if (map && !e.target.isPopupOpen()) {
        const targetLatLng = e.target.getLatLng()
        const containerSize = map.getSize()

        // Calculate offset to place marker at bottom center
        // We want the marker at 75% down from the top (bottom center area)
        const targetY = containerSize.y * 0.75

        const newPoint = L.point(containerSize.x / 2, targetY)
        const newLatLng = map.containerPointToLatLng(newPoint)

        // Calculate the difference and pan
        const latDiff = targetLatLng.lat - newLatLng.lat
        const lngDiff = targetLatLng.lng - newLatLng.lng

        map.panTo([targetLatLng.lat + latDiff, targetLatLng.lng + lngDiff], { animate: true })
      }
    })

    markerInstances.push(marker)
  })
}

// Watch for marker changes
watch(() => props.markers, () => {
  addMarkers()
}, { deep: true })

// Watch for center changes
watch(() => props.center, (newCenter) => {
  if (map) {
    map.setView(newCenter as LatLngExpression, props.zoom)
  }
})

onUnmounted(() => {
  if (map) {
    map.remove()
    map = null
  }
})

const setCenter = (center: [number, number], zoomLevel?: number) => {
  if (map) {
    map.setView(center as LatLngExpression, zoomLevel ?? props.zoom)
  }
}

// Expose map instance for parent components
defineExpose({
  getMap: () => map,
  setCenter
})
</script>

<style scoped>
.leaflet-map {
  min-height: 400px;
  border-radius: 8px;
  overflow: hidden;
}
</style>
