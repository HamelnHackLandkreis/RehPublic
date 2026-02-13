#!/usr/bin/env python3
"""
Make the lines in the RehPublic icon thicker
"""
import xml.etree.ElementTree as ET

def thicken_svg_strokes(input_path, output_path, stroke_multiplier=2.0):
    """
    Increase stroke widths in SVG file
    
    Args:
        input_path: Path to input SVG file
        output_path: Path to output SVG file
        stroke_multiplier: Factor to multiply stroke widths by
    """
    # Parse the SVG
    tree = ET.parse(input_path)
    root = tree.getroot()
    
    # Define namespaces
    namespaces = {
        'svg': 'http://www.w3.org/2000/svg',
        'inkscape': 'http://www.inkscape.org/namespaces/inkscape',
        'sodipodi': 'http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd'
    }
    
    # Register namespaces to preserve them
    for prefix, uri in namespaces.items():
        ET.register_namespace(prefix, uri)
    
    # Find all elements with stroke or style attributes
    for elem in root.iter():
        # Check for stroke-width attribute
        if 'stroke-width' in elem.attrib:
            try:
                current_width = float(elem.attrib['stroke-width'])
                elem.attrib['stroke-width'] = str(current_width * stroke_multiplier)
            except ValueError:
                pass
        
        # Check for style attribute containing stroke-width
        if 'style' in elem.attrib:
            style = elem.attrib['style']
            style_parts = style.split(';')
            new_style_parts = []
            
            for part in style_parts:
                if 'stroke-width:' in part:
                    try:
                        key, value = part.split(':')
                        # Remove any units and convert to number
                        numeric_value = ''.join(c for c in value if c.isdigit() or c == '.')
                        if numeric_value:
                            new_width = float(numeric_value) * stroke_multiplier
                            # Keep any units that were there
                            units = ''.join(c for c in value if not (c.isdigit() or c == '.' or c == ' '))
                            new_style_parts.append(f'{key}:{new_width}{units}')
                        else:
                            new_style_parts.append(part)
                    except (ValueError, AttributeError):
                        new_style_parts.append(part)
                else:
                    new_style_parts.append(part)
            
            elem.attrib['style'] = ';'.join(new_style_parts)
    
    # Write the modified SVG
    tree.write(output_path, encoding='utf-8', xml_declaration=True)
    print(f"Created {output_path} with {stroke_multiplier}x thicker strokes")

def main():
    input_svg = 'public/RehPublic_Icon.svg'
    output_svg = 'public/RehPublic_Icon_thick.svg'
    
    # Make strokes 2.5x thicker
    thicken_svg_strokes(input_svg, output_svg, stroke_multiplier=2.5)
    
    print("\nNow regenerating favicons with thicker icon...")
    
    # Update the favicon generation to use the thick version
    import create_favicon
    create_favicon.svg_path_override = output_svg

if __name__ == '__main__':
    main()
