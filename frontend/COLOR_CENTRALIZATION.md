# Color Centralization - Complete

## Summary

All colors have been centralized and standardized across the RehPublic frontend application. Custom color values have been replaced with a unified color system using CSS variables and Tailwind CSS utility classes.

## Color System

### Primary Colors (Green - Wildlife/Nature Theme)
- **Primary**: `#22c55e` (green-500) - Main brand color
- **Primary Dark**: `#16a34a` (green-600) - Hover states
- **Primary Light**: `#4ade80` (green-400) - Accents

### Secondary Colors (Blue - Interactive Elements)
- **Secondary**: `#3b82f6` (blue-500) - Buttons, links, interactive elements
- **Secondary Dark**: `#2563eb` (blue-600) - Hover states
- **Secondary Light**: `#60a5fa` (blue-400) - Accents

### Semantic Colors
- **Error/Alert**: `#ef4444` (red-500) / `#dc2626` (red-600)
- **Success**: Uses primary green colors

### Neutral Colors
- Gray palette from 50-900 for backgrounds, text, borders

### Dark Theme
- Slate 700, 800, 900 for dark mode elements

## Implementation

### 1. CSS Variables (`main.css`)
Defined all color values as CSS custom properties in `:root`:
```css
:root {
  --color-primary: #22c55e;
  --color-secondary: #3b82f6;
  --color-error: #ef4444;
  /* etc... */
}
```

### 2. Tailwind Config (`tailwind.config.js`)
Extended Tailwind theme to use CSS variables:
```js
colors: {
  primary: {
    DEFAULT: 'var(--color-primary)',
    dark: 'var(--color-primary-dark)',
    light: 'var(--color-primary-light)',
  },
  secondary: { /* ... */ },
  error: { /* ... */ },
  success: { /* ... */ },
}
```

### 3. Usage
Components now use either:
- **Tailwind classes**: `bg-secondary`, `text-primary`, `hover:bg-secondary-dark`
- **CSS variables**: `var(--color-secondary)` in scoped styles

## Files Updated

### Configuration
- ✅ `app/assets/css/main.css` - CSS variables defined
- ✅ `tailwind.config.js` - Tailwind theme extended

### Components
- ✅ `app/components/Sidebar.vue` - Changed indigo to primary
- ✅ `app/components/LoginButton.vue` - Changed blue to secondary
- ✅ `app/components/LogoutButton.vue` - Changed red to error
- ✅ `app/components/WildlifeMap.vue` - Changed blue to secondary, added pulse animations

### Pages
- ✅ `app/pages/profile.vue` - Changed indigo/green/red to primary/success/error
- ✅ `app/pages/statistics.vue` - Changed blue to secondary
- ✅ `app/pages/camera/index.vue` - Changed blue to secondary
- ✅ `app/pages/camera/[id].vue` - Changed blue to secondary

## Color Usage Guidelines

### When to Use Each Color

**Primary (Green)**:
- Active navigation states
- Success messages
- Wildlife/nature-related elements
- Brand identity elements

**Secondary (Blue)**:
- Buttons and CTAs
- Links and interactive elements
- Tab selections
- Form focus states
- Hover effects on cards/items

**Error (Red)**:
- Error messages
- Logout buttons
- Deletion warnings
- Failed states

**Neutral (Gray/Slate)**:
- Text content
- Backgrounds
- Borders
- Disabled states

## Benefits

1. **Consistency**: All colors follow a unified design system
2. **Maintainability**: Change colors in one place (CSS variables)
3. **Themability**: Easy to implement dark mode or theme switching
4. **Accessibility**: Centralized control makes it easier to ensure color contrast ratios
5. **Developer Experience**: Clear naming conventions and Tailwind utilities

## Next Steps (Optional)

1. Consider implementing a dark mode toggle
2. Add color contrast checking for accessibility
3. Document color usage in a design system guide
4. Create component library with color examples
