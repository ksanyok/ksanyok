#!/usr/bin/env python3
"""Build neofetch-style profile SVG (dark + light) with colored ASCII portrait."""
from PIL import Image, ImageOps, ImageEnhance
import html

SRC = "avatar.png"
W = 84
GAMMA = 0.58
CHAR_ASPECT = 0.47
RAMP = " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"

img = Image.open(SRC).convert("RGB")
w, h = img.size
img = img.crop((int(w*0.10), int(h*0.02), int(w*0.90), int(h*0.86)))
H = int(W * img.height / img.width * CHAR_ASPECT)
small = img.resize((W, H), Image.LANCZOS)
gray = ImageOps.autocontrast(small.convert("L"), cutoff=1)

def make_colors(lift):
    c = ImageEnhance.Color(small).enhance(1.85)
    return c.point(lambda v: int(255 * ((v / 255.0) ** lift)))

def quant(rgb, step=28):
    return tuple(min(255, (v // step) * step + step // 2) for v in rgb)

def build_art_rows(color_img):
    rows = []
    for y in range(H):
        runs = []  # (color, text)
        cur_color, cur_text = None, ""
        for x in range(W):
            l = (gray.getpixel((x, y)) / 255.0) ** GAMMA
            ch = RAMP[int(l * (len(RAMP) - 1))]
            col = quant(color_img.getpixel((x, y)))
            if ch == " ":
                col = None  # color irrelevant for spaces; merge into current run
            if cur_color is None and cur_text == "":
                cur_color, cur_text = col, ch
            elif col is None or col == cur_color or cur_color is None:
                if cur_color is None and col is not None:
                    cur_color = col
                cur_text += ch
            else:
                runs.append((cur_color, cur_text))
                cur_color, cur_text = col, ch
        runs.append((cur_color, cur_text))
        rows.append(runs)
    return rows

# ---------------- info block content ----------------
# segments: (text, colorkey)  colorkeys: user, host, dim, label, value, accent, star
FIELD = 12  # label field width before dots padding

def info_lines(stats):
    L = []
    L.append([("aleksandr", "user"), ("@", "dim"), ("ksanyok", "host")])
    L.append([("─" * 52, "dim")])
    def kv(label, value_segs):
        dots = FIELD - len(label)
        segs = [(label, "label"), (" " + "·" * dots + " ", "dim")]
        segs += value_segs
        return segs
    L.append(kv("OS", [("macOS · Debian · iOS · Android", "value")]))
    L.append(kv("Uptime", [(stats["uptime"], "value", "stat_uptime")]))
    L.append(kv("Host", [("BuyReadySite.com", "accent"), (" — Founder", "value")]))
    L.append(kv("Kernel", [("Full-Stack Dev · SaaS Builder", "value")]))
    L.append(kv("IDE", [("VS Code · Xcode · Claude Code", "value")]))
    L.append([])
    L.append(kv("Code", [("PHP · Python · TypeScript · Swift · JS", "value")]))
    L.append(kv("Stack", [("React · Node.js · WordPress · MySQL", "value")]))
    L.append(kv("AI", [("OpenAI · Claude · Whisper · OpenRouter", "value")]))
    L.append(kv("Human", [("Українська · English · Русский", "value")]))
    L.append([])
    L.append(kv("SaaS", [("PromoPilot · TextHumanize · RankBot AI", "accent")]))
    L.append(kv("Apps", [("Sonus · Brisa · VoltPing", "value")]))
    L.append(kv("Focus", [("AI automation · SEO · macOS/iOS apps", "value")]))
    L.append([])
    L.append(kv("Web", [("buyreadysite.com", "link")]))
    L.append(kv("Telegram", [("t.me/buyreadysite", "link")]))
    L.append(kv("LinkedIn", [("in/ksanyok", "link")]))
    L.append([])
    L.append([("GitHub Stats", "user")])
    L.append([("─" * 52, "dim")])
    L.append(kv("Repos", [
        (stats["repos"], "value", "stat_repos"),
        (" { ", "dim"), (stats["public"], "value", "stat_public"), (" public }", "dim"),
        ("  ★ ", "star"), (stats["stars"], "value", "stat_stars"), (" stars", "dim")]))
    L.append(kv("Commits", [
        (stats["contribs"], "value", "stat_contribs"),
        (" contributions (last year)", "dim")]))
    L.append([])
    return L

PALETTES = {
    "dark": {
        "bg": "#0d1117", "border": "#30363d", "titlebar": "#161b22",
        "title": "#8b949e",
        "user": "#3fb950", "host": "#3fb950", "dim": "#8b949e",
        "label": "#58a6ff", "value": "#c9d1d9", "accent": "#d2a8ff",
        "link": "#a5d6ff", "star": "#e3b341",
        "blocks": ["#ff7b72", "#ffa657", "#e3b341", "#3fb950", "#58a6ff", "#bc8cff", "#f778ba", "#c9d1d9"],
        "lift": 0.50,
    },
    "light": {
        "bg": "#ffffff", "border": "#d0d7de", "titlebar": "#f6f8fa",
        "title": "#57606a",
        "user": "#1a7f37", "host": "#1a7f37", "dim": "#6e7781",
        "label": "#0969da", "value": "#24292f", "accent": "#8250df",
        "link": "#0a3069", "star": "#9a6700",
        "blocks": ["#cf222e", "#bc4c00", "#9a6700", "#1a7f37", "#0969da", "#8250df", "#bf3989", "#57606a"],
        "lift": 1.0,
    },
}

def esc(t):
    return html.escape(t, quote=False).replace(" ", " ")

def build_svg(theme):
    P = PALETTES[theme]
    art_rows = build_art_rows(make_colors(P["lift"]))

    FS = 10          # art font size
    RH = 10.4        # art row height
    CW = 6.02        # char advance
    art_w = W * CW
    pad = 18
    bar_h = 30
    art_x, art_y = pad, bar_h + 16
    info_x = art_x + art_w + 26
    info_fs = 12.0
    info_cw = info_fs * 0.602
    info_rh = 16.6
    total_w = int(info_x + 54 * info_cw + 20)
    total_h = int(max(art_y + H * RH, art_y + 24 * info_rh) + 26)

    s = []
    s.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="{total_h}" viewBox="0 0 {total_w} {total_h}" font-family="\'SFMono-Regular\',\'Cascadia Code\',Consolas,\'Liberation Mono\',Menlo,monospace">')
    s.append(f'<rect x="0.5" y="0.5" width="{total_w-1}" height="{total_h-1}" rx="12" fill="{P["bg"]}" stroke="{P["border"]}"/>')
    # title bar
    s.append(f'<path d="M0.5 {bar_h} L0.5 12.5 A12 12 0 0 1 12.5 0.5 L{total_w-12.5} 0.5 A12 12 0 0 1 {total_w-0.5} 12.5 L{total_w-0.5} {bar_h} Z" fill="{P["titlebar"]}"/>')
    s.append(f'<line x1="0.5" y1="{bar_h}" x2="{total_w-0.5}" y2="{bar_h}" stroke="{P["border"]}"/>')
    for i, c in enumerate(["#ff5f57", "#febc2e", "#28c840"]):
        s.append(f'<circle cx="{20 + i*20}" cy="{bar_h/2}" r="5.5" fill="{c}"/>')
    s.append(f'<text x="{total_w/2}" y="{bar_h/2 + 4}" text-anchor="middle" font-size="11.5" fill="{P["title"]}">aleksandr@ksanyok: ~/neofetch</text>')

    # ASCII art
    for y, runs in enumerate(art_rows):
        yy = art_y + y * RH + FS
        parts = []
        for col, text in runs:
            if col is None:
                parts.append(f'<tspan>{esc(text)}</tspan>')
            else:
                parts.append(f'<tspan fill="rgb({col[0]},{col[1]},{col[2]})">{esc(text)}</tspan>')
        s.append(f'<text x="{art_x}" y="{yy:.1f}" font-size="{FS}" textLength="{art_w:.0f}" lengthAdjust="spacingAndGlyphs" xml:space="preserve">{"".join(parts)}</text>')

    # info block
    stats = {
        "uptime": "7 yrs 8 mos on GitHub", "repos": "49", "public": "26",
        "stars": "61", "contribs": "3,038",
    }
    lines = info_lines(stats)
    iy = art_y + 6
    for line in lines:
        iy += info_rh
        if not line:
            continue
        parts = []
        nchars = 0
        for seg in line:
            text, key = seg[0], seg[1]
            nchars += len(text)
            sid = f' id="{seg[2]}"' if len(seg) > 2 else ""
            parts.append(f'<tspan{sid} fill="{P[key]}">{esc(text)}</tspan>')
        tl = f' textLength="{nchars * info_cw:.1f}" lengthAdjust="spacingAndGlyphs"' if nchars > 20 else ""
        s.append(f'<text x="{info_x}" y="{iy:.1f}" font-size="{info_fs}"{tl} xml:space="preserve">{"".join(parts)}</text>')

    # neofetch color blocks
    iy += 6
    bw = (52 * info_cw) / 8
    bh = 13
    for i, c in enumerate(P["blocks"]):
        s.append(f'<rect x="{info_x + i*bw:.1f}" y="{iy:.1f}" width="{bw:.1f}" height="{bh}" fill="{c}"/>')

    s.append("</svg>")
    return "\n".join(s)

for theme in ("dark", "light"):
    svg = build_svg(theme)
    fn = f"neofetch-{theme}.svg"
    open(fn, "w").write(svg)
    print(fn, len(svg), "bytes")
