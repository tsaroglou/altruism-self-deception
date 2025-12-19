"""
Simple script to generate a grid image with all O's.
Run this script to create a PNG image of a 7x7 grid filled with O symbols.
"""

from PIL import Image, ImageDraw, ImageFont
import os

# Grid dimensions
GRID_ROWS = 7
GRID_COLS = 7
CELL_SIZE = 80  # Size of each cell in pixels
BORDER_WIDTH = 2  # Border width between cells
PADDING = 20  # Padding around the grid

# Calculate image dimensions
IMG_WIDTH = GRID_COLS * CELL_SIZE + (GRID_COLS - 1) * BORDER_WIDTH + 2 * PADDING
IMG_HEIGHT = GRID_ROWS * CELL_SIZE + (GRID_ROWS - 1) * BORDER_WIDTH + 2 * PADDING

# Create image with white background
img = Image.new('RGB', (IMG_WIDTH, IMG_HEIGHT), color='white')
draw = ImageDraw.Draw(img)

# Try to use a nice font, fallback to default if not available
try:
    # Try to use Arial or similar
    font = ImageFont.truetype("arial.ttf", size=50)
except:
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", size=50)
    except:
        # Fallback to default font
        font = ImageFont.load_default()

# Draw grid cells with O's
for row in range(GRID_ROWS):
    for col in range(GRID_COLS):
        # Calculate cell position
        x = PADDING + col * (CELL_SIZE + BORDER_WIDTH)
        y = PADDING + row * (CELL_SIZE + BORDER_WIDTH)
        
        # Draw cell border (light gray)
        draw.rectangle(
            [x, y, x + CELL_SIZE, y + CELL_SIZE],
            outline='lightgray',
            width=BORDER_WIDTH
        )
        
        # Draw O symbol in the center of the cell
        text = "O"
        # Get text bounding box to center it
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        text_x = x + (CELL_SIZE - text_width) // 2
        text_y = y + (CELL_SIZE - text_height) // 2
        
        draw.text((text_x, text_y), text, fill='black', font=font)

# Save the image
output_path = "grid_all_O.png"
img.save(output_path)
print(f"Grid image saved as: {output_path}")
print(f"Image size: {IMG_WIDTH}x{IMG_HEIGHT} pixels")
print(f"Grid: {GRID_ROWS}x{GRID_COLS} cells, all filled with 'O'")



