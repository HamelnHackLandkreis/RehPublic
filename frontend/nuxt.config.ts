import tailwindcss from "@tailwindcss/vite";
// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: "2025-07-15",
  devtools: { enabled: true },
  css: ["./app/assets/css/main.css"],
  modules: ["@nuxt/image", "@nuxt/eslint", "@nuxt/ui", "@vite-pwa/nuxt"],
  // Skip prerendering for auth-protected routes
  routeRules: {
    '/settings': { ssr: false },
    '/upload': { ssr: false },
  },
  app: {
    head: {
      title: 'RehPublic',
      link: [
        { rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' },
        { rel: 'icon', type: 'image/png', href: '/favicon.png' }
      ]
    }
  },
  runtimeConfig: {
    public: {
      apiUrl: process.env.NUXT_PUBLIC_API_URL || 'http://localhost:8000',
      auth0Domain: process.env.NUXT_PUBLIC_AUTH0_DOMAIN || '',
      auth0ClientId: process.env.NUXT_PUBLIC_AUTH0_CLIENT_ID || '',
      auth0Audience: process.env.NUXT_PUBLIC_AUTH0_AUDIENCE || ''
    }
  },
  pwa: {
    registerType: 'autoUpdate',
    manifest: {
      name: 'RehPublic - Wildlife Monitoring',
      short_name: 'RehPublic',
      description: 'Wildlife camera trap monitoring and analysis platform',
      theme_color: '#4CAF50',
      background_color: '#ffffff',
      display: 'standalone',
      icons: [
        {
          src: '/icon-192x192.png',
          sizes: '192x192',
          type: 'image/png'
        },
        {
          src: '/icon-512x512.png',
          sizes: '512x512',
          type: 'image/png'
        }
      ]
    },
    workbox: {
      navigateFallback: '/',
      cleanupOutdatedCaches: true,
      runtimeCaching: [
        {
          urlPattern: /^https:\/\/api\..*/i,
          handler: 'NetworkFirst',
          options: {
            cacheName: 'api-cache',
            expiration: {
              maxEntries: 50,
              maxAgeSeconds: 60 * 60 * 24 // 24 hours
            }
          }
        }
      ]
    },
    client: {
      installPrompt: true,
      // Disable periodic sync in dev
      periodicSyncForUpdates: 3600
    },
    devOptions: {
      enabled: false,
      suppressWarnings: true,
      navigateFallback: '/',
      type: 'module'
    },
    disable: true  // Disable PWA in development completely
  },
  vite: {
    plugins: [
      tailwindcss(),
    ],
  },
})
