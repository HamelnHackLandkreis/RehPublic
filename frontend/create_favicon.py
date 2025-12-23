#!/usr/bin/env python3
"""
Create a favicon with white rounded background from RehPublic_Icon.svg
"""
from PIL import Image, ImageDraw
import cairosvg
import io

def create_favicon_with_background(svg_path, output_png_path, size=512, padding=30, corner_radius=60, scale_factor=1.5):
    """
    Create a favicon with white rounded rectangle background
    
    Args:
        svg_path: Path to input SVG file
        output_png_path: Path to output PNG file
        size: Output image size (square)
        padding: Padding around the icon
        corner_radius: Radius for rounded corners
        scale_factor: How much bigger to make the icon (>1 = bigger)
    """
    # Convert SVG to PNG with transparency - make it bigger than needed
    render_size = int((size - (2 * padding)) * scale_factor)
    png_data = cairosvg.svg2png(
        url=svg_path,
        output_width=render_size,
        output_height=render_size
    )
    
    # Load the icon
    icon = Image.open(io.BytesIO(png_data)).convert('RGBA')
    
    # Get the bounding box of non-transparent pixels
    bbox = icon.getbbox()
    if bbox:
        # Crop more aggressively at the bottom to remove text
        # Reduce bottom boundary by 18% of the height to cut off text
        left, top, right, bottom = bbox
        height = bottom - top
        new_bottom = bottom - int(height * 0.18)
        icon = icon.crop((left, top, right, new_bottom))
    
    # Resize to fit the available space while maintaining aspect ratio
    available_size = size
    icon.thumbnail((available_size, available_size), Image.Resampling.LANCZOS)
    
    # Create a new image with white rounded rectangle background
    output = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    
    # Create rounded rectangle mask
    mask = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), (size, size)], radius=corner_radius, fill=255)
    
    # Create white background with rounded corners
    white_bg = Image.new('RGBA', (size, size), (255, 255, 255, 255))
    output.paste(white_bg, (0, 0), mask)
    
    # Center the icon
    icon_x = (size - icon.width) // 2
    icon_y = (size - icon.height) // 2
    output.paste(icon, (icon_x, icon_y), icon)
    
    # Save the result
    output.save(output_png_path, 'PNG')
    print(f"Created {output_png_path} ({size}x{size})")

def main():
    svg_path = 'public/RehPublic_Icon_thick.svg'
    
    # Create different sizes for favicon and PWA icons with large scale factor
    create_favicon_with_background(svg_path, 'public/favicon.png', size=32, padding=2, corner_radius=6, scale_factor=2.0)
    create_favicon_with_background(svg_path, 'public/icon-192x192.png', size=192, padding=10, corner_radius=30, scale_factor=2.0)
    create_favicon_with_background(svg_path, 'public/icon-512x512.png', size=512, padding=20, corner_radius=60, scale_factor=2.0)
    
    # Also create an SVG version with background
    create_svg_with_background()

def create_svg_with_background():
    """Create an SVG version with white rounded background"""
    svg_content = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg width="512" height="512" viewBox="0 0 512 512" version="1.1" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <clipPath id="roundedClip">
      <rect x="0" y="0" width="512" height="512" rx="60" ry="60"/>
    </clipPath>
  </defs>
  
  <!-- White rounded background -->
  <rect x="0" y="0" width="512" height="512" rx="60" ry="60" fill="white"/>
  
  <!-- Icon content (scaled and centered) -->
  <g transform="translate(40, 40) scale(0.83)">
    <image href="RehPublic_Icon.svg" width="432" height="432" preserveAspectRatio="xMidYMid meet"/>
  </g>
</svg>'''
    
    with open('public/favicon.svg', 'w') as f:
        f.write(svg_content)
    print("Created public/favicon.svg")

if __name__ == '__main__':
    main()
