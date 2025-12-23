<template>
  <button
    @click="handleLogout"
    class="button logout"
    :disabled="isLoading"
  >
    {{ isLoading ? 'Loading...' : 'Log Out' }}
  </button>
</template>

<script setup lang="ts">
import { useAuth } from '#imports'

const { logout, isLoading } = useAuth()

const handleLogout = () => {
  logout()
}
</script>

<style scoped>
.button {
  padding: 1.1rem 2.8rem;
  font-size: 1.2rem;
  font-weight: 600;
  border-radius: 10px;
  border: none;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  outline: none;
}

.button:focus {
  box-shadow: 0 0 0 4px rgba(var(--color-secondary), 0.5);
}

.button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.button.logout {
  background-color: var(--color-error);
  color: white;
}

.button.logout:hover:not(:disabled) {
  background-color: var(--color-error-dark);
  transform: translateY(-5px) scale(1.03);
  box-shadow: 0 12px 25px rgba(0, 0, 0, 0.5);
}
</style>
