"""news-image-20261120: deterministic newspaper front page for 20 Nov 2026.

Draws a 1024x1024 PNG of Friday 20 November 2026 world news with the
Python 3.12 standard library only (zlib + struct). No network, no files
read, no clock, no randomness: two runs write identical bytes.

Layout: masthead, one full-width lead story, seven story cells in two
columns, one "in brief" box, and a footer strip. Text is drawn with a
hand-made 5x7 bitmap font; icons are drawn from lines, circles and
triangles (no bitmaps). Written fresh for this competition.
"""

import os
import struct
import zlib

W, H = 1024, 1024
PAPER = (246, 241, 227)
INK = (22, 22, 22)
RED = (166, 30, 30)
BLUE = (29, 78, 137)
GREY = (110, 104, 90)
PALE = (233, 227, 211)
GOLD = (176, 124, 24)

# ---------------------------------------------------------------- font
# 5x7 glyphs: seven rows of five characters, '#' = ink.
FONT = {
    'A': (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'B': ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    'C': (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    'D': ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    'E': ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    'F': ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    'G': (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    'H': ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'I': (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    'J': ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    'K': ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    'L': ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    'M': ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    'N': ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    'O': (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'P': ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    'Q': (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    'R': ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    'S': (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    'T': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    'U': ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'V': ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    'W': ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    'X': ("#...#", ".#.#.", "..#..", "..#..", "..#..", ".#.#.", "#...#"),
    'Y': ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    'Z': ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    '0': (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    '1': ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    '2': (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    '3': ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    '4': ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    '5': ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    '6': (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    '7': ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    '8': (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    '9': (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    ' ': (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    '.': (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ',': (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    '-': (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    ':': (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ';': (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    '$': ("..#..", ".####", "#.#.#", ".###.", "..#.#", "####.", "..#.."),
    '%': ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.#.#", "#..##"),
    '(': ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ')': (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    '/': ("....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."),
    '+': (".....", "..#..", "..#..", ".###.", "..#..", "..#..", "....."),
    '&': (".##..", "#..#.", "#..#.", ".#...", "#.#.#", "#..#.", ".##.#"),
    '!': ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    '?': (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    '|': ("..#..", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
}

# ---------------------------------------------------------------- canvas
buf = bytearray(W * H * 3)
for i in range(0, W * H * 3, 3):
    buf[i], buf[i + 1], buf[i + 2] = PAPER


def px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        o = (y * W + x) * 3
        buf[o], buf[o + 1], buf[o + 2] = c


def rect(x, y, w, h, c):
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            px(xx, yy, c)


def hline(x, y, w, c):
    rect(x, y, w, 1, c)


def vline(x, y, h, c):
    rect(x, y, 1, h, c)


def line(x0, y0, x1, y1, c):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        px(x0, y0, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def disc(cx, cy, r, c):
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            if (xx - cx) * (xx - cx) + (yy - cy) * (yy - cy) <= r * r:
                px(xx, yy, c)


def ring(cx, cy, r, c, t=2):
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            d = (xx - cx) * (xx - cx) + (yy - cy) * (yy - cy)
            if (r - t) * (r - t) <= d <= r * r:
                px(xx, yy, c)


def tri(x0, y0, x1, y1, x2, y2, c):
    minx, maxx = min(x0, x1, x2), max(x0, x1, x2)
    miny, maxy = min(y0, y1, y2), max(y0, y1, y2)

    def s(ax, ay, bx, by, cx_, cy_):
        return (ax - cx_) * (by - cy_) - (bx - cx_) * (ay - cy_)

    d = s(x0, y0, x1, y1, x2, y2)
    if d == 0:
        return
    for yy in range(miny, maxy + 1):
        for xx in range(minx, maxx + 1):
            a = s(xx, yy, x1, y1, x2, y2)
            b = s(x0, y0, xx, yy, x2, y2)
            cc = s(x0, y0, x1, y1, xx, yy)
            if (d > 0 and a >= 0 and b >= 0 and cc >= 0) or \
               (d < 0 and a <= 0 and b <= 0 and cc <= 0):
                px(xx, yy, c)


# ---------------------------------------------------------------- text
def text_w(s, sc):
    return len(s) * 6 * sc - sc


def draw_text(x, y, s, sc, c):
    cx = x
    for ch in s:
        g = FONT[ch]
        for r in range(7):
            row = g[r]
            for col in range(5):
                if row[col] == '#':
                    rect(cx + col * sc, y + r * sc, sc, sc, c)
        cx += 6 * sc
    return cx


def wrap(s, max_chars):
    words = s.split(' ')
    lines, cur = [], ''
    for w in words:
        nxt = w if not cur else cur + ' ' + w
        if len(nxt) <= max_chars:
            cur = nxt
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def para(x, y, s, sc, c, max_chars, max_lines, lh=None):
    if lh is None:
        lh = 8 * sc + 2
    lines = wrap(s, max_chars)[:max_lines]
    for i, ln in enumerate(lines):
        draw_text(x, y + i * lh, ln, sc, c)
    return y + len(lines) * lh


# ---------------------------------------------------------------- icons
def icon_clock(x, y, s, c):
    ring(x + s // 2, y + s // 2, s // 2 - 2, c, 3)
    line(x + s // 2, y + s // 2, x + s // 2, y + 8, c)
    line(x + s // 2, y + s // 2, x + s - 12, y + s // 2 + 6, c)
    disc(x + s // 2, y + s // 2, 3, c)


def icon_storm(x, y, s, c):
    cx, cy = x + s // 2, y + s // 2
    ring(cx, cy, s // 2 - 2, c, 3)
    ring(cx, cy, s // 3, c, 3)
    ring(cx, cy, s // 6, c, 2)
    line(cx, cy - s // 2 + 2, cx + 4, cy - s // 2 + 10, c)


def icon_chart(x, y, s, c):
    hline(x + 4, y + s - 6, s - 8, c)
    vline(x + 4, y + 6, s - 12, c)
    bw = (s - 18) // 3
    for i, h in enumerate((s // 3, s // 2, s - 14)):
        rect(x + 10 + i * (bw + 3), y + s - 6 - h, bw, h, c)


def icon_pad(x, y, s, c):
    rect(x + 4, y + s // 3, s - 8, s // 3 + 6, c)
    disc(x + s // 4, y + s // 2, 4, PAPER)
    disc(x + 3 * s // 4 - 4, y + s // 2 - 4, 3, PAPER)
    disc(x + 3 * s // 4 + 4, y + s // 2 + 4, 3, PAPER)


def icon_talk(x, y, s, c):
    disc(x + s // 3, y + s // 3, s // 4, c)
    disc(x + 2 * s // 3, y + 2 * s // 3, s // 4, c)
    tri(x + s // 3 - 4, y + s // 2, x + s // 3 + 8, y + s // 2,
        x + s // 3 + 2, y + s - 6, c)
    tri(x + 2 * s // 3 - 8, y + s // 2 + 6, x + 2 * s // 3 + 4,
        y + s // 2 + 6, x + 2 * s // 3 - 2, y + 6, c)


def icon_probe(x, y, s, c):
    cx, cy = x + s // 2, y + s // 2
    ring(cx, cy, s // 3, c, 3)
    line(cx - s // 3, cy + s // 3, cx + s // 3, cy - s // 3, c)
    rect(x + s - 14, y + 6, 8, 8, c)
    disc(x + 8, y + s - 10, 2, GOLD)
    disc(x + s - 8, y + s - 8, 2, GOLD)


def icon_rock(x, y, s, c):
    tri(x + 8, y + s - 8, x + s // 2, y + 6, x + s - 10, y + s // 3, c)
    tri(x + 8, y + s - 8, x + s - 10, y + s // 3, x + s - 6, y + s - 8, c)
    disc(x + s // 2, y + s // 2 + 4, 4, PAPER)


def icon_ball(x, y, s, c):
    cx, cy = x + s // 2, y + s // 2
    ring(cx, cy, s // 2 - 3, c, 3)
    disc(cx, cy, 6, c)
    line(cx, cy - 6, cx, cy - s // 2 + 4, c)
    line(cx - 5, cy + 3, cx - s // 2 + 6, cy + 8, c)
    line(cx + 5, cy + 3, cx + s // 2 - 6, cy + 8, c)


ICONS = {
    'clock': icon_clock, 'storm': icon_storm, 'chart': icon_chart,
    'pad': icon_pad, 'talk': icon_talk, 'probe': icon_probe,
    'rock': icon_rock, 'ball': icon_ball,
}

# ---------------------------------------------------------------- stories
# (kicker, headline lines, deck, icon, accent)
LEAD = (
    "USA  /  IRAN",
    ["TRUMP PUTS IRAN WAR", "DECISION OFF TO 2027"],
    "TRUMP SAYS THERE IS NO RUSH ON A DECISION OVER IRAN. HE WILL "
    "'SEE WHAT HAPPENS' AFTER JAN 1, PUSHING ANY WAR CALL INTO 2027.",
    'clock', RED,
)

STORIES = [
    ("INDIA  /  WEATHER",
     ["CYCLONE AKVAN HITS", "ODISHA AT NOON"],
     "MORE THAN 100,000 PEOPLE MOVED TO SHELTERS AS THE SEVERE STORM "
     "CROSSES INDIA'S EAST COAST WITH 100 KM/H WINDS.",
     'storm', BLUE),
    ("MARKETS",
     ["ANT CLOSES FIRST DAY", "UP 17 PERCENT"],
     "ANTHROPIC SHARES END AT $97.17 ON NASDAQ. ITS RECORD $81.3BN "
     "IPO CLOSES TODAY.",
     'chart', GOLD),
    ("CULTURE",
     ["GTA VI OUTSELLS", "THE ODYSSEY"],
     "ROCKSTAR'S GAME PASSES $1.80BN WORLDWIDE, MORE THAN THE YEAR'S "
     "BIGGEST FILM MADE IN ITS WHOLE RUN.",
     'pad', RED),
    ("EUROPE  /  UKRAINE",
     ["EUROPE READY TO TALK", "TO RUSSIA ON UKRAINE"],
     "EUROPEAN LEADERS SAY THEY ARE READY FOR TALKS WITH MOSCOW ON "
     "ENDING THE WAR, THE BBC REPORTS.",
     'talk', BLUE),
    ("SPACE",
     ["VOYAGER 1, A LIGHT-DAY", "AWAY FROM EARTH"],
     "NASA CONFIRMS THE PROBE IS NOW ONE LIGHT-DAY FROM EARTH, ABOUT "
     "16 BILLION MILES OUT.",
     'probe', GOLD),
    ("JAPAN  /  SPACE",
     ["HAYABUSA2 DROPS", "ASTEROID LANDING"],
     "ENGINE TROUBLE FORCES JAPAN'S PROBE TO GIVE UP ITS LANDING PLAN "
     "AND CHANGE COURSE.",
     'rock', RED),
    ("SPORT",
     ["INFANTINO FACES TWO", "RIVALS FOR FIFA TOP JOB"],
     "TWO CHALLENGERS STEP FORWARD FOR THE 2027 FIFA PRESIDENTIAL "
     "RACE AGAINST GIANNI INFANTINO.",
     'ball', BLUE),
]

BRIEF = [
    "GTA VI REVIEWS ARE IN.",
    "TODAY IS WORLD CHILDREN'S DAY.",
    "BRENT CRUDE HOLDS AT $92.",
]

# ---------------------------------------------------------------- compose
MX = 36
CW = W - 2 * MX  # 952

# masthead
title = "THE WORLD TODAY"
tw = text_w(title, 7)
draw_text(MX + (CW - tw) // 2, 34, title, 7, INK)
date_line = "FRIDAY - 20 NOVEMBER 2026"
dw = text_w(date_line, 2)
draw_text(MX + (CW - dw) // 2, 96, date_line, 2, RED)
hline(MX, 124, CW, INK)
hline(MX, 129, CW, INK)

# lead story, full width
LY, LH = 146, 196
rect(MX, LY, CW, LH, PALE)
rect(MX, LY, CW, 4, LEAD[4])
kicker, head, deck, icon, accent = LEAD
draw_text(MX + 22, LY + 16, kicker, 1, RED)
for i, ln in enumerate(head):
    draw_text(MX + 22, LY + 40 + i * 34, ln, 3, INK)
para(MX + 22, LY + 118, deck, 2, INK, 62, 3, 20)
ICONS[icon](MX + CW - 150, LY + 42, 110, accent)
hline(MX, LY + LH, CW, INK)

# grid: 2 columns x 4 rows
GX, GY = MX, 360
GW = (CW - 16) // 2  # 468
GH = 142
GAP = 16
cells = STORIES + [None]
for idx, st in enumerate(cells):
    col = idx % 2
    row = idx // 2
    x = GX + col * (GW + GAP)
    y = GY + row * (GH + 14)
    rect(x, y, GW, GH, PAPER)
    rect(x, y, GW, 3, INK)
    if st is None:
        draw_text(x + 16, y + 14, "IN BRIEF", 2, RED)
        for i, b in enumerate(BRIEF):
            draw_text(x + 16, y + 44 + i * 26, b, 1, INK)
        continue
    kicker, head, deck, icon, accent = st
    ICONS[icon](x + 14, y + 16, 56, accent)
    draw_text(x + 82, y + 12, kicker, 1, RED)
    for i, ln in enumerate(head):
        draw_text(x + 82, y + 32 + i * 18, ln, 2, INK)
    para(x + 16, y + 84, deck, 1, INK, 72, 3, 10)

# footer strip
FY = GY + 4 * GH + 3 * 14 + 16
hline(MX, FY, CW, INK)
foot = "THE WORLD TODAY  |  FRIDAY, 20 NOVEMBER 2026  |  NEWS AS REPORTED TODAY"
fw = text_w(foot, 1)
draw_text(MX + (CW - fw) // 2, FY + 12, foot, 1, GREY)

# ---------------------------------------------------------------- png write
def chunk(typ, data):
    out = struct.pack(">I", len(data)) + typ + data
    out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return out


raw = bytearray()
for yy in range(H):
    raw.append(0)
    raw += buf[yy * W * 3:(yy + 1) * W * 3]

ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
png = b"\x89PNG\r\n\x1a\n"
png += chunk(b"IHDR", ihdr)
png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
png += chunk(b"IEND", b"")

out = os.environ.get("OUT", "/output/entry.png")
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "wb") as f:
    f.write(png)
print("wrote", out, len(png), "bytes")
