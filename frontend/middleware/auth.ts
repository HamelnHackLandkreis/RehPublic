export default defineNuxtRouteMiddleware(async (to) => {
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
