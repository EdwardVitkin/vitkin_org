import sys
import os
import urllib.request

try:
    from PIL import Image
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image

def make_transparent(input_path, output_path):
    print(f"Processing {input_path}...")
    img = Image.open(input_path)
    img = img.convert("RGBA")
    datas = img.getdata()
    
    newData = []
    for item in datas:
        # Check if pixel is white or close to white
        if item[0] > 230 and item[1] > 230 and item[2] > 230:
            newData.append((255, 255, 255, 0))
        else:
            newData.append(item)
            
    img.putdata(newData)
    img.save(output_path, "PNG")
    print(f"Saved to {output_path}")

os.chdir(r"c:\Users\Edward\Documents\Projects\AI\about me\edwardvitkin")

if os.path.exists("images/logos/technion.png"):
    make_transparent("images/logos/technion.png", "images/logos/technion_transparent.png")
if os.path.exists("images/logos/tau.jpg"):
    make_transparent("images/logos/tau.jpg", "images/logos/tau_transparent.png")

print("Downloading Reichman SVG...")
url = "https://upload.wikimedia.org/wikipedia/en/a/a8/Reichman_University.svg"
urllib.request.urlretrieve(url, "images/logos/reichman.svg")
print("Done!")
