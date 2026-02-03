#!/usr/bin/env python3
import re

# Read the complete country options
with open('/Users/craighalliday/Desktop/repos/pirihub/country-options.html', 'r') as f:
    country_options = f.read().strip()

# Function to update each file
def update_country_select(filename, select_id):
    filepath = f'/Users/craighalliday/Desktop/repos/pirihub/{filename}'
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Pattern to match the select element and its options
    pattern = rf'(<select id="{select_id}" name="country" required>)(.*?)(</select>)'
    replacement = rf'\1\n                {country_options}\n            \3'
    
    updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    with open(filepath, 'w') as f:
        f.write(updated_content)
    
    print(f'Updated {filename}')

# Update all four house pages
update_country_select('casa-matutina.html', 'country-matutina')
update_country_select('casa-atelier.html', 'country-atelier')
update_country_select('casa-do-vale.html', 'country-vale')
update_country_select('casa-do-rio.html', 'country-rio')

print('\nAll house pages updated with complete country list (180+ countries)!')
