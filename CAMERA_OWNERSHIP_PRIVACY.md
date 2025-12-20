# Camera Ownership and Privacy Feature

## Overview
This document describes the camera/location ownership and privacy control system implemented in RehPublic.

## Features Implemented

### 1. Database Changes

**Migration: `003_add_location_ownership.sql`**
- Added `owner_id` column to `locations` table (foreign key to `users.id`)
- Added `is_public` column to `locations` table (boolean, default TRUE)
- Added indexes on both columns for efficient querying

### 2. Backend Changes

#### Location Model (`location_models.py`)
- Added `owner_id` field with relationship to User model
- Added `is_public` field to control visibility
- Added `owner` relationship for easy access to owner information

#### Location Repository (`location_repository.py`)
- Updated `create()` to accept `owner_id` and `is_public` parameters
- Updated `update()` to allow changing `is_public` status

#### Location Schemas (`locations_schemas.py`)
- Added `is_public` field to `LocationCreate` schema (default: True)
- Added `is_public` field to `LocationUpdate` schema
- Added `owner_id`, `is_public`, and `is_owner` fields to response schemas (`LocationResponse`, `LocationWithImagesResponse`)

#### Location Controller (`locations_controller.py`)
**Create Location:**
- Automatically sets `owner_id` to authenticated user
- Respects `is_public` setting from request

**Get Location:**
- Returns 404 for private locations not owned by requesting user
- Includes ownership information in response

**Update Location:**
- Checks ownership before allowing updates
- Returns 403 if user is not the owner
- Allows owner to change privacy settings

**Delete Location:**
- Checks ownership before allowing deletion
- Returns 403 if user is not the owner

**List Locations:**
- Filters locations to show only:
  - Public locations (visible to everyone)
  - Private locations owned by the requesting user

#### Location Service (`locations_service.py`)
- Updated `get_spottings_by_location()` to filter locations by privacy
- Includes `is_owner` flag in location responses

#### Image Pull Sources (`image_pull_controller.py`)
- Added ownership check when creating image pull sources
- Only location owners can create integrations for their locations
- Modified list endpoint to only show user's own sources
- Added `get_by_user_id()` method to repository

### 3. Frontend Changes

#### Camera Index Page (`/camera/index.vue`)
**Location List:**
- Shows "Yours" badge for locations owned by the user
- Shows "Private" indicator for private locations (shouldn't appear since private locations are filtered)
- Added privacy toggle checkbox in create camera modal

**Create Camera Modal:**
- Added "Make this camera public" checkbox
- Default value is public (checked)
- Clear explanation of public vs private

#### Camera Detail Page (`/camera/[id].vue`)
**Privacy Toggle:**
- For camera owners: Interactive toggle to switch between public/private
- Shows current status with icon (🌍 for public, 🔒 for private)
- Immediately updates privacy setting on server
- For non-owners: Read-only indicator if viewing a private camera

**Edit/Delete Buttons:**
- Edit button only visible to camera owners
- Delete button only visible to camera owners
- Delete modal requires typing the camera name to confirm
- Warns about deletion of all images and detections

**Integration Tab:**
- Only accessible to camera owners (verified on backend)
- Integration management respects ownership

## User Experience

### Camera Owner
1. **Creating a camera:**
   - Can choose to make it public or private during creation
   - Default is public for easy sharing

2. **Managing cameras:**
   - Can edit location details (name, description, coordinates, privacy)
   - Can delete cameras with confirmation
   - Can toggle privacy at any time
   - Can add image pull source integrations

3. **Viewing:**
   - Sees "Yours" badge on owned cameras in list
   - Has full access to all camera data and settings

### Non-Owner Users
1. **Public cameras:**
   - Can view all details and images
   - Cannot edit or delete
   - Cannot see edit/delete buttons
   - Cannot modify integrations

2. **Private cameras:**
   - Cannot see them in camera list
   - Get 404 error if trying to access directly
   - Cannot view any data

## API Changes Summary

### New/Modified Endpoints

**POST /locations**
- Now accepts `is_public` field (optional, default: true)
- Automatically sets `owner_id` to authenticated user

**PATCH /locations/{location_id}**
- Requires ownership to update
- Can update `is_public` field
- Returns 403 if not owner

**DELETE /locations/{location_id}**
- Requires ownership to delete
- Returns 403 if not owner

**GET /locations**
- Filters by privacy (only shows public + user's private)

**GET /locations/{location_id}**
- Returns 404 for private locations if not owner

**POST /image-pull-sources**
- Requires location ownership
- Returns 403 if user doesn't own the location

**GET /image-pull-sources**
- Only returns user's own sources

## Database Migration

To apply the migration:
```bash
cd backend
./run_migration.sh 003_add_location_ownership.sql
```

## Security Considerations

1. **Authorization:**
   - All ownership checks happen on the backend
   - Frontend hides buttons but backend enforces permissions
   - 403 errors for unauthorized actions, 404 for privacy violations

2. **Privacy:**
   - Private locations are truly private - not visible in lists or accessible by URL
   - Image pull sources are tied to user ownership
   - Only owners can modify privacy settings

3. **Data Integrity:**
   - Existing locations have NULL `owner_id` (legacy data)
   - New locations always have an owner
   - CASCADE delete on user removes their locations

## Testing Recommendations

1. Create cameras as different users
2. Try to edit/delete other users' cameras (should fail)
3. Toggle privacy and verify visibility
4. Create integrations on owned vs non-owned locations
5. Verify legacy locations (without owner_id) still work

## Future Enhancements

Potential improvements:
- Share cameras with specific users
- Camera groups/organizations
- Transfer ownership
- View-only sharing links
- Audit log for privacy changes
