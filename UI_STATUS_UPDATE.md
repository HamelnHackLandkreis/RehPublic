# UI Status Update - Pending Detection Badge

## Problem
Previously, images that were still being processed (e.g., from automated pulls) showed the same badge as images with no animals detected: "No detection" in gray. This was confusing for users who couldn't distinguish between:
- Images still being processed (pending)
- Images that completed processing but found no animals

## Solution
Added clear visual distinction between different image states with color-coded badges and descriptive text.

## Status Badge States

### 1. **Has Detections** (Red Badge)
```
[🔴 2 detections]
```
- **When**: Image has been processed and animals were detected
- **Color**: Red (`bg-red-500`)
- **Behavior**: Clickable, navigates to match view
- **Shows**: Count of detections

### 2. **Pending Detection** (Blue Badge - Animated)
```
[🔵 Pending detection] (pulsing)
```
- **When**: Image is still being processed
- **Conditions**:
  - `processed = false`, OR
  - `processing_status = "detecting"`, OR
  - `processing_status = "uploading"`
- **Color**: Blue (`bg-blue-500`)
- **Behavior**: Animated pulse to indicate ongoing process
- **Shows**: "Pending detection" text

### 3. **Processing Failed** (Dark Red Badge)
```
[🔴 Processing failed]
```
- **When**: Image processing encountered an error
- **Condition**: `processing_status = "failed"`
- **Color**: Dark red (`bg-red-600`)
- **Shows**: "Processing failed" text

### 4. **No Detection** (Gray Badge)
```
[⚫ No detection]
```
- **When**: Image completed processing successfully but no animals found
- **Conditions**:
  - `processed = true`, AND
  - `processing_status = "completed"`, AND
  - `detections.length = 0`
- **Color**: Gray (`bg-gray-500`)
- **Shows**: "No detection" text

## Changes Made

### Backend Changes

**File**: `backend/src/api/images/images_schemas.py`
```python
class SpottingImageResponse(BaseModel):
    """Schema for spotting image response without base64 data."""

    image_id: UUID
    location_id: UUID
    upload_timestamp: datetime
    detections: List[DetectionResponse]
    processing_status: str  # uploading, detecting, completed, failed
    processed: bool  # Added field
```

**File**: `backend/src/api/locations/locations_service.py`
```python
SpottingImageResponse(
    image_id=UUID(image.id),
    location_id=UUID(image.location_id),
    upload_timestamp=image.upload_timestamp,
    detections=detections,
    processing_status=image.processing_status or "completed",  # Added
    processed=image.processed or False,  # Added
)
```

### Frontend Changes

**File**: `frontend/app/pages/camera/[id].vue`

Updated TypeScript interface:
```typescript
interface ImageDetection {
  image_id: string
  location_id: string
  upload_timestamp: string
  processing_status?: string  // Added
  processed?: boolean          // Added
  detections: Array<{ ... }>
}
```

Updated template with conditional rendering:
```vue
<!-- Has detections -->
<div v-if="image.detections && image.detections.length > 0">
  {{ image.detections.length }} detection(s)
</div>

<!-- Processing/Pending -->
<span v-else-if="!image.processed ||
                  image.processing_status === 'detecting' ||
                  image.processing_status === 'uploading'"
      class="bg-blue-500 animate-pulse">
  Pending detection
</span>

<!-- Failed -->
<span v-else-if="image.processing_status === 'failed'"
      class="bg-red-600">
  Processing failed
</span>

<!-- No detections (completed but empty) -->
<span v-else class="bg-gray-500">
  No detection
</span>
```

## User Experience

### Automatic Polling Scenario

1. **Hour 0:00** - Celery Beat pulls new images
2. **Images appear in UI** with blue "Pending detection" badge (pulsing)
3. **Processing happens** (wildlife detection runs)
4. **After ~30 seconds** - Status updates:
   - If animals found → Red badge with count
   - If no animals → Gray "No detection" badge
   - If error → Red "Processing failed" badge

### Visual Flow

```
Upload/Pull
    ↓
[🔵 Pending detection] (animated pulse)
    ↓
Processing...
    ↓
    ├─→ [🔴 2 detections] (success with animals)
    ├─→ [⚫ No detection] (success, no animals)
    └─→ [🔴 Processing failed] (error)
```

## CSS Classes Used

- **Blue (Pending)**: `bg-blue-500 text-white animate-pulse`
- **Red (Detections)**: `bg-red-500 text-white hover:opacity-85 cursor-pointer`
- **Dark Red (Failed)**: `bg-red-600 text-white`
- **Gray (No Detection)**: `bg-gray-500 text-white`
- **Badge Base**: `px-3 py-1 rounded-full text-xs font-semibold`

## Benefits

### For Users
✅ Clear visual feedback on processing state
✅ No confusion between "still processing" vs "found nothing"
✅ Immediate visibility of failed processing
✅ Animated pulse draws attention to pending items

### For Developers
✅ Consistent with existing status fields from backend
✅ Minimal changes - reuses existing infrastructure
✅ Easy to extend with more states if needed

## Testing

### Manual Test Cases

1. **Upload new image** → Should show blue "Pending detection"
2. **Wait for processing** → Should change to appropriate final state
3. **Trigger integration test pull** → New images show blue badge
4. **Refresh page with pending images** → Badge persists correctly
5. **View old completed images** → Show correct final state

### Edge Cases Handled

- Missing `processing_status` field → Defaults to "completed"
- Missing `processed` field → Defaults to `false` (shows pending)
- Network delay → Pulse animation indicates activity
- Failed processing → Clear error state shown

## Migration Notes

- **No database migration needed** - Fields already exist in Image model
- **Backend changes are additive** - Existing API clients still work
- **Frontend gracefully handles missing fields** - Uses optional chaining (`?.`)

---

## Summary

Users can now clearly distinguish between:
- 🔵 **Images being processed** (blue, pulsing)
- 🔴 **Images with animals** (red, clickable)
- ⚫ **Processed but no animals** (gray)
- 🔴 **Processing errors** (dark red)

This eliminates confusion and provides better user experience for the automated image polling feature.
