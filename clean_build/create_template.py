from PIL import Image, ImageDraw
import os

def create_gradient_template():
    """Create a gradient background template for share cards."""
    # Create a new image with a white background
    width = 800
    height = 400
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    # Create a subtle gradient background
    for y in range(height):
        # Calculate gradient color (from light blue to very light teal)
        r = int(240 + (y / height) * (245 - 240))
        g = int(245 + (y / height) * (248 - 245))
        b = int(248 + (y / height) * (250 - 248))
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    # Add a subtle border
    border_color = (200, 200, 200)
    for i in range(2):  # 2px border
        draw.rectangle(
            [(i, i), (width - 1 - i, height - 1 - i)],
            outline=border_color
        )
    
    # Save the template
    os.makedirs('assets', exist_ok=True)
    template_path = os.path.join('assets', 'share_card_template.png')
    image.save(template_path, 'PNG', quality=95)
    print(f"Created share card template at: {template_path}")

if __name__ == "__main__":
    create_gradient_template() 