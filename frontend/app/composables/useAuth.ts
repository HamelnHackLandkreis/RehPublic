import { useAuth0 } from '@auth0/auth0-vue'

export const useAuth = () => {
  if (typeof window === 'undefined') {
    return {
      user: computed(() => null),
      isAuthenticated: computed(() => false),
      isLoading: computed(() => true),
      error: computed(() => null),
      login: () => { },
      logout: () => { },
      getToken: async (): Promise<string | null> => null
    }
  }

  const auth0 = useAuth0()

  const login = async () => {
    const config = useRuntimeConfig()
    await auth0.loginWithRedirect({
      authorizationParams: {
        redirect_uri: window.location.origin + '/callback',
        audience: config.public.auth0Audience as string
      }
    })
  }

  const logout = () => {
    auth0.logout({
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

      return await auth0.getAccessTokenSilently(options) as unknown as string
    } catch (error) {
      console.error('Failed to get access token:', error)
      return null
    }
  }

  return {
    user: computed(() => auth0.user.value),
    isAuthenticated: computed(() => auth0.isAuthenticated.value),
    isLoading: computed(() => auth0.isLoading.value),
    error: computed(() => auth0.error.value),
    login,
    logout,
    getToken
  }
}
