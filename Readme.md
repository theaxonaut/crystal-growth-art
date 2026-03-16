# 🔮 All-RGB Crystal Growth

> *Every pixel a different color. 16,777,216 of them. Growing like a crystal from a single seed.*

A Python art project that generates a **4096×4096 image containing every possible 8-bit RGB color exactly once** — no color repeated, none missing. The colors are placed using a crystal growth algorithm that makes the image look like a living nebula or a starburst explosion rather than random noise.

---

## ✨ Inspiration

This project was directly inspired by the Corridor Crew video:

**[This art TRICKS Your Eyes Into Seeing Color](https://youtu.be/SxsN6FRXMWQ)**

The video explores how images containing every possible color can fool your visual system into perceiving colors that aren't really there. Watching it made me want to build my own version and push the shapes further — into rays, nebulae, and organic crystal forms.

---

## 🖼️ How It Works

### The Core Idea

There are exactly **256 × 256 × 256 = 16,777,216** colors in 8-bit RGB space. A 4096×4096 image has exactly 4096² = 16,777,216 pixels. So it's theoretically possible to make an image where every pixel is a completely unique color.

The challenge is: *in what order do you place them?* Random order looks like TV static. The trick is placing perceptually similar colors next to each other so the image has smooth gradients and organic shapes.

### Step 1 — Morton Curve Ordering

All 16M colors are sorted by their **3D Morton code** (Z-order curve). This interleaves the bits of R, G, and B:

```
Morton(R, G, B) = ...B₇G₇R₇ B₆G₆R₆ B₅G₅R₅ ...
```

Colors that are close together in RGB space end up close together in the sorted list. This means when the crystal grows and places colors in sequence, neighboring pixels get perceptually similar colors — producing smooth gradients rather than noise.

### Step 2 — Crystal Growth BFS

A single seed pixel is planted (you choose where). Then a **breadth-first search frontier** expands outward, filling one pixel at a time. At each step, a pixel is chosen from the frontier using a **tournament selector**:

- Sample K random candidates from the frontier
- Pick the one with the highest **score** for the current shape mode
- Fill it with the next color in the Morton-sorted sequence

This random-but-guided selection is what creates the organic, branching crystal arms rather than smooth circles.

### Step 3 — Shape Modes

The score map that guides the tournament selector determines the overall shape:

| Mode | How the score map works |
|---|---|
| `organic` | Uniform scores — pure random walk, flowing painterly blobs |
| `rays` | Scores peak along evenly-spaced angular directions from the seed — starburst arms |
| `nebula` | Fractional Brownian Motion (layered rotated sine waves) — cloudy drifting masses |

---

## 🚀 Quick Start

### Google Colab (recommended)

1. Open [Google Colab](https://colab.research.google.com)
2. Create a new notebook
3. Paste the contents of `crystal_with_nebula.py` into a cell
4. Run it — the image will download automatically when done

No GPU required. Expected time: **~2 minutes** on any Colab runtime.

### Local

```bash
pip install numpy pillow numba
python crystal_with_nebula.py
```

---

## ⚙️ Settings

All editable parameters are grouped at the top of the script under a clearly marked section. Everything below that is hands-off.

```python
RANDOM_SEED = 42      # change for a completely different crystal

SEED_X      = 0.5     # where the crystal starts (0.0–1.0)
SEED_Y      = 0.5

SHAPE_MODE  = "nebula"  # "organic" | "rays" | "nebula"
NUM_RAYS    = 16        # arms in rays mode
SHARPNESS   = 8.0       # 1 = fuzzy    8 = clear    15 = laser thin

# nebula mode only:
NEBULA_SCALE    = 1.5   # cloud size (0.5 = huge, 3.0 = fine wisps)
NEBULA_OCTAVES  = 6     # detail layers (3 = smooth, 9 = chaotic)
NEBULA_CONTRAST = 3.0   # edge crispness (1 = soft fog, 6 = harsh)
```

### Shape mode quick reference

**`organic`** — uniform random walk. Flowing, painterly explosion of color. Seed position dramatically changes the composition.

**`rays`** — starburst from the seed. Increase `NUM_RAYS` for more arms, increase `SHARPNESS` for tighter laser-thin rays.

**`nebula`** — guided by procedural noise. Produces rolling clouds with dark voids between them, like a space nebula. `NEBULA_SCALE` is the biggest visual lever — try `0.5` for huge cloudscapes, `3.0` for fine atmospheric wisps.

### Good starting combos to try

| Look | Settings |
|---|---|
| Classic explosion | `SHAPE_MODE="organic"`, `SHARPNESS=1` |
| Sharp starburst | `SHAPE_MODE="rays"`, `NUM_RAYS=16`, `SHARPNESS=10` |
| Flower | `SHAPE_MODE="rays"`, `NUM_RAYS=6`, `SHARPNESS=5` |
| Deep space nebula | `SHAPE_MODE="nebula"`, `NEBULA_SCALE=1.0`, `NEBULA_OCTAVES=6`, `NEBULA_CONTRAST=2.5` |
| Stormy clouds | `SHAPE_MODE="nebula"`, `NEBULA_SCALE=0.6`, `NEBULA_OCTAVES=8`, `NEBULA_CONTRAST=1.5` |
| Off-center drama | `SEED_X=0.2`, `SEED_Y=0.8`, any mode |

---

## 🔬 Technical Notes

**Why Numba?** The BFS loop touches 16 million pixels sequentially — it's fundamentally not parallelisable at the pixel level because each step depends on the frontier state. Python's interpreter overhead alone would make this take 30+ minutes. `@njit` compiles the loop to native machine code, bringing it down to ~2 minutes. The first run takes ~30 seconds to compile; subsequent runs are instant.

**Why Morton ordering?** Other orderings were tried: HSV sort, Hilbert curve, random. Morton is the sweet spot — it's fast to compute (just bit interleaving), and produces smooth enough gradients that the crystal looks painterly rather than noisy, without being so smooth that it looks like a simple gradient.

**Why a single seed?** Multiple seeds produce "grain boundaries" where separate crystals collide — a cool effect on its own, but a single seed gives one unified organism growing outward, which lets the shape modes express themselves more cleanly.

**Image size:** 4096×4096 is both the minimum needed to hold all 16M colors *and* a standard wallpaper resolution that fills a laptop or desktop screen.

---

## 📁 Files

| File | Description |
|---|---|
| `crystal_with_nebula.py` | Main script — organic, rays, and nebula modes |

---

## 📄 License

MIT — do whatever you want with it. If you make something cool, share it.

---

## 🙏 Credits

Inspired by the Corridor Crew video [This art TRICKS Your Eyes Into Seeing Color](https://youtu.be/SxsN6FRXMWQ).

The crystal growth algorithm concept has been explored by various generative artists — notably [Jared Tarbell](http://www.complexification.net) and the broader allRGB community at [allrgb.com](https://allrgb.com).
