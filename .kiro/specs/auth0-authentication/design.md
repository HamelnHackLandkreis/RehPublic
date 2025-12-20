# Design Document

## Overview

This design document specifies the integration of Auth0 authentication into the RehPublic wildlife monitoring platform. The system will authenticate users via JWT tokens, associate uploaded images with user accounts, and provide privacy controls for image visibility. The design maintains the existing location-sharing model while adding user-specific ownership and privacy features.

The authentication flow follows a standard OAuth2/OIDC pattern where the frontend redirects unauthenticated users to Auth0, receives JWT tokens upon successful authentication, and includes these tokens in API requests. The backend validates tokens via middleware and extracts user identity for authorization decisions.

## Architecture

### High-Level Architecture

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Browser   │────────▶│   Auth0     │────────▶│   Backend   │
│  (Frontend) │◀────────│   Service   │◀────────│   (FastAPI) │
└─────────────┘         └─────────────┘         └─────────────┘
      │                                                 │
      │                                                 │
      ▼                                                 ▼
┌─────────────┐                                 ┌─────────────┐
│   Nuxt.js   │                                 │ PostgreSQL  │
│   Runtime   │                                 │  Database   │
└─────────────┘                                 └─────────────┘
```

### Authentication Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Auth0
    participant Backend
    participant Database

    User->>Frontend: Access protected page
    Frontend->>Frontend: Check auth state
    alt Not authenticated
        Frontend->>Auth0: Redirect to login
        Auth0->>User: Show login page
        User->>Auth0: Enter credentials
        Auth0->>Frontend: Redirect with JWT token
        Frontend->>Frontend: Store token
    end
    Frontend->>Backend: API request + Bearer token
    Backend->>Backend: Validate JWT signature
    Backend->>Backend: Extract user_id
    Backend->>Database: Query with user context
    Database->>Backend: Return filtered data
    Backend->>Frontend: Response
    Frontend->>User: Display content
```

### Component Layers

1. **Frontend Layer** (Nuxt.js)
   - Auth0 SDK integration for login/logout
   - Token storage and management
   - Protected route guards
   - API client with token injection

2. **Middleware Layer** (FastAPI)
   - JWT validation and decoding
   - User identity extraction
   - Request state enrichment
   - Error handling for auth failures

3. **Service Layer** (Business Logic)
   - User-aware data filtering
   - Privacy rule enforcement
   - Ownership validation

4. **Data Layer** (PostgreSQL)
   - User table for identity and settings
   - Image-user associations
   - Privacy setting storage

## Components and Interfaces

### Backend Components

#### 1. Authentication Middleware

**Purpose**: Validate JWT tokens and extract user identity for all protected endpoints.

**Location**: `backend/src/api/middleware/auth.py`

**Interface**:
```python
async def authentication_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """
    Middleware to extract and validate user info from Authorization header.

    Expects: 'Authorization: Bearer <jwt_token>'
    Sets: request.state.user (JWTUser object)
    Raises: HTTPException (401/403) on auth failure
    """
```

**Dependencies**:
- `jwt` library for token decoding
- Auth0 public key from environment
- Auth0 audience from environment

**Behavior**:
- Skip authentication for `/health` endpoint
- Skip authentication for OPTIONS requests (CORS)
- Extract Bearer token from Authorization header
- Decode and validate JWT using Auth0 public key
- Attach decoded user to `request.state.user`
- Return 401 if token missing, 403 if invalid

#### 2. User Model

**Purpose**: Store user identity and privacy preferences.

**Location**: `backend/src/api/users/user_models.py`

**Schema**:
```python
class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)  # Auth0 user ID
    email = Column(String, nullable=True, index=True)
    name = Column(String, nullable=True)
    privacy_public = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    images = relationship("Image", back_populates="user")
```

#### 3. JWT User Model

**Purpose**: Pydantic model for validated JWT payload.

**Location**: `backend/src/api/models.py`

**Schema**:
```python
class JWTUser(BaseModel):
    sub: str  # Auth0 user ID (subject)
    email: Optional[str] = None
    name: Optional[str] = None
    aud: str  # Audience
    iss: str  # Issuer
    exp: int  # Expiration timestamp
```

#### 4. Updated Image Model

**Purpose**: Associate images with users and support privacy filtering.

**Location**: `backend/src/api/images/image_models.py`

**Changes**:
```python
class Image(Base):
    __tablename__ = "images"

    # ... existing fields ...
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)

    # Relationships
    user = relationship("User", back_populates="images")
```

#### 5. User Service

**Purpose**: Manage user records and privacy settings.

**Location**: `backend/src/api/users/user_service.py`

**Interface**:
```python
class UserService:
    def get_or_create_user(self, user_id: str, email: str, name: str) -> User:
        """Get existing user or create new one from JWT data."""

    def update_privacy_setting(self, user_id: str, privacy_public: bool) -> User:
        """Update user's privacy preference."""

    def get_user(self, user_id: str) -> Optional[User]:
        """Retrieve user by ID."""
```

#### 6. Updated Image Service

**Purpose**: Filter images based on ownership and privacy settings.

**Location**: `backend/src/api/images/image_service.py`

**Changes**:
```python
class ImageService:
    def create_image(
        self,
        location_id: str,
        base64_data: str,
        user_id: str  # NEW: Required user ID
    ) -> Image:
        """Create image associated with user."""

    def get_visible_images(
        self,
        requesting_user_id: str,
        filters: dict
    ) -> List[Image]:
        """
        Get images visible to requesting user.
        Returns: Images where (user.privacy_public = true) OR (image.user_id = requesting_user_id)
        """
```

#### 7. User Settings Controller

**Purpose**: API endpoints for user settings management.

**Location**: `backend/src/api/users/user_controller.py`

**Endpoints**:
```python
@router.get("/users/me")
async def get_current_user(request: Request) -> UserResponse:
    """Get current authenticated user's profile."""

@router.patch("/users/me/privacy")
async def update_privacy_setting(
    request: Request,
    privacy_update: PrivacyUpdateRequest
) -> UserResponse:
    """Update current user's privacy setting."""
```

### Frontend Components

#### 1. Auth0 Plugin

**Purpose**: Initialize Auth0 SDK and provide authentication methods.

**Location**: `frontend/plugins/auth0.ts`

**Interface**:
```typescript
export default defineNuxtPlugin(() => {
  const auth0Client = createAuth0Client({
    domain: config.auth0Domain,
    clientId: config.auth0ClientId,
    authorizationParams: {
      redirect_uri: config.auth0RedirectUri,
      audience: config.auth0Audience
    }
  })

  return {
    provide: {
      auth: {
        loginWithRedirect: () => auth0Client.loginWithRedirect(),
        logout: () => auth0Client.logout(),
        getAccessToken: () => auth0Client.getTokenSilently(),
        getUser: () => auth0Client.getUser(),
        isAuthenticated: () => auth0Client.isAuthenticated()
      }
    }
  }
})
```

#### 2. Auth Composable

**Purpose**: Provide reactive authentication state and methods.

**Location**: `frontend/app/composables/useAuth.ts`

**Interface**:
```typescript
export const useAuth = () => {
  const { $auth } = useNuxtApp()
  const user = ref(null)
  const isAuthenticated = ref(false)
  const token = ref<string | null>(null)

  const login = async () => {
    await $auth.loginWithRedirect()
  }

  const logout = async () => {
    await $auth.logout({ returnTo: window.location.origin })
  }

  const getToken = async (): Promise<string> => {
    if (!token.value) {
      token.value = await $auth.getAccessToken()
    }
    return token.value
  }

  return { user, isAuthenticated, login, logout, getToken }
}
```

#### 3. API Client with Auth

**Purpose**: Inject authentication tokens into API requests.

**Location**: `frontend/app/composables/useAuthenticatedApi.ts`

**Interface**:
```typescript
export const useAuthenticatedApi = () => {
  const { getToken } = useAuth()
  const apiUrl = useApiUrl()

  const fetchWithAuth = async (endpoint: string, options: RequestInit = {}) => {
    const token = await getToken()
    const headers = {
      ...options.headers,
      'Authorization': `Bearer ${token}`
    }

    const response = await fetch(`${apiUrl}${endpoint}`, {
      ...options,
      headers
    })

    if (response.status === 401) {
      // Token expired, redirect to login
      const { login } = useAuth()
      await login()
    }

    return response
  }

  return { fetchWithAuth }
}
```

#### 4. Auth Guard Middleware

**Purpose**: Protect routes requiring authentication.

**Location**: `frontend/middleware/auth.ts`

**Interface**:
```typescript
export default defineNuxtRouteMiddleware(async (to, from) => {
  const { isAuthenticated, login } = useAuth()

  if (!isAuthenticated.value) {
    await login()
    return abortNavigation()
  }
})
```

#### 5. User Settings Page

**Purpose**: UI for managing privacy preferences.

**Location**: `frontend/app/pages/settings.vue`

**Features**:
- Display current privacy setting
- Toggle for public/private image visibility
- Save button with API integration
- Success/error feedback

#### 6. Updated Upload Page

**Purpose**: Associate uploads with authenticated user.

**Location**: `frontend/app/pages/upload.vue`

**Changes**:
- Use `useAuthenticatedApi` for uploads
- Display user's current privacy setting
- Show privacy toggle near upload area

## Data Models

### User Table

```sql
CREATE TABLE users (
    id VARCHAR PRIMARY KEY,  -- Auth0 user ID (sub claim)
    email VARCHAR,
    name VARCHAR,
    privacy_public BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_users_email (email),
    INDEX idx_users_privacy (privacy_public)
);
```

### Updated Images Table

```sql
ALTER TABLE images
ADD COLUMN user_id VARCHAR REFERENCES users(id),
ADD INDEX idx_images_user_id (user_id);
```

### Database Migration Script

**Location**: `backend/migrations/001_add_auth0_support.sql`

```sql
-- Migration: Add Auth0 authentication support
-- Version: 001
-- Date: 2025-01-XX

BEGIN;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR PRIMARY KEY,
    email VARCHAR,
    name VARCHAR,
    privacy_public BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_privacy ON users(privacy_public);

-- Add user_id to images table
ALTER TABLE images
ADD COLUMN IF NOT EXISTS user_id VARCHAR REFERENCES users(id);

CREATE INDEX IF NOT EXISTS idx_images_user_id ON images(user_id);

COMMIT;

-- Rollback script (run separately if needed):
-- BEGIN;
-- DROP INDEX IF EXISTS idx_images_user_id;
-- ALTER TABLE images DROP COLUMN IF EXISTS user_id;
-- DROP INDEX IF EXISTS idx_users_privacy;
-- DROP INDEX IF EXISTS idx_users_email;
-- DROP TABLE IF EXISTS users;
-- COMMIT;
```

## Data Models

### Configuration Model

**Environment Variables**:

Backend (`backend/.env`):
```
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_AUDIENCE=https://api.rehpublic.com
AUTH0_PUBLIC_KEY=-----BEGIN CERTIFICATE-----...
DATABASE_URL=postgresql://user:pass@host:5432/rehpublic
```

Frontend (`frontend/.env`):
```
NUXT_PUBLIC_AUTH0_DOMAIN=your-tenant.auth0.com
NUXT_PUBLIC_AUTH0_CLIENT_ID=your-client-id
NUXT_PUBLIC_AUTH0_AUDIENCE=https://api.rehpublic.com
NUXT_PUBLIC_API_URL=http://localhost:8000
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Authorization header inclusion

*For any* authenticated API request from the frontend, the request SHALL include the JWT bearer token in the Authorization header.
**Validates: Requirements 1.3**

### Property 2: User ID extraction from valid JWT

*For any* valid JWT token received by the backend, the middleware SHALL correctly extract the user ID from the token and attach it to the request state.
**Validates: Requirements 1.4**

### Property 3: Invalid JWT rejection

*For any* invalid or malformed JWT token (expired, wrong signature, malformed), the backend SHALL return HTTP 401 or 403 status.
**Validates: Requirements 1.5**

### Property 4: JWT decoding with Auth0 public key

*For any* JWT token in the Authorization header, the middleware SHALL decode it using the configured Auth0 public key.
**Validates: Requirements 2.4**

### Property 5: Valid JWT user attachment

*For any* valid and non-expired JWT, the middleware SHALL attach the decoded user information to request.state.user.
**Validates: Requirements 2.5**

### Property 6: Invalid JWT forbidden response

*For any* JWT with invalid signature or expired timestamp, the middleware SHALL return HTTP 403 Forbidden status.
**Validates: Requirements 2.6**

### Property 7: Image-user association

*For any* image upload, the backend SHALL store the user ID from the authenticated request with the image record.
**Validates: Requirements 3.1**

### Property 8: Non-null user ID invariant

*For any* newly stored image, the image record SHALL contain a non-null user_id field.
**Validates: Requirements 3.2**

### Property 9: User image filtering

*For any* user querying their images, the backend SHALL return only images where the user_id matches the authenticated user.
**Validates: Requirements 3.4**

### Property 10: Location accessibility

*For any* authenticated user creating a location, all other authenticated users SHALL be able to access that location.
**Validates: Requirements 4.2**

### Property 11: Universal location upload access

*For any* authenticated user and any location, the user SHALL be able to upload images to that location regardless of who created it.
**Validates: Requirements 4.3**

### Property 12: Unfiltered location queries

*For any* user querying locations, the backend SHALL return all locations without filtering by user ownership.
**Validates: Requirements 4.4**

### Property 13: Privacy-based image filtering

*For any* user querying images, the backend SHALL return only images where (owner.privacy_public = true) OR (image.user_id = requesting_user_id).
**Validates: Requirements 5.4**

### Property 14: Privacy update authorization

*For any* privacy setting update request, the backend SHALL only allow the update if the requesting user ID matches the user being updated.
**Validates: Requirements 6.3**

### Property 15: Successful privacy update response

*For any* valid privacy setting update, the backend SHALL return HTTP 200 status with the updated setting value.
**Validates: Requirements 6.5**

### Property 16: Map image privacy filtering

*For any* user viewing images on the map, the frontend SHALL display only images that are public OR owned by the authenticated user.
**Validates: Requirements 7.4**

### Property 17: Location page image privacy filtering

*For any* user viewing a camera location page, the frontend SHALL filter displayed images according to privacy rules (public OR owned by user).
**Validates: Requirements 7.5**

### Property 18: Migration idempotency

*For any* number of executions of the migration script, running it multiple times SHALL not fail or corrupt existing data.
**Validates: Requirements 8.6**

### Property 19: JWT validation uses configured public key

*For any* JWT validation, the backend SHALL use the Auth0 public key from environment configuration.
**Validates: Requirements 9.2**

### Property 20: JWT validation uses configured audience

*For any* JWT validation, the backend SHALL verify the token audience matches the configured Auth0 audience from environment variables.
**Validates: Requirements 9.3**

## Error Handling

### Authentication Errors

1. **Missing Token (401)**
   - Scenario: Authorization header is missing
   - Response: HTTP 401 Unauthorized
   - Message: "Authentication required"
   - Frontend Action: Redirect to Auth0 login

2. **Expired Token (401)**
   - Scenario: JWT exp claim is in the past
   - Response: HTTP 401 Unauthorized
   - Message: "Token expired"
   - Frontend Action: Redirect to Auth0 login

3. **Invalid Signature (403)**
   - Scenario: JWT signature verification fails
   - Response: HTTP 403 Forbidden
   - Message: "Invalid credentials"
   - Frontend Action: Clear token, redirect to login

4. **Malformed Token (403)**
   - Scenario: JWT cannot be decoded
   - Response: HTTP 403 Forbidden
   - Message: "Invalid token format"
   - Backend Action: Log error details for debugging

5. **Wrong Audience (403)**
   - Scenario: JWT aud claim doesn't match configured audience
   - Response: HTTP 403 Forbidden
   - Message: "Invalid token audience"

### Authorization Errors

1. **Unauthorized Privacy Update (403)**
   - Scenario: User attempts to modify another user's settings
   - Response: HTTP 403 Forbidden
   - Message: "Not authorized to modify this user's settings"

### Service Errors

1. **Auth0 Unavailable**
   - Scenario: Auth0 service is down or unreachable
   - Frontend Response: Display error message
   - Message: "Authentication service temporarily unavailable. Please try again later."

2. **Missing Configuration**
   - Scenario: Required environment variables are missing
   - Backend Response: Fail to start
   - Message: "Missing required Auth0 configuration: AUTH0_DOMAIN, AUTH0_AUDIENCE, AUTH0_PUBLIC_KEY"

### Error Logging

- All authentication failures SHALL be logged with:
  - Timestamp
  - Request path
  - Error type
  - User agent (if available)
  - IP address (if available)
- Sensitive information (tokens, keys) SHALL NOT be logged
- Generic error messages SHALL be returned to clients
- Detailed error information SHALL only be logged server-side

## Testing Strategy

### Unit Testing

The implementation will include unit tests for:

1. **Middleware Components**
   - JWT decoding with valid tokens
   - JWT validation with invalid tokens
   - User extraction from JWT payload
   - Path exclusion logic (/health, OPTIONS)

2. **Service Layer**
   - User creation and retrieval
   - Privacy setting updates
   - Image filtering by privacy rules
   - Location access validation

3. **Model Validation**
   - User model field validation
   - JWT user model validation
   - Image model with user_id

4. **API Endpoints**
   - User settings retrieval
   - Privacy setting updates
   - Authorization checks

### Property-Based Testing

We will use **Hypothesis** (Python) for backend property-based testing and **fast-check** (TypeScript) for frontend property-based testing.

Property-based tests will verify:

1. **Token Validation Properties**
   - Generate random valid JWTs → verify user extraction
   - Generate random invalid JWTs → verify rejection
   - Generate random expired JWTs → verify 401 response

2. **Privacy Filtering Properties**
   - Generate random image sets with various owners and privacy settings
   - Verify filtering returns correct subset based on requesting user

3. **Authorization Properties**
   - Generate random user pairs
   - Verify users can only modify their own settings

4. **Location Access Properties**
   - Generate random users and locations
   - Verify all users can access all locations

Each property-based test will:
- Run a minimum of 100 iterations
- Be tagged with the correctness property it validates
- Use the format: `# Feature: auth0-authentication, Property X: [property text]`

### Integration Testing

Integration tests will verify:

1. **End-to-End Authentication Flow**
   - Mock Auth0 login → receive token → make authenticated request
   - Token expiration → 401 response → redirect to login

2. **Image Upload with Authentication**
   - Upload image with valid token → verify user_id stored
   - Upload image without token → verify 401 rejection

3. **Privacy Settings Flow**
   - Update privacy setting → verify database update
   - Query images → verify privacy filtering applied

4. **Migration Testing**
   - Run migration on test database
   - Verify schema changes
   - Run migration again → verify idempotency

### Frontend Testing

Frontend tests will include:

1. **Component Tests**
   - Auth guard middleware behavior
   - Settings page privacy toggle
   - Login/logout button rendering

2. **API Client Tests**
   - Token injection in requests
   - 401 response handling
   - Token refresh logic

3. **E2E Tests** (optional)
   - Full authentication flow with Auth0 test tenant
   - Image upload with authentication
   - Privacy setting changes

## Security Considerations

1. **Token Storage**
   - Store tokens in memory only (not localStorage)
   - Use httpOnly cookies if possible
   - Clear tokens on logout

2. **Token Validation**
   - Always validate signature with Auth0 public key
   - Check expiration timestamp
   - Verify audience claim

3. **HTTPS Enforcement**
   - All authentication flows must use HTTPS in production
   - Redirect HTTP to HTTPS

4. **CORS Configuration**
   - Restrict allowed origins in production
   - Allow credentials for authenticated requests

5. **Rate Limiting**
   - Implement rate limiting on authentication endpoints
   - Prevent brute force attacks

6. **Logging**
   - Never log tokens or sensitive user data
   - Log authentication failures for security monitoring
   - Implement audit trail for privacy setting changes

## Deployment Considerations

1. **Environment Configuration**
   - Use separate Auth0 tenants for dev/staging/production
   - Store secrets in secure secret management system
   - Validate all required environment variables on startup

2. **Database Migration**
   - Test migration on staging environment first
   - Backup production database before migration
   - Run migration during maintenance window
   - Verify data integrity after migration

3. **Rollback Plan**
   - Keep rollback SQL script ready
   - Document rollback procedure
   - Test rollback on staging environment

4. **Monitoring**
   - Monitor authentication success/failure rates
   - Alert on unusual authentication patterns
   - Track token validation errors

5. **Zero-Downtime Deployment**
   - Deploy backend with nullable user_id first
   - Run migration
   - Deploy frontend with authentication
   - Gradually enforce authentication requirements
