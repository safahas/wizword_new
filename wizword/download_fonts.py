import os
import requests

def download_font(url, filename):
    """Download a font file from URL and save it to assets directory."""
    os.makedirs('assets', exist_ok=True)
    response = requests.get(url)
    response.raise_for_status()
    
    filepath = os.path.join('assets', filename)
    with open(filepath, 'wb') as f:
        f.write(response.content)
    print(f"Downloaded {filename}")

# Font URLs from Google Fonts CDN
fonts = {
    'Roboto-Regular.ttf': 'https://fonts.gstatic.com/s/roboto/v30/KFOmCnqEu92Fr1Mu4mxKKTU1Kg.woff2',
    'Roboto-Bold.ttf': 'https://fonts.gstatic.com/s/roboto/v30/KFOlCnqEu92Fr1MmWUlfBBc4AMP6lQ.woff2'
}

for filename, url in fonts.items():
    try:
        download_font(url, filename)
    except Exception as e:
        print(f"Error downloading {filename}: {e}")
        
print("\nNote: If you need the fonts for production use, please download them from fonts.google.com") 