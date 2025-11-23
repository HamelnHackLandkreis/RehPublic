import { useAuth0 } from '@auth0/auth0-vue'

export const useAuth = () => {
  if (typeof window === 'undefined') {
    const login = () => { }
    const logout = () => { }
    const getToken = async (): Promise<string | null> => null

    return {
      user: computed(() => null),
      isAuthenticated: computed(() => false),
      isLoading: computed(() => true),
      error: computed(() => null),
      login,
      logout,
      getToken
    }
  }

  console.log('useAuth called')
  let auth0: ReturnType<typeof useAuth0> | null = null

  try {
    auth0 = useAuth0()
    console.log('useAuth0 returned:', !!auth0)
    if (auth0 && auth0.isLoading.value) {
      const unwatch = watch(() => auth0!.isLoading.value, (loading) => {
        if (!loading) {
          unwatch()
        }
      }, { immediate: true })
    }
  } catch (error) {
    console.warn('Auth0 not initialized yet:', error)
  }

  if (!auth0) {
    console.warn('useAuth: auth0 is null, using fallback')
    const config = useRuntimeConfig()
    const domain = config.public.auth0Domain as string
    const clientId = config.public.auth0ClientId as string
    const audience = config.public.auth0Audience as string
    let isRedirecting = false

    const login = () => {
      console.log('useAuth (fallback): login called')
      if (isRedirecting) {
        console.log('Already redirecting to login, skipping...')
        return
      }

      if (window.location.search.includes('code=') || window.location.search.includes('error=')) {
        console.log('Already on Auth0 callback page, waiting for processing...')
        return
      }

      console.warn('Auth0 not initialized, attempting manual redirect')
      if (domain && clientId) {
        isRedirecting = true
        const redirectUri = encodeURIComponent(window.location.origin)
        const audienceParam = audience ? `&audience=${encodeURIComponent(audience)}` : ''
        const authUrl = `https://${domain}/authorize?client_id=${clientId}&response_type=code&redirect_uri=${redirectUri}&scope=openid profile email${audienceParam}`
        console.log('Redirecting to:', authUrl)
        window.location.href = authUrl
      } else {
        console.error('Auth0 configuration missing, cannot redirect to login')
      }
    }

    const logout = () => {
      console.warn('Auth0 not initialized, cannot logout')
    }

    const getToken = async (): Promise<string | null> => {
      console.warn('Auth0 not initialized, cannot get token')
      return null
    }

    return {
      user: computed(() => null),
      isAuthenticated: computed(() => false),
      isLoading: computed(() => false),
      error: computed(() => null),
      login,
      logout,
      getToken
    }
  }

  let isRedirecting = false

  const login = async () => {
    console.log('useAuth (SDK): login called')
    if (isRedirecting) {
      console.log('Already redirecting to login, skipping...')
      return
    }

    if (window.location.search.includes('code=') || window.location.search.includes('error=')) {
      console.log('Already on Auth0 callback page, waiting for processing...')
      return
    }

    isRedirecting = true

    console.log('Redirecting to Auth0 login via SDK...')
    console.log('auth0 object keys:', Object.keys(auth0!))
    console.log('loginWithRedirect type:', typeof auth0!.loginWithRedirect)

    try {
      await auth0!.loginWithRedirect()
      console.log('loginWithRedirect promise resolved (redirect should happen)')

      setTimeout(() => {
        console.log('Checking if redirect happened...')
        // If we are still here, force a redirect
        console.warn('Redirect did not happen! Attempting manual fallback...')
        const config = useRuntimeConfig()
        const domain = config.public.auth0Domain as string
        const clientId = config.public.auth0ClientId as string
        const audience = config.public.auth0Audience as string

        const redirectUri = encodeURIComponent(window.location.origin)
        const audienceParam = audience ? `&audience=${encodeURIComponent(audience)}` : ''
        const authUrl = `https://${domain}/authorize?client_id=${clientId}&response_type=code&redirect_uri=${redirectUri}&scope=openid profile email${audienceParam}`

        console.log('Manual fallback URL:', authUrl)
        window.location.href = authUrl
      }, 1000)
    } catch (err) {
      console.error('Login failed:', err)
      isRedirecting = false
    }
  }

  const logout = () => {
    console.log('useAuth (SDK): logout called')
    auth0!.logout({
      logoutParams: {
        returnTo: window.location.origin
      }
    })
  }

  const getToken = async (): Promise<string | null> => {
    try {
      const config = useRuntimeConfig()
      const audience = config.public.auth0Audience as string

      const options: any = {}
      if (audience) {
        options.authorizationParams = {
          audience
        }
      }

      return await auth0!.getAccessTokenSilently(options) as unknown as string
    } catch (error) {
      console.error('Failed to get access token:', error)
      return null
    }
  }

  return {
    user: computed(() => auth0!.user.value),
    isAuthenticated: computed(() => auth0!.isAuthenticated.value),
    isLoading: computed(() => auth0!.isLoading.value),
    error: computed(() => auth0!.error.value),
    login,
    logout,
    getToken
  }
}
