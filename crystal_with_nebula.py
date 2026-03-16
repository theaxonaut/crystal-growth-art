# ================================================================
#  ALL-RGB CRYSTAL GROWTH — Fast & Simple (Numba JIT)
#  Every pixel is a unique 8-bit RGB color. No extras.
#  Expected time: ~2 min total on Colab (any runtime type)
# ================================================================


# ╔═══════════════════════════════════════════════════════════╗
# ║  ✏️  YOU CAN EDIT THESE                                   ║
# ╚═══════════════════════════════════════════════════════════╝

RANDOM_SEED = 51

SEED_X      = 0.3      # 0.0 = left    0.5 = center    1.0 = right
SEED_Y      = 0.2      # 0.0 = top     0.5 = center    1.0 = bottom

# ── Shape ────────────────────────────────────────────────────
SHAPE_MODE  = "nebula" # "organic"  →  even random blob
                       # "rays"     →  sharp starburst arms
                       # "nebula"   →  cloudy drifting masses

NUM_RAYS    = 2        # arms (rays mode only)
SHARPNESS   = 8.0      # 1 = fuzzy   8 = clear   15 = laser  (rays + nebula)

# ── Nebula controls (nebula mode only) ───────────────────────
NEBULA_SCALE    = 1.5  # cloud size: 0.5 = huge rolling clouds
                       #             1.0 = medium   3.0 = fine wisps
NEBULA_OCTAVES  = 6    # detail layers: 3 = smooth   6 = detailed   9 = noisy
NEBULA_CONTRAST = 3.0  # cloud edge sharpness: 1 = soft   3 = crisp   6 = harsh

OUT_PATH    = "crystal.png"


# ╔═══════════════════════════════════════════════════════════╗
# ║  🔒  DON'T EDIT BELOW HERE                               ║
# ╚═══════════════════════════════════════════════════════════╝

import numpy as np
from PIL import Image
from numba import njit
import math, time

np.random.seed(RANDOM_SEED)

WIDTH = HEIGHT = 4096
N = WIDTH * HEIGHT
TOURNAMENT_K = max(1, int(SHARPNESS ** 1.6))

seed_y = int(max(0, min(HEIGHT-1, round(SEED_Y*(HEIGHT-1)))))
seed_x = int(max(0, min(WIDTH-1,  round(SEED_X*(WIDTH-1)))))
print(f"Seed: ({seed_x}, {seed_y})  |  Shape: {SHAPE_MODE}  "
      f"|  Rays: {NUM_RAYS}  |  K: {TOURNAMENT_K}")

# ── Step 1: all 16M colors ────────────────────────────────────
print("\nStep 1: Generating colors...")
t = time.time()
idx   = np.arange(N, dtype=np.int32)
r_all = ((idx >> 16) & 0xFF).astype(np.uint8)
g_all = ((idx >>  8) & 0xFF).astype(np.uint8)
b_all = ( idx        & 0xFF).astype(np.uint8)
print(f"  {time.time()-t:.2f}s")

# ── Step 2: Morton sort ───────────────────────────────────────
print("Step 2: Morton sort...")
t = time.time()
lut = np.zeros(256, dtype=np.uint32)
for i in range(256):
    v = np.uint32(0)
    for bit in range(8):
        if i & (1 << bit):
            v |= np.uint32(1 << (bit*3))
    lut[i] = v
mort  = lut[r_all] | (lut[g_all] << np.uint32(1)) | (lut[b_all] << np.uint32(2))
order = np.argsort(mort, kind='stable')
colors = np.stack([r_all[order], g_all[order], b_all[order]], axis=1)
colors = np.ascontiguousarray(colors)
print(f"  {time.time()-t:.2f}s")

# ── Step 3: score map ─────────────────────────────────────────
print("Step 3: Score map...")
t = time.time()

dy_m = (np.arange(HEIGHT, dtype=np.float32) - seed_y)[:, None] * np.ones((1, WIDTH), dtype=np.float32)
dx_m = (np.arange(WIDTH,  dtype=np.float32) - seed_x)[None, :] * np.ones((HEIGHT, 1), dtype=np.float32)

if SHAPE_MODE == "rays" and TOURNAMENT_K > 1:
    theta   = np.arctan2(dy_m, dx_m)
    step_a  = 2 * math.pi / NUM_RAYS
    nearest = np.round(theta / step_a) * step_a
    diff    = np.abs(theta - nearest)
    diff    = np.minimum(diff, step_a - diff)
    score   = np.exp(-SHARPNESS * diff**2 * NUM_RAYS).astype(np.float32)

elif SHAPE_MODE == "nebula" and TOURNAMENT_K > 1:
    # Fractional Brownian Motion (fBm) using layered sine waves.
    # Each octave adds a finer layer of detail at a random angle.
    # No external library needed — pure numpy.
    rng = np.random.RandomState(RANDOM_SEED)
    xs = np.linspace(0, NEBULA_SCALE * 4, WIDTH,  dtype=np.float32)
    ys = np.linspace(0, NEBULA_SCALE * 4, HEIGHT, dtype=np.float32)
    xg, yg = np.meshgrid(xs, ys)

    noise = np.zeros((HEIGHT, WIDTH), dtype=np.float32)
    amp, freq = 1.0, 1.0
    total_amp  = 0.0

    for _ in range(NEBULA_OCTAVES):
        # random rotation angle per octave gives natural-looking swirling
        angle  = rng.uniform(0, 2 * math.pi)
        ox     = rng.uniform(0, 100)
        oy     = rng.uniform(0, 100)
        rx = np.cos(angle) * xg * freq - np.sin(angle) * yg * freq + ox
        ry = np.sin(angle) * xg * freq + np.cos(angle) * yg * freq + oy
        # layered sin×cos gives smoother, more varied cloud shapes than sin alone
        layer  = np.sin(rx) * np.cos(ry) + 0.5 * np.sin(rx * 1.7 + ry * 0.9)
        noise += amp * layer
        total_amp += amp
        amp  *= 0.5
        freq *= 2.1    # slightly non-power-of-2 avoids grid artefacts

    noise /= total_amp                         # normalise to [-1, 1]
    noise  = (noise - noise.min()) / (noise.max() - noise.min())  # → [0, 1]

    # raise to power to punch up contrast (crisp bright clouds, dark voids)
    score  = np.power(noise, NEBULA_CONTRAST).astype(np.float32)

    # optionally blend with a radial falloff so growth still centres on seed
    dist  = np.sqrt(dy_m**2 + dx_m**2)
    radial = np.exp(-dist / (max(WIDTH, HEIGHT) * 0.6)).astype(np.float32)
    score  = score * 0.85 + radial * 0.15     # mostly noise, slight pull to seed

else:
    score = np.ones((HEIGHT, WIDTH), dtype=np.float32)

score[seed_y, seed_x] = 1.0
score_flat = np.ascontiguousarray(score.ravel())
print(f"  {time.time()-t:.2f}s")

# ── Step 4: Numba BFS ─────────────────────────────────────────
@njit(cache=True)
def crystal_bfs(colors, score_flat, seed_y, seed_x, W, H, tournament_k, rng_seed):
    N      = W * H
    pixels = np.zeros((H, W, 3), dtype=np.uint8)
    filled = np.zeros(N, dtype=np.bool_)
    queued = np.zeros(N, dtype=np.bool_)
    front  = np.empty(N, dtype=np.int32)
    f_size = np.int32(0)
    color_idx = np.int32(0)

    DY = np.array([-1,-1,-1, 0, 0, 1, 1, 1], dtype=np.int32)
    DX = np.array([-1, 0, 1,-1, 1,-1, 0, 1], dtype=np.int32)

    rng = np.uint64(rng_seed * 6364136223846793005 + 1442695040888963407)

    def rand_int(n):
        nonlocal rng
        rng = rng * np.uint64(6364136223846793005) + np.uint64(1442695040888963407)
        return int((rng >> np.uint64(33)) % np.uint64(n))

    # plant seed
    sp = seed_y * W + seed_x
    pixels[seed_y, seed_x, 0] = colors[color_idx, 0]
    pixels[seed_y, seed_x, 1] = colors[color_idx, 1]
    pixels[seed_y, seed_x, 2] = colors[color_idx, 2]
    filled[sp] = True
    color_idx += 1

    for d in range(8):
        ny = seed_y + DY[d]
        nx = seed_x + DX[d]
        if 0 <= ny < H and 0 <= nx < W:
            np_ = ny * W + nx
            if not queued[np_]:
                front[f_size] = np_
                f_size += 1
                queued[np_] = True

    while f_size > 0 and color_idx < N:
        if tournament_k <= 1:
            i = rand_int(f_size)
        else:
            k      = min(tournament_k, int(f_size))
            best_i = rand_int(f_size)
            best_s = score_flat[front[best_i]]
            for _ in range(k - 1):
                ci = rand_int(f_size)
                s  = score_flat[front[ci]]
                if s > best_s:
                    best_s = s
                    best_i = ci
            i = best_i

        packed     = front[i]
        front[i]   = front[f_size - 1]
        f_size    -= 1

        y = packed // W
        x = packed  % W
        queued[packed] = False

        if filled[packed]:
            continue

        pixels[y, x, 0] = colors[color_idx, 0]
        pixels[y, x, 1] = colors[color_idx, 1]
        pixels[y, x, 2] = colors[color_idx, 2]
        filled[packed]  = True
        color_idx      += 1

        for d in range(8):
            ny = y + DY[d]
            nx = x + DX[d]
            if 0 <= ny < H and 0 <= nx < W:
                np_ = ny * W + nx
                if not filled[np_] and not queued[np_]:
                    front[f_size] = np_
                    f_size += 1
                    queued[np_] = True

    return pixels


print("Step 4: Compiling BFS (~30s first time)...")
t = time.time()
_dc = np.zeros((64*64, 3), dtype=np.uint8)
_ds = np.ones(64*64, dtype=np.float32)
crystal_bfs(_dc, _ds, 32, 32, 64, 64, 1, 42)
print(f"  Compiled in {time.time()-t:.1f}s")

print("  Running on 4096×4096...")
t = time.time()
pixels = crystal_bfs(colors, score_flat, seed_y, seed_x,
                     WIDTH, HEIGHT, TOURNAMENT_K, RANDOM_SEED)
elapsed = time.time()-t
print(f"  Done in {elapsed:.1f}s  ({N/elapsed/1e3:.0f}K px/s)")

# ── Step 5: save ──────────────────────────────────────────────
print(f"\nStep 5: Saving → {OUT_PATH}")
Image.fromarray(pixels, 'RGB').save(OUT_PATH)

try:
    from google.colab import files
    files.download(OUT_PATH)
    print("  Download triggered!")
except ImportError:
    print("  Saved locally.")

print("Done ✓")
