# API URL Configuration

## Overview

The application now uses a centralized API URL configuration that can be customized via environment variables.

## Default Behavior

- **Development**: Uses `http://localhost:8000` by default
- **Production (Docker)**: Uses `http://135.181.78.114:9002` as configured in the Dockerfile

## How It Works

### 1. Composable (`app/composables/useApiUrl.ts`)

```typescript
export const useApiUrl = () => {
  const config = useRuntimeConfig()
  return config.public.apiUrl || 'http://localhost:8000'
}
```

### 2. Nuxt Configuration (`nuxt.config.ts`)

```typescript
runtimeConfig: {
  public: {
    apiUrl: process.env.NUXT_PUBLIC_API_URL || 'http://localhost:8000'
  }
}
```

### 3. Docker Build

The Dockerfile uses a build argument to set the API URL at build time:

```dockerfile
ARG NUXT_PUBLIC_API_URL=http://135.181.78.114:9002
ENV NUXT_PUBLIC_API_URL=$NUXT_PUBLIC_API_URL
```

## Usage in Components

Simply call the composable:

```typescript
const apiUrl = useApiUrl()

// Then use it in fetch calls
fetch(`${apiUrl}/locations`)
```

## Customizing the API URL

### During Development

Set the environment variable before running:

```bash
NUXT_PUBLIC_API_URL=http://your-api-url:port npm run dev
```

### During Docker Build

Override the build argument:

```bash
docker build --build-arg NUXT_PUBLIC_API_URL=http://your-api-url:port -t frontend .
```

Or in docker-compose.yml:

```yaml
services:
  nuxt-frontend:
    build:
      context: ./frontend
      args:
        - NUXT_PUBLIC_API_URL=http://your-api-url:port
```

## Files Modified

- `frontend/app/composables/useApiUrl.ts` (new)
- `frontend/nuxt.config.ts`
- `frontend/app/pages/upload.vue`
- `frontend/app/pages/match.vue`
- `frontend/app/components/WildlifeMap.vue`
- `frontend/Dockerfile`
- `docker-compose.yml`
