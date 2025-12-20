export const useAuthenticatedApi = () => {
  const { getToken, login, isAuthenticated, isLoading } = useAuth()
  const apiUrl = useApiUrl()
  let redirectTriggered = false

  const fetchWithAuth = async (endpoint: string, options: RequestInit = {}) => {
    // Skip during server-side rendering
    if (typeof window === 'undefined') {
      throw new Error('fetchWithAuth cannot be used during SSR')
    }

    if (isLoading.value) {
      await new Promise(resolve => setTimeout(resolve, 100))
      return fetchWithAuth(endpoint, options)
    }

    if (window.location.search.includes('code=') || window.location.search.includes('error=')) {
      throw new Error('Waiting for Auth0 callback to complete')
    }

    if (!isAuthenticated.value) {
      if (!redirectTriggered) {
        redirectTriggered = true
        login()
      }
      throw new Error('Authentication required - redirecting to login')
    }

    let token: string | null = null
    try {
      token = await getToken()
    } catch (error) {
      console.error('Failed to get token:', error)
      if (!redirectTriggered) {
        redirectTriggered = true
        login()
      }
      return new Response(null, { status: 401, statusText: 'Unauthorized' })
    }

    if (!token) {
      if (!redirectTriggered) {
        // Token unavailable - likely need to re-authenticate
        redirectTriggered = true
        login()
      }
      return new Response(null, { status: 401, statusText: 'Unauthorized' })
    }

    const headers = {
      ...options.headers,
      'Authorization': `Bearer ${token}`
    }

    try {
      const response = await fetch(`${apiUrl}${endpoint}`, {
        ...options,
        headers
      })

      if (response.status === 401) {
        if (!redirectTriggered) {
          redirectTriggered = true
          login()
        }
        return response
      }

      return response
    } catch (error) {
      if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
        throw error
      }
      throw error
    }
  }

  return { fetchWithAuth }
}
