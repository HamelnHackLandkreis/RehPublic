export default defineNuxtRouteMiddleware(async (to, from) => {
  const { isAuthenticated, login } = useAuth()

  // Check if user is authenticated
  if (!isAuthenticated.value) {
    // Redirect to login
    await login()
    return abortNavigation()
  }
})
