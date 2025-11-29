import { createAuth0 } from '@auth0/auth0-vue'

export default defineNuxtPlugin((nuxtApp) => {
  if (typeof window === 'undefined') {
    return
  }

  const config = useRuntimeConfig()

  const domain = config.public.auth0Domain as string
  const clientId = config.public.auth0ClientId as string
  const audience = config.public.auth0Audience as string

  if (!domain || !clientId) {
    console.error('Auth0 configuration missing')
    return
  }

  const auth0Config: any = {
    domain,
    clientId,
    authorizationParams: {
      redirect_uri: window.location.origin + '/callback'
    },
    cacheLocation: 'localstorage' as const,
    useRefreshTokens: true
  }

  if (audience) {
    auth0Config.authorizationParams.audience = audience
  }

  try {
    const auth0Instance = createAuth0(auth0Config)
    nuxtApp.vueApp.use(auth0Instance)
  } catch (error) {
    console.error('Failed to initialize Auth0:', error)
  }
})
