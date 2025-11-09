<template>
  <div class="statistics-page">
    <div class="header">
      <h1>Wildlife Statistics</h1>
      <div class="controls">
        <div class="control-group">
          <label for="time-range">Time Range</label>
          <select id="time-range" v-model="period" class="time-range-select">
            <option v-for="p in periods" :key="p.value" :value="p.value">
              {{ p.label }}
            </option>
          </select>
        </div>
      </div>
    </div>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Loading statistics...</p>
    </div>

    <div v-else-if="error" class="error">
      <p>{{ error }}</p>
      <button @click="fetchStatistics" class="retry-btn">Retry</button>
    </div>

    <div v-else class="statistics-content">
      <div class="chart-section">
        <canvas id="speciesChart"></canvas>
      </div>

      <div class="species-breakdown">
        <div class="species-header">
          <h2>Species Breakdown</h2>
          <div class="species-stats">
            <span class="stat-item">{{ totalSpottings }} Total Spottings</span>
            <span class="stat-divider">•</span>
            <span class="stat-item">{{ uniqueSpecies.size }} Unique Species</span>
          </div>
        </div>
        <div class="species-list">
          <div v-for="(species, index) in topSpecies" :key="species.name" v-show="showAllSpecies || index < 3"
            class="species-item">
            <div class="species-content">
              <div class="species-info">
                <span class="species-name">{{ species.name }}</span>
                <span class="species-count">{{ species.count }} sightings</span>
              </div>
              <div class="species-bar">
                <div class="species-bar-fill" :style="{ width: `${(species.count / totalSpottings) * 100}%` }"></div>
              </div>
            </div>
            <button @click="showInMap(species.name)" class="map-icon-btn" title="Show in map">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                <circle cx="12" cy="10" r="3"></circle>
              </svg>
            </button>
          </div>
        </div>
        <button v-if="topSpecies.length > 3" @click="showAllSpecies = !showAllSpecies" class="toggle-species-btn">
          {{ showAllSpecies ? 'Show Less' : `Show All (${topSpecies.length - 3} more)` }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Chart } from 'chart.js'
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'

interface SpeciesCount {
  name: string
  count: number
}

interface TimePeriodStatistics {
  start_time: string
  end_time: string
  species: SpeciesCount[]
  total_spottings: number
}

interface StatisticsResponse {
  statistics: TimePeriodStatistics[]
}

const apiUrl = useApiUrl()

const periods = [
  { value: 'day', label: 'Today' },
  { value: 'week', label: 'Last 7 Days' },
  { value: 'month', label: 'Last 30 Days' }
]

const period = ref<string>('day')
const statistics = ref<TimePeriodStatistics[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const showAllSpecies = ref(false)
let chartInstance: Chart | null = null

const granularity = computed(() => {
  // Auto-set granularity based on period
  if (period.value === 'day') {
    return 'hourly'
  } else {
    return 'daily'
  }
})

const totalSpottings = computed(() =>
  statistics.value.reduce((sum, stat) => sum + stat.total_spottings, 0)
)

const uniqueSpecies = computed(() => {
  const species = new Set<string>()
  statistics.value.forEach(stat => {
    stat.species.forEach(s => species.add(s.name))
  })
  return species
})

const topSpecies = computed(() => {
  const speciesMap = new Map<string, number>()

  statistics.value.forEach(stat => {
    stat.species.forEach(s => {
      speciesMap.set(s.name, (speciesMap.get(s.name) || 0) + s.count)
    })
  })

  return Array.from(speciesMap.entries())
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
})

const showInMap = (speciesName: string) => {
  const params = new URLSearchParams()

  // Add species parameter
  params.set('species', speciesName)

  // Navigate to map page with query parameters
  navigateTo(`/map?${params.toString()}`)
}

const fetchStatistics = async () => {
  loading.value = true
  error.value = null

  try {
    const response = await fetch(`${apiUrl}/statistics?period=${period.value}&granularity=${granularity.value}`)

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data: StatisticsResponse = await response.json()
    statistics.value = data.statistics
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to fetch statistics'
    console.error('Error fetching statistics:', err)
  } finally {
    loading.value = false
    // Wait for DOM to update after loading is set to false
    await nextTick()
    if (statistics.value.length > 0 && !error.value) {
      renderChart()
    }
  }
}

const renderChart = async () => {
  const canvas = document.getElementById('speciesChart') as HTMLCanvasElement | null

  if (!canvas) {
    console.error('Chart canvas not found')
    return
  }

  if (statistics.value.length === 0) {
    console.warn('No statistics data available')
    return
  }

  console.log('Rendering chart with', statistics.value.length, 'data points')

  const { Chart, registerables } = await import('chart.js')
  Chart.register(...registerables)

  // Destroy existing chart
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }

  const ctx = canvas.getContext('2d')
  if (!ctx) {
    console.error('Could not get 2D context')
    return
  }

  // Prepare labels (timestamps)
  const labels = statistics.value.map(stat => {
    const start = new Date(stat.start_time)
    if (granularity.value === 'hourly') {
      return start.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
    } else {
      return start.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    }
  })

  // Get all unique species
  const allSpecies = new Set<string>()
  statistics.value.forEach(stat => {
    stat.species.forEach(s => allSpecies.add(s.name))
  })

  console.log('Species found:', allSpecies.size, 'Labels:', labels.length)

  // Define colors for species
  const colors = [
    '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6',
    '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1'
  ]

  // Create datasets for stacked bar chart
  const datasets = Array.from(allSpecies).map((speciesName, index) => ({
    label: speciesName,
    data: statistics.value.map(stat => {
      const species = stat.species.find(s => s.name === speciesName)
      return species ? species.count : 0
    }),
    backgroundColor: colors[index % colors.length],
    borderColor: colors[index % colors.length],
    borderWidth: 1
  }))

  console.log('Creating chart with', datasets.length, 'datasets')

  chartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top' as const,
          labels: {
            usePointStyle: true,
            padding: 15,
            font: {
              size: 12
            }
          }
        },
        tooltip: {
          mode: 'index',
          intersect: false,
          callbacks: {
            footer: (items: any[]) => {
              const total = items.reduce((sum: number, item: any) => sum + (item.parsed.y || 0), 0)
              return `Total: ${total} sightings`
            }
          }
        }
      },
      scales: {
        x: {
          stacked: true,
          title: {
            display: true,
            text: granularity.value === 'hourly' ? 'Time' : 'Date'
          }
        },
        y: {
          stacked: true,
          beginAtZero: true,
          ticks: {
            stepSize: 1
          },
          title: {
            display: true,
            text: 'Number of Sightings'
          }
        }
      }
    }
  })

  console.log('Chart created successfully:', chartInstance)
}

watch(period, () => {
  fetchStatistics()
})

watch(statistics, async () => {
  if (statistics.value.length > 0) {
    await nextTick()
    renderChart()
  }
}, { deep: true })

onMounted(() => {
  fetchStatistics()
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.destroy()
  }
})
</script>

<style scoped>
.statistics-page {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.header {
  margin-bottom: 32px;
}

.header h1 {
  font-size: 32px;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 20px;
}

.controls {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.control-group label {
  font-size: 14px;
  font-weight: 600;
  color: #4b5563;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.time-range-select {
  padding: 10px 16px;
  border: 2px solid #e5e7eb;
  background: white;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
  cursor: pointer;
  transition: all 0.2s;
  outline: none;
}

.time-range-select:hover {
  border-color: #3b82f6;
}

.time-range-select:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.loading,
.error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  gap: 16px;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.error {
  color: #ef4444;
}

.retry-btn {
  padding: 10px 24px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.2s;
}

.retry-btn:hover {
  background: #2563eb;
}

.chart-section {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid #e5e7eb;
  margin-bottom: 24px;
  height: 400px;
  position: relative;
}

.chart-section canvas {
  width: 100% !important;
  height: 100% !important;
}

.species-breakdown {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid #e5e7eb;
}

.species-header {
  margin-bottom: 24px;
}

.species-header h2 {
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 8px 0;
}

.species-stats {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: #6b7280;
}

.stat-item {
  font-weight: 600;
}

.stat-divider {
  color: #d1d5db;
}

.species-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.species-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.species-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.species-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.species-name {
  font-weight: 600;
  color: #1f2937;
}

.species-count {
  font-size: 14px;
  color: #6b7280;
}

.species-bar {
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
}

.species-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #2563eb);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.map-icon-btn {
  padding: 8px;
  background: transparent;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  color: #6b7280;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
}

.map-icon-btn:hover {
  border-color: #3b82f6;
  color: #3b82f6;
  background: rgba(59, 130, 246, 0.05);
}

.toggle-species-btn {
  margin-top: 16px;
  padding: 10px 20px;
  background: transparent;
  color: #3b82f6;
  border: 2px solid #3b82f6;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.2s;
  width: 100%;
}

.toggle-species-btn:hover {
  background: #3b82f6;
  color: white;
}
</style>
