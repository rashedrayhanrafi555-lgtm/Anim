import json, math, subprocess, sys
import matplotlib
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

W, H, FPS = 1080, 1920, 24
TOTAL = 90.0
NFRAMES = int(TOTAL * FPS)

FONTS = matplotlib.get_data_path() + "/fonts/ttf/"
F_BOLD = FONTS + "DejaVuSans-Bold.ttf"
F_REG = FONTS + "DejaVuSans.ttf"
font_cap = ImageFont.truetype(F_BOLD, 54)
font_title = ImageFont.truetype(F_BOLD, 44)
font_small = ImageFont.truetype(F_REG, 30)

# ---------- load narration ----------
data = json.load(open("/mnt/vibefs/uploads/d3b627b2-13aa-4aa0-9a43-bc84b6495bb6/Nkoz9ZoX-The_king_eng.json"))
words = [w for w in data["segments"][0]["words"] if w["text"].strip()]

# caption chunks: <=42 chars, break at punctuation
chunks = []
cur = []
for w in words:
    cur.append(w)
    t = " ".join(x["text"].strip() for x in cur)
    if len(t) > 42 or (w["text"].strip().endswith((".", "!", "?")) and len(cur) > 2):
        chunks.append({"words": cur, "text": t, "t0": cur[0]["start_time"], "t1": cur[-1]["end_time"]})
        cur = []
if cur:
    chunks.append({"words": cur, "text": " ".join(x["text"].strip() for x in cur), "t0": cur[0]["start_time"], "t1": cur[-1]["end_time"]})
for c in chunks:
    c["t1"] = min(c["t1"] + 0.35, 89.9)

# ---------- scenes ----------
CUTS = [0.0, 3.44, 7.42, 12.09, 21.00, 25.77, 31.70, 35.55, 41.22, 46.92, 52.85, 58.21, 67.06, 73.99, 79.44, TOTAL]
SCENES = [f"img/s{i+1:02d}.jpg" for i in range(15)]
FADE = 0.6

def ease(u):
    return u * u * (3 - 2 * u)

# ---------- precompute scene assets ----------
def make_scene_assets(path, idx):
    im = Image.open(path).convert("RGB")
    # background: cover-crop to 16:9-ish, blur, darken, 1.5x canvas for drift
    bw, bh = int(1920 * 16 / 9 * 1.5), int(1920 * 1.5)  # 5120x2880 too big; use scale factor different
    bw, bh = 1920, 2880
    scale = max(bw / im.width, bh / im.height)
    bg = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
    cx, cy = bg.width // 2, bg.height // 2
    bg = bg.crop((cx - bw // 2, cy - bh // 2, cx + bw // 2, cy + bh // 2))
    bg = bg.filter(ImageFilter.GaussianBlur(28))
    bg = ImageEnhance.Brightness(bg).enhance(0.38)
    bg = ImageEnhance.Color(bg).enhance(0.85)
    # band: 1.2x of final 1080x817
    bs = 1180 / im.width * 1.2  # slight margin
    band = im.resize((int(im.width * bs), int(im.height * bs)), Image.LANCZOS)
    return {"bg": bg, "band": band}

assets = [make_scene_assets(p, i) for i, p in enumerate(SCENES)]

BAND_W, BAND_H = 1080, 817
BAND_Y = 470

def band_frame(a, u, zoom_in):
    band = a["band"]
    if zoom_in:
        z = 1.02 + 0.14 * ease(u)
        off = ease(u)
    else:
        z = 1.16 - 0.14 * ease(u)
        off = 1 - ease(u)
    win_w = band.width / z
    win_h = BAND_H * 1.2 / z
    x0 = (band.width - win_w) / 2
    y0 = (band.height - win_h) * (0.15 + 0.7 * off)
    crop = band.crop((int(x0), int(y0), int(x0 + win_w), int(y0 + win_h))).resize((BAND_W, BAND_H), Image.BILINEAR)
    return crop

def bg_frame(a, u):
    bg = a["bg"]
    z = 1.0 + 0.05 * ease(u)
    win_w = bg.width / z
    win_h = bg.height / z
    x0 = (bg.width - win_w) / 2
    y0 = (bg.height - win_h) / 2
    crop = bg.crop((int(x0), int(y0), int(x0 + win_w), int(y0 + win_h))).resize((W, H), Image.BILINEAR)
    return crop

# ---------- overlays (cached surfaces) ----------
def wrap_text(text, font, maxw):
    lines, line = [], ""
    for wd in text.split():
        trial = (line + " " + wd).strip()
        if font.getbbox(trial)[2] <= maxw or not line:
            line = trial
        else:
            lines.append(line)
            line = wd
    if line:
        lines.append(line)
    return lines

def caption_surface(text):
    lines = wrap_text(text, font_cap, 920)
    lh = font_cap.getbbox("Ag")[3] + 16
    img = Image.new("RGBA", (920, lh * len(lines)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i, ln in enumerate(lines):
        tw = d.textbbox((0, 0), ln, font=font_cap)[2]
        x = (920 - tw) // 2
        d.text((x + 3, i * lh + 3), ln, font=font_cap, fill=(0, 0, 0, 200))
        d.text((x, i * lh), ln, font=font_cap, fill=(255, 255, 255, 235))
    return img

cap_imgs = [caption_surface(c["text"]) for c in chunks]

def active_chunk(t):
    for c, img in zip(chunks, cap_imgs):
        if c["t0"] - 0.1 <= t < c["t1"]:
            return img
    return None

# bottom scrim + top gradient (static, once)
scrim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sd = ImageDraw.Draw(scrim)
for y in range(H - 560, H):
    a = int(150 * (1 - (H - y) / 560))
    sd.line([(0, y), (W, y)], fill=(10, 10, 18, a))
for y in range(0, 300):
    a = int(120 * (1 - y / 300))
    sd.line([(0, y), (W, y)], fill=(10, 10, 18, a))

TITLE = "THE KING WHO COULD NOT BE POISONED"
tw = ImageDraw.Draw(Image.new("RGB", (8, 8))).textbbox((0, 0), TITLE, font=font_title)[2]

MUST = (212, 175, 55, 255)

# ---------- render loop ----------
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
ff = subprocess.Popen(
    [FF, "-y", "-loglevel", "error",
     "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
     "-i", "/mnt/vibefs/uploads/d3b627b2-13aa-4aa0-9a43-bc84b6495bb6/9OK0mfJC-The king.mp3",
     "-af", "apad,atrim=0:%.2f" % TOTAL,
     "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
     "-c:a", "aac", "-b:a", "160k", "-t", "%.2f" % TOTAL, "-r", str(FPS),
     "the_king_9x16.mp4"],
    stdin=subprocess.PIPE)

for f in range(NFRAMES):
    t = f / FPS
    scene = 0
    for i, c in enumerate(CUTS[:-1]):
        if t >= c:
            scene = i
    cut = CUTS[scene]
    u = min(max((t - cut) / max(CUTS[scene + 1] - cut - FADE, 1e-6), 0.0), 1.0)
    frac = 0 if scene % 2 == 0 else 1
    base = bg_frame(assets[scene], u).convert("RGB")
    img_c = band_frame(assets[scene], u, zoom_in=(scene % 2 == 0)).convert("RGB")
    if scene + 1 < len(CUTS) - 1 and t < cut + FADE and scene > 0:
        a = ease((t - cut) / FADE)
        prev = scene - 1
        uprev = min(max((t - CUTS[prev]) / max(CUTS[prev + 1] - CUTS[prev] - FADE, 1e-6), 0), 1)
        prev_bg = bg_frame(assets[prev], uprev).convert("RGB")
        prev_band = band_frame(assets[prev], uprev, zoom_in=(prev % 2 == 0)).convert("RGB")
        base = Image.blend(prev_bg, base, a)
        img_c = Image.blend(prev_band, img_c, a)

    img = base.copy()
    img.paste(img_c, (0, BAND_Y))
    d = ImageDraw.Draw(img, "RGBA")
    d.line([(0, BAND_Y - 5), (W, BAND_Y - 5)], fill=MUST)
    d.line([(0, BAND_Y + BAND_H + 5), (W, BAND_Y + BAND_H + 5)], fill=MUST)
    img.paste(scrim, (0, 0), scrim)
    d = ImageDraw.Draw(img, "RGBA")
    # title
    d.text(((W - tw) // 2 + 2, 152 + 2), TITLE, font=font_title, fill=(0, 0, 0, 180))
    d.text(((W - tw) // 2, 152), TITLE, font=font_title, fill=MUST)
    # caption
    ci = active_chunk(t)
    if ci is not None:
        img.paste(ci, ((W - ci.width) // 2, H - 560 + (520 - ci.height) // 2 - 30), ci)
    # fade in/out
    if t < FADE:
        k = t / FADE
        d.rectangle([0, 0, W, H], fill=(0, 0, 0, int(255 * (1 - k))))
    rem = TOTAL - t
    if rem < 1.4:
        d.rectangle([0, 0, W, H], fill=(0, 0, 0, int(255 * (1 - rem / 1.4))))
    ff.stdin.write(img.tobytes())
    if f % 240 == 0:
        print(f"frame {f}/{NFRAMES}", flush=True)

ff.stdin.close()
ff.wait()
print("done rc=", ff.returncode)
