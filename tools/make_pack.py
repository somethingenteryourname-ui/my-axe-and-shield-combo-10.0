# Regenerates the resource pack textures/models:  python3 tools/make_pack.py  (needs numpy + pillow)
"""Builds the AegisTitan resource pack textures + models."""
import json, math, os, random
import numpy as np
from PIL import Image

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "resourcepack")
TEX = f"{OUT}/assets/aegis/textures/item"
MOD = f"{OUT}/assets/aegis/models/item"
ITM = f"{OUT}/assets/aegis/items"
for d in (TEX, MOD, ITM):
    os.makedirs(d, exist_ok=True)

def rgb(h): return np.array([(h >> 16) & 255, (h >> 8) & 255, h & 255], dtype=float) / 255.0

def over(dst_rgb, dst_a, col, a):
    """alpha-composite a layer (col: HxWx3 or 3, a: HxW) over dst"""
    a = np.clip(a, 0, 1)[..., None]
    out_a = a + dst_a[..., None] * (1 - a)
    safe = np.where(out_a > 1e-6, out_a, 1)
    out_rgb = (col * a + dst_rgb * dst_a[..., None] * (1 - a)) / safe
    return out_rgb, out_a[..., 0]

def save(rgbf, af, path):
    img = np.dstack([np.clip(rgbf, 0, 1) * 255, np.clip(af, 0, 1) * 255]).astype(np.uint8)
    Image.fromarray(img, "RGBA").save(path)

# ============================================================ shield wall
N = 128
FRAMES = 16
ys, xs = np.mgrid[0:N, 0:N]
U = (xs + 0.5) / (N / 2) - 1.0          # -1..1 left->right
V = 1.0 - (ys + 0.5) / (N / 2)          # -1..1 bottom->top
TAPER = 0.38
CR_U, CR_V = 0.17, 0.24                  # rounded top corners (in normalised units)

def half_width(v):
    hw = np.ones_like(v)
    tt = (v + 1) / (2 * TAPER)
    hw = np.where(v < -1 + 2 * TAPER, np.sin(np.clip(tt, 0, 1) * np.pi / 2), hw)
    return np.where((v < -1) | (v > 1), -1, hw)

hw = half_width(V)
inside = (np.abs(U) <= hw)
corner = (V > 1 - CR_V) & (np.abs(U) > 1 - CR_U)
cu = (np.abs(U) - (1 - CR_U)) / CR_U
cv = (V - (1 - CR_V)) / CR_V
inside &= ~(corner & (cu * cu + cv * cv > 1))

# distance (pixels) from each inside pixel to the outline
edge_pts = np.argwhere(inside & ~(np.roll(inside, 1, 0) & np.roll(inside, -1, 0) & np.roll(inside, 1, 1) & np.roll(inside, -1, 1)))
ins = np.argwhere(inside)
dist = np.full((N, N), 99.0)
for chunk in np.array_split(ins, 32):
    d = np.sqrt(((chunk[:, None, :] - edge_pts[None, :, :]) ** 2).sum(-1)).min(1)
    dist[chunk[:, 0], chunk[:, 1]] = d

# "world-ish" coordinates for a 14 x 10 wall so the pattern matches the particle version
X = U * 7.0
Y = V * 5.0
SPACING = 1.45

def wall_frame(f, tint=None, rng=None):
    phase = f / FRAMES * 2 * np.pi
    col = np.zeros((N, N, 3)); a = np.zeros((N, N))
    # soft energy fill
    col, a = over(col, a, rgb(0x2B6BFF), np.where(inside, 0.16, 0))
    # diamond lattice with a shimmer wave running through it
    wave = np.sin(Y * 0.8 + X * 0.25 - phase)
    for sgn in (1, -1):
        c = (X * sgn + Y) / SPACING
        dline = np.abs(c - np.round(c)) * SPACING
        line = np.clip(1 - dline / 0.14, 0, 1) * inside * (dist > 3)
        bright = wave > 0.75; mid = (wave > 0) & ~bright
        lc = np.where(bright[..., None], rgb(0xC8F8FF), np.where(mid[..., None], rgb(0x3FB8FF), rgb(0x2B6BFF)))
        la = line * np.where(bright, 0.95, np.where(mid, 0.75, 0.5))
        col, a = over(col, a, lc, la)
    # scan line sweeping up
    vs = -1 + 2 * (f / FRAMES)
    band = np.clip(1 - np.abs(V - vs) / 0.05, 0, 1) * inside
    col, a = over(col, a, rgb(0xE8FDFF), band * 0.85)
    # spinning emblem (a circle once stretched onto the 14x10 wall)
    ex, ey = X - 0.0, Y - 0.5
    r = np.sqrt(ex ** 2 + ey ** 2); th = np.arctan2(ey, ex)
    R = 2.1
    ring = np.clip(1 - np.abs(r - R) / 0.16, 0, 1)
    dots = (np.cos(22 * (th - phase / 3)) > -0.2)
    col, a = over(col, a, rgb(0xB44CFF), ring * dots * inside)
    for arm in range(4):
        ang = -phase / 2 + arm * np.pi / 2
        ax, ay = np.cos(ang), np.sin(ang)
        along = ex * ax + ey * ay
        across = np.abs(-ex * ay + ey * ax)
        spoke = np.clip(1 - across / 0.11, 0, 1) * (along > 0.25) * (along < R * 0.8)
        col, a = over(col, a, rgb(0xFF7BFF), spoke * inside)
    # glowing rim
    glow = np.clip(1 - (dist - 2.5) / 5.0, 0, 1) * inside
    col, a = over(col, a, rgb(0x3FE0FF), glow * 0.85)
    rim = (dist < 2.6) & inside
    col, a = over(col, a, rgb(0xE6FFFF), rim * 1.0)
    # twinkles
    rng = rng or random.Random(f * 7 + 3)
    for _ in range(6):
        for _try in range(20):
            px, py = rng.randrange(N), rng.randrange(N)
            if inside[py, px]:
                break
        sp = np.clip(1 - np.sqrt((xs - px) ** 2 + (ys - py) ** 2) / 1.8, 0, 1)
        col, a = over(col, a, rgb(0xFFFFFF), sp)
    if tint is not None:
        col = col * 0.45 + tint * 0.55 * (col.mean(-1, keepdims=True) + 0.3)
    return col, a

frames = [wall_frame(f) for f in range(FRAMES)]
strip_c = np.concatenate([c for c, _ in frames], 0)
strip_a = np.concatenate([a for _, a in frames], 0)
save(strip_c, strip_a, f"{TEX}/aegis_wall.png")
json.dump({"animation": {"frametime": 2, "interpolate": True}}, open(f"{TEX}/aegis_wall.png.mcmeta", "w"), indent=2)

# broken halves (static, red-hot)
bc, ba = wall_frame(0, tint=rgb(0xFF4A30))
rng = random.Random(5)
jag = np.array([rng.uniform(-3, 3) for _ in range(N)])
for side, name in ((-1, "left"), (1, "right")):
    cut_x = N / 2 + jag[ys]
    mask = (xs < cut_x) if side < 0 else (xs >= cut_x)
    near = np.clip(1 - np.abs(xs - cut_x) / 4, 0, 1) * mask * inside
    c2, a2 = over(bc.copy(), ba * mask, rgb(0xFFB040), near * 0.95)
    save(c2, a2 * mask, f"{TEX}/wall_broken_{name}.png")

def plane_model(tex):
    return {"textures": {"t": f"aegis:item/{tex}", "particle": f"aegis:item/{tex}"},
            "elements": [{"from": [0, 0, 8], "to": [16, 16, 8], "shade": False,
                          "faces": {"north": {"uv": [0, 0, 16, 16], "texture": "#t"},
                                    "south": {"uv": [16, 0, 0, 16], "texture": "#t"}}}]}

for name in ("aegis_wall", "wall_broken_left", "wall_broken_right"):
    json.dump(plane_model(name), open(f"{MOD}/{name}.json", "w"), indent=2)

# ============================================================ giant axe (extruded, solid)
AX = 128
SS = 4                      # supersample for smooth colours / clean edges
G = AX * SS
PPU = AX / 13.5            # pixels per block at size 1 (texture covers 13.5 x 13.5 blocks)
HX, HY = 17.0, 119.0       # pivot (bottom of handle) in texture pixels
gy, gx = np.mgrid[0:G, 0:G]
px = (gx + 0.5) / SS; py = (gy + 0.5) / SS
T = (px - HX) / PPU        # toward the blade
S = (HY - py) / PPU        # up the handle
ac = np.zeros((G, G, 3)); aa = np.zeros((G, G))

def paint(mask, color, alpha=1.0):
    global ac, aa
    ac, aa = over(ac, aa, color if np.ndim(color) == 3 else np.broadcast_to(color, (G, G, 3)), mask * alpha)

HANDLE, BLADE, HEAD = 11.0, 3.4, 10.0
# handle with leather wraps and a highlight
handle = (np.abs(T) <= 0.24) & (S >= -0.4) & (S <= HANDLE + 0.5)
wrap = handle & (S < HANDLE * 0.55) & ((np.floor(S / 1.1) % 2) == 0)
paint(handle, rgb(0x2B2527))
paint(wrap, rgb(0x5A4636))
paint(handle & (T > 0.08), rgb(0x4A4046), 0.6)
# pommel
paint(((T ** 2 + (S + 0.6) ** 2) < 0.36 ** 2), rgb(0x6B3F7A))
# blade: flares out to a curved cutting edge
q = S - HEAD
hl = 0.75 + 1.55 * np.clip(T / BLADE, 0, 1) ** 1.6
edgeT = BLADE - 0.55 * (q / 2.3) ** 2
blade = (T >= 0) & (T <= edgeT) & (np.abs(q) <= hl)
shade = np.clip(0.75 + 0.35 * (T / BLADE), 0, 1)[..., None]
paint(blade, rgb(0x4D494F) * shade)
trim = blade & ((np.abs(q) > hl - 0.28) | (T < 0.32))
paint(trim, rgb(0x6B3F7A))
edge = blade & (T > edgeT - 0.5)
paint(edge, rgb(0x9C97A0))
hot = blade & (T > edgeT - 0.22)
hotc = np.dstack([np.ones((G, G)), 0.48 + 0.4 * np.clip((T - (edgeT - 0.22)) / 0.22, 0, 1), 0.1 + 0.5 * np.clip((T - (edgeT - 0.22)) / 0.22, 0, 1)])
paint(hot, hotc)
# back spike
tb = -T
spike_hl = 0.55 * (1 - np.clip(tb - 0.3, 0, 1))
spike = (tb >= 0.2) & (tb <= 1.3) & (np.abs(q) <= spike_hl)
paint(spike, rgb(0x4D494F))
paint(spike & (np.abs(q) > spike_hl - 0.2), rgb(0x6B3F7A))
# collar where the head grips the handle
paint((np.abs(T) <= 0.36) & (S > HEAD - 1.3) & (S < HEAD + 1.3), rgb(0x3A3440))
paint((np.abs(T) <= 0.36) & (np.abs(S - (HEAD - 1.3)) < 0.12), rgb(0x6B3F7A))

# downsample: average colour of covered samples, crisp 0/1 alpha
def down(c, a):
    c4 = (c * a[..., None]).reshape(AX, SS, AX, SS, 3).sum((1, 3))
    a4 = a.reshape(AX, SS, AX, SS).sum((1, 3))
    col = c4 / np.maximum(a4, 1e-6)[..., None]
    alpha = (a4 / (SS * SS) >= 0.5).astype(float)
    return col, alpha
c_ax, a_ax = down(ac, aa)
save(c_ax, a_ax, f"{TEX}/titan_axe_giant.png")
json.dump({"parent": "minecraft:item/generated", "textures": {"layer0": "aegis:item/titan_axe_giant"}},
          open(f"{MOD}/titan_axe_giant.json", "w"), indent=2)

# ============================================================ flying spike (crossed planes)
SP = 64
G = SP * SS
gy, gx = np.mgrid[0:G, 0:G]
px = (gx + 0.5) / SS; py = (gy + 0.5) / SS
f = np.clip((62 - py) / 60, 0, 1)                   # 0 at the base, 1 at the tip
halfw = 10.5 * (1 - f) ** 0.9 * (1 + 0.08 * np.sin(py * 1.3))
rock = (np.abs(px - 32) <= halfw) & (py >= 2) & (py <= 62)
ac = np.zeros((G, G, 3)); aa = np.zeros((G, G))
G_ = G
def paint2(mask, color, alpha=1.0):
    global ac, aa
    ac, aa = over(ac, aa, np.broadcast_to(color, (G_, G_, 3)) if np.ndim(color) == 1 else color, mask * alpha)
paint2(rock, rgb(0x4A4450))
paint2(rock & (((px - 32) / np.maximum(halfw, 0.1)) > 0.15), rgb(0x77707F))
crack_x = 32 + 3.5 * np.sin(py * 0.45)
paint2(rock & (np.abs(px - crack_x) < 0.9) & (f < 0.8), rgb(0xFF5A10))
tipc = np.dstack([np.ones((G, G)), 0.5 + 0.45 * np.clip((f - 0.72) / 0.28, 0, 1), 0.1 + 0.8 * np.clip((f - 0.72) / 0.28, 0, 1)])
paint2(rock & (f > 0.72), tipc)
cs = (ac * aa[..., None]).reshape(SP, SS, SP, SS, 3).sum((1, 3))
as_ = aa.reshape(SP, SS, SP, SS).sum((1, 3))
save(cs / np.maximum(as_, 1e-6)[..., None], (as_ / (SS * SS) >= 0.5).astype(float), f"{TEX}/titan_spike.png")
json.dump({"textures": {"s": "aegis:item/titan_spike", "particle": "aegis:item/titan_spike"},
           "elements": [
               {"from": [0, 0, 8], "to": [16, 16, 8], "shade": False,
                "faces": {"north": {"uv": [0, 0, 16, 16], "texture": "#s"}, "south": {"uv": [16, 0, 0, 16], "texture": "#s"}}},
               {"from": [8, 0, 0], "to": [8, 16, 16], "shade": False,
                "faces": {"east": {"uv": [0, 0, 16, 16], "texture": "#s"}, "west": {"uv": [16, 0, 0, 16], "texture": "#s"}}}]},
          open(f"{MOD}/titan_spike.json", "w"), indent=2)

# ============================================================ item model definitions + pack.mcmeta
for name in ("aegis_wall", "wall_broken_left", "wall_broken_right", "titan_axe_giant", "titan_spike"):
    json.dump({"model": {"type": "minecraft:model", "model": f"aegis:item/{name}"}}, open(f"{ITM}/{name}.json", "w"), indent=2)
json.dump({"pack": {"description": "AegisTitan solid shield wall & Titan Cleaver models", "min_format": 75, "max_format": 99}},
          open(f"{OUT}/pack.mcmeta", "w"), indent=2)
print("pack built")
