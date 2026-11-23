"""Regenerate the images in img/ (needs: pip install pillow).

The game itself does not need Pillow: the PNGs are committed.

game2dboard shows one image per cell, so every car is drawn as one picture
(a top-down car or truck, facing right or down) and then cut into one slice
per cell. File names:  <colour>-<h|v><length>-<slice>[-sel].png
e.g. blue-h2-0.png is the back half of a horizontal blue car, and
blue-h2-0-sel.png the same slice with the selection glow.
"""

import os

from PIL import Image, ImageDraw, ImageFilter

CELL = 88                       # must match CELL_SIZE in display.py
S = 4                           # supersampling factor for smooth edges
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "img")

TRAY = (58, 62, 82)             # board colour between the slots
SLOT = (78, 84, 108)            # an empty parking slot
SLOT_EDGE = (66, 71, 93)
GLASS = (170, 205, 225)
GLASS_DARK = (95, 125, 150)
TYRE = (28, 28, 32)
SELECT = (255, 214, 10)

# must match CAR_COLOURS in display.py ("red" is the red car only)
COLOURS = {
    "red": (235, 28, 36),
    "blue": (52, 110, 220),
    "teal": (28, 160, 160),
    "green": (70, 170, 75),
    "yellow": (235, 200, 40),
    "orange": (235, 125, 35),
    "purple": (135, 85, 205),
    "pink": (225, 120, 185),
    "sky": (95, 185, 235),
    "lime": (160, 205, 60),
    "silver": (165, 170, 180),
}


def shade(rgb, f):
    """f < 1 darkens, f > 1 lightens."""
    if f < 1:
        return tuple(int(c * f) for c in rgb)
    return tuple(int(c + (255 - c) * (f - 1)) for c in rgb)


def slot_tile(d, x, y):
    """Draw one empty parking slot with its top-left at (x, y) (big pixels)."""
    c, m = CELL * S, 5 * S
    d.rectangle([x, y, x + c, y + c], fill=TRAY)
    d.rounded_rectangle([x + m, y + m, x + c - m, y + c - m], radius=10 * S,
                        fill=SLOT, outline=SLOT_EDGE, width=3 * S)


def draw_vehicle(length, rgb, selected, hero=False):
    """A vehicle facing right, as a (length*CELL x CELL) RGBA image.

    hero=True is the red car: it gets a warm glow and white racing stripes
    so it stands out from every other car.
    """
    W, H = length * CELL * S, CELL * S
    img = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(img)
    for i in range(length):
        slot_tile(d, i * CELL * S, 0)

    p = 9 * S                                   # gap to the slot edge
    x0, x1, y0, y1 = p, W - p, p + 4 * S, H - p - 4 * S
    body_r = 22 * S
    dark, darker, light = shade(rgb, 0.75), shade(rgb, 0.55), shade(rgb, 1.35)

    # soft shadow
    sh = Image.new("RGBA", (W, H))
    ImageDraw.Draw(sh).rounded_rectangle([x0 + 3 * S, y0 + 5 * S, x1 + 3 * S, y1 + 5 * S],
                                         radius=body_r, fill=(0, 0, 0, 110))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(5 * S)))
    if hero:
        glow = Image.new("RGBA", (W, H))
        ImageDraw.Draw(glow).rounded_rectangle([x0 - 2 * S, y0 - 2 * S, x1 + 2 * S, y1 + 2 * S],
                                               radius=body_r, fill=(255, 120, 60, 235))
        glow = glow.filter(ImageFilter.GaussianBlur(5 * S))
        img.alpha_composite(glow)
        img.alpha_composite(glow)
    d = ImageDraw.Draw(img)

    # tyres poking out at the sides
    tw, th = 15 * S, 7 * S
    axles = [x0 + 0.17 * (x1 - x0), x1 - 0.17 * (x1 - x0)]
    if length == 3:
        axles.insert(1, x0 + 0.42 * (x1 - x0))
    for ax in axles:
        for ty in (y0 - 3 * S, y1 - th + 3 * S):
            d.rounded_rectangle([ax - tw, ty, ax + tw, ty + th], radius=3 * S, fill=TYRE)

    if selected:
        g = 6 * S
        d.rounded_rectangle([x0 - g, y0 - g, x1 + g, y1 + g], radius=body_r + g,
                            fill=SELECT)

    # body
    d.rounded_rectangle([x0, y0, x1, y1], radius=body_r, fill=dark)
    d.rounded_rectangle([x0 + 3 * S, y0 + 3 * S, x1 - 3 * S, y1 - 5 * S],
                        radius=body_r - 3 * S, fill=rgb)
    hh = (y1 - y0)
    mid = y0 + 0.5 * hh - 1 * S

    def stripes(xa, xb):
        if hero:
            for off in (-7 * S, 3 * S):
                d.rectangle([xa, mid + off, xb, mid + off + 4 * S], fill=(255, 255, 255))

    stripes(x0 + 6 * S, x1 - 8 * S)
    if length == 2:
        # car: bonnet at the front (right), cabin in the middle, boot at back
        cx0, cx1 = x0 + 0.30 * (x1 - x0), x0 + 0.74 * (x1 - x0)
        cy0, cy1 = y0 + 0.14 * hh, y1 - 0.14 * hh
        d.rounded_rectangle([cx0, cy0, cx1, cy1], radius=16 * S, fill=darker)
        # windscreen (front) and rear window as trapezoids
        d.polygon([(cx1 - 26 * S, cy0 + 4 * S), (cx1 - 4 * S, cy0 - 1 * S),
                   (cx1 - 4 * S, cy1 + 1 * S), (cx1 - 26 * S, cy1 - 4 * S)], fill=GLASS)
        d.polygon([(cx0 + 4 * S, cy0 + 2 * S), (cx0 + 13 * S, cy0 + 6 * S),
                   (cx0 + 13 * S, cy1 - 6 * S), (cx0 + 4 * S, cy1 - 2 * S)], fill=GLASS_DARK)
        # roof
        d.rounded_rectangle([cx0 + 15 * S, cy0 + 5 * S, cx1 - 28 * S, cy1 - 5 * S],
                            radius=10 * S, fill=rgb)
        d.rounded_rectangle([cx0 + 20 * S, cy0 + 9 * S, cx1 - 36 * S, cy0 + 15 * S],
                            radius=4 * S, fill=light)
        stripes(cx0 + 17 * S, cx1 - 30 * S)
        # bonnet crease and mirrors
        d.line([(cx1 + 8 * S, y0 + 0.5 * hh), (x1 - 16 * S, y0 + 0.5 * hh)],
               fill=dark, width=2 * S)
        for my in (y0 - 4 * S, y1 - 3 * S):
            d.ellipse([cx1 - 30 * S, my, cx1 - 20 * S, my + 7 * S], fill=darker)
    else:
        # truck: cab at the front (right), ribbed cargo box behind it
        bx1 = x0 + 0.68 * (x1 - x0)
        d.rounded_rectangle([x0 + 4 * S, y0 + 5 * S, bx1, y1 - 7 * S],
                            radius=12 * S, fill=light)
        for i in range(1, 8):
            lx = x0 + 4 * S + i * (bx1 - x0 - 4 * S) / 8
            d.line([(lx, y0 + 9 * S), (lx, y1 - 11 * S)], fill=shade(rgb, 1.1), width=3 * S)
        d.rectangle([bx1 + 2 * S, y0 + 0.30 * hh, bx1 + 9 * S, y1 - 0.30 * hh], fill=TYRE)
        cx0 = bx1 + 12 * S
        d.rounded_rectangle([cx0, y0 + 0.12 * hh, x1 - 14 * S, y1 - 0.12 * hh],
                            radius=12 * S, fill=darker)
        d.polygon([(x1 - 38 * S, y0 + 0.16 * hh), (x1 - 17 * S, y0 + 0.12 * hh),
                   (x1 - 17 * S, y1 - 0.12 * hh), (x1 - 38 * S, y1 - 0.16 * hh)], fill=GLASS)
        d.rounded_rectangle([cx0 + 5 * S, y0 + 0.22 * hh, x1 - 42 * S, y1 - 0.22 * hh],
                            radius=8 * S, fill=rgb)
        for my in (y0 - 4 * S, y1 - 3 * S):
            d.ellipse([x1 - 40 * S, my, x1 - 30 * S, my + 7 * S], fill=darker)

    # head lights (front) and tail lights (back)
    for ly in (y0 + 8 * S, y1 - 18 * S):
        d.rounded_rectangle([x1 - 9 * S, ly, x1 - 3 * S, ly + 10 * S], radius=3 * S,
                            fill=(255, 245, 190))
        d.rounded_rectangle([x0 + 3 * S, ly, x0 + 8 * S, ly + 10 * S], radius=2 * S,
                            fill=(150, 10, 15))

    return img.resize((length * CELL, CELL), Image.LANCZOS)


def save_slices(img, name, orient, length, selected):
    for i in range(length):
        box = ((i * CELL, 0, (i + 1) * CELL, CELL) if orient == "h"
               else (0, i * CELL, CELL, (i + 1) * CELL))
        suffix = "-sel" if selected else ""
        img.crop(box).save(os.path.join(OUT, f"{name}-{orient}{length}-{i}{suffix}.png"))


def main():
    os.makedirs(OUT, exist_ok=True)
    for old in os.listdir(OUT):
        if old.endswith(".png"):
            os.remove(os.path.join(OUT, old))
    for name, rgb in COLOURS.items():
        for length in (2, 3):
            for selected in (False, True):
                car = draw_vehicle(length, rgb, selected, hero=(name == "red"))
                save_slices(car, name, "h", length, selected)
                if name != "red":       # the red car always lies across
                    # facing right -> rotate to face down
                    save_slices(car.rotate(-90, expand=True), name, "v", length, selected)

    big = Image.new("RGBA", (CELL * S, CELL * S))
    slot_tile(ImageDraw.Draw(big), 0, 0)
    big.resize((CELL, CELL), Image.LANCZOS).save(os.path.join(OUT, "slot.png"))

    # exit slot: a slot with green arrows pointing out of the board
    d = ImageDraw.Draw(big)
    c = CELL * S
    for k in range(3):
        ax = c * 0.30 + k * 15 * S
        d.polygon([(ax, c * 0.38), (ax + 12 * S, c / 2), (ax, c * 0.62)],
                  fill=(90, 200, 110, 120 + 60 * k))
    big.resize((CELL, CELL), Image.LANCZOS).save(os.path.join(OUT, "exit.png"))


if __name__ == "__main__":
    main()
