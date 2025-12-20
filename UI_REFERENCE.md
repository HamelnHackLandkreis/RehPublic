# UI Screenshots Reference

## Integration Tab - No Integration

When viewing a camera location with no integration configured:

```
┌────────────────────────────────────────────────────────┐
│  [Overview] [Upload] [Integration ✓]                  │
├────────────────────────────────────────────────────────┤
│                                                        │
│  External Image Source Integration                    │
│  Configure an external image source that will be       │
│  automatically polled every hour...                    │
│                                                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │  Integration Name                                 │ │
│  │  ┌──────────────────────────────────────────────┐│ │
│  │  │ e.g., Hameln-Pyrmont Camera Feed             ││ │
│  │  └──────────────────────────────────────────────┘│ │
│  │                                                   │ │
│  │  Base URL                                         │ │
│  │  ┌──────────────────────────────────────────────┐│ │
│  │  │ https://assets.hameln-pyrmont.digital/...    ││ │
│  │  └──────────────────────────────────────────────┘│ │
│  │  URL to the directory listing containing images  │ │
│  │                                                   │ │
│  │  Username                                         │ │
│  │  ┌──────────────────────────────────────────────┐│ │
│  │  │ mitwirker                                     ││ │
│  │  └──────────────────────────────────────────────┘│ │
│  │                                                   │ │
│  │  Password                                         │ │
│  │  ┌──────────────────────────────────────────────┐│ │
│  │  │ ••••••••                                      ││ │
│  │  └──────────────────────────────────────────────┘│ │
│  │  Leave empty if no authentication is required    │ │
│  │                                                   │ │
│  │  [ Create Integration ]                          │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │ ℹ️ How it works                                   │ │
│  │ • Images are automatically pulled from the       │ │
│  │   configured URL every hour                      │ │
│  │ • Each image is processed through the wildlife   │ │
│  │   detection system                               │ │
│  │ • Detected animals appear in the Overview tab    │ │
│  │ • The system tracks which files have been        │ │
│  │   processed to avoid duplicates                  │ │
│  │ • Up to 10 new images are processed per hour     │ │
│  └──────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
```

## Integration Tab - Active Integration

When an integration is already configured:

```
┌────────────────────────────────────────────────────────┐
│  [Overview] [Upload] [Integration ✓]                  │
├────────────────────────────────────────────────────────┤
│                                                        │
│  External Image Source Integration                    │
│  Configure an external image source that will be       │
│  automatically polled every hour...                    │
│                                                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │  Active Integration                    [✓ Active]│ │
│  │  Hameln-Pyrmont Camera Feed                      │ │
│  │                                                   │ │
│  │  Base URL:        https://assets.hameln-...      │ │
│  │  Auth Type:       basic                          │ │
│  │  Last Pulled:     Aufnahme_251220_1100_BYWP9.jpg │ │
│  │  Last Pull Time:  12/20/2025, 11:32:45 AM       │ │
│  │                                                   │ │
│  │  [ Deactivate ] [ Test Pull (2 files) ] [Delete]│ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │ ℹ️ How it works                                   │ │
│  │ ...                                               │ │
│  └──────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
```

## Success State

After creating or testing an integration:

```
┌──────────────────────────────────────────────────────┐
│  ✅ Integration created successfully! Images will be │
│     pulled hourly.                                   │
└──────────────────────────────────────────────────────┘
```

```
┌──────────────────────────────────────────────────────┐
│  ✅ Test successful! Processed 2 file(s). Check the  │
│     Overview tab to see the results.                 │
└──────────────────────────────────────────────────────┘
```

## Error State

If something goes wrong:

```
┌──────────────────────────────────────────────────────┐
│  ❌ Failed to create integration: Location not found │
└──────────────────────────────────────────────────────┘
```

## Color Scheme

- **Active Integration Card**: Green background (#F0FDF4), green border (#BBF7D0)
- **Status Badge**: Green (#059669) with checkmark icon
- **Form Background**: Light gray (#F9FAFB) with gray border
- **Info Box**: Blue background (#EFF6FF), blue border (#BFDBFE)
- **Primary Button**: Blue (#3B82F6), hover (#2563EB)
- **Warning Button**: Yellow (#EAB308), hover (#CA8A04)
- **Danger Button**: Red (#EF4444), hover (#DC2626)
- **Success Message**: Green background (#F0FDF4), green text (#15803D)
- **Error Message**: Red background (#FEF2F2), red text (#DC2626)

## Responsive Behavior

- **Desktop**: Full-width form with proper spacing
- **Tablet**: Slightly compressed but still readable
- **Mobile**: Stacked layout, full-width inputs, touch-friendly buttons

## Button States

- **Default**: Solid color with hover effect
- **Hover**: Slightly darker color, subtle transition
- **Loading**: Disabled state with 50% opacity and "Creating..." text
- **Disabled**: Grayed out, no pointer events

## Form Validation

- **Required fields**: Browser native validation (HTML5)
- **URL field**: Type="url" ensures valid URL format
- **Password field**: Type="password" for security
- **Empty state**: Optional fields can be left blank (no auth)
