from PIL import Image
# usage: python zoom.py <img> <x1 y1 x2 y2> <out> [scale]
import sys
src = sys.argv[1]
box = tuple(int(v) for v in sys.argv[2:6])
out = sys.argv[6]
scale = int(sys.argv[7]) if len(sys.argv) > 7 else 3
im = Image.open(src)
c = im.crop(box)
c = c.resize((c.width*scale, c.height*scale), Image.LANCZOS)
c.save(out)
print(out, c.size)
