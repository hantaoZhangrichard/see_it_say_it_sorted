# color_utils.py

from __future__ import annotations
import re
from typing import Tuple

#  CSS named colors 
CSS_COLOR_MAP = {
    "black": "#000000", "white": "#ffffff", "red": "#ff0000", "green": "#008000",
    "blue": "#0000ff", "yellow": "#ffff00", "purple": "#800080", "orange": "#ffa500",
    "coral": "#ff7f50", "navy": "#000080", "teal": "#008080", "olive": "#808000",
    "gray": "#808080", "grey": "#808080", "pink": "#ffc0cb", "brown": "#a52a2a",
    "gold": "#ffd700", "silver": "#c0c0c0", "indigo": "#4b0082", "violet": "#ee82ee",
    "salmon": "#fa8072", "tomato": "#ff6347", "crimson": "#dc143c", "khaki": "#f0e68c",
    "plum": "#dda0dd", "orchid": "#da70d6", "turquoise": "#40e0d0", "cyan": "#00ffff",
    "magenta": "#ff00ff", "aquamarine": "#7fffd4", "beige": "#f5f5dc",
    "chocolate": "#d2691e", "darkblue": "#00008b", "darkgreen": "#006400",
    "darkred": "#8b0000", "lightblue": "#add8e6", "lightgreen": "#90ee90",
    "lightpink": "#ffb6c1",
    # ... can add more
}


COLLOQUIAL_BASE = {
    "matcha": "#a3c686",          
    "baby blue": "#a7c7e7",      
    "baby pink": "#f6c1cf",       
    "baby purple": "#cab8ff",
    "pastel blue": "#aec6ff",
    "pastel green": "#bfe3b4",
    "pastel yellow": "#fff4a3",
    "pastel pink": "#ffcfe1",
    "pastel purple": "#cbb9ff",
    "mint": "#aee5c9",
    "lavender": "#e6e6fa",
    "peach":    "#ffcba4",   
    "cream":    "#fffdd0",   
    "sage":     "#9caf88",  
    "charcoal": "#36454f",   
}

HEX_RE = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
RGB_RE = re.compile(r"^rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)$")
HSL_RE = re.compile(r"^hsl\(\s*(\d{1,3})\s*,\s*(\d{1,3})%\s*,\s*(\d{1,3})%\s*\)$")
DESAT_ONE_TOKEN_RE = re.compile(r"^desaturate[-_]?(\d{1,3})%?$")  # desaturate-20 / desaturate20 / desaturate-20%
PCT_RE             = re.compile(r"^(\d{1,3})%$")                  # 20%


def desaturate_hex(hexv: str, pct: int) -> str:
    """Reduce saturation of a color by pct% while keeping hue and lightness."""
    pct = int(clamp(pct, 0, 100))
    r, g, b = hex_to_rgb(hexv)
    h, s, l = rgb_to_hsl(r, g, b)
    s_scaled = s * (1 - pct / 100.0)  # shrink saturation multiplicatively
    r2, g2, b2 = hsl_to_rgb(h, s_scaled, l)
    return rgb_to_hex(r2, g2, b2)


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

def hex_to_rgb(hexv: str) -> Tuple[int,int,int]:
    hexv = hexv.lstrip("#")
    if len(hexv) == 3:
        hexv = "".join(ch*2 for ch in hexv)
    return tuple(int(hexv[i:i+2], 16) for i in (0,2,4))

def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02x}{g:02x}{b:02x}"

def rgb_to_hsl(r: int, g: int, b: int) -> Tuple[float,float,float]:
    r_, g_, b_ = [c/255.0 for c in (r,g,b)]
    mx, mn = max(r_, g_, b_), min(r_, g_, b_)
    l = (mx + mn) / 2.0
    if mx == mn:
        h = s = 0.0
    else:
        d = mx - mn
        s = d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)
        if mx == r_:
            h = (g_ - b_) / d + (6 if g_ < b_ else 0)
        elif mx == g_:
            h = (b_ - r_) / d + 2
        else:
            h = (r_ - g_) / d + 4
        h /= 6
    return (h*360.0, s*100.0, l*100.0)

def _hue_to_rgb(p, q, t):
    if t < 0: t += 1
    if t > 1: t -= 1
    if t < 1/6: return p + (q - p) * 6 * t
    if t < 1/2: return q
    if t < 2/3: return p + (q - p) * (2/3 - t) * 6
    return p

def hsl_to_rgb(h: float, s: float, l: float) -> Tuple[int,int,int]:
    h_, s_, l_ = (h/360.0, s/100.0, l/100.0)
    if s_ == 0:
        v = int(round(l_*255))
        return (v, v, v)
    # --- fix here ---
    q = l_ * (1 + s_) if l_ < 0.5 else l_ + s_ - l_ * s_
    p = 2*l_ - q
    r = _hue_to_rgb(p, q, h_ + 1/3)
    g = _hue_to_rgb(p, q, h_)
    b = _hue_to_rgb(p, q, h_ - 1/3)
    return (int(round(r*255)), int(round(g*255)), int(round(b*255)))

def adjust_hsl(hexv: str, d_h=0, d_s=0, d_l=0) -> str:
    r,g,b = hex_to_rgb(hexv)
    h,s,l = rgb_to_hsl(r,g,b)
    h = (h + d_h) % 360
    s = clamp(s + d_s, 0, 100)
    l = clamp(l + d_l, 0, 100)
    r2,g2,b2 = hsl_to_rgb(h, s, l)
    return rgb_to_hex(r2,g2,b2)


MODIFIERS = {
    "baby":   {"d_s": -25, "d_l": +20}, 
    "pastel": {"d_s": -30, "d_l": +18},   
    "light":  {"d_s":   0, "d_l": +15},
    "dark":   {"d_s":   0, "d_l": -15},
    "bright": {"d_s": +20, "d_l":  0},
    "deep":   {"d_s": +10, "d_l": -10},
    "neon":   {"d_s": +35, "d_l":  0},
}

def _apply_modifiers(hexv: str, tokens) -> str:
    out = hexv
    i = 0
    while i < len(tokens):
        t = tokens[i]

        m = MODIFIERS.get(t)
        if m:
            out = adjust_hsl(out, d_s=m.get("d_s", 0), d_l=m.get("d_l", 0))
            i += 1
            continue

        m_desat = DESAT_ONE_TOKEN_RE.match(t)
        if m_desat:
            pct = int(m_desat.group(1))
            out = desaturate_hex(out, pct)
            i += 1
            continue

        if t == "desaturate" and i + 1 < len(tokens):
            m_pct = PCT_RE.match(tokens[i+1])
            if m_pct:
                pct = int(m_pct.group(1))
                out = desaturate_hex(out, pct)
                i += 2
                continue
        i += 1

    return out


def _parse_tokens(name: str) -> str | None:
    if name in COLLOQUIAL_BASE:
        return COLLOQUIAL_BASE[name]
    
    parts = name.split()
    for k in range(len(parts)-1, -1, -1):
        base = " ".join(parts[k:])
        if base in COLLOQUIAL_BASE:
            base_hex = COLLOQUIAL_BASE[base]
            return _apply_modifiers(base_hex, parts[:k])
        if base in CSS_COLOR_MAP:
            base_hex = CSS_COLOR_MAP[base]
            return _apply_modifiers(base_hex, parts[:k])

    return None

def normalize_color(value: str) -> str:
    """Return a #rrggbb hex (or 'none') for a wide range of inputs."""
    v = value.strip().lower()
    if v == "none":
        return "none"

    if HEX_RE.match(v):
        if len(v) == 4:
            r,g,b = v[1], v[2], v[3]
            v = f"#{r}{r}{g}{g}{b}{b}"
        return v

    m = RGB_RE.match(v)
    if m:
        r,g,b = [clamp(int(x), 0, 255) for x in m.groups()]
        return rgb_to_hex(int(r), int(g), int(b))

    m = HSL_RE.match(v)
    if m:
        h = clamp(int(m.group(1)), 0, 360)
        s = clamp(int(m.group(2)), 0, 100)
        l = clamp(int(m.group(3)), 0, 100)
        r,g,b = hsl_to_rgb(h, s, l)
        return rgb_to_hex(r,g,b)

    if v in CSS_COLOR_MAP:
        return CSS_COLOR_MAP[v]

    parsed = _parse_tokens(v)
    if parsed:
        return parsed

    if v.replace(" ", "") in CSS_COLOR_MAP:
        return CSS_COLOR_MAP[v.replace(" ", "")]
    return "#000000"
