# Image Status Badges - Visual Guide

## Badge States Overview

```
┌─────────────────────────────────────────────────────────────┐
│ Image Card                                                  │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │                                                         │ │
│ │              [Image Thumbnail]                          │ │
│ │                                                         │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ 12/20/2025, 11:00:00 AM              [STATUS BADGE]       │
└─────────────────────────────────────────────────────────────┘
```

## 1. Pending Detection (Blue - Animated)

```
┌──────────────────────────────┐
│  🔵 Pending detection       │  ← Pulsing animation
└──────────────────────────────┘
   Blue background (#3B82F6)
   White text
   Appears when:
   - processed = false
   - OR status = "detecting"
   - OR status = "uploading"
```

**When You'll See This:**
- Immediately after uploading an image
- When automated pull brings in new images
- While wildlife detection AI is analyzing

**What It Means:**
- Image is currently being processed
- Check back in 30-60 seconds for results

---

## 2. Has Detections (Red - Clickable)

```
┌──────────────────────────────┐
│  🔴 2 detections           │  ← Clickable/Hoverable
└──────────────────────────────┘
   Red background (#EF4444)
   White text
   Clickable → navigates to match view
   Shows count of detected animals
```

**When You'll See This:**
- After processing completes successfully
- One or more animals were detected

**What It Means:**
- Wildlife AI found animals in the image
- Click to view details and bounding boxes

---

## 3. No Detection (Gray)

```
┌──────────────────────────────┐
│  ⚫ No detection            │
└──────────────────────────────┘
   Gray background (#6B7280)
   White text
   Static (no animation)
```

**When You'll See This:**
- After processing completes successfully
- No animals were detected in the image

**What It Means:**
- Processing finished
- Image was clear/valid but no wildlife present
- This is a normal, expected state

---

## 4. Processing Failed (Dark Red)

```
┌──────────────────────────────┐
│  🔴 Processing failed       │
└──────────────────────────────┘
   Dark red background (#DC2626)
   White text
   Static
```

**When You'll See This:**
- After processing encountered an error
- Image couldn't be analyzed

**What It Means:**
- Something went wrong during processing
- Check logs for details
- Image may be corrupted or unsupported format

---

## State Flow Diagram

```
        ╔═══════════════════════╗
        ║   Image Uploaded /    ║
        ║   Pulled from Source  ║
        ╚═══════════════════════╝
                    │
                    ▼
        ┌───────────────────────┐
        │  🔵 Pending detection  │ ← BLUE (pulsing)
        │   (30-60 seconds)      │
        └───────────────────────┘
                    │
          ┌─────────┴─────────┐
          │                   │
          ▼                   ▼
    ┌─────────┐         ┌──────────┐
    │ Success │         │  Error   │
    └────┬────┘         └────┬─────┘
         │                   │
    ┌────┴────┐              ▼
    │         │    ┌──────────────────────┐
    ▼         ▼    │ 🔴 Processing failed │ ← DARK RED
┌────────┐ ┌──────┐└──────────────────────┘
│Animals?│ │ None │
└───┬────┘ └──┬───┘
    │         │
    ▼         ▼
┌─────────┐ ┌───────────────┐
│🔴 2     │ │⚫ No detection│
│detections│ └───────────────┘
└─────────┘   GRAY (static)
RED (clickable)
```

---

## Color Palette

| Status           | Background | Text  | Hex Code |
|------------------|------------|-------|----------|
| Pending          | Blue       | White | #3B82F6  |
| Has Detections   | Red        | White | #EF4444  |
| No Detection     | Gray       | White | #6B7280  |
| Failed           | Dark Red   | White | #DC2626  |

---

## Animation Details

### Pending Detection Pulse

```css
.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: .5;
  }
}
```

The blue "Pending detection" badge pulses to indicate ongoing activity:
- **Fast enough** to catch attention
- **Slow enough** to not be annoying
- **Stops automatically** when processing completes

---

## Responsive Behavior

### Desktop
```
┌─────────────────────────────────────────────────┐
│ [Image]                                         │
│                                                 │
│ 12/20/2025, 11:00 AM    [🔵 Pending detection] │
└─────────────────────────────────────────────────┘
```

### Mobile
```
┌─────────────────────┐
│     [Image]         │
│                     │
│ 12/20/2025, 11:00   │
│ [🔵 Pending]        │
└─────────────────────┘
```

Badges adapt to screen size:
- Maintain readability
- Text may truncate on very small screens
- Always show status icon/color

---

## Accessibility

### Color Blindness Considerations

The badges use multiple visual cues:
1. **Text Label** - "Pending detection", "No detection", etc.
2. **Position** - Always in the same location
3. **Animation** - Pending badge pulses
4. **Icon** (future) - Could add icons for better recognition

### Screen Readers

Badges are semantic and will be read as:
- "Pending detection"
- "2 detections, button" (clickable)
- "No detection"
- "Processing failed"

---

## Usage Examples

### Scenario 1: Manual Upload

```
User uploads image
    ↓
[🔵 Pending detection] ← Shows immediately
    ↓ (30 seconds)
[🔴 1 detection] ← Updates automatically
```

### Scenario 2: Automated Pull

```
Celery Beat runs at 12:00
    ↓
10 new images appear
    ↓
All show [🔵 Pending detection]
    ↓ (staggered, 30-60 seconds each)
Results update individually:
- [🔴 3 detections]
- [⚫ No detection]
- [🔴 1 detection]
- [⚫ No detection]
... etc
```

### Scenario 3: Processing Error

```
Image upload succeeds
    ↓
[🔵 Pending detection]
    ↓ (30 seconds)
Error in wildlife AI
    ↓
[🔴 Processing failed] ← Indicates problem
```

---

## Developer Notes

### Badge Component Logic

```typescript
// Pseudo-code for badge selection
if (image.detections.length > 0) {
  return <RedBadge>{count} detections</RedBadge>
}
else if (!image.processed ||
         image.processing_status === 'detecting' ||
         image.processing_status === 'uploading') {
  return <BlueBadge pulse>Pending detection</BlueBadge>
}
else if (image.processing_status === 'failed') {
  return <DarkRedBadge>Processing failed</DarkRedBadge>
}
else {
  return <GrayBadge>No detection</GrayBadge>
}
```

### API Fields Required

```json
{
  "image_id": "uuid",
  "detections": [...],
  "processing_status": "detecting|completed|failed",
  "processed": true|false
}
```

---

## Future Enhancements

Potential improvements:
1. **Progress Percentage** - "Processing... 75%"
2. **Time Estimate** - "~30 seconds remaining"
3. **Retry Button** - For failed processing
4. **Detailed Error** - Tooltip with error message
5. **Species Icons** - Visual indicators for detected animals
6. **Confidence Meter** - Show AI confidence level
