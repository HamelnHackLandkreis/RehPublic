# Implementation Plan

- [x] 1. Create database migration script
  - Create SQL migration file with users table and image user_id column
  - Include indexes for performance
  - Add rollback instructions
  - Make script idempotent with IF NOT EXISTS checks
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7_

- [x] 2. Create backend user models and schemas
  - [x] 2.1 Create User SQLAlchemy model
    - Add User model with id, email, name, privacy_public fields
    - Add created_at and updated_at timestamps
    - Add relationship to images
    - _Requirements: 3.1, 5.2, 5.3_

  - [x] 2.2 Create JWTUser Pydantic model
    - Add JWTUser model with sub, email, name, aud, iss, exp fields
    - Add validation for required fields
    - _Requirements: 1.2, 1.4_

  - [x] 2.3 Update Image model with user relationship
    - Add user_id foreign key column to Image model
    - Add user relationship
    - Add index on user_id
    - _Requirements: 3.1, 3.2, 3.5_

  - [x] 2.4 Create user API schemas
    - Create UserResponse schema
    - Create PrivacyUpdateRequest schema
    - _Requirements: 6.1, 6.2, 6.5_

- [x] 3. Implement authentication middleware
  - [x] 3.1 Create authentication middleware module
    - Create middleware/auth.py file
    - Implement JWT extraction from Authorization header
    - Implement JWT decoding with Auth0 public key
    - Attach decoded user to request.state.user
    - Skip authentication for /health endpoint
    - Skip authentication for OPTIONS requests
    - _Requirements: 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_

  - [x] 3.2 Add configuration for Auth0
    - Read AUTH0_DOMAIN from environment
    - Read AUTH0_AUDIENCE from environment
    - Read AUTH0_PUBLIC_KEY from environment
    - Validate required configuration on startup
    - _Requirements: 9.1, 9.2, 9.3, 9.5_

  - [x] 3.3 Register middleware in FastAPI app
    - Add middleware to main.py
    - Ensure middleware runs before endpoint handlers
    - _Requirements: 2.1_

  - [ ]* 3.4 Write property test for JWT validation
    - **Property 2: User ID extraction from valid JWT**
    - **Property 3: Invalid JWT rejection**
    - **Validates: Requirements 1.4, 1.5**

  - [ ]* 3.5 Write property test for middleware behavior
    - **Property 4: JWT decoding with Auth0 public key**
    - **Property 5: Valid JWT user attachment**
    - **Property 6: Invalid JWT forbidden response**
    - **Validates: Requirements 2.4, 2.5, 2.6**

- [x] 4. Implement user service and repository
  - [x] 4.1 Create user repository
    - Implement get_user method
    - Implement create_user method
    - Implement update_user method
    - Implement get_or_create_user method
    - _Requirements: 5.1, 6.3_

  - [x] 4.2 Create user service
    - Implement get_or_create_user business logic
    - Implement update_privacy_setting with authorization check
    - Implement get_user method
    - _Requirements: 5.1, 6.3, 6.4_

  - [ ]* 4.3 Write property test for privacy update authorization
    - **Property 14: Privacy update authorization**
    - **Validates: Requirements 6.3**

- [x] 5. Update image service for user association and privacy
  - [x] 5.1 Update image creation to require user_id
    - Modify create_image to accept user_id parameter
    - Ensure user_id is stored with image
    - Validate user_id is not null
    - _Requirements: 3.1, 3.2_

  - [x] 5.2 Implement privacy-aware image filtering
    - Add get_visible_images method
    - Filter by (privacy_public = true OR user_id = requesting_user)
    - Apply privacy filter to all image queries
    - _Requirements: 5.4, 7.4, 7.5_

  - [x] 5.3 Update image queries to use privacy filtering
    - Update get_images_by_location to use privacy filter
    - Update get_images_by_user to use privacy filter
    - Update map image queries to use privacy filter
    - _Requirements: 5.4, 7.4, 7.5_

  - [ ]* 5.4 Write property test for image-user association
    - **Property 7: Image-user association**
    - **Property 8: Non-null user ID invariant**
    - **Validates: Requirements 3.1, 3.2**

  - [ ]* 5.5 Write property test for privacy filtering
    - **Property 13: Privacy-based image filtering**
    - **Validates: Requirements 5.4**

- [x] 6. Update image upload endpoints
  - [x] 6.1 Update image upload endpoint to extract user from request
    - Get user_id from request.state.user
    - Pass user_id to image service
    - Return 401 if user not authenticated
    - _Requirements: 3.1, 3.3_

  - [x] 6.2 Update image query endpoints with privacy filtering
    - Update GET /images endpoint
    - Update GET /locations/{id}/images endpoint
    - Pass requesting user_id to service layer
    - _Requirements: 5.4, 7.4, 7.5_

- [x] 7. Implement user settings endpoints
  - [x] 7.1 Create user controller module
    - Create users/user_controller.py file
    - Add router for user endpoints
    - _Requirements: 6.1, 6.2_

  - [x] 7.2 Implement GET /users/me endpoint
    - Extract user from request.state.user
    - Return user profile with privacy setting
    - _Requirements: 6.1_

  - [x] 7.3 Implement PATCH /users/me/privacy endpoint
    - Extract user from request.state.user
    - Validate user can only update own settings
    - Call user service to update privacy setting
    - Return updated user profile
    - _Requirements: 6.2, 6.3, 6.4, 6.5_

  - [x] 7.4 Register user router in main.py
    - Add user router to FastAPI app
    - _Requirements: 6.1, 6.2_

  - [ ]* 7.5 Write property test for privacy update response
    - **Property 15: Successful privacy update response**
    - **Validates: Requirements 6.5**

- [x] 8. Verify location sharing remains unchanged
  - [x] 8.1 Verify Location model has no user_id field
    - Check Location model definition
    - Ensure no user ownership added
    - _Requirements: 4.1_

  - [x] 8.2 Verify location endpoints allow universal access
    - Test location creation by any user
    - Test location queries return all locations
    - Test image upload to any location
    - _Requirements: 4.2, 4.3, 4.4_

  - [ ]* 8.3 Write property test for location accessibility
    - **Property 10: Location accessibility**
    - **Property 11: Universal location upload access**
    - **Property 12: Unfiltered location queries**
    - **Validates: Requirements 4.2, 4.3, 4.4**

- [x] 9. Checkpoint - Ensure all backend tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Install and configure Auth0 SDK in frontend
  - [x] 10.1 Install Auth0 SPA SDK
    - Add @auth0/auth0-spa-js package
    - _Requirements: 1.1, 1.2_

  - [x] 10.2 Create Auth0 plugin
    - Create plugins/auth0.ts
    - Initialize Auth0 client with configuration
    - Provide auth methods (login, logout, getToken, getUser)
    - Read configuration from environment variables
    - _Requirements: 1.1, 1.2, 9.4_

  - [x] 10.3 Add Auth0 configuration to nuxt.config.ts
    - Add AUTH0_DOMAIN to runtimeConfig
    - Add AUTH0_CLIENT_ID to runtimeConfig
    - Add AUTH0_AUDIENCE to runtimeConfig
    - _Requirements: 9.4_

- [x] 11. Create frontend authentication composables
  - [x] 11.1 Create useAuth composable
    - Implement reactive auth state
    - Implement login method
    - Implement logout method
    - Implement getToken method
    - Implement getUser method
    - _Requirements: 1.1, 1.2, 1.3_

  - [x] 11.2 Create useAuthenticatedApi composable
    - Implement fetchWithAuth method
    - Inject Authorization header with token
    - Handle 401 responses with redirect to login
    - _Requirements: 1.3, 10.3_

  - [ ]* 11.3 Write property test for authorization header inclusion
    - **Property 1: Authorization header inclusion**
    - **Validates: Requirements 1.3**

- [x] 12. Create authentication middleware and guards
  - [x] 12.1 Create auth route middleware
    - Create middleware/auth.ts
    - Check authentication state
    - Redirect to login if not authenticated
    - _Requirements: 1.1, 7.1_

  - [x] 12.2 Apply auth middleware to protected routes
    - Add middleware to upload page
    - Add middleware to settings page
    - _Requirements: 1.1, 7.1_

- [x] 13. Create user settings page
  - [x] 13.1 Create settings page component
    - Create pages/settings.vue
    - Fetch current user data
    - Display privacy setting toggle
    - Implement save functionality
    - Show success/error feedback
    - _Requirements: 6.1, 6.2, 7.3_

  - [x] 13.2 Add navigation to settings page
    - Add settings link to navigation menu
    - Show only when authenticated
    - _Requirements: 6.1_

- [x] 14. Update upload page with authentication
  - [x] 14.1 Update upload page to use authenticated API
    - Replace fetch with useAuthenticatedApi
    - Pass Authorization header in upload requests
    - _Requirements: 1.3, 3.1_

  - [x] 14.2 Display user's privacy setting on upload page
    - Fetch current user's privacy setting
    - Display privacy toggle or indicator
    - Link to settings page for changes
    - _Requirements: 7.3_

- [x] 15. Update map and location pages with privacy filtering
  - [x] 15.1 Update map page to use authenticated API
    - Use useAuthenticatedApi for image queries
    - Display only visible images based on privacy
    - _Requirements: 7.4_

  - [x] 15.2 Update camera location page with privacy filtering
    - Use useAuthenticatedApi for location image queries
    - Filter images by privacy rules
    - _Requirements: 7.5_

  - [ ]* 15.3 Write property test for frontend image filtering
    - **Property 16: Map image privacy filtering**
    - **Property 17: Location page image privacy filtering**
    - **Validates: Requirements 7.4, 7.5**

- [x] 16. Add authentication UI components
  - [x] 16.1 Create login/logout button component
    - Show login button when not authenticated
    - Show user profile and logout when authenticated
    - _Requirements: 7.1, 7.2_

  - [x] 16.2 Add authentication UI to navigation
    - Add login/logout button to header
    - Display user name when authenticated
    - _Requirements: 7.1, 7.2_

- [x] 17. Implement error handling
  - [x] 17.1 Add backend error handling for authentication
    - Return 401 for missing tokens with clear message
    - Return 403 for invalid tokens with clear message
    - Return 401 for expired tokens with clear message
    - Log authentication errors
    - _Requirements: 10.1, 10.2, 10.5_

  - [x] 17.2 Add frontend error handling
    - Detect 401 responses and redirect to login
    - Display error message for Auth0 unavailability
    - Handle token refresh failures
    - _Requirements: 10.3, 10.4_

- [x] 18. Update environment configuration files
  - [x] 18.1 Create backend .env.example
    - Add AUTH0_DOMAIN example
    - Add AUTH0_AUDIENCE example
    - Add AUTH0_PUBLIC_KEY example
    - _Requirements: 9.1, 9.2, 9.3_

  - [x] 18.2 Create frontend .env.example
    - Add NUXT_PUBLIC_AUTH0_DOMAIN example
    - Add NUXT_PUBLIC_AUTH0_CLIENT_ID example
    - Add NUXT_PUBLIC_AUTH0_AUDIENCE example
    - _Requirements: 9.4_

  - [x] 18.3 Update docker-compose.yml with environment variables
    - Add Auth0 environment variables to backend service
    - Add Auth0 environment variables to frontend service
    - _Requirements: 9.1, 9.4_

- [x] 19. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ]* 20. Write property test for migration idempotency
  - **Property 18: Migration idempotency**
  - **Validates: Requirements 8.6**

- [ ]* 21. Write property test for JWT configuration usage
  - **Property 19: JWT validation uses configured public key**
  - **Property 20: JWT validation uses configured audience**
  - **Validates: Requirements 9.2, 9.3**
