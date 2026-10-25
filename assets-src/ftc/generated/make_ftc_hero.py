"""Frames the robot-demo photo for the FTC hero: the robot and Eric cropped out, centred on a transparent
canvas with feathered edges, so the hero's fade (strongest at its edges) leaves the whole robot visible.
Usage: python3 make_ftc_hero.py <photo.jpg> <out.webp>
"""
import sys
from PIL import Image, ImageDraw, ImageFilter

src, out = sys.argv[1], sys.argv[2]
photo = Image.open(src).convert("RGB")
box = (0, 0, 600, 1024)                        # the robot (left, its arm up to y 270) and Eric, head to shoes
crop = photo.crop(box)
w, h = crop.size
fill = 0.74                                    # share of the canvas the photo takes
W, H = round(w / fill), round(h / fill)
feather = 60
mask = Image.new("L", (w, h), 0)
ImageDraw.Draw(mask).rectangle((feather, feather, w - feather, h - feather), fill=255)
mask = mask.filter(ImageFilter.GaussianBlur(feather / 2))
canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
canvas.paste(crop, ((W - w) // 2, (H - h) // 2), mask)
canvas.save(out, quality=85, method=6)
print(out, W, H)
