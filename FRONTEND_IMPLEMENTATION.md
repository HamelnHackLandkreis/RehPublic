# Frontend Implementation - Integration Tab

## Overview

Added a new "Integration" tab to the camera detail view that allows users to configure external image sources for automated polling. This provides a user-friendly interface to set up the image pull sources that are processed by the backend Celery Beat task.

## What Was Implemented

### 1. New Tab in Camera View

**Location**: `frontend/app/pages/camera/[id].vue`

Added a third tab called "Integration" alongside the existing "Overview" and "Upload" tabs.

### 2. Integration Form

When no integration exists for the location, users see a form with:

- **Integration Name**: Friendly name for the source (e.g., "Hameln-Pyrmont Camera Feed")
- **Base URL**: URL to the image directory listing (e.g., `https://assets.hameln-pyrmont.digital/image-api/`)
- **Username**: Optional username for HTTP basic authentication
- **Password**: Optional password for HTTP basic authentication
- **Submit Button**: Creates the integration

### 3. Existing Integration Display

When an integration already exists, users see:

- **Status Badge**: Shows if integration is Active/Inactive
- **Configuration Details**:
  - Base URL
  - Authentication type
  - Last pulled filename
  - Last pull timestamp
- **Action Buttons**:
  - **Activate/Deactivate**: Toggle the integration on/off
  - **Test Pull (2 files)**: Manually trigger a pull of 2 files to test configuration
  - **Delete**: Remove the integration

### 4. Information Section

Helpful information box explaining:
- Images are pulled hourly automatically
- Each image is processed through wildlife detection
- Results appear in the Overview tab
- System tracks processed files to avoid duplicates
- Up to 10 images per hour by default

## API Integration

The frontend communicates with these backend endpoints:

```typescript
// Fetch existing integrations
GET /image-pull-sources
Response: Array of integration objects

// Create new integration
POST /image-pull-sources
Body: {
  name: string,
  location_id: string,
  base_url: string,
  auth_type: "basic" | "none",
  auth_username?: string,
  auth_password?: string,
  is_active: boolean
}

// Toggle active status
PATCH /image-pull-sources/{id}/toggle?is_active=true|false

// Test integration (manual trigger)
POST /image-pull-sources/{id}/process?max_files=2
```

## User Flow

### Creating an Integration

1. User navigates to camera detail page (e.g., `/camera/e2e440dc-12c3-48b1-bac1-e97ae99f431a`)
2. Clicks on "Integration" tab
3. Sees the form (if no integration exists)
4. Fills in:
   - Name: "My Camera Feed"
   - URL: "https://example.com/images/"
   - Username: "user"
   - Password: "pass"
5. Clicks "Create Integration"
6. System creates the integration in the database
7. User sees success message and the integration display

### Testing an Integration

1. User clicks "Test Pull (2 files)" button
2. System immediately fetches 2 new images from the source
3. Images are processed through wildlife detection
4. Success message shows number of files processed
5. After 2 seconds, the Overview tab refreshes automatically
6. User can switch to Overview to see the new images

### Managing an Integration

- **Deactivate**: Stops hourly polling but keeps configuration
- **Activate**: Resumes hourly polling
- **Delete**: Removes the integration entirely (requires confirmation)

## Features

### ✅ Real-time Feedback

- Loading states during operations
- Success messages (green)
- Error messages (red)
- Disabled buttons during loading

### ✅ Smart Form Handling

- Required fields validation
- URL validation
- Optional authentication (leave empty for public sources)
- Form reset after successful creation

### ✅ Visual Design

- Clean, modern UI matching the existing design
- Color-coded status badges (green for active)
- Responsive layout
- Clear information hierarchy

### ✅ Error Handling

- Network errors caught and displayed
- API errors shown with details
- Confirmation dialogs for destructive actions

## Code Structure

```typescript
// State Management
const existingIntegration = ref<any>(null)
const integrationLoading = ref(false)
const integrationError = ref<string | null>(null)
const integrationSuccess = ref<string | null>(null)
const integrationForm = ref({ name, baseUrl, username, password })

// Core Functions
fetchExistingIntegration()  // Load integration on mount
createIntegration()          // POST new integration
toggleIntegration()          // PATCH to activate/deactivate
testIntegration()            // POST to manually process files
deleteIntegration()          // Remove integration

// Lifecycle
onMounted(() => {
  fetchCameraData()           // Existing function
  fetchExistingIntegration()  // New function
})
```

## Example Usage

### For Hameln-Pyrmont Camera:

1. Navigate to the camera page
2. Click "Integration" tab
3. Fill in the form:
   ```
   Name: Hameln-Pyrmont Wildlife Camera
   URL: https://assets.hameln-pyrmont.digital/image-api/
   Username: mitwirker
   Password: gtdbGDfzCcUDQs2CK6FHYLq34
   ```
4. Click "Create Integration"
5. Click "Test Pull (2 files)" to verify it works
6. Images will now be pulled automatically every hour

## Benefits

### For Users

- **No Code Required**: Set up automated image pulling through UI
- **Instant Testing**: Test configuration before committing
- **Full Control**: Activate/deactivate without deletion
- **Transparency**: See last pulled file and timestamp

### For System

- **One Integration Per Location**: Prevents conflicts
- **Automatic Discovery**: Frontend finds existing integrations
- **Seamless Integration**: Uses same auth as other API calls
- **User Association**: Each integration tied to authenticated user

## Styling

Uses Tailwind CSS classes consistent with the rest of the application:

- `bg-white`, `rounded-xl`, `shadow-sm` - Card styling
- `text-blue-600`, `border-blue-500` - Active tab colors
- `bg-green-50`, `border-green-200` - Success states
- `bg-red-50`, `border-red-200` - Error states
- `bg-blue-50`, `border-blue-200` - Information boxes
- Responsive grid and flexbox layouts
- Hover states and transitions for better UX

## Future Enhancements

Potential improvements:

1. **Delete Endpoint**: Add proper DELETE method in backend
2. **Multiple Sources**: Support multiple integrations per location
3. **Schedule Customization**: Allow users to set custom polling intervals
4. **History**: Show recent pull history and results
5. **Validation**: Test URL reachability before saving
6. **Auth Preview**: Show Base64-encoded auth header for debugging
7. **Logs**: Display recent pull logs and errors

## Testing

### Manual Testing Steps:

1. **Create Integration**:
   - Fill form with valid data → Should create successfully
   - Fill form with invalid URL → Should show validation error
   - Leave username/password empty → Should create with auth_type="none"

2. **Test Pull**:
   - Click test button → Should process 2 files
   - Check Overview tab → New images should appear

3. **Toggle Status**:
   - Click Deactivate → Badge should change to Inactive
   - Click Activate → Badge should change to Active

4. **Delete**:
   - Click Delete → Confirmation dialog appears
   - Confirm → Integration removed, form reappears

5. **Persistence**:
   - Create integration → Refresh page → Integration still shown
   - Navigate away → Return to page → Integration still shown

## Files Modified

- `frontend/app/pages/camera/[id].vue`: Added Integration tab and functionality

No new files needed - all functionality added to existing camera detail page.

---

The frontend implementation is complete and ready to use! Users can now configure automated image sources directly from the camera detail page without needing to use the CLI or API directly.
