#!/usr/bin/env python3
"""Generate placeholder PWA icons"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size, filename):
    # Create a green background
    img = Image.new('RGB', (size, size), color='#4CAF50')
    draw = ImageDraw.Draw(img)
    
    # Draw white text "RP" in the center
    try:
        # Try to use a system font
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size // 3)
    except Exception:
        # Fallback to default font
        font = ImageFont.load_default()
    
    text = "RP"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    position = ((size - text_width) // 2, (size - text_height) // 2)
    draw.text(position, text, fill='white', font=font)
    
    img.save(filename)
    print(f"Created {filename}")

if __name__ == "__main__":
    public_dir = os.path.join(os.path.dirname(__file__), 'public')
    os.makedirs(public_dir, exist_ok=True)
    
    create_icon(192, os.path.join(public_dir, 'icon-192x192.png'))
    create_icon(512, os.path.join(public_dir, 'icon-512x512.png'))
    
    print("Icon generation complete!")
