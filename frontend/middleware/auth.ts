export default defineNuxtRouteMiddleware(async (to) => {
  // Skip middleware during server-side rendering/prerendering
  // Auth will be handled on the client side
  if (import.meta.server) {
    return
  }

  const { isAuthenticated, isLoading, login } = useAuth()

  // Allow callback page to process Auth0 redirect
  if (to.path === '/callback') {
    return
  }

  // Wait for auth to initialize
  if (isLoading.value) {
    return
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated.value) {
    return login()
  }
})
