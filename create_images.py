#!/usr/bin/env python3
from PIL import Image, ImageDraw, ImageFont
import os

os.chdir('/Users/craighalliday/Desktop/repos/pirihub/img')

def create_image(filename, title, color):
    width, height = 600, 400
    img = Image.new('RGB', (width, height), color=color)
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
    except:
        font = ImageFont.load_default()
    
    # Add text with better positioning
    bbox = draw.textbbox((0, 0), title, font=font)
    text_width = bbox[2] - bbox[0]
    text_x = (width - text_width) // 2
    text_y = (height - (bbox[3] - bbox[1])) // 2
    
    draw.text((text_x, text_y), title, fill=(255, 255, 255), font=font)
    
    img.save(filename, quality=95)
    print(f'Created {filename}')

# Create images
images = [
    ('pirenopolis-waterfall.jpg', 'Waterfalls & Nature', (70, 160, 200)),
    ('pirenopolis-town.jpg', 'Colonial Architecture', (180, 140, 80)),
]

for filename, title, color in images:
    create_image(filename, title, color)

print('\nDone!')
