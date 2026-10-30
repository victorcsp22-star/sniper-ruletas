import os
from PIL import Image, ImageDraw, ImageFont

out_dir = r"C:\Users\victo\nuevas_ruletas\app_movil\static"
os.makedirs(out_dir, exist_ok=True)

def create_icon(size):
    img = Image.new("RGBA", (size, size), (11, 15, 25, 255))
    draw = ImageDraw.Draw(img)

    # Draw rounded background circle/border
    margin = int(size * 0.08)
    draw.ellipse([margin, margin, size - margin, size - margin], fill=(16, 185, 129, 255))
    
    inner_margin = int(size * 0.14)
    draw.ellipse([inner_margin, inner_margin, size - inner_margin, size - inner_margin], fill=(15, 23, 42, 255))

    # Crosshair lines
    cx, cy = size // 2, size // 2
    arm = int(size * 0.32)
    lw = max(3, int(size * 0.03))
    draw.line([(cx - arm, cy), (cx + arm, cy)], fill=(16, 185, 129, 255), width=lw)
    draw.line([(cx, cy - arm), (cx, cy + arm)], fill=(16, 185, 129, 255), width=lw)

    # Center target dot
    r_dot = int(size * 0.08)
    draw.ellipse([cx - r_dot, cy - r_dot, cx + r_dot, cy + r_dot], fill=(52, 211, 153, 255))

    return img

create_icon(192).save(os.path.join(out_dir, "icon-192.png"))
create_icon(512).save(os.path.join(out_dir, "icon-512.png"))
print("✅ Iconos 192x192 y 512x512 creados con éxito.")
