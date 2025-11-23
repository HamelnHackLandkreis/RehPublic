import { createAuth0 } from '@auth0/auth0-vue'

export default defineNuxtPlugin((nuxtApp) => {
  console.log('Auth0 Plugin: Starting initialization...')

  if (typeof window === 'undefined') {
    console.log('Auth0 Plugin: Skipping server-side execution')
    return
  }

  const config = useRuntimeConfig()

  const domain = config.public.auth0Domain as string
  const clientId = config.public.auth0ClientId as string
  const audience = config.public.auth0Audience as string

  console.log('Auth0 Plugin: Config loaded', { domain, clientId, audience })

  if (!domain || !clientId) {
    console.error('Auth0 configuration missing. Please check your environment variables.')
    console.error('Required environment variables:')
    console.error('- NUXT_PUBLIC_AUTH0_DOMAIN')
    console.error('- NUXT_PUBLIC_AUTH0_CLIENT_ID')
    console.error('Current values:', { domain, clientId, audience })
    return
  }

  if (!domain.includes('.auth0.com') && !domain.includes('.us.auth0.com') && !domain.includes('.eu.auth0.com') && !domain.includes('.au.auth0.com')) {
    console.warn('Auth0 domain format might be incorrect. Expected format: your-domain.auth0.com')
  }

  const auth0Config: any = {
    domain,
    clientId,
    authorizationParams: {
      redirect_uri: window.location.origin
    },
    openUrl: async (url: string) => {
      console.log('Auth0 SDK custom openUrl called with:', url)
      window.location.replace(url)
    }
  }

  if (audience) {
    auth0Config.authorizationParams.audience = audience
  }

  try {
    console.log('Auth0 Plugin: Registering Auth0 instance...')
    const auth0Instance = createAuth0(auth0Config)
    nuxtApp.vueApp.use(auth0Instance)
    console.log('Auth0 plugin initialized successfully')
  } catch (error) {
    console.error('Failed to initialize Auth0:', error)
  }
})
