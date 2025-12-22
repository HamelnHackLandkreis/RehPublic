<template>
  <div class="statistics-page">
    <div class="header">
      <h1>Wildlife Statistics</h1>
      <p class="header-description">View and analyze wildlife detection data across different time periods</p>
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
      <LoadingSpinner size="md" />
      <p>Loading statistics...</p>
    </div>

    <div v-else-if="error" class="error">
      <p>{{ error }}</p>
      <button @click="fetchStatistics" class="retry-btn">Retry</button>
    </div>

    <div v-else class="statistics-content">
      <div class="chart-section">
        <div class="chart-header">
          <h2>Timeline Overview</h2>
          <button @click="showBarChart = !showBarChart" class="collapse-btn"
            :title="showBarChart ? 'Collapse chart' : 'Expand chart'">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
              :class="{ rotated: !showBarChart }">
              <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
          </button>
        </div>
        <div class="chart-canvas-container" :class="{ collapsed: !showBarChart }">
          <canvas id="speciesChart"></canvas>
        </div>
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
            class="species-item-wrapper">
            <div class="species-item">
              <div class="species-content">
                <div class="species-info">
                  <span class="species-name">{{ species.name }}</span>
                  <span class="species-count">{{ species.count }} sightings</span>
                </div>
                <div class="species-bar">
                  <div class="species-bar-fill" :style="{ width: `${(species.count / totalSpottings) * 100}%` }"></div>
                </div>
              </div>
              <div class="species-actions">
                <button @click="showInMap(species.name)" class="map-icon-btn" title="Show in map">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                    <circle cx="12" cy="10" r="3"></circle>
                  </svg>
                </button>
                <button @click="toggleSpeciesChart(species.name)" class="chart-icon-btn"
                  :class="{ active: expandedSpecies === species.name }"
                  :title="expandedSpecies === species.name ? 'Hide chart' : 'Show trend'">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
                  </svg>
                </button>
              </div>
            </div>
            <!-- Species trend chart -->
            <div v-if="expandedSpecies === species.name" class="species-chart-container">
              <canvas :id="`species-chart-${species.name.replace(/\s+/g, '-')}`"></canvas>
            </div>
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
const { fetchWithAuth } = useAuthenticatedApi()

const periods = [
  { value: 'day', label: 'Today' },
  { value: 'week', label: 'Last 7 Days' },
  { value: 'month', label: 'Last 30 Days' },
  { value: 'year', label: 'Last 365 Days' }
]

const period = ref<string>('month')
const statistics = ref<TimePeriodStatistics[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const showAllSpecies = ref(false)
const expandedSpecies = ref<string | null>(null)
const showBarChart = ref(true)
let chartInstance: Chart | null = null
const speciesChartInstances = new Map<string, Chart>()

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

  // Add time range from statistics data
  if (statistics.value.length > 0) {
    const firstStat = statistics.value[0]
    const lastStat = statistics.value[statistics.value.length - 1]
    if (firstStat && lastStat) {
      params.set('time_start', firstStat.start_time)
      params.set('time_end', lastStat.end_time)
    }
  }

  // Navigate to map page with query parameters
  navigateTo(`/map?${params.toString()}`)
}

const fetchStatistics = async () => {
  loading.value = true
  error.value = null

  try {
    const response = await fetchWithAuth(`/statistics?period=${period.value}&granularity=${granularity.value}`)

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

// Toggle species chart visibility
const toggleSpeciesChart = async (speciesName: string) => {
  if (expandedSpecies.value === speciesName) {
    // Close chart
    const chart = speciesChartInstances.get(speciesName)
    if (chart) {
      chart.destroy()
      speciesChartInstances.delete(speciesName)
    }
    expandedSpecies.value = null
  } else {
    // Close any existing chart
    if (expandedSpecies.value) {
      const chart = speciesChartInstances.get(expandedSpecies.value)
      if (chart) {
        chart.destroy()
        speciesChartInstances.delete(expandedSpecies.value)
      }
    }
    // Open new chart
    expandedSpecies.value = speciesName
    await nextTick()
    renderSpeciesChart(speciesName)
  }
}

// Render line chart for individual species
const renderSpeciesChart = async (speciesName: string) => {
  const canvasId = `species-chart-${speciesName.replace(/\s+/g, '-')}`
  const canvas = document.getElementById(canvasId) as HTMLCanvasElement

  if (!canvas) {
    console.error('Canvas not found for species:', speciesName)
    return
  }

  const { Chart, registerables } = await import('chart.js')
  Chart.register(...registerables)

  const ctx = canvas.getContext('2d')
  if (!ctx) {
    console.error('Could not get 2D context')
    return
  }

  // Prepare data for this species
  let labels: string[]
  let data: number[]

  if (period.value === 'year') {
    // Group by month for year view
    const monthlyData = new Map<string, number>()

    statistics.value.forEach(stat => {
      const start = new Date(stat.start_time)
      const monthKey = `${start.getFullYear()}-${String(start.getMonth() + 1).padStart(2, '0')}`
      const monthLabel = start.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })

      const species = stat.species.find(s => s.name === speciesName)
      const count = species ? species.count : 0

      monthlyData.set(monthKey, (monthlyData.get(monthKey) || 0) + count)
    })

    // Sort by month key and extract labels and data
    const sortedEntries = Array.from(monthlyData.entries()).sort((a, b) => a[0].localeCompare(b[0]))
    labels = sortedEntries.map(([key]) => {
      const [year, month] = key.split('-')
      if (year && month) {
        const date = new Date(parseInt(year), parseInt(month) - 1, 1)
        return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
      }
      return key
    })
    data = sortedEntries.map(([, count]) => count)
  } else {
    // Use existing granularity for other periods
    labels = statistics.value.map(stat => {
      const start = new Date(stat.start_time)
      if (granularity.value === 'hourly') {
        return start.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
      } else {
        return start.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
      }
    })

    data = statistics.value.map(stat => {
      const species = stat.species.find(s => s.name === speciesName)
      return species ? species.count : 0
    })
  }

  const chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: speciesName,
        data,
        borderColor: 'var(--color-secondary)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 3,
        fill: true,
        tension: 0.4,
        pointRadius: 4,
        pointHoverRadius: 6,
        pointBackgroundColor: 'var(--color-secondary)',
        pointBorderColor: '#fff',
        pointBorderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      aspectRatio: 3,
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          padding: 12,
          titleFont: { size: 14 },
          bodyFont: { size: 13 }
        }
      },
      scales: {
        x: {
          grid: {
            display: false
          }
        },
        y: {
          beginAtZero: true,
          ticks: {
            stepSize: 1
          },
          grid: {
            color: 'rgba(0, 0, 0, 0.05)'
          },
          title: {
            display: true,
            text: 'Sightings'
          }
        }
      }
    }
  })

  speciesChartInstances.set(speciesName, chart)
}

watch(period, () => {
  // Close all species charts when period changes
  speciesChartInstances.forEach((chart) => {
    chart.destroy()
  })
  speciesChartInstances.clear()
  expandedSpecies.value = null

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
  padding: 1.5rem 1rem;
  max-width: 1400px;
  margin: 0 auto;
}

@media (min-width: 640px) {
  .statistics-page {
    padding: 1.5rem 1.5rem;
  }
}

@media (min-width: 1024px) {
  .statistics-page {
    padding: 1.5rem 2rem;
  }
}

.header {
  margin-bottom: 32px;
}

.header h1 {
  font-size: 32px;
  font-weight: 700;
  color: #ffffff;
  margin-bottom: 8px;
  text-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}

.header-description {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 20px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
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
  color: #ffffff;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
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
  border-color: var(--color-secondary);
}

.time-range-select:focus {
  border-color: var(--color-secondary);
  box-shadow: 0 0 0 3px rgba(var(--color-secondary), 0.1);
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


.error {
  color: var(--color-error);
}

.retry-btn {
  padding: 10px 24px;
  background: var(--color-secondary);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.2s;
}

.retry-btn:hover {
  background: var(--color-secondary-dark);
}

.chart-section {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid #e5e7eb;
  margin-bottom: 24px;
  position: relative;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.chart-header h2 {
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
}

.collapse-btn {
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
}

.collapse-btn:hover {
  border-color: var(--color-secondary);
  color: var(--color-secondary);
  background: rgba(var(--color-secondary), 0.05);
}

.collapse-btn svg {
  transition: transform 0.3s ease;
}

.collapse-btn svg.rotated {
  transform: rotate(-90deg);
}

.chart-canvas-container {
  height: 360px;
  position: relative;
  overflow: hidden;
  transition: height 0.3s ease, opacity 0.3s ease, margin 0.3s ease;
}

.chart-canvas-container.collapsed {
  height: 0;
  opacity: 0;
  margin: 0;
}

.chart-canvas-container canvas {
  width: 100% !important;
  height: 100% !important;
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

.species-item-wrapper {
  display: flex;
  flex-direction: column;
  gap: 12px;
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

.species-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
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
  background: linear-gradient(90deg, var(--color-secondary), var(--color-secondary-dark));
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
  border-color: var(--color-secondary);
  color: var(--color-secondary);
  background: rgba(var(--color-secondary), 0.05);
}

.chart-icon-btn {
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

.chart-icon-btn:hover {
  border-color: var(--color-secondary);
  color: var(--color-secondary);
  background: rgba(var(--color-secondary), 0.05);
}

.chart-icon-btn.active {
  border-color: var(--color-secondary);
  color: var(--color-secondary);
  background: rgba(var(--color-secondary), 0.1);
}

.species-chart-container {
  background: #f9fafb;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.species-chart-container canvas {
  width: 100% !important;
  height: auto !important;
}

.toggle-species-btn {
  margin-top: 16px;
  padding: 10px 20px;
  background: transparent;
  color: var(--color-secondary);
  border: 2px solid var(--color-secondary);
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.2s;
  width: 100%;
}

.toggle-species-btn:hover {
  background: var(--color-secondary);
  color: white;
}
</style>
