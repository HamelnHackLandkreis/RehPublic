<template>
  <button
    type="button"
    @click="login"
    class="button login"
    :disabled="isLoading"
  >
    {{ isLoading ? 'Loading...' : 'Log In' }}
  </button>
</template>

<script setup lang="ts">
const { login, isLoading } = useAuth()
</script>

<style scoped>
.button {
  padding: 0.75rem 1.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  outline: none;
  width: 100%;
}

.button:focus {
  box-shadow: 0 0 0 3px rgba(var(--color-secondary), 0.5);
}

.button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.button.login {
  background-color: var(--color-secondary);
  color: white;
}

.button.login:hover:not(:disabled) {
  background-color: var(--color-secondary-dark);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.4);
}
</style>
