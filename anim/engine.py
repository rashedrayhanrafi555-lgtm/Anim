"""2D animation engine: Pillow draws frames, ffmpeg encodes the video."""
import math
import subprocess

from PIL import Image, ImageDraw
from PIL import ImageFont


def get_font(size=48):
    for name in ("DejaVuSans-Bold", "DejaVuSans", "Arial"):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            pass
    return ImageFont.load_default()


def lerp(a, b, f):
    return a + (b - a) * f


def lerp_color(c1, c2, f):
    return tuple(int(lerp(a, b, f)) for a, b in zip(c1, c2))


def clamp01(v):
    return max(0.0, min(1.0, v))


def linear(t):
    return clamp01(t)


def ease_in_out(t):
    t = clamp01(t)
    return 3 * t * t - 2 * t * t * t


def ease_out_back(t):
    t = clamp01(t)
    s = 1.70158
    return 1 + (s + 1) * (t - 1) ** 3 + s * (t - 1) ** 2


def ease_out(t):
    t = clamp01(t)
    return 1 - (1 - t) ** 3


def segment(t, start, duration):
    """Local progress [0, 1] within a time span."""
    if duration <= 0:
        return 0.0
    return clamp01((t - start) / duration)


class Scene:
    """Subclass and override draw(). Then render('out.mp4')."""

    def setup(self):
        self.width = 1280
        self.height = 720
        self.fps = 30
        self.duration = 6.0

    def draw(self, t, img, dr):
        raise NotImplementedError

    def render(self, path, crf=18):
        w, h, fps = self.width, self.height, self.fps
        total = int(self.duration * fps)
        cmd = [
            subprocess_kwargs()["ffmpeg"], "-y",
            "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{w}x{h}", "-r", str(fps), "-i", "-",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", str(crf), "-movflags", "+faststart", path,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for i in range(total):
            t = i / fps
            frame = Image.new("RGB", (w, h))
            dr = ImageDraw.Draw(frame)
            self.draw(t, frame, dr)
            proc.stdin.write(frame.tobytes())
            if i % (total // 10 or 1) == 0:
                print(f"  frame {i}/{total} ({100 * i / total:.0f}%)")
        proc.stdin.close()
        proc.wait()
        if proc.returncode != 0:
            raise RuntimeError("ffmpeg failed")
        print(f"done: {path} ({total} frames, {self.duration}s @ {fps}fps)")


def subprocess_kwargs():
    try:
        import imageio_ffmpeg
        return {"ffmpeg": imageio_ffmpeg.get_ffmpeg_exe()}
    except ImportError:
        return {"ffmpeg": "ffmpeg"}
