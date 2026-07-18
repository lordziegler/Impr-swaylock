#!/usr/bin/env python3
"""
Imperator lockscreen background generator (retrofuturist HUD / amber CRT).

Draws the Imperator-graded, aged "Pandemonium" backdrop, then a centered,
hard-cornered HUD panel: a frosted-glass field (cheap cairo down/upscale blur +
smoked amber tint) laced with CRT scanlines, targeting-reticle corner brackets,
the House Ziegler crest, a terminal-style "insert password" prompt and the House
epitaph "Leoni Nvlla Vis Avrae". The live HH:MM:SS clock is NOT baked here —
swaylock-effects renders it on top at the panel's clock slot so the seconds tick.
Pass --preview-clock to bake a sample time for layout checks.

Usage:
  wallpaper.py --lock [--out P] [--size WxH] [--preview-clock]
  wallpaper.py [--out P] [--size WxH]          # static wallpaper
"""
import cairo
import math
import os
import random
import argparse

random.seed(0xC8960C)
TAU = math.tau

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
ASSETS = os.path.join(SCRIPT_DIR, "assests")
PANDEMONIUM = os.path.join(ASSETS, "pandemonium.png")
CREST = os.path.join(ASSETS, "shield.png")

SERIF = "Noto Serif"          # epitaph — Roman-inscription feel
MONO = "JetBrainsMonoNL Nerd Font Mono"


def rgba(h, a=1.0):
    h = h.lstrip("#")
    return int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a


BG      = rgba("#0E0C08")
BORDER  = rgba("#2A2010")
DIM     = rgba("#3A2E10")
LINENUM = rgba("#5E4E28")
SUBTLE  = rgba("#8A7040")
FG      = rgba("#D4A843")
MUTED   = rgba("#B8860B")
ACCENT2 = rgba("#C8960C")
ACCENT3 = rgba("#A07820")
ACCENT  = rgba("#FFD700")


# ---------------------------------------------------------------- helpers

def blur_surface(src, W, H, factor=0.085):
    """Cheap gaussian-ish blur: downscale then bilinear upscale."""
    sw, sh = max(1, int(W * factor)), max(1, int(H * factor))
    small = cairo.ImageSurface(cairo.FORMAT_RGB24, sw, sh)
    sc = cairo.Context(small)
    sc.scale(sw / W, sh / H)
    sc.set_source_surface(src, 0, 0)
    sc.get_source().set_filter(cairo.FILTER_GOOD)
    sc.paint()
    out = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
    oc = cairo.Context(out)
    oc.scale(W / sw, H / sh)
    oc.set_source_surface(small, 0, 0)
    oc.get_source().set_filter(cairo.FILTER_GOOD)
    oc.paint()
    return out


def tracked_text(ctx, text, cx, baseline, size, color, track, face=MONO,
                 weight=cairo.FONT_WEIGHT_NORMAL, upper=True):
    """Centered, letter-spaced text. Returns (start_x, end_x)."""
    ctx.select_font_face(face, cairo.FONT_SLANT_NORMAL, weight)
    ctx.set_font_size(size)
    if upper:
        text = text.upper()
    widths = [ctx.text_extents(ch).x_advance for ch in text]
    total = sum(widths) + track * (len(text) - 1)
    x0 = cx - total / 2
    x = x0
    ctx.set_source_rgba(*color)
    for ch, w in zip(text, widths):
        ctx.move_to(x, baseline)
        ctx.show_text(ch)
        x += w + track
    return x0, x - track


def diamond(ctx, cx, cy, r, color):
    ctx.set_source_rgba(*color)
    ctx.move_to(cx, cy - r)
    ctx.line_to(cx + r, cy)
    ctx.line_to(cx, cy + r)
    ctx.line_to(cx - r, cy)
    ctx.close_path()
    ctx.fill()


def hrule(ctx, x1, x2, y, color, lw=1.0):
    ctx.set_source_rgba(*color)
    ctx.set_line_width(lw)
    ctx.move_to(x1, y)
    ctx.line_to(x2, y)
    ctx.stroke()


def bracket(ctx, x, y, dx, dy, size, color, lw=2.0):
    """HUD targeting-reticle corner."""
    ctx.set_source_rgba(*color)
    ctx.set_line_width(lw)
    ctx.move_to(x, y + dy * size)
    ctx.line_to(x, y)
    ctx.line_to(x + dx * size, y)
    ctx.stroke()
    ctx.set_line_width(lw)
    ctx.move_to(x + dx * size * 0.30, y + dy * size * 0.30)
    ctx.line_to(x + dx * size * 0.30, y + dy * size * 0.30)
    diamond(ctx, x + dx * size * 1.5, y + dy * size * 1.5, 1.8, color)


def scanlines(ctx, x, y, w, h, gap, color):
    ctx.save()
    ctx.rectangle(x, y, w, h)
    ctx.clip()
    ctx.set_source_rgba(*color)
    ctx.set_line_width(1)
    yy = y + 0.5
    while yy < y + h:
        ctx.move_to(x, yy)
        ctx.line_to(x + w, yy)
        ctx.stroke()
        yy += gap
    ctx.restore()


def tick_row(ctx, x1, x2, y, n, hgt, color, lw=1.0):
    ctx.set_source_rgba(*color)
    ctx.set_line_width(lw)
    for i in range(n + 1):
        tx = x1 + (x2 - x1) * i / n
        th = hgt if i % 5 == 0 else hgt * 0.5
        ctx.move_to(tx, y)
        ctx.line_to(tx, y - th)
        ctx.stroke()


# ---------------------------------------------------------------- backgrounds

def draw_edge_burn(ctx, W, H):
    burn = int(H * 0.16)
    for grad, rect in [
        (cairo.LinearGradient(0, 0, burn, 0), (0, 0, burn, H)),
        (cairo.LinearGradient(W, 0, W - burn, 0), (W - burn, 0, burn, H)),
        (cairo.LinearGradient(0, 0, 0, burn), (0, 0, W, burn)),
        (cairo.LinearGradient(0, H, 0, H - burn), (0, H - burn, W, burn)),
    ]:
        grad.add_color_stop_rgba(0, *rgba("#0E0C08", 0.62))
        grad.add_color_stop_rgba(1, 0, 0, 0, 0)
        ctx.set_source(grad)
        ctx.rectangle(*rect)
        ctx.fill()


def draw_pandemonium(ctx, W, H):
    img = cairo.ImageSurface.create_from_png(PANDEMONIUM)
    iw, ih = img.get_width(), img.get_height()
    scale = max(W / iw, H / ih)
    ctx.save()
    ctx.translate((W - iw * scale) / 2, (H - ih * scale) / 2)
    ctx.scale(scale, scale)
    ctx.set_source_surface(img, 0, 0)
    src = ctx.get_source()
    src.set_filter(cairo.FILTER_GOOD)
    src.set_extend(cairo.EXTEND_PAD)
    ctx.paint()
    ctx.restore()
    draw_edge_burn(ctx, W, H)


def draw_procedural(ctx, W, H):
    ctx.set_source_rgba(*BG)
    ctx.paint()
    ctx.set_line_width(0.5)
    ctx.set_source_rgba(*rgba("#111008"))
    step = 80
    for y in range(0, H + 1, step):
        ctx.move_to(0, y); ctx.line_to(W, y); ctx.stroke()
    for x in range(0, W + 1, step):
        ctx.move_to(x, 0); ctx.line_to(x, H); ctx.stroke()
    gvig = cairo.RadialGradient(W // 2, H // 2, min(W, H) * 0.15, W // 2, H // 2, min(W, H) * 0.78)
    gvig.add_color_stop_rgba(0, 0, 0, 0, 0)
    gvig.add_color_stop_rgba(1, *rgba("#0E0C08", 0.85))
    ctx.set_source(gvig)
    ctx.paint()
    draw_edge_burn(ctx, W, H)


def draw_background(ctx, W, H):
    if os.path.exists(PANDEMONIUM):
        draw_pandemonium(ctx, W, H)
    else:
        draw_procedural(ctx, W, H)


# ---------------------------------------------------------------- crest

def draw_crest(ctx, cx, cy, target_h):
    if not os.path.exists(CREST):
        return
    img = cairo.ImageSurface.create_from_png(CREST)
    iw, ih = img.get_width(), img.get_height()
    scale = target_h / ih
    glow = cairo.RadialGradient(cx, cy, 0, cx, cy, target_h * 0.75)
    glow.add_color_stop_rgba(0, *rgba("#C8960C", 0.20))
    glow.add_color_stop_rgba(1, 0, 0, 0, 0)
    ctx.set_source(glow)
    ctx.rectangle(cx - target_h, cy - target_h, target_h * 2, target_h * 2)
    ctx.fill()
    ctx.save()
    ctx.translate(cx - iw * scale / 2, cy - ih * scale / 2)
    ctx.scale(scale, scale)
    ctx.set_source_surface(img, 0, 0)
    ctx.get_source().set_filter(cairo.FILTER_GOOD)
    ctx.paint()
    ctx.restore()


# ---------------------------------------------------------------- HUD panel

def clock_center(W, H):
    """Screen coords where swaylock-effects renders the live clock — the output
    center, which is swaylock's own default indicator position (so lock.sh needs
    no position override, avoiding the offset-from-center ambiguity)."""
    return W / 2, H / 2


def draw_panel(ctx, surface, W, H, preview_clock=False):
    s = H / 1080.0
    pw, ph = 512 * s, 580 * s
    px, py = round((W - pw) / 2), round((H - ph) / 2)
    pw, ph = round(pw), round(ph)
    cx = W // 2
    yc = H / 2.0  # clock slot / panel center

    # frosted-glass field (real blur of the backdrop + smoked amber tint)
    blurred = blur_surface(surface, W, H)
    ctx.save()
    ctx.rectangle(px, py, pw, ph)
    ctx.clip()
    ctx.set_source_surface(blurred, 0, 0)
    ctx.get_source().set_filter(cairo.FILTER_GOOD)
    ctx.paint()
    ctx.set_source_rgba(*rgba("#0E0C08", 0.50))
    ctx.paint()
    sheen = cairo.LinearGradient(0, py, 0, py + ph)
    sheen.add_color_stop_rgba(0, *rgba("#241C0C", 0.30))
    sheen.add_color_stop_rgba(0.5, 0, 0, 0, 0)
    sheen.add_color_stop_rgba(1, *rgba("#0E0C08", 0.35))
    ctx.set_source(sheen)
    ctx.paint()
    ctx.restore()

    # CRT scanlines inside the panel
    scanlines(ctx, px, py, pw, ph, 3 * s, rgba("#0E0C08", 0.22))

    # hard-cornered frame: thin amber border + inner hairline
    ctx.set_source_rgba(*ACCENT2)
    ctx.set_line_width(1.4)
    ctx.rectangle(px + 0.5, py + 0.5, pw - 1, ph - 1)
    ctx.stroke()
    ctx.set_source_rgba(*rgba("#FFD700", 0.30))
    ctx.set_line_width(0.8)
    ctx.rectangle(px + 7 * s, py + 7 * s, pw - 14 * s, ph - 14 * s)
    ctx.stroke()

    # targeting-reticle brackets, sitting just outside the border
    b, bl = 30 * s, 2.0
    bracket(ctx, px - 5, py - 5, 1, 1, b, ACCENT, bl)
    bracket(ctx, px + pw + 5, py - 5, -1, 1, b, ACCENT, bl)
    bracket(ctx, px - 5, py + ph + 5, 1, -1, b, ACCENT, bl)
    bracket(ctx, px + pw + 5, py + ph + 5, -1, -1, b, ACCENT, bl)

    inx1, inx2 = px + 40 * s, px + pw - 40 * s

    # crest (top)
    draw_crest(ctx, cx, yc - 215 * s, 130 * s)

    # clock/ring zone — swaylock-effects draws its ring + the live clock inside
    # it, centered here; bake a soft glow behind
    glow = cairo.RadialGradient(cx, yc, 0, cx, yc, 165 * s)
    glow.add_color_stop_rgba(0, *rgba("#C8960C", 0.16))
    glow.add_color_stop_rgba(1, 0, 0, 0, 0)
    ctx.set_source(glow)
    ctx.rectangle(px, yc - 170 * s, pw, 340 * s)
    ctx.fill()
    if preview_clock:
        # mock swaylock's ring + clock to check the layout (not drawn at runtime)
        ctx.set_source_rgba(*ACCENT3)
        ctx.set_line_width(5 * s)
        ctx.arc(cx, yc, 145 * s, 0, TAU)
        ctx.stroke()
        tracked_text(ctx, "14:34:07", cx, yc + 15 * s, 46 * s, ACCENT, 2 * s, face=MONO)

    # epitaph — the House motto, framed tightly between two points
    hrule(ctx, inx1, inx2, yc + 162 * s, rgba("#5E4E28", 0.6))
    mb = yc + 200 * s
    mx0, mx1 = tracked_text(ctx, "Leoni Nvlla Vis Avrae", cx, mb, 18 * s, MUTED, 3 * s,
                            face=SERIF)
    dy = mb - 18 * s * 0.34
    diamond(ctx, mx0 - 16 * s, dy, 2.6 * s, ACCENT2)
    diamond(ctx, mx1 + 16 * s, dy, 2.6 * s, ACCENT2)


def draw_global_scanlines(ctx, W, H):
    scanlines(ctx, 0, 0, W, H, 3, rgba("#0E0C08", 0.06))


# ---------------------------------------------------------------- main

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--lock", action="store_true")
    p.add_argument("--preview-clock", action="store_true",
                   help="Bake a sample time into the clock slot (layout preview)")
    p.add_argument("--out", default=None)
    p.add_argument("--size", default="1920x1080")
    args = p.parse_args()

    W, H = map(int, args.size.split("x"))
    out = args.out or ("/tmp/imperator-lock.png" if args.lock else "imperator-wallpaper.png")

    surface = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
    ctx = cairo.Context(surface)

    draw_background(ctx, W, H)
    if args.lock:
        draw_panel(ctx, surface, W, H, preview_clock=args.preview_clock)
    draw_global_scanlines(ctx, W, H)

    surface.write_to_png(out)
    print(out)


if __name__ == "__main__":
    main()
